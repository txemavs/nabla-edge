# NablaEdge

Dom's edge system — ESPHome components for rotary encoders, OLEDs, and the nabla.menu engine.

---

## Overview

NablaEdge devices receive menu definitions over MQTT and render them locally. Menu updates happen without firmware reflash.

## Documentation

**[📚 docs/](docs/)** — Learning-oriented how-to guides:

| Topic | Description |
|-------|-------------|
| [architecture](docs/architecture/) | Big picture: edge nodes, protocols, data flow |
| [pi-config-menu](docs/pi-config-menu/) | The nabla-config whiptail menu |
| [network-modes](docs/network-modes/) | Nabla Net: cable, ap, cable-ap, off |
| [imaging](docs/imaging/) | nabla-image: SD/USB imaging + first-boot |
| [accessories](docs/accessories/) | OLED, rotary, large SPI + OLED UI |
| [ble-mesh](docs/ble-mesh/) | BLE presence/contagion protocol |
| [packages-apt](docs/packages-apt/) | Apt packages and HTTP publishing |

## Structure

```
nablaedge/
├── docs/                     # ← How-to documentation
│   ├── architecture/
│   ├── pi-config-menu/
│   ├── network-modes/
│   ├── imaging/
│   ├── accessories/
│   │   └── oled-ui/
│   ├── ble-mesh/
│   ├── packages-apt/
│   ├── voice-satellite/
│   └── manuals/
├── esphome/
│   └── components/
│       └── nabla_menu/       # Menu rendering engine
├── firmware/                 # Device-specific configs (gitignored binaries)
└── ui/
    └── ssd/                  # OLED paint layer (SSD1306/1309)
```

## Key Concepts

- **Menu Engine**: Parses JSON menu definitions, renders to OLED, handles rotary input
- **MQTT-Driven**: Menus arrive via retained MQTT messages
- **No Reflash**: Change menus by publishing new JSON; device updates immediately

## UI Components

### [ui/ssd/](ui/ssd/)

Shared visual style for small monochrome OLED displays. Defines layout regions, design tokens, and resolution profiles.

Used by both:
- **Raspberry Pi** (SSD1306) via luma.oled
- **ESP32** (SSD1309) via ESPHome

Both share the same 128×64 resolution profiles. Paint layer only — menu logic lives in `protocols/menu`.

## Status

🚧 **Stub** — Components to be added.

See [protocols/menu/](../protocols/menu/) for the menu protocol specification.
