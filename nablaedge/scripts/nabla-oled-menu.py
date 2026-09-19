#!/usr/bin/env python3
"""
OLED Root Shell for nabla-edge.

Manages the OLED display with multiple apps:
  - Reloj (clock/idle) — default home screen with ∇ logo
  - Config (menu) — nabla-config menu tree navigation
  - (Future apps) — extension point

Navigated via EC11 rotary encoder (GPIO17/27/22).

Production-ready implementation for Phase 2.
See: docs/pi-config-menu/OLED-MENU-DESIGN.md
"""

from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional
import subprocess
import time
import threading
import signal
import sys

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
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
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
TEXT_X = 12
CLOCK_X = 100
CARET_CHAR = "▶"

# --- Idle timeout ---
IDLE_TIMEOUT = 60  # seconds

# --- Nabla triangle logo points (scaled for title region) ---
# Simple triangle ∇ approximation for 128x64
NABLA_POINTS = [(44, 14), (54, 28), (34, 28)]


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
    submenu: Optional[str] = None
    handler: Optional[str] = None
    description: Optional[str] = None


@dataclass
class MenuItem:
    """A single menu item."""
    id: str
    label: str
    submenu: Optional[str] = None
    action: Optional[str] = None
    state_key: Optional[str] = None
    back: bool = False
    description: Optional[str] = None


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
    action_message: str = ""      # Temporary message after action
    action_message_until: float = 0.0

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

    def set_message(self, msg: str, duration: float = 2.0):
        """Show a temporary message overlay."""
        self.action_message = msg
        self.action_message_until = time.time() + duration

    def clear_message_if_expired(self):
        """Clear message if its display time has passed."""
        if self.action_message and time.time() > self.action_message_until:
            self.action_message = ""


# =============================================================================
# OLED Shell (Main Controller)
# =============================================================================

class OledShell:
    """Root shell managing multiple OLED apps."""

    def __init__(self, tree: MenuTree, device, font_small=None, font_title=None):
        self.tree = tree
        self.device = device
        self.state = ShellState()
        self.font_small = font_small
        self.font_title = font_title
        self._lock = threading.Lock()

    @property
    def root_apps(self) -> list[RootApp]:
        return self.tree.root_apps

    @property
    def current_menu(self) -> Optional[Menu]:
        if not self.state.menu_stack:
            return None
        key = self.state.menu_stack[-1]
        return self.tree.menus.get(key)

    # --- Input Handlers ---

    def on_rotate(self, delta: int):
        """Handle encoder rotation."""
        with self._lock:
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
        with self._lock:
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
        with self._lock:
            # Clear expired action message
            self.state.clear_message_if_expired()

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
        new_index = self.state.menu_index + delta
        self.state.menu_index = max(0, min(n - 1, new_index))

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

        # Handle exit action specially
        if item.action == "exit":
            self._exit_to_root()
            return

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
            msg = execute_action(item.action, item.state_key)
            if msg:
                self.state.set_message(msg)

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

    def _draw_status_bar(self, draw, show_menu_title: str = None):
        """Draw the status bar with optional title and clock."""
        clock = time.strftime("%H:%M")
        font = self.font_small

        # Optional left-aligned menu title (abbreviated if needed)
        if show_menu_title:
            # Truncate title if too long
            title = show_menu_title[:12]
            draw.text((CARET_X, 1), title, fill=1, font=font)

        # Right-aligned clock
        draw.text((CLOCK_X, 1), clock, fill=1, font=font)

    def _draw_nabla_logo(self, draw):
        """Draw the nabla (∇) triangle logo."""
        draw.polygon(NABLA_POINTS, outline=1, fill=0)

    def _render_clock(self):
        """Render Reloj (clock/idle) screen with nabla logo."""
        from PIL import Image, ImageDraw

        image = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 0)
        draw = ImageDraw.Draw(image)

        # Status bar with clock only
        self._draw_status_bar(draw)

        # Nabla logo triangle
        self._draw_nabla_logo(draw)

        # Title: "nabla.net" next to logo
        if self.font_title:
            draw.text((60, 16), "nabla.net", fill=1, font=self.font_title)
        else:
            draw.text((60, 18), "nabla.net", fill=1)

        # Subtitle: "Edge Node"
        if self.font_small:
            draw.text((64, REGION_SUBTITLE_Y + 2), "Edge Node", fill=1, font=self.font_small, anchor="mm")
        else:
            draw.text((44, REGION_SUBTITLE_Y + 2), "Edge Node", fill=1)

        self.device.display(image)

    def _render_root_menu(self):
        """Render root shell app selector."""
        from PIL import Image, ImageDraw

        image = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 0)
        draw = ImageDraw.Draw(image)

        # Status bar
        self._draw_status_bar(draw)

        # Title: "nabla.net"
        if self.font_title:
            draw.text((64, REGION_TITLE_Y + 8), "nabla.net", fill=1, font=self.font_title, anchor="mm")
        else:
            draw.text((40, REGION_TITLE_Y + 6), "nabla.net", fill=1)

        # App list in body region
        font = self.font_small
        for i, app in enumerate(self.root_apps[:VISIBLE_ITEMS]):
            y = REGION_BODY_Y + (i * MENU_ITEM_HEIGHT)

            if i == self.state.root_index:
                draw.text((CARET_X, y), CARET_CHAR, fill=1, font=font)

            draw.text((TEXT_X, y), app.label, fill=1, font=font)

        self.device.display(image)

    def _render_config_menu(self):
        """Render nabla-config menu tree."""
        from PIL import Image, ImageDraw

        menu = self.current_menu
        if not menu:
            return

        image = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 0)
        draw = ImageDraw.Draw(image)

        # Status bar with abbreviated menu path
        self._draw_status_bar(draw)

        # Title: current menu label
        if self.font_title:
            draw.text((64, REGION_TITLE_Y + 8), menu.label, fill=1, font=self.font_title, anchor="mm")
        else:
            draw.text((20, REGION_TITLE_Y + 6), menu.label, fill=1)

        # Scroll indicator if needed
        font = self.font_small
        total = len(menu.items)
        if total > VISIBLE_ITEMS:
            # Show scroll position indicator
            if self.state.scroll_offset > 0:
                draw.text((120, REGION_BODY_Y - 2), "^", fill=1, font=font)
            if self.state.scroll_offset + VISIBLE_ITEMS < total:
                draw.text((120, REGION_BODY_Y + REGION_BODY_H - 2), "v", fill=1, font=font)

        # Menu items
        for i in range(VISIBLE_ITEMS):
            item_idx = self.state.scroll_offset + i
            if item_idx >= len(menu.items):
                break

            item = menu.items[item_idx]
            y = REGION_BODY_Y + (i * MENU_ITEM_HEIGHT)

            if item_idx == self.state.menu_index:
                draw.text((CARET_X, y), CARET_CHAR, fill=1, font=font)

            # Build label with optional state indicator
            label = item.label
            if item.state_key:
                val = read_accessory_state(item.state_key)
                label = f"{label} [{val}]"

            # Truncate if too long
            max_chars = 14
            if len(label) > max_chars:
                label = label[:max_chars - 1] + "…"

            draw.text((TEXT_X, y), label, fill=1, font=font)

        # Overlay action message if set
        if self.state.action_message:
            # Draw message box centered
            msg = self.state.action_message
            box_w = min(len(msg) * 6 + 8, 120)
            box_h = 16
            box_x = (DISPLAY_WIDTH - box_w) // 2
            box_y = (DISPLAY_HEIGHT - box_h) // 2
            draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=0, outline=1)
            draw.text((64, box_y + 4), msg, fill=1, font=font, anchor="mt")

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
                    extra = ""
                    if item.state_key:
                        extra = f" [{read_accessory_state(item.state_key)}]"
                    print(f"  {marker} {item.label}{extra}")


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


