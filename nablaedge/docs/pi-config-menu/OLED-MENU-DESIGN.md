# OLED nabla-config Menu — Design Document

Mirror the whiptail/CLI `nabla-config` menu on the Pi's I2C OLED display, navigated via rotary encoder.

---

## 1. Overview

### Problem

`nabla-config` today is a terminal-only whiptail menu. For headless Pi nodes with a small OLED and rotary encoder, there's no way to navigate configuration without SSH.

### Solution

A Python OLED renderer that:

1. Displays the same menu tree as `nabla-config`
2. Accepts rotary encoder input (rotate = navigate, press = select)
3. Shares a single source of truth for the menu structure

### Ownership Split (Confirmed with Spui)

| Component | Owner | Notes |
|-----------|-------|-------|
| `nabla-config` menu tree | **Edge** | `menu_tree.yaml` — single source of truth |
| Pi encoder input (GPIO17/27/22) | **Edge** | BCM pinout, internal pull-ups |
| Python OLED renderer | **Edge** | Consumes menu tree, renders list |
| Menu ↔ OLED sync process | **Edge** | Contributor checklist, CI validation |
| Tiny OLED chrome contract | **Spui** | App supplies list only; shell draws ▶, high-contrast, nabla branding |
| Keyboard component | **Spui** | `components/keyboard/` in nabla-esp-ui |

