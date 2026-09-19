#!/usr/bin/env python3
"""
OLED Menu Renderer for nabla-config.

Renders the menu_tree.yaml on a 128×64 SSD1306 I2C OLED display,
navigated via EC11 rotary encoder.

STUB/SKETCH — not yet production-ready.
See: docs/pi-config-menu/OLED-MENU-DESIGN.md
"""

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
    """Complete menu tree."""
    version: str
    menus: dict[str, Menu] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "MenuTree":
        """Load menu tree from YAML file."""
        import yaml
        data = yaml.safe_load(path.read_text())
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
        return cls(version=data.get("version", "1.0"), menus=menus)


class MenuState:
    """Tracks current menu position and navigation stack."""

    def __init__(self, tree: MenuTree):
        self.tree = tree
        self.stack: list[str] = ["main"]
        self.index: int = 0
        self.scroll_offset: int = 0

    @property
    def current_menu(self) -> Menu:
        return self.tree.menus[self.stack[-1]]

    @property
    def items(self) -> list[MenuItem]:
        return self.current_menu.items

    @property
    def selected_item(self) -> MenuItem:
        return self.items[self.index]

    def navigate(self, delta: int) -> None:
        """Move selection up (negative) or down (positive)."""
        self.index = max(0, min(len(self.items) - 1, self.index + delta))
        # Adjust scroll to keep selection visible
        if self.index < self.scroll_offset:
            self.scroll_offset = self.index
        elif self.index >= self.scroll_offset + VISIBLE_ITEMS:
            self.scroll_offset = self.index - VISIBLE_ITEMS + 1

    def select(self) -> str | None:
        """
        Handle selection of current item.
        Returns action string if action needed, None otherwise.
        """
        item = self.selected_item

        if item.back:
            if len(self.stack) > 1:
                self.stack.pop()
                self.index = 0
                self.scroll_offset = 0
            return None

        if item.submenu and item.submenu in self.tree.menus:
            self.stack.append(item.submenu)
            self.index = 0
            self.scroll_offset = 0
            return None

        return item.action


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


class OledRenderer:
    """Renders menu state to SSD1306 OLED display."""

    def __init__(self, device):
        self.device = device
        # In production, load proper fonts from ui/ssd/tokens.yaml sizes
        # Stub uses PIL default

    def render(self, state: MenuState, clock_str: str = "") -> None:
        """Render current menu state to OLED."""
        from PIL import Image, ImageDraw

        image = Image.new("1", (128, 64), 0)
        draw = ImageDraw.Draw(image)

        # Status bar: clock right-aligned
        if clock_str:
            draw.text((100, 1), clock_str, fill=1)

        # Title: centered in title region
        title = state.current_menu.label
        # Simple centering (proper anchor needs font metrics)
        draw.text((64, 18), title, fill=1, anchor="mm")

        # Body: visible menu items with selection caret
        for i in range(VISIBLE_ITEMS):
            item_idx = state.scroll_offset + i
            if item_idx >= len(state.items):
                break

            item = state.items[item_idx]
            y = REGION_BODY_Y + (i * MENU_ITEM_HEIGHT)

            # Selection caret
            if item_idx == state.index:
                draw.text((CARET_X, y), CARET_CHAR, fill=1)

            # Item label with optional toggle state
            label = item.label
            if item.state_key:
                val = read_accessory_state(item.state_key)
                label = f"{label} [{val}]"

            draw.text((TEXT_X, y), label, fill=1)

        self.device.display(image)

    def render_idle(self, clock_str: str = "") -> None:
        """Render idle/home screen (clock mode)."""
        from PIL import Image, ImageDraw

        image = Image.new("1", (128, 64), 0)
        draw = ImageDraw.Draw(image)

        # Status bar: clock
        if clock_str:
            draw.text((100, 1), clock_str, fill=1)

        # Title: branding
        draw.text((64, 18), "nabla.net", fill=1, anchor="mm")

        # Subtitle
        draw.text((64, 38), "Edge Node", fill=1, anchor="mm")

        self.device.display(image)


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