def write_accessory_state(key: str, value: str) -> bool:
    """Write toggle state to accessories.conf."""
    try:
        conf_path = ACCESSORIES_CONF
        lines = []
        found = False

        if conf_path.exists():
            for line in conf_path.read_text().splitlines():
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}")
                    found = True
                else:
                    lines.append(line)

        if not found:
            lines.append(f"{key}={value}")

        conf_path.parent.mkdir(parents=True, exist_ok=True)
        conf_path.write_text("\n".join(lines) + "\n")
        return True
    except Exception as e:
        print(f"Failed to write accessory state: {e}")
        return False


# Action handlers mapped to subprocess commands or inline logic
ACTION_MAP: dict[str, list[str]] = {
    "network_status": ["nabla-config", "network", "status"],
    "network_cable": ["sudo", "vpn-mode", "cable"],
    "network_ap": ["sudo", "vpn-mode", "ap"],
    "network_cable_ap": ["sudo", "vpn-mode", "cable-ap"],
    "network_off": ["sudo", "vpn-mode", "off"],
    "camera_go2rtc": ["nabla-net", "camera"],
    "info": ["nabla-config", "info"],
    "media_list_disks": ["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"],
    "voice_status": ["docker", "compose", "-f", "/opt/nabla-edge/voice/lva/docker-compose.yml", "ps"],
    "voice_start": ["docker", "compose", "-f", "/opt/nabla-edge/voice/lva/docker-compose.yml", "up", "-d"],
    "voice_stop": ["docker", "compose", "-f", "/opt/nabla-edge/voice/lva/docker-compose.yml", "down"],
}