> **Reference**: nabla-esp-ui PRs [#19](https://github.com/txemavs/nabla-esp-ui/pull/19), [#21](https://github.com/txemavs/nabla-esp-ui/pull/21) on main.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SINGLE SOURCE OF TRUTH                         │
│                                                                         │
│   nablaedge/scripts/menu_tree.yaml (or menu_tree.json)                 │
│                                                                         │
│   Defines:                                                              │
│     - Menu hierarchy (items, submenus, back)                           │
│     - Labels for display                                                │
│     - Action identifiers (mapped to shell functions / Python calls)    │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│   nabla-config (bash)   │       │  nabla-oled-menu.py     │
│                         │       │  (Python OLED renderer) │
│ - Reads menu_tree.yaml  │       │                         │
│ - Renders via whiptail  │       │ - Reads menu_tree.yaml  │
│ - Executes shell funcs  │       │ - Renders on 128×64     │
│                         │       │ - Encoder navigation    │
└─────────────────────────┘       │ - Executes via subprocess│
                                  └─────────────────────────┘
```

### Key Principle

**One menu definition, two renderers.** When the bash menu changes, the YAML changes, and both displays update.

---

## 3. Menu Model — `menu_tree.yaml`

A structured YAML file defining the complete menu hierarchy.

### Location

```
/usr/share/nabla-edge/menu_tree.yaml   # Installed location
nablaedge/scripts/menu_tree.yaml       # Source repo location
```

### Schema

```yaml
version: "1.0"
menus:
  main:
    label: "Nabla Config"
    items:
      - id: network
        label: "Network"
        submenu: network
      - id: media
        label: "Media (USB/SD)"
        submenu: media
      - id: accessories
        label: "Accessories"
        submenu: accessories
      - id: camera
        label: "Camera"
        action: camera_go2rtc
      - id: voice
        label: "Voice Satellite"
        submenu: voice
      - id: exit
        label: "Exit"
        action: exit

  network:
    label: "Network"
    items:
      - id: status
        label: "Status"
        action: network_status
      - id: cable
        label: "CABLE"
        action: network_cable
      - id: ap
        label: "AP"
        action: network_ap
      - id: cable_ap
        label: "CABLE-AP"
        action: network_cable_ap
      - id: off
        label: "OFF"
        action: network_off
      - id: back
        label: "← Back"
        back: true

  accessories:
    label: "Accessories"
    items:
      - id: oled
        label: "OLED I2C"
        action: acc_toggle_oled
        state_key: display_oled
      - id: rotary
        label: "Rotary Encoder"
        action: acc_toggle_rotary
        state_key: rotary
      - id: large
        label: "Large SPI"
        action: acc_toggle_large
        state_key: display_large
      - id: apply_oled
        label: "Apply OLED now"
        action: acc_apply_oled
      - id: view
        label: "View profile"
        action: acc_view
      - id: back
        label: "← Back"
        back: true

  # ... additional submenus ...
```

### Item Types

| Field | Description |
|-------|-------------|
| `label` | Display text |
| `submenu` | Reference to child menu key |
| `action` | Action identifier (maps to handler) |
| `state_key` | For toggles: key in accessories.conf |
| `back` | Returns to parent menu |

---

## 4. Python OLED Renderer

### File Location

```
nablaedge/scripts/nabla-oled-menu.py
```

### Architecture

```python
#!/usr/bin/env python3
"""
OLED menu renderer for nabla-config.
Reads menu_tree.yaml, renders on SSD1306, handles encoder input.
"""

from pathlib import Path
import yaml
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO
import subprocess
import time

# --- Configuration ---
MENU_TREE_PATH = Path("/usr/share/nabla-edge/menu_tree.yaml")
ACCESSORIES_CONF = Path("/etc/nabla-net/accessories.conf")

# Encoder GPIO (BCM numbering)
PIN_CLK = 17   # Encoder A (CLK)
PIN_DT = 27    # Encoder B (DT)
PIN_SW = 22    # Encoder switch

# Layout from ui/ssd/profiles/128x64.yaml
REGION_STATUS_Y = 0
REGION_STATUS_H = 10
REGION_TITLE_Y = 10
REGION_TITLE_H = 22
REGION_BODY_Y = 44
REGION_BODY_H = 20
MENU_ITEM_HEIGHT = 10
VISIBLE_ITEMS = 2
CARET_X = 2
TEXT_X = 10


class MenuState:
    """Tracks current menu position and navigation stack."""
    
    def __init__(self, tree: dict):
        self.tree = tree
        self.stack = ["main"]  # Menu key stack
        self.index = 0          # Selected item index
        self.scroll_offset = 0  # For scrolling long lists
    
    @property
    def current_menu(self) -> dict:
        return self.tree["menus"][self.stack[-1]]
    
    @property
    def items(self) -> list:
        return self.current_menu["items"]
    
    def navigate(self, delta: int):
        """Move selection up/down."""
        self.index = max(0, min(len(self.items) - 1, self.index + delta))
        # Adjust scroll offset to keep selection visible
        if self.index < self.scroll_offset:
            self.scroll_offset = self.index
        elif self.index >= self.scroll_offset + VISIBLE_ITEMS:
            self.scroll_offset = self.index - VISIBLE_ITEMS + 1
    
    def select(self) -> str | None:
        """Handle selection of current item. Returns action or None."""
        item = self.items[self.index]
        
        if item.get("back"):
            if len(self.stack) > 1:
                self.stack.pop()
                self.index = 0
                self.scroll_offset = 0
            return None
        
        if "submenu" in item:
            self.stack.append(item["submenu"])
            self.index = 0
            self.scroll_offset = 0
            return None
        
        if "action" in item:
            return item["action"]
        
        return None


class OledRenderer:
    """Renders menu state to SSD1306 display."""
    
    def __init__(self, device):
        self.device = device
        self.font_title = ImageFont.load_default()
        self.font_body = ImageFont.load_default()
    
    def render(self, state: MenuState, clock_str: str = ""):
        """Render current menu state to display."""
        image = Image.new("1", (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        # Status bar: clock right-aligned
        if clock_str:
            draw.text((100, 1), clock_str, fill=1)
        
        # Title: current menu label
        title = state.current_menu["label"]
        draw.text((64, 18), title, fill=1, anchor="mm")
        
        # Body: visible menu items with selection caret
        items = state.items
        for i in range(VISIBLE_ITEMS):
            item_idx = state.scroll_offset + i
            if item_idx >= len(items):
                break
            
            item = items[item_idx]
            y = REGION_BODY_Y + (i * MENU_ITEM_HEIGHT)
            
            # Selection caret
            if item_idx == state.index:
                draw.text((CARET_X, y), "▶", fill=1)
            
            # Item label (with toggle state if applicable)
            label = item["label"]
            if "state_key" in item:
                val = self._read_state(item["state_key"])
                label = f"{label} [{val}]"
            
            draw.text((TEXT_X, y), label, fill=1)
        
        self.device.display(image)
    
    def _read_state(self, key: str) -> str:
        """Read toggle state from accessories.conf."""
        try:
            conf = ACCESSORIES_CONF.read_text()
            for line in conf.splitlines():
                if line.startswith(f"{key}="):
                    return "ON" if line.split("=")[1].strip() == "1" else "OFF"
        except FileNotFoundError:
            pass
        return "OFF"


class EncoderInput:
    """Handles rotary encoder input via GPIO."""
    
    def __init__(self, on_rotate, on_press):
        self.on_rotate = on_rotate
        self.on_press = on_press
        self._last_clk = 1
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        GPIO.add_event_detect(PIN_CLK, GPIO.BOTH, callback=self._clk_callback, bouncetime=5)
        GPIO.add_event_detect(PIN_SW, GPIO.FALLING, callback=self._sw_callback, bouncetime=200)
    
    def _clk_callback(self, channel):
        clk = GPIO.input(PIN_CLK)
        dt = GPIO.input(PIN_DT)
        if clk != self._last_clk:
            if dt != clk:
                self.on_rotate(1)   # CW
            else:
                self.on_rotate(-1)  # CCW
        self._last_clk = clk
    
    def _sw_callback(self, channel):
        self.on_press()
    
    def cleanup(self):
        GPIO.cleanup()


def execute_action(action: str):
    """Execute action by calling nabla-config or subprocess."""
    action_map = {
        "network_status": ["nabla-config", "network-status"],
        "network_cable": ["sudo", "vpn-mode", "cable"],
        "network_ap": ["sudo", "vpn-mode", "ap"],
        "acc_toggle_oled": ["nabla-config-action", "toggle-oled"],
        # ... map other actions ...
    }
    
    if action in action_map:
        subprocess.run(action_map[action], check=False)


def main():
    # Load menu tree
    tree = yaml.safe_load(MENU_TREE_PATH.read_text())
    
    # Initialize display
    serial = i2c(port=1, address=0x3C)
    device = ssd1306(serial, width=128, height=64)
    
    # Initialize state and renderer
    state = MenuState(tree)
    renderer = OledRenderer(device)
    
    def on_rotate(delta):
        state.navigate(delta)
        renderer.render(state, time.strftime("%H:%M"))
    
    def on_press():
        action = state.select()
        if action:
            execute_action(action)
        renderer.render(state, time.strftime("%H:%M"))
    
    encoder = EncoderInput(on_rotate, on_press)
    
    try:
        renderer.render(state, time.strftime("%H:%M"))
        while True:
            time.sleep(60)
            renderer.render(state, time.strftime("%H:%M"))  # Update clock
    except KeyboardInterrupt:
        pass
    finally:
        encoder.cleanup()


if __name__ == "__main__":
    main()
```

### Idle vs Menu Mode

| Mode | Trigger | Display |
|------|---------|---------|
| Idle (clock) | No input for 60s | Home page: nabla.net + time |
| Menu | Encoder rotate or press | Menu list with selection |

The service defaults to idle clock mode (existing `nabla-oled-clock.py` behavior) and switches to menu mode on encoder activity.

---

## 5. Encoder Wiring — GPIO Pinout

### Partial Mode (Current Sticker)

This pinout matches the user's encoder sticker photo:

| Encoder Pin | BCM GPIO | Physical Pin | Function |
|-------------|----------|--------------|----------|
| CLK (A) | **GPIO17** | Pin 11 | Encoder channel A |
| DT (B) | **GPIO27** | Pin 13 | Encoder channel B |
| SW | **GPIO22** | Pin 15 | Push button switch |
| GND | GND | Pin 6, 9, 14, etc. | Ground |
| + (3V3) | 3V3 | Pin 1 or 17 | Optional power if encoder has internal pull-ups |

### Full Mode (Future)

> **Caveat**: The sticker pinout is a **subset** of a future "full mode" pinout that may include additional encoder GPIOs or alternate functions. Document and test the partial pinout first; extend when full-mode hardware is defined.

### Internal Pull-ups

The Pi's BCM GPIO pins support internal pull-ups. Configure in software:

```python
GPIO.setup(PIN_CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
```

If the encoder module has onboard pull-ups, these may not be needed, but enabling them is harmless.

### OLED I2C Pins (Reference)

| OLED Pin | Pi Connection |
|----------|---------------|
| SDA | GPIO2 (Pin 3) |
| SCL | GPIO3 (Pin 5) |
| VCC | 3.3V (Pin 1) |
| GND | GND (Pin 6) |

---

## 6. Systemd Service

### Service File

```ini
# /etc/systemd/system/nabla-oled-menu.service

[Unit]
Description=Nabla OLED Menu Renderer
After=network.target
Requires=nabla-oled.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/nabla-oled-menu.py
Restart=on-failure
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
```

### Integration with Existing Clock Service

Option A: Replace `nabla-oled.service` entirely with `nabla-oled-menu.service` that handles both clock and menu.

Option B: Run both services; menu service signals clock service to pause during menu interaction.

**Recommended**: Option A — single service with idle/menu modes.

---

## 7. Keeping Menus in Sync

### The Sync Rule

> **When you edit `nabla-config` menu structure, you MUST update `menu_tree.yaml` in the same commit.**

### Contributor Checklist

When modifying `nabla-config` menus:

- [ ] Update `nablaedge/scripts/menu_tree.yaml` with matching changes
- [ ] Test both whiptail and OLED rendering (if hardware available)
- [ ] Update screenshots/test notes if UI changed significantly
- [ ] Verify new actions have handler mappings in `nabla-oled-menu.py`

### CI Validation (Future)

A linter script could:

1. Parse `menu_tree.yaml`
2. Extract menu labels/structure from `nabla-config` bash
3. Report mismatches

---

## 8. Collaboration: Edge + Spui (Boundary Contract)

### Ownership Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│  EDGE owns (this repo — nabla-edge)                                      │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  menu_tree.yaml        ← Single source of truth for menu structure │ │
│  │  nabla-oled-menu.py    ← Python renderer (list + focus + actions)  │ │
│  │  Encoder GPIO service  ← GPIO17/27/22, pull-ups, events            │ │
│  │  Sync process          ← Checklist, CI linter                      │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  Consumes: Tiny OLED chrome contract (below)                             │
└──────────────────────────────────────────────────────────────────────────┘

                              ▼  contract boundary  ▼

┌──────────────────────────────────────────────────────────────────────────┐
│  SPUI owns (nabla-esp-ui repo)                                           │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Tiny OLED Chrome Contract                                          │ │
│  │    - App supplies: list of items + focus index                      │ │
│  │    - Shell draws: ▶ caret, high-contrast selection, nabla branding  │ │
│  │    - Keyboard: components/keyboard/ (text entry)                    │ │
│  │    - Reference: PRs #19, #21 on main                                │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

### Tiny OLED Chrome Contract

Spui's nabla-esp-ui defines the visual chrome rules for small OLEDs. The Pi renderer **follows the same contract** rather than reinventing borders/keyboard chrome:

| Responsibility | Owner | Rule |
|----------------|-------|------|
| **List rendering** | App (Edge) | Supplies `items[]` + `focus_index` |
| **Selection caret** | Shell (Spui) | Draws `▶` at `CARET_X` for focused item |
| **High-contrast focus** | Shell (Spui) | Optionally inverts row or uses bold |
| **Nabla branding** | Shell (Spui) | Status bar, logo glyph, fonts |
| **Keyboard input** | Shell (Spui) | `components/keyboard/` for text entry |

**Pi implementation**: The Python renderer implements the same visual rules documented in nabla-esp-ui. It does not duplicate chrome logic — just follows the contract.

### Shared Resources

| Resource | Location | Purpose |
|----------|----------|---------|
| `ui/ssd/tokens.yaml` | nabla-edge | Font sizes, caret char (`▶`), colors |
| `ui/ssd/profiles/128x64.yaml` | nabla-edge | Region coordinates (status, title, body) |
| Tiny chrome spec | nabla-esp-ui | Visual rules for ▶, high-contrast, branding |

### Menu Structure Sharing

The Pi renderer consumes the **same menu structure** as nabla-config. When the main menu changes, the OLED automatically reflects it:

```
menu_tree.yaml  ──┬──▶  nabla-config (bash/whiptail)
                  │
                  └──▶  nabla-oled-menu.py (Python/luma)
                        └── follows Tiny OLED chrome contract
```

No duplication of menu labels or hierarchy — one source, multiple renderers.

### Interface Contract Summary

The Pi renderer implements this minimal interface:

```python
# Pi renderer provides:
def get_visible_items() -> list[str]:
    """Labels for visible menu items (2 rows on 128×64)."""

def get_focus_index() -> int:
    """Index of currently focused item (0-based within visible)."""

# Chrome draws (per Tiny contract):
# - ▶ at CARET_X for focused row
# - High-contrast or invert for focused row (optional)
# - Status bar with clock, icons
# - Nabla branding on idle screen
```

This keeps the app logic (menu navigation, actions) separate from visual chrome.

---

## 9. nabla-config Message Update

Currently, the rotary encoder message in `nabla-config` says:

> "EC11: A/B + switch to GPIO (pull-ups). See AGENTS.md."

### Updated Message

```bash
msg "Accessories" "Rotary encoder: ON\n\nEC11 wiring (BCM GPIO):\n  CLK (A) = GPIO17 (pin 11)\n  DT  (B) = GPIO27 (pin 13)\n  SW      = GPIO22 (pin 15)\n  GND     = any GND pin\n  3V3     = optional (pin 1)\n\nInternal pull-ups enabled in software."
```

This provides canonical pinout directly in the UI.

---

## 10. File Summary

| Path | Description | Owner |
|------|-------------|-------|
| `nablaedge/scripts/menu_tree.yaml` | Menu structure definition | Edge |
| `nablaedge/scripts/nabla-oled-menu.py` | Python OLED renderer (sketch) | Edge |
| `nablaedge/scripts/nabla-config` | Whiptail menu (updates rotary message) | Edge |
| `nablaedge/docs/pi-config-menu/OLED-MENU-DESIGN.md` | This document | Edge |
| `nablaedge/ui/ssd/` | Shared layout profiles + tokens | Edge/Spui |
| `protocols/menu/` | MQTT menu protocol (future use) | Spui |

---

## 11. Implementation Phases

### Phase 1: Design + Stubs (This PR)

- Design document (this file)
- `menu_tree.yaml` initial structure
- `nabla-oled-menu.py` skeleton/stub
- Updated `nabla-config` rotary message

### Phase 2: Working Renderer

- Full `nabla-oled-menu.py` implementation
- Systemd service
- Testing on Pi hardware

### Phase 3: Sync Validation

- CI linter for menu_tree ↔ nabla-config sync
- Integration with existing OLED clock service

---

## 12. References

### This Repo (nabla-edge)

- [`nablaedge/docs/accessories/oled-ui/`](../accessories/oled-ui/) — OLED paint layer overview
- [`nablaedge/ui/ssd/`](../../ui/ssd/) — Layout profiles and tokens
- [`protocols/menu/PROTOCOL.md`](../../../protocols/menu/PROTOCOL.md) — MQTT menu protocol (ESP focus)
- [`nablaedge/docs/esphome-patterns/examples/demo-oled-encoder.yaml`](../esphome-patterns/examples/demo-oled-encoder.yaml) — ESP encoder example

### External (nabla-esp-ui)

- [nabla-esp-ui PR #19](https://github.com/txemavs/nabla-esp-ui/pull/19) — Tiny OLED chrome initial implementation
- [nabla-esp-ui PR #21](https://github.com/txemavs/nabla-esp-ui/pull/21) — Keyboard component
- `components/keyboard/` — Text entry for ESP OLED (Spui-owned)