# --- Action Handlers ---

ACTION_MAP: dict[str, list[str]] = {
    "network_status": ["nabla-config", "network-status"],
    "network_cable": ["sudo", "vpn-mode", "cable"],
    "network_ap": ["sudo", "vpn-mode", "ap"],
    "network_cable_ap": ["sudo", "vpn-mode", "cable-ap"],
    "network_off": ["sudo", "vpn-mode", "off"],
    "camera_go2rtc": ["nabla-net", "camera"],
    "info": ["nabla-config", "info"],
    # Accessories toggle actions handled separately
}


def execute_action(action: str) -> None:
    """Execute action via subprocess or inline handler."""
    if action.startswith("acc_toggle_"):
        key = action.replace("acc_toggle_", "")
        toggle_accessory(key)
    elif action in ACTION_MAP:
        subprocess.run(ACTION_MAP[action], check=False)
    else:
        # Unknown action — log or ignore
        print(f"Unknown action: {action}")


def toggle_accessory(key: str) -> None:
    """Toggle an accessory flag in accessories.conf."""
    current = read_accessory_state(key)
    new_val = "0" if current == "ON" else "1"
    # This would need proper implementation to update the file
    subprocess.run(
        ["sudo", "nabla-config-action", "set-accessory", key, new_val],
        check=False,
    )


# --- Main Loop ---


def main():
    """Main entry point."""
    # Determine menu tree path
    tree_path = MENU_TREE_PATH if MENU_TREE_PATH.exists() else MENU_TREE_DEV_PATH
    if not tree_path.exists():
        print(f"Menu tree not found: {tree_path}")
        return 1

    # Load menu
    tree = MenuTree.from_yaml(tree_path)
    state = MenuState(tree)

    # Initialize display
    try:
        from luma.core.interface.serial import i2c
        from luma.oled.device import ssd1306

        serial = i2c(port=1, address=0x3C)
        device = ssd1306(serial, width=128, height=64)
    except ImportError:
        print("luma.oled not installed — dry run mode")
        device = None
    except Exception as e:
        print(f"OLED init failed: {e}")
        device = None

    if device is None:
        print("Running in dry-run mode (no display)")
        # Just print menu for testing
        print(f"Menu: {state.current_menu.label}")
        for i, item in enumerate(state.items):
            marker = ">" if i == state.index else " "
            print(f"  {marker} {item.label}")
        return 0

    renderer = OledRenderer(device)

    # Idle/menu mode tracking
    idle_mode = True
    last_activity = time.time()
    IDLE_TIMEOUT = 60  # seconds

    def on_rotate(delta: int):
        nonlocal idle_mode, last_activity
        idle_mode = False
        last_activity = time.time()
        state.navigate(delta)
        renderer.render(state, time.strftime("%H:%M"))

    def on_press():
        nonlocal idle_mode, last_activity
        idle_mode = False
        last_activity = time.time()
        action = state.select()
        if action == "exit":
            idle_mode = True
        elif action:
            execute_action(action)
        renderer.render(state, time.strftime("%H:%M"))

    # Initialize encoder
    try:
        encoder = EncoderInput(on_rotate, on_press)
    except ImportError:
        print("RPi.GPIO not available — encoder disabled")
        encoder = None

    try:
        # Initial render
        renderer.render_idle(time.strftime("%H:%M"))

        while True:
            time.sleep(1)

            # Check for idle timeout
            if not idle_mode and (time.time() - last_activity) > IDLE_TIMEOUT:
                idle_mode = True

            # Refresh display (clock update)
            clock = time.strftime("%H:%M")
            if idle_mode:
                renderer.render_idle(clock)
            else:
                renderer.render(state, clock)

    except KeyboardInterrupt:
        pass
    finally:
        if encoder:
            encoder.cleanup()

    return 0


if __name__ == "__main__":
    exit(main())