def execute_action(action: str, state_key: Optional[str] = None) -> str:
    """Execute action via subprocess or inline handler. Returns status message."""
    # Handle toggle actions
    if action.startswith("acc_toggle_"):
        key_map = {
            "acc_toggle_oled": "display_oled",
            "acc_toggle_rotary": "rotary",
            "acc_toggle_large": "display_large",
        }
        key = key_map.get(action, state_key)
        if key:
            current = read_accessory_state(key)
            new_val = "0" if current == "ON" else "1"
            if write_accessory_state(key, new_val):
                return f"{key}: {'ON' if new_val == '1' else 'OFF'}"
        return "Toggle failed"

    # Handle apply OLED action
    if action == "acc_apply_oled":
        try:
            subprocess.run(
                ["systemctl", "restart", "nabla-oled-menu.service"],
                check=True,
                capture_output=True,
                timeout=10
            )
            return "OLED restarted"
        except Exception:
            return "Restart failed"

    # Handle view profile action
    if action == "acc_view":
        # This is informational - just acknowledge
        return "See SSH terminal"

    # Handle mapped subprocess actions
    if action in ACTION_MAP:
        try:
            subprocess.Popen(
                ACTION_MAP[action],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "Running..."
        except Exception as e:
            return f"Error: {e}"

    return f"Unknown: {action}"


def toggle_accessory(key: str) -> None:
    """Toggle an accessory flag in accessories.conf (legacy helper)."""
    current = read_accessory_state(key)
    new_val = "0" if current == "ON" else "1"
    write_accessory_state(key, new_val)


# =============================================================================
# Encoder Input
# =============================================================================

class EncoderInput:
    """Handles rotary encoder input via RPi.GPIO with debouncing."""

    def __init__(self, on_rotate: Callable[[int], None], on_press: Callable[[], None]):
        import RPi.GPIO as GPIO

        self.GPIO = GPIO
        self.on_rotate = on_rotate
        self.on_press = on_press
        self._last_clk = 1
        self._last_dt = 1
        self._last_rotate_time = 0
        self._last_press_time = 0
        self._debounce_rotate = 0.02  # 20ms debounce for rotation
        self._debounce_press = 0.25   # 250ms debounce for press

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Read initial state
        self._last_clk = GPIO.input(PIN_CLK)
        self._last_dt = GPIO.input(PIN_DT)

        GPIO.add_event_detect(
            PIN_CLK, GPIO.BOTH, callback=self._clk_callback, bouncetime=2
        )
        GPIO.add_event_detect(
            PIN_SW, GPIO.FALLING, callback=self._sw_callback, bouncetime=50
        )

    def _clk_callback(self, channel):
        """Handle CLK edge - determine rotation direction."""
        now = time.time()
        if now - self._last_rotate_time < self._debounce_rotate:
            return

        clk = self.GPIO.input(PIN_CLK)
        dt = self.GPIO.input(PIN_DT)

        if clk != self._last_clk:
            self._last_rotate_time = now
            if dt != clk:
                self.on_rotate(1)   # CW = down/next
            else:
                self.on_rotate(-1)  # CCW = up/previous

        self._last_clk = clk
        self._last_dt = dt

    def _sw_callback(self, channel):
        """Handle switch press."""
        now = time.time()
        if now - self._last_press_time < self._debounce_press:
            return

        # Verify switch is actually pressed (active low)
        if self.GPIO.input(PIN_SW) == 0:
            self._last_press_time = now
            self.on_press()

    def cleanup(self):
        """Release GPIO resources."""
        self.GPIO.cleanup()


# =============================================================================
# Main
# =============================================================================

def load_fonts():
    """Load PIL fonts, with fallback to default."""
    font_small = None
    font_title = None

    try:
        from PIL import ImageFont

        # Try to load system fonts
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]

        for font_path in font_paths:
            if Path(font_path).exists():
                font_small = ImageFont.truetype(font_path, 10)
                font_title = ImageFont.truetype(font_path, 14)
                break

        if font_small is None:
            # Use default bitmap font
            font_small = ImageFont.load_default()
            font_title = font_small

    except Exception as e:
        print(f"Font loading warning: {e}")

    return font_small, font_title


def main():
    """Main entry point."""
    # Determine menu tree path
    tree_path = MENU_TREE_PATH if MENU_TREE_PATH.exists() else MENU_TREE_DEV_PATH
    if not tree_path.exists():
        print(f"Menu tree not found: {tree_path}")
        return 1

    # Load menu tree
    try:
        tree = MenuTree.from_yaml(tree_path)
    except Exception as e:
        print(f"Failed to load menu tree: {e}")
        return 1

    # Load fonts
    font_small, font_title = load_fonts()

    # Initialize display
    device = None
    try:
        from luma.core.interface.serial import i2c
        from luma.oled.device import ssd1306

        serial = i2c(port=1, address=0x3C)
        device = ssd1306(serial, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)
        print("OLED initialized (SSD1306 I2C)")
    except ImportError:
        print("luma.oled not installed — dry run mode (text output)")
    except Exception as e:
        print(f"OLED init failed: {e}")
        print("Running in dry-run mode (text output)")

    # Create shell
    shell = OledShell(tree, device, font_small, font_title)

    # Initialize encoder
    encoder = None
    try:
        encoder = EncoderInput(shell.on_rotate, shell.on_press)
        print("Encoder initialized (GPIO17/27/22)")
    except ImportError:
        print("RPi.GPIO not available — encoder disabled")
    except Exception as e:
        print(f"Encoder init failed: {e}")

    # Signal handler for clean shutdown
    def shutdown_handler(sig, frame):
        print("\nShutting down...")
        if encoder:
            encoder.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    # Main loop
    print("OLED menu shell running. Press Ctrl+C to exit.")
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
        print("OLED menu shell stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
