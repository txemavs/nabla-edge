# SSD OLED Paint Layer — Layout Specification

This document defines the **visual layout** for small monochrome OLED displays (e.g., 128×64 SSD1306/SSD1309). It covers screen regions, coordinate mappings, and how design tokens translate to pixels.

> **Scope**: Paint and layout only. Menu *logic* (navigation, selection state, event handling) lives in `protocols/menu`. This folder handles *how things look*, not *what happens when buttons are pressed*.

---

## Screen Regions

A 128×64 display is divided into horizontal bands:

```
┌────────────────────────────────────────┐  y=0
│  STATUS BAR (icons + clock)            │  h=10
├────────────────────────────────────────┤  y=10
│                                        │
│         TITLE (large, centered)        │  h=22
│                                        │
├────────────────────────────────────────┤  y=32
│       SUBTITLE (smaller, centered)     │  h=12
├────────────────────────────────────────┤  y=44
│                                        │
│  BODY / MENU LIST (scrollable)         │  h=20
│                                        │
└────────────────────────────────────────┘  y=64
```

| Region      | Y Start | Height | Purpose                                 |
|-------------|---------|--------|-----------------------------------------|
| Status Bar  | 0       | 10 px  | Icons (WiFi, BT, alerts) + HH:MM clock  |
| Title       | 10      | 22 px  | Primary information, large font         |
| Subtitle    | 32      | 12 px  | Secondary label or state                |
| Body/Menu   | 44      | 20 px  | Optional list items or extra content    |

### Margins & Padding

- **Horizontal margin**: 2 px on each side (usable width = 124 px).
- **Status bar padding**: 1 px top/bottom.
- **Title vertical centering**: within its 22 px band.
- **Menu item height**: 10 px per row (2 visible in body region).

---

## Token Mapping

Design tokens from `tokens.yaml` map to concrete values per profile:

| Token Role      | 128×64 Value        | Notes                           |
|-----------------|---------------------|---------------------------------|
| `color.on`      | 1 (white pixel)     | Foreground                      |
| `color.off`     | 0 (black pixel)     | Background                      |
| `font.status`   | 8 px height         | Monospace or condensed          |
| `font.title`    | 16 px height        | Bold weight when available      |
| `font.subtitle` | 10 px height        | Regular weight                  |
| `font.body`     | 8 px height         | For menu items / lists          |
| `spacing.line`  | 2 px                | Between text lines in body      |
| `caret.char`    | `▶` or `>`          | Selection indicator, left side  |

---

## Page Types

### 1. Home Page

Displays identity/branding and clock.

```
┌────────────────────────────────────────┐
│ ▲ WiFi  ♦ BT              14:32       │  status bar
├────────────────────────────────────────┤
│                                        │
│           ◢  nabla.net                 │  title (logo + domain)
│                                        │
├────────────────────────────────────────┤
│            Edge Node                   │  subtitle
├────────────────────────────────────────┤
│                                        │  body (empty or stats)
└────────────────────────────────────────┘
```

### 2. Menu Page

Displays a scrollable list with selection caret.

```
┌────────────────────────────────────────┐
│ ▲  Settings                   14:32   │  status bar (shows menu name)
├────────────────────────────────────────┤
│                                        │
│           Settings                     │  title
│                                        │
├────────────────────────────────────────┤
│                                        │  subtitle (empty or breadcrumb)
├────────────────────────────────────────┤
│ ▶ Display                              │  selected item
│   Network                              │  next item
└────────────────────────────────────────┘
```

---

## Platform Consumption

### Raspberry Pi (luma.oled)

```python
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import ImageDraw, ImageFont

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=64)

# Load profile: profiles/128x64.yaml
# Use tokens for font sizes, colors, region coords
```

The Pi renderer:
1. Loads `profiles/128x64.yaml` for region coordinates.
2. Uses `tokens.yaml` for font/color lookups.
3. Calls `ImageDraw` primitives to paint each region.

### ESP32 / ESPHome

```yaml
display:
  - platform: ssd1309_spi
    # ... pin config ...
    lambda: |-
      // Same logical regions, translated to ESPHome display API
      // Status bar: it.printf(2, 1, status_font, "%s", wifi_icon);
      // Title: it.printf(64, 20, title_font, TextAlign::CENTER, "nabla.net");
```

ESPHome displays:
1. Reference the same `128x64.yaml` for coordinates (hard-coded in lambda or via substitution).
2. Font assets compiled separately but follow `tokens.yaml` size guidelines.
3. Paint calls map 1:1 to region bands.

---

## Adding New Profiles

To support a different resolution (e.g., 128×32):

1. Create `profiles/128x32.yaml`.
2. Adjust region heights proportionally.
3. Reference smaller font tokens or define new ones.
4. Test on hardware to ensure readability.

---

## Relationship to Menu Protocol

```
┌─────────────────────────────────────────────────────────────┐
│  protocols/menu                                              │
│  (navigation logic, item definitions, state machine)         │
└────────────────────────────┬────────────────────────────────┘
                             │ provides: current_page, items[], selected_index
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  ui/ssd                                                      │
│  (layout regions, tokens, profiles)                          │
│  → produces: pixel buffer                                    │
└─────────────────────────────────────────────────────────────┘
```

Menu protocol emits *what* to show; this paint layer decides *where* and *how*.
