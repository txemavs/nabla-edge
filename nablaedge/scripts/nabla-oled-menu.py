#!/usr/bin/env python3
"""
OLED Root Shell for nabla-edge.

Manages the OLED display with multiple apps:
  - Reloj (clock/idle) — default home screen
  - Config (menu) — nabla-config menu tree
  - (Future apps) — extension point

Navigated via EC11 rotary encoder (GPIO17/27/22).

STUB/SKETCH — not yet production-ready.
See: docs/pi-config-menu/OLED-MENU-DESIGN.md
"""

from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable
import subprocess
import time

# --- Paths ---
MENU_TREE_PATH = Path("/usr/share/nabla-edge/menu_tree.yaml")
MENU_TREE_DEV_PATH = Path(__file__).parent / "menu_tree.yaml"
ACCESSORIES_CONF = Path("/etc/nabla-net/accessories.conf")

# --- Encoder GPIO (BCM numbering) ---
# Matches sticker pinout (partial mode):
#   CLK (A) = GPIO17 (physical pin 11)
#   DT  (B) = GPIO27 (physical pin 13)
#   SW      = GPIO22 (physical pin 15)
PIN_CLK = 17
PIN_DT = 27
PIN_SW = 22

# --- Layout constants from ui/ssd/profiles/128x64.yaml ---
REGION_STATUS_Y = 0
REGION_STATUS_H = 10
REGION_TITLE_Y = 10
REGION_TITLE_H = 22
REGION_SUBTITLE_Y = 32
REGION_SUBTITLE_H = 12
REGION_BODY_Y = 44
REGION_BODY_H = 20
MENU_ITEM_HEIGHT = 10
VISIBLE_ITEMS = 2
CARET_X = 2
TEXT_X = 10
CARET_CHAR = "▶"

# --- Idle timeout ---
IDLE_TIMEOUT = 60  # seconds


# =============================================================================
# OLED Modes (Root Shell)
# =============================================================================

class OledMode(Enum):
    """OLED display modes."""
    RELOJ = "reloj"         # Clock/idle (default home screen)
    ROOT_MENU = "root"      # Root shell app selector
    CONFIG = "config"       # nabla-config menu tree
    # Future: SENSORS, STATUS, etc.


@dataclass
class RootApp:
    """A root shell app definition."""
    id: str
    label: str
    type: str  # "clock", "menu", "app"
    submenu: str | None = None
    handler: str | None = None
    description: str | None = None


@dataclass
class MenuItem:
    """A single menu item."""
    id: str
    label: str
    submenu: str | None = None
    action: str | None = None
    state_key: str | None = None
    back: bool = False
    description: str | None = None


@dataclass
class Menu:
    """A menu with label and items."""
    label: str
    items: list[MenuItem] = field(default_factory=list)


@dataclass
class MenuTree:
    """Complete menu tree with root shell and config menus."""
    version: str
    root_apps: list[RootApp] = field(default_factory=list)
    default_app: str = "reloj"
    menus: dict[str, Menu] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "MenuTree":
        """Load menu tree from YAML file."""
        import yaml
        data = yaml.safe_load(path.read_text())
        
        # Parse root shell
        root_shell = data.get("root_shell", {})
        root_apps = [
            RootApp(
                id=app.get("id", ""),
                label=app.get("label", ""),
                type=app.get("type", "app"),
                submenu=app.get("submenu"),
                handler=app.get("handler"),
                description=app.get("description"),
            )
            for app in root_shell.get("apps", [])
        ]
        default_app = root_shell.get("default", "reloj")
        
        # Parse config menus
        menus = {}
        for key, menu_data in data.get("menus", {}).items():
            items = [
                MenuItem(
                    id=item.get("id", ""),
                    label=item.get("label", ""),
                    submenu=item.get("submenu"),
                    action=item.get("action"),
                    state_key=item.get("state_key"),
                    back=item.get("back", False),
                    description=item.get("description"),
                )
                for item in menu_data.get("items", [])
            ]
            menus[key] = Menu(label=menu_data.get("label", key), items=items)
        
        return cls(
            version=data.get("version", "1.0"),
            root_apps=root_apps,
            default_app=default_app,
            menus=menus,
        )


