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

> **Contract Spui; implementación Pi = Edge / ESP = nabla-esp-ui**

| Component | Owner | Notes |
|-----------|-------|-------|
| `nabla-config` menu tree | **Edge** | `menu_tree.yaml` — single source of truth |
| Pi encoder input (GPIO17/27/22) | **Edge** | BCM pinout, internal pull-ups |
| Python OLED renderer | **Edge** | Implements Tiny chrome contract on Pi |
| Menu ↔ OLED sync process | **Edge** | Contributor checklist, CI validation |
| **Tiny OLED chrome contract (rules)** | **Spui** | Defines focus/input behavior for all platforms |
| ESP OLED implementation | **Spui** | nabla-esp-ui implements the contract |
| Keyboard contract | **Spui** | `components/keyboard/` in nabla-esp-ui |

> **References**: nabla-esp-ui PRs [#15](https://github.com/txemavs/nabla-esp-ui/pull/15), [#16](https://github.com/txemavs/nabla-esp-ui/pull/16), [#19](https://github.com/txemavs/nabla-esp-ui/pull/19), [#20](https://github.com/txemavs/nabla-esp-ui/pull/20), [#21](https://github.com/txemavs/nabla-esp-ui/pull/21) on main.

---

## 2. Architecture

### OLED Root Shell

The OLED display has a **root shell** with multiple top-level apps. Config is one of them, not the only screen:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OLED ROOT SHELL                                 │
│                                                                         │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                  │
│   │   Reloj     │   │   Config    │   │   (More)    │                  │
│   │  (Clock)    │   │  (Menu)     │   │  (Future)   │                  │
│   │             │   │             │   │             │                  │
│   │  ∇ + time   │   │ nabla-config│   │ Extension   │                  │
│   │  idle/home  │   │ menu tree   │   │ point       │                  │
│   └─────────────┘   └─────────────┘   └─────────────┘                  │
│         ▲                 ▲                 ▲                          │
│         └────────── encoder select ─────────┘                          │
└─────────────────────────────────────────────────────────────────────────┘
```

| Root App | Description | Behavior |
|----------|-------------|----------|
| **Reloj** | Clock/home screen | Default idle display: ∇ logo + "nabla.net" + HH:MM |
| **Config** | nabla-config menu | Full menu tree navigation (this design) |
| **(More)** | Extension point | Reserved for future apps (sensors, status, etc.) |

### Mode Switching

```
                    ┌─────────────────────────────────────────┐
                    │           OLED Service State            │
                    │                                         │
     idle timeout   │   ┌────────┐   encoder    ┌──────────┐ │
    ───────────────▶│   │ Reloj  │◀────────────▶│ Root Menu│ │
         60s        │   │ (Clock)│   rotate/    │ (select  │ │
                    │   └────────┘   press      │  app)    │ │
                    │       ▲                        │      │
                    │       │ "← Back" from root     ▼      │
                    │       │                   ┌──────────┐ │
                    │       └───────────────────│  Config  │ │
                    │                           │  (Menu)  │ │
                    │                           └──────────┘ │
                    └─────────────────────────────────────────┘
```

1. **Idle/Home** = Reloj (clock) — current `nabla-oled-clock.py` behavior
2. **Encoder rotate** → shows root menu with app options
3. **Encoder press** → enters selected app (Config, future apps)
4. **"← Back" from root** or **60s idle** → returns to Reloj

### Menu Tree Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SINGLE SOURCE OF TRUTH                         │
│                                                                         │
│   nablaedge/scripts/menu_tree.yaml                                     │
│                                                                         │
│   Defines:                                                              │
│     - Root shell apps (reloj, config, ...)                             │
│     - Config menu hierarchy (items, submenus, back)                    │
│     - Labels for display                                                │
│     - Action identifiers (mapped to shell functions / Python calls)    │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│   nabla-config (bash)   │       │  nabla-oled-menu.py     │
│                         │       │  (Python OLED renderer) │
│ - Reads config submenu  │       │                         │
│ - Renders via whiptail  │       │ - Reads full tree       │
│ - Executes shell funcs  │       │ - Renders root shell    │
│                         │       │ - Handles mode switch   │
└─────────────────────────┘       │ - Encoder navigation    │
                                  └─────────────────────────┘
```

### Key Principles

1. **One menu definition, two renderers.** When the bash menu changes, the YAML changes, and both displays update.

2. **Root shell, not single-purpose display.** The OLED is a multi-app shell; Config is one app alongside Reloj (clock) and future extensions.

3. **Clock is not a one-off.** Reloj is a first-class root app, not special-cased idle behavior. The renderer has a clean app abstraction.

---

## 3. Menu Model — `menu_tree.yaml`

A structured YAML file defining the OLED root shell and config menu hierarchy.

### Location

```
/usr/share/nabla-edge/menu_tree.yaml   # Installed location
nablaedge/scripts/menu_tree.yaml       # Source repo location
```

### Schema

```yaml
version: "1.0"

# --- Root Shell ---
# Top-level OLED apps (Reloj, Config, future extensions)
root_shell:
  default: reloj                    # Idle/home app
  apps:
    - id: reloj
      label: "Reloj"
      type: clock                   # Built-in clock renderer
      description: "∇ nabla.net + time"
    - id: config
      label: "Config"
      type: menu                    # Opens a menu from `menus`
      submenu: main
    # Extension point:
    # - id: sensors
    #   label: "Sensors"
    #   type: app
    #   handler: sensors_app

# --- Config Menus ---
# The nabla-config submenu tree
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
        back: true                  # Returns to root shell

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

  # ... additional submenus (media, voice) ...
```

### Root Shell Apps

| Field | Description |
|-------|-------------|
| `id` | Unique app identifier |
| `label` | Display text in root menu |
| `type` | App type: `clock`, `menu`, `app` |
| `submenu` | For `type: menu`: which menu key to open |
| `handler` | For `type: app`: Python handler function |

### Menu Item Types

| Field | Description |
|-------|-------------|
| `label` | Display text |
| `submenu` | Reference to child menu key |
| `action` | Action identifier (maps to handler) |
| `state_key` | For toggles: key in accessories.conf |
| `back` | Returns to parent menu (or root shell from main) |

---

## 4. Python OLED Renderer

### File Location

```
nablaedge/scripts/nabla-oled-menu.py
```

### Architecture (Root Shell)

The renderer implements a state machine with multiple modes:

```python
#!/usr/bin/env python3
"""
OLED Root Shell renderer.
Manages Reloj (clock), Config (menu), and future apps.
"""

from enum import Enum
from pathlib import Path
from dataclasses import dataclass
import time

# --- Modes ---
class OledMode(Enum):
    RELOJ = "reloj"         # Clock/idle (default)
    ROOT_MENU = "root"      # Root shell app selector
    CONFIG = "config"       # nabla-config menu tree


@dataclass
class AppState:
    """State for root shell and current app."""
    mode: OledMode = OledMode.RELOJ
    root_index: int = 0           # Selected app in root menu
    menu_stack: list = None       # For CONFIG mode: menu navigation
    menu_index: int = 0
    last_activity: float = 0.0    # For idle timeout
    
    def __post_init__(self):
        self.menu_stack = ["main"]
        self.last_activity = time.time()


class OledShell:
    """Root shell managing multiple OLED apps."""
    
    IDLE_TIMEOUT = 60  # seconds
    
    def __init__(self, tree: dict, device):
        self.tree = tree
        self.device = device
        self.state = AppState()
        self.root_apps = tree.get("root_shell", {}).get("apps", [])
    
    def on_rotate(self, delta: int):
        """Handle encoder rotation."""
        self.state.last_activity = time.time()
        
        if self.state.mode == OledMode.RELOJ:
            # Wake from idle → show root menu
            self.state.mode = OledMode.ROOT_MENU
        elif self.state.mode == OledMode.ROOT_MENU:
            # Navigate root apps
            self.state.root_index = (self.state.root_index + delta) % len(self.root_apps)
        elif self.state.mode == OledMode.CONFIG:
            # Navigate config menu
            self._navigate_menu(delta)
        
        self.render()
    
    def on_press(self):
        """Handle encoder press."""
        self.state.last_activity = time.time()
        
        if self.state.mode == OledMode.RELOJ:
            # Wake from idle → show root menu
            self.state.mode = OledMode.ROOT_MENU
        elif self.state.mode == OledMode.ROOT_MENU:
            # Select app
            app = self.root_apps[self.state.root_index]
            if app["type"] == "clock":
                self.state.mode = OledMode.RELOJ
            elif app["type"] == "menu":
                self.state.mode = OledMode.CONFIG
                self.state.menu_stack = [app.get("submenu", "main")]
                self.state.menu_index = 0
        elif self.state.mode == OledMode.CONFIG:
            # Select menu item
            result = self._select_menu_item()
            if result == "exit_to_root":
                self.state.mode = OledMode.ROOT_MENU
        
        self.render()
    
    def tick(self):
        """Called periodically (e.g., every second)."""
        # Check idle timeout
        if self.state.mode != OledMode.RELOJ:
            if time.time() - self.state.last_activity > self.IDLE_TIMEOUT:
                self.state.mode = OledMode.RELOJ
        
        self.render()
    
    def render(self):
        """Render current mode to display."""
        if self.state.mode == OledMode.RELOJ:
            self._render_clock()
        elif self.state.mode == OledMode.ROOT_MENU:
            self._render_root_menu()
        elif self.state.mode == OledMode.CONFIG:
            self._render_config_menu()
    
    def _render_clock(self):
        """Render Reloj (clock/idle) screen."""
        # ∇ logo + "nabla.net" + HH:MM
        # (existing nabla-oled-clock.py logic)
        pass
    
    def _render_root_menu(self):
        """Render root shell app selector."""
        # Show list of apps: Reloj, Config, ...
        # Highlight selected with ▶
        pass
    
    def _render_config_menu(self):
        """Render nabla-config menu tree."""
        # Current menu from stack, items with ▶ selection
        pass
    
    # ... menu navigation helpers ...
```

### Key Design Points

1. **Single service** — One Python process handles all OLED modes
2. **Clean mode separation** — Each mode has its own render/input logic
3. **Reloj is an app** — Clock is a first-class root app, not special-cased idle
4. **Easy extension** — Add new `OledMode` values and handlers for future apps
5. **Idle timeout** — Returns to Reloj after 60s of inactivity

### OLED Modes (Root Shell)

The Python renderer implements a state machine for the root shell:

| Mode | Trigger | Display |
|------|---------|---------|
| **Reloj** (idle) | Default / 60s timeout / back from root | Clock: ∇ + "nabla.net" + HH:MM |
| **Root Menu** | Encoder rotate from Reloj | App selector: Reloj, Config, ... |
| **Config** | Select "Config" from root | nabla-config menu tree navigation |
| *(Future apps)* | Select from root | Extension point for sensors, status, etc. |

```python
class OledMode(Enum):
    RELOJ = "reloj"       # Clock/idle (default)
    ROOT_MENU = "root"    # Root shell app selector
    CONFIG = "config"     # nabla-config menu tree
    # Future: SENSORS, STATUS, etc.
```

### Mode Transitions

```
┌─────────┐  rotate   ┌───────────┐  select   ┌──────────┐
│  RELOJ  │──────────▶│ ROOT_MENU │──────────▶│  CONFIG  │
│ (clock) │           │ (apps)    │           │  (menu)  │
└────▲────┘           └─────┬─────┘           └────┬─────┘
     │                      │                      │
     │    60s timeout       │ select "Reloj"       │ "← Back"
     │◀─────────────────────┴──────────────────────┘  from main
```

The service defaults to Reloj mode (existing `nabla-oled-clock.py` behavior). Encoder activity opens the root menu; selecting an app enters that mode.

### Why Root Shell (Not Single-Purpose)

The clock is **not** special-cased idle behavior — it's a first-class app called "Reloj". This keeps the renderer generic:

1. **Clean abstraction**: Each mode is an app with its own render/input handlers
2. **Easy extension**: Add new root apps without modifying core state machine
3. **Consistent UX**: All apps follow the same enter/exit patterns
4. **No clock rewrite**: Reloj reuses existing clock rendering logic

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

> **Contract Spui; implementación Pi = Edge / ESP = nabla-esp-ui**
>
> Spui owns the **Tiny OLED chrome rules** (the contract). Each platform implements those rules:
> - **Pi**: Edge Python renderer (`nabla-oled-menu.py`)
> - **ESP**: nabla-esp-ui display components

### Ownership Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│  SPUI owns: Tiny OLED Chrome CONTRACT (rules)                            │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Tiny Chrome Rules:                                                 │ │
│  │    - App supplies: list of items + focus index                      │ │
│  │    - Normal mode: ▶ caret marks focus                               │ │
│  │    - Alto contraste mode: inverted bar on focus row                 │ │
│  │    - Keyboard contract: components/keyboard/                        │ │
│  │    - Reference: PRs #15, #16, #19, #20, #21 on nabla-esp-ui main    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘

        ▼  implements contract  ▼              ▼  implements contract  ▼

┌────────────────────────────────────┐    ┌────────────────────────────────┐
│  EDGE owns (Pi implementation)     │    │  SPUI owns (ESP implementation)│
│                                    │    │                                │
│  nabla-oled-menu.py                │    │  nabla-esp-ui display          │
│  - Reads menu_tree.yaml            │    │  - Reads MQTT menu JSON        │
│  - Implements chrome rules         │    │  - Implements chrome rules     │
│  - Encoder GPIO service            │    │  - Encoder/touch input         │
└────────────────────────────────────┘    └────────────────────────────────┘
```

### Ownership Table

| What | Owner | Notes |
|------|-------|-------|
| **Tiny chrome contract (rules)** | Spui | Defines visual behavior for all OLED platforms |
| **Pi chrome implementation** | Edge | Python renderer implements the rules |
| **ESP chrome implementation** | Spui | nabla-esp-ui implements the rules |
| `menu_tree.yaml` | Edge | Single source of truth for Pi menu structure |
| Encoder GPIO (GPIO17/27/22) | Edge | BCM pinout, pull-ups, events |
| Keyboard contract | Spui | `components/keyboard/` in nabla-esp-ui |
| **Pi keyboard implementation** | Edge | Must align with Spui keyboard contract (no ad-hoc) |

### Tiny OLED Chrome Contract (Rules)

The Tiny contract defines how focus and input work across all OLED platforms:

| Rule | Normal Mode | Alto Contraste Mode |
|------|-------------|---------------------|
| **Focus indicator** | `▶` caret at `CARET_X` | Inverted bar (white-on-black row) |
| **Non-focused items** | Plain text | Plain text |
| **Scrolling** | Keep focus in visible region | Same |

> **Global setting**: Normal vs Alto contraste is a **system-wide** appearance setting (from Ajustes/Appearance), not per-screen. The renderer reads this setting and applies the appropriate focus style everywhere.

### Text Input Contract

When a menu item requires text input (e.g., entering a hostname), the renderer must follow the keyboard contract:

| Principle | Rule |
|-----------|------|
| **No ad-hoc keyboard** | Pi renderer must NOT embed a custom keyboard implementation |
| **Semantic field** | App declares "this field needs text input" |
| **Shell chooses input source** | Compact encoder chars, touch keyboard, or **BT HID** if paired/focused |
| **Contract alignment** | Pi keyboard (if needed) must align with `components/keyboard/` in nabla-esp-ui |

For Phase 1 (this PR), text input is out of scope. Future implementation must follow this contract.

### Shared Resources

| Resource | Location | Purpose |
|----------|----------|---------|
| `ui/ssd/tokens.yaml` | nabla-edge | Font sizes, caret char (`▶`), colors |
| `ui/ssd/profiles/128x64.yaml` | nabla-edge | Region coordinates (status, title, body) |
| Tiny chrome contract | nabla-esp-ui | Visual rules (implemented by each platform) |
| Keyboard contract | nabla-esp-ui | `components/keyboard/` (PRs #15, #16, #20, #21) |

### Menu Structure Sharing

The Pi renderer consumes the **same menu structure** as nabla-config. When the main menu changes, the OLED automatically reflects it:

```
menu_tree.yaml  ──┬──▶  nabla-config (bash/whiptail)
                  │
                  └──▶  nabla-oled-menu.py (Python/luma)
                        └── implements Tiny chrome contract
```

No duplication of menu labels or hierarchy — one source, multiple renderers.

### Interface Contract Summary

The Pi renderer implements this minimal interface:

```python
# App provides (Edge):
def get_visible_items() -> list[str]:
    """Labels for visible menu items (2 rows on 128×64)."""

def get_focus_index() -> int:
    """Index of currently focused item (0-based within visible)."""

# Chrome implementation (Edge, per Spui contract):
# - Normal: ▶ at CARET_X for focused row
# - Alto contraste: inverted bar for focused row
# - Status bar with clock, icons
# - Nabla branding on idle screen
# - Text input: defer to keyboard contract (no ad-hoc)
```

This keeps the app logic (menu navigation, actions) separate from visual chrome, while ensuring Pi and ESP have consistent UX.

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

- [nabla-esp-ui PR #15](https://github.com/txemavs/nabla-esp-ui/pull/15) — Keyboard component foundation
- [nabla-esp-ui PR #16](https://github.com/txemavs/nabla-esp-ui/pull/16) — Keyboard in `components/keyboard/`
- [nabla-esp-ui PR #19](https://github.com/txemavs/nabla-esp-ui/pull/19) — Tiny OLED chrome philosophy
- [nabla-esp-ui PR #20](https://github.com/txemavs/nabla-esp-ui/pull/20) — Keyboard refinements
- [nabla-esp-ui PR #21](https://github.com/txemavs/nabla-esp-ui/pull/21) — Keyboard component completion
- `components/keyboard/` — Text input contract for OLED (Spui-owned, Pi must align)
