# NablaEdge

Edge system — ESPHome components for rotary encoders, OLEDs, nabla.menu engine, and voice satellite support.

---

## Overview

NablaEdge devices receive menu definitions over MQTT and render them locally. Menu updates happen without firmware reflash. Raspberry Pi nodes can also serve as voice satellites for Home Assistant Assist.

## Structure

```
nablaedge/
├── scripts/
│   └── nabla-config         # Interactive config menu (whiptail)
├── voice/
│   ├── install-lva.sh       # Linux Voice Assistant installer
│   └── voice.conf.example   # Voice satellite config template
├── ui/
│   └── ssd/                 # OLED paint layer (SSD1306/1309)
└── docs/
    ├── voice-satellite/     # Voice satellite documentation
    ├── pi-config-menu/      # nabla-config usage
    └── ...
```

## Key Features

### Menu Engine
- **MQTT-Driven**: Menus arrive via retained MQTT messages
- **No Reflash**: Change menus by publishing new JSON; device updates immediately
- **Rotary Input**: EC11 encoder support for menu navigation

### Voice Satellite
- **LVA**: Linux Voice Assistant (ESPHome protocol, port 6053)
- **Button trigger**: HA `start_conversation` from phone/dashboard (default)
- **Wake word**: Optional continuous listening (desktop hosts)
- **GPIO**: Physical button support for local trigger

### UI Components
- **OLED**: Shared visual style for SSD1306/SSD1309 displays
- **Profiles**: 128x64 resolution profiles for Pi and ESP32

## Quick Start

### Voice Satellite (Pi)

```bash
sudo nabla-config
# → Voice Satellite → Install / update LVA
```

See [docs/voice-satellite/](docs/voice-satellite/) for full setup.

### Configuration Menu

```bash
sudo nabla-config
```

See [docs/pi-config-menu/](docs/pi-config-menu/) for menu reference.

## Related

- [protocols/menu/](../protocols/menu/) — Menu protocol specification
- [ui/ssd/](ui/ssd/) — OLED paint layer and layout profiles