# =============================================================================
# Shell State
# =============================================================================

@dataclass
class ShellState:
    """State for root shell and current app."""
    mode: OledMode = OledMode.RELOJ
    root_index: int = 0           # Selected app in root menu
    menu_stack: list = None       # For CONFIG mode: menu navigation
    menu_index: int = 0
    scroll_offset: int = 0
    last_activity: float = 0.0    # For idle timeout
    
    def __post_init__(self):
        if self.menu_stack is None:
            self.menu_stack = ["main"]
        self.last_activity = time.time()
    
    def touch(self):
        """Record user activity (resets idle timer)."""
        self.last_activity = time.time()
    
    def is_idle_timeout(self) -> bool:
        """Check if idle timeout has expired."""
        return time.time() - self.last_activity > IDLE_TIMEOUT


# =============================================================================
# OLED Shell (Main Controller)
# =============================================================================

class OledShell:
    """Root shell managing multiple OLED apps."""
    
    def __init__(self, tree: MenuTree, device):
        self.tree = tree
        self.device = device
        self.state = ShellState()
    
    @property
    def root_apps(self) -> list[RootApp]:
        return self.tree.root_apps
    
    @property
    def current_menu(self) -> Menu | None:
        if not self.state.menu_stack:
            return None
        key = self.state.menu_stack[-1]
        return self.tree.menus.get(key)
    
    # --- Input Handlers ---
    
    def on_rotate(self, delta: int):
        """Handle encoder rotation."""
        self.state.touch()
        
        if self.state.mode == OledMode.RELOJ:
            # Wake from idle → show root menu
            self.state.mode = OledMode.ROOT_MENU
            self.state.root_index = 0
        
        elif self.state.mode == OledMode.ROOT_MENU:
            # Navigate root apps
            n = len(self.root_apps)
            if n > 0:
                self.state.root_index = (self.state.root_index + delta) % n
        
        elif self.state.mode == OledMode.CONFIG:
            # Navigate config menu
            self._navigate_menu(delta)
        
        self.render()
    
    def on_press(self):
        """Handle encoder press."""
        self.state.touch()
        
        if self.state.mode == OledMode.RELOJ:
            # Wake from idle → show root menu
            self.state.mode = OledMode.ROOT_MENU
            self.state.root_index = 0
        
        elif self.state.mode == OledMode.ROOT_MENU:
            # Select app
            if self.root_apps:
                app = self.root_apps[self.state.root_index]
                self._enter_app(app)
        
        elif self.state.mode == OledMode.CONFIG:
            # Select menu item
            self._select_menu_item()
        
        self.render()
    
    def tick(self):
        """Called periodically (e.g., every second)."""
        # Check idle timeout
        if self.state.mode != OledMode.RELOJ and self.state.is_idle_timeout():
            self.state.mode = OledMode.RELOJ
        
        self.render()
    
    # --- App Management ---
    
    def _enter_app(self, app: RootApp):
        """Enter a root shell app."""
        if app.type == "clock":
            self.state.mode = OledMode.RELOJ
        elif app.type == "menu":
            self.state.mode = OledMode.CONFIG
            self.state.menu_stack = [app.submenu or "main"]
            self.state.menu_index = 0
            self.state.scroll_offset = 0
        # Future: elif app.type == "app": call handler
    
    def _exit_to_root(self):
        """Return to root menu from current app."""
        self.state.mode = OledMode.ROOT_MENU
    
    # --- Menu Navigation ---
    
    def _navigate_menu(self, delta: int):
        """Navigate within config menu."""
        menu = self.current_menu
        if not menu:
            return
        
        n = len(menu.items)
        self.state.menu_index = max(0, min(n - 1, self.state.menu_index + delta))
        
        # Adjust scroll to keep selection visible
        if self.state.menu_index < self.state.scroll_offset:
            self.state.scroll_offset = self.state.menu_index
        elif self.state.menu_index >= self.state.scroll_offset + VISIBLE_ITEMS:
            self.state.scroll_offset = self.state.menu_index - VISIBLE_ITEMS + 1
    
    def _select_menu_item(self):
        """Handle selection in config menu."""
        menu = self.current_menu
        if not menu or not menu.items:
            return
        
        item = menu.items[self.state.menu_index]
        
        if item.back:
            if len(self.state.menu_stack) > 1:
                # Go back one level
                self.state.menu_stack.pop()
                self.state.menu_index = 0
                self.state.scroll_offset = 0
            else:
                # At root of config menu → return to root shell
                self._exit_to_root()
            return
        
        if item.submenu and item.submenu in self.tree.menus:
            self.state.menu_stack.append(item.submenu)
            self.state.menu_index = 0
            self.state.scroll_offset = 0
            return
        
        if item.action:
            execute_action(item.action)
    
    # --- Rendering ---
    
    def render(self):
        """Render current mode to display."""
        if self.device is None:
            self._render_text()
            return
        
        if self.state.mode == OledMode.RELOJ:
            self._render_clock()
        elif self.state.mode == OledMode.ROOT_MENU:
            self._render_root_menu()
        elif self.state.mode == OledMode.CONFIG:
            self._render_config_menu()
    
    def _render_clock(self):
        """Render Reloj (clock/idle) screen."""
        from PIL import Image, ImageDraw
        
        image = Image.new("1", (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        clock = time.strftime("%H:%M")
        
        # Status bar: clock right-aligned
        draw.text((100, 1), clock, fill=1)
        
        # Title: ∇ + nabla.net (centered)
        draw.text((64, 18), "nabla.net", fill=1, anchor="mm")
        
        # Subtitle: Edge Node
        draw.text((64, 38), "Edge Node", fill=1, anchor="mm")
        
        self.device.display(image)
    
    def _render_root_menu(self):
        """Render root shell app selector."""
        from PIL import Image, ImageDraw
        
        image = Image.new("1", (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        clock = time.strftime("%H:%M")
        draw.text((100, 1), clock, fill=1)
        
        # Title
        draw.text((64, 18), "nabla.net", fill=1, anchor="mm")
        
        # App list
        for i, app in enumerate(self.root_apps[:VISIBLE_ITEMS]):
            y = REGION_BODY_Y + (i * MENU_ITEM_HEIGHT)
            
            if i == self.state.root_index:
                draw.text((CARET_X, y), CARET_CHAR, fill=1)
            
            draw.text((TEXT_X, y), app.label, fill=1)
        
        self.device.display(image)
    
    def _render_config_menu(self):
        """Render nabla-config menu tree."""
        from PIL import Image, ImageDraw
        
        menu = self.current_menu
        if not menu:
            return
        
        image = Image.new("1", (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        clock = time.strftime("%H:%M")
        draw.text((100, 1), clock, fill=1)
        
        # Title: current menu label
        draw.text((64, 18), menu.label, fill=1, anchor="mm")
        
        # Menu items
        for i in range(VISIBLE_ITEMS):
            item_idx = self.state.scroll_offset + i
            if item_idx >= len(menu.items):
                break
            
            item = menu.items[item_idx]
            y = REGION_BODY_Y + (i * MENU_ITEM_HEIGHT)
            
            if item_idx == self.state.menu_index:
                draw.text((CARET_X, y), CARET_CHAR, fill=1)
            
            # Label with optional toggle state
            label = item.label
            if item.state_key:
                val = read_accessory_state(item.state_key)
                label = f"{label} [{val}]"
            
            draw.text((TEXT_X, y), label, fill=1)
        
        self.device.display(image)
    
    def _render_text(self):
        """Text-mode rendering for dry-run / debugging."""
        print(f"\n--- Mode: {self.state.mode.value} ---")
        
        if self.state.mode == OledMode.RELOJ:
            print(f"  ∇ nabla.net  {time.strftime('%H:%M')}")
        
        elif self.state.mode == OledMode.ROOT_MENU:
            print("Root Apps:")
            for i, app in enumerate(self.root_apps):
                marker = "▶" if i == self.state.root_index else " "
                print(f"  {marker} {app.label}")
        
        elif self.state.mode == OledMode.CONFIG:
            menu = self.current_menu
            if menu:
                print(f"Menu: {menu.label}")
                for i, item in enumerate(menu.items):
                    marker = "▶" if i == self.state.menu_index else " "
                    print(f"  {marker} {item.label}")


# =============================================================================
# Helpers
# =============================================================================

def read_accessory_state(key: str) -> str:
    """Read toggle state from accessories.conf."""
    try:
        for line in ACCESSORIES_CONF.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                val = line.split("=", 1)[1].strip()
                return "ON" if val == "1" else "OFF"
    except FileNotFoundError:
        pass
    return "OFF"


ACTION_MAP: dict[str, list[str]] = {
    "network_status": ["nabla-config", "network-status"],
    "network_cable": ["sudo", "vpn-mode", "cable"],
    "network_ap": ["sudo", "vpn-mode", "ap"],
    "network_cable_ap": ["sudo", "vpn-mode", "cable-ap"],
    "network_off": ["sudo", "vpn-mode", "off"],
    "camera_go2rtc": ["nabla-net", "camera"],
    "info": ["nabla-config", "info"],
}


def execute_action(action: str) -> None:
    """Execute action via subprocess or inline handler."""
    if action.startswith("acc_toggle_"):
        key = action.replace("acc_toggle_", "")
        toggle_accessory(key)
    elif action in ACTION_MAP:
        subprocess.run(ACTION_MAP[action], check=False)
    else:
        print(f"Unknown action: {action}")


def toggle_accessory(key: str) -> None:
    """Toggle an accessory flag in accessories.conf."""
    current = read_accessory_state(key)
    new_val = "0" if current == "ON" else "1"
    subprocess.run(
        ["sudo", "nabla-config-action", "set-accessory", key, new_val],
        check=False,
    )


# =============================================================================
# Encoder Input
# =============================================================================

class EncoderInput:
    """Handles rotary encoder input via RPi.GPIO."""

    def __init__(self, on_rotate: Callable[[int], None], on_press: Callable[[], None]):
        import RPi.GPIO as GPIO

        self.GPIO = GPIO
        self.on_rotate = on_rotate
        self.on_press = on_press
        self._last_clk = 1

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(
            PIN_CLK, GPIO.BOTH, callback=self._clk_callback, bouncetime=5
        )
        GPIO.add_event_detect(
            PIN_SW, GPIO.FALLING, callback=self._sw_callback, bouncetime=200
        )

    def _clk_callback(self, channel):
        clk = self.GPIO.input(PIN_CLK)
        dt = self.GPIO.input(PIN_DT)
        if clk != self._last_clk:
            if dt != clk:
                self.on_rotate(1)  # CW = down
            else:
                self.on_rotate(-1)  # CCW = up
        self._last_clk = clk

    def _sw_callback(self, channel):
        self.on_press()

    def cleanup(self):
        self.GPIO.cleanup()


# =============================================================================
# Main
# =============================================================================

def main():
    """Main entry point."""
    # Determine menu tree path
    tree_path = MENU_TREE_PATH if MENU_TREE_PATH.exists() else MENU_TREE_DEV_PATH
    if not tree_path.exists():
        print(f"Menu tree not found: {tree_path}")
        return 1

    # Load menu tree
    tree = MenuTree.from_yaml(tree_path)

    # Initialize display
    device = None
    try:
        from luma.core.interface.serial import i2c
        from luma.oled.device import ssd1306

        serial = i2c(port=1, address=0x3C)
        device = ssd1306(serial, width=128, height=64)
    except ImportError:
        print("luma.oled not installed — dry run mode")
    except Exception as e:
        print(f"OLED init failed: {e}")

    # Create shell
    shell = OledShell(tree, device)

    # Initialize encoder
    encoder = None
    try:
        encoder = EncoderInput(shell.on_rotate, shell.on_press)
    except ImportError:
        print("RPi.GPIO not available — encoder disabled")
    except Exception as e:
        print(f"Encoder init failed: {e}")

    # Main loop
    try:
        shell.render()
        while True:
            time.sleep(1)
            shell.tick()

    except KeyboardInterrupt:
        pass
    finally:
        if encoder:
            encoder.cleanup()

    return 0


if __name__ == "__main__":
    exit(main())
