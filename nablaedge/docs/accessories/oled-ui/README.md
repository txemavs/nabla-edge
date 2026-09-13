# OLED UI — Paint Layer

Shared 128×64 monochrome display layout for SSD1306 (Pi) and SSD1309 (ESP).

---

## Overview

The OLED UI layer defines **how things look** — not what to show:

| Concern | Location |
|---------|----------|
| **Paint layer** (this) | Screen regions, fonts, colors |
| **Menu protocol** | What items to display |
| **Menu engine** | Navigation, selection state |

---

## Source of Truth

Layout profiles and tokens live in [`../../../ui/ssd/`](../../../ui/ssd/):

```
ui/ssd/
├── README.md           # Overview
├── LAYOUT.md           # Region specification
├── tokens.yaml         # Design tokens
└── profiles/
    └── 128x64.yaml     # 128×64 resolution profile
```

---

## Screen Layout (128×64)

```
┌────────────────────────────────────────┐  y=0
│ ∇ WiFi  BT                   14:32     │  Status Bar (h=10)
├────────────────────────────────────────┤  y=10
│                                        │
│           Main Title                   │  Title (h=22)
│                                        │
├────────────────────────────────────────┤  y=32
│          Subtitle Text                 │  Subtitle (h=12)
├────────────────────────────────────────┤  y=44
│ ▶ Selected Item                        │  Body (h=20)
│   Next Item                            │  2 visible rows
└────────────────────────────────────────┘  y=64
```

| Region | Y | Height | Purpose |
|--------|---|--------|---------|
| Status Bar | 0 | 10px | Nabla mark ∇, icons, clock |
| Title | 10 | 22px | Primary text, large font |
| Subtitle | 32 | 12px | Secondary label |
| Body | 44 | 20px | Menu items, 2 rows visible |

---

## Design Tokens

From `tokens.yaml`:

```yaml
color:
  on: 1           # White pixel (foreground)
  off: 0          # Black pixel (background)

font:
  status:   { height: 8, weight: regular }
  title:    { height: 16, weight: bold }
  subtitle: { height: 10, weight: regular }
  body:     { height: 8, weight: regular }

spacing:
  line: 2         # Between text lines
  margin_h: 2     # Horizontal margin

selection:
  caret: "▶"      # Selected item indicator
  caret_alt: ">"  # ASCII fallback
```

---

## Platform Drivers

### Raspberry Pi: luma.oled (SSD1306 I2C)

```python
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=64)

with canvas(device) as draw:
    # Status bar
    draw.text((2, 1), "∇", fill="white")
    draw.text((100, 1), "14:32", fill="white")
    
    # Title
    draw.text((64, 20), "Settings", fill="white", anchor="mm")
    
    # Menu items
    draw.text((2, 46), "▶ Network", fill="white")
    draw.text((2, 56), "  Display", fill="white")
```

### ESP32: ESPHome (SSD1309 SPI)

```yaml
display:
  - platform: ssd1309_spi
    cs_pin: GPIO5
    dc_pin: GPIO16
    reset_pin: GPIO17
    lambda: |-
      // Status bar
      it.printf(2, 1, id(font_small), "∇");
      it.printf(100, 1, id(font_small), "%02d:%02d", hour, minute);
      
      // Title
      it.printf(64, 20, id(font_large), TextAlign::CENTER, "Settings");
      
      // Menu items
      it.printf(2, 46, id(font_small), "▶ Network");
      it.printf(2, 56, id(font_small), "  Display");
```

---

## The Nabla Mark: ∇

The Nabla symbol appears in the status bar — a hollow inverted triangle, tip-down:

```
  ╱╲
 ╱  ╲
╱────╲
   ▼
```

Use Unicode character `∇` (U+2207) or draw manually:

```python
def draw_nabla(draw, x, y, size):
    """Draw nabla triangle at (x, y) with given size."""
    draw.polygon([
        (x + size//2, y + size),  # Bottom tip
        (x, y),                    # Top left
        (x + size, y)              # Top right
    ], outline="white")
```

---

## Page Types

### Home Page

```
┌────────────────────────────────────────┐
│ ∇ ▲ ♦                         14:32   │
├────────────────────────────────────────┤
│         ∇ nabla.net                    │
├────────────────────────────────────────┤
│           Edge Node                    │
├────────────────────────────────────────┤
│                                        │
└────────────────────────────────────────┘
```

### Menu Page

```
┌────────────────────────────────────────┐
│ ∇ Settings                    14:32   │
├────────────────────────────────────────┤
│           Settings                     │
├────────────────────────────────────────┤
│                                        │
├────────────────────────────────────────┤
│ ▶ Network                              │
│   Display                              │
└────────────────────────────────────────┘
```

### Info Page

```
┌────────────────────────────────────────┐
│ ∇ Temperature                 14:32   │
├────────────────────────────────────────┤
│            23.5°C                      │
├────────────────────────────────────────┤
│           Kitchen                      │
├────────────────────────────────────────┤
│                                        │
└────────────────────────────────────────┘
```

---

## Adding New Profiles

For different resolutions (e.g., 128×32):

1. Create `profiles/128x32.yaml`
2. Adjust region heights proportionally
3. Consider smaller fonts
4. Test on hardware

---

## Related

- [`../../../ui/ssd/`](../../../ui/ssd/) — Authoritative layout source
- [`../`](../) — Accessories overview
- [`../../esphome-patterns/`](../../esphome-patterns/) — ESP32 integration
- [`../../../../protocols/menu/`](../../../../protocols/menu/) — Menu protocol
