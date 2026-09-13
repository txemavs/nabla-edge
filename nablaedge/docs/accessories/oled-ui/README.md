# OLED UI — Paint Layer

How the OLED display paint layer works: layout profiles, design tokens, and platform drivers.

---

## Overview

The OLED UI layer defines **how things look** on small monochrome displays:

- Screen regions (status bar, title, body)
- Font sizes and colors
- Spacing and margins

Menu **logic** (what to show, navigation) lives in [protocols/menu/](../../../../protocols/menu/). This layer handles **paint only**.

---

## Source Location

The authoritative source is **[ui/ssd/](../../../ui/ssd/)**:

```
nablaedge/ui/ssd/
├── README.md              # Overview
├── LAYOUT.md              # Region specification
├── tokens.yaml            # Design tokens
└── profiles/
    └── 128x64.yaml        # 128×64 resolution profile
```

---

## Supported Hardware

| Platform | Chip | Resolution | Interface | Driver |
|----------|------|------------|-----------|--------|
| Raspberry Pi | SSD1306 | 128×64 | I2C | luma.oled |
| ESP32 | SSD1309 | 128×64 | SPI | ESPHome |

Both share the **same layout profile** — only the driver differs.

---

## Screen Layout (128×64)

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

| Region | Y Start | Height | Purpose |
|--------|---------|--------|---------|
| Status Bar | 0 | 10 px | Icons (WiFi, BT) + clock |
| Title | 10 | 22 px | Primary text, large font |
| Subtitle | 32 | 12 px | Secondary label |
| Body/Menu | 44 | 20 px | Menu items (2 visible rows) |

---

## Design Tokens

From `tokens.yaml`:

```yaml
color:
  on: 1          # White pixel
  off: 0         # Black pixel

font:
  status:  { height: 8 }
  title:   { height: 16, weight: bold }
  subtitle: { height: 10 }
  body:    { height: 8 }

selection:
  caret: "▶"     # Selection indicator
  caret_alt: ">" # ASCII fallback
```

---

## Pi Driver: luma.oled

### Installation

```bash
pip install luma.oled
```

### Usage

```python
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import ImageDraw, ImageFont

# Initialize
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=64)

# Draw using profile coordinates
with canvas(device) as draw:
    # Status bar (y=0, h=10)
    draw.text((100, 1), "14:32", fill="white")
    
    # Title (y=10, h=22)
    draw.text((64, 20), "nabla.net", fill="white", anchor="mm")
    
    # Body (y=44, h=20)
    draw.text((10, 46), "▶ Settings", fill="white")
    draw.text((10, 56), "  Network", fill="white")
```

### Service: nabla-oled

The `nabla-oled` systemd service runs the display:

```bash
sudo systemctl status nabla-oled
sudo systemctl restart nabla-oled
```

Controlled by `display_oled=1` in `/etc/nabla-net/accessories.conf`.

---

## ESP Driver: ESPHome

### Configuration

```yaml
display:
  - platform: ssd1309_spi
    id: oled
    cs_pin: GPIO5
    dc_pin: GPIO4
    reset_pin: GPIO16
    lambda: |-
      // Status bar
      it.printf(100, 1, id(font_small), "%s", id(time_now).c_str());
      
      // Title
      it.printf(64, 20, id(font_large), TextAlign::CENTER, "nabla.net");
      
      // Menu items
      it.printf(10, 46, id(font_small), "▶ Settings");
      it.printf(10, 56, id(font_small), "  Network");
```

### Font Assets

ESP fonts are compiled into firmware. Use sizes matching `tokens.yaml`:

```yaml
font:
  - file: "fonts/roboto.ttf"
    id: font_small
    size: 8
  - file: "fonts/roboto.ttf"
    id: font_large
    size: 16
```

---

## Profile Files

### 128x64.yaml

Full layout specification for 128×64 displays:

```yaml
meta:
  resolution: { width: 128, height: 64 }
  color_depth: 1

regions:
  status_bar: { y: 0, height: 10 }
  title: { y: 10, height: 22, align: center }
  subtitle: { y: 32, height: 12, align: center }
  body: { y: 44, height: 20 }

layout:
  margin_h: 2
  usable_width: 124
```

See [ui/ssd/profiles/128x64.yaml](../../../ui/ssd/profiles/128x64.yaml) for full spec.

---

## Page Types

### Home Page

```
┌────────────────────────────────────────┐
│ ▲ WiFi  ♦ BT              14:32       │
├────────────────────────────────────────┤
│           ◢  nabla.net                 │
├────────────────────────────────────────┤
│            Edge Node                   │
├────────────────────────────────────────┤
│                                        │
└────────────────────────────────────────┘
```

### Menu Page

```
┌────────────────────────────────────────┐
│ ▲  Settings                   14:32   │
├────────────────────────────────────────┤
│           Settings                     │
├────────────────────────────────────────┤
│                                        │
├────────────────────────────────────────┤
│ ▶ Display                              │
│   Network                              │
└────────────────────────────────────────┘
```

---

## Clock Service: nabla-oled

The `nabla-oled` service handles:

1. Clock display in status bar
2. Menu rendering from MQTT state
3. Icon updates (WiFi, Bluetooth status)

Configuration in `/etc/nabla-net/oled.conf`:

```ini
clock_format=%H:%M
show_wifi_icon=1
show_bt_icon=1
```

---

## Adding a New Resolution

To support a different display (e.g., 128×32):

1. Create `profiles/128x32.yaml`
2. Adjust region heights proportionally
3. May need smaller fonts
4. Test on actual hardware

---

## How to Change This

1. Edit profile YAML for layout changes
2. Update tokens for font/color changes
3. Test on both Pi and ESP hardware
4. Update this README with findings

---

## Related

- [../../../ui/ssd/](../../../ui/ssd/) — Authoritative source
- [../](../) — Accessories overview
- [../../../../protocols/menu/](../../../../protocols/menu/) — Menu logic
