# NablaEdge

Dom's edge system — ESPHome components for rotary encoders, OLEDs, and the nabla.menu engine.

---

## Overview

NablaEdge devices receive menu definitions over MQTT and render them locally. Menu updates happen without firmware reflash.

## Planned Structure

```
nablaedge/
├── esphome/
│   └── components/
│       └── nabla_menu/      # Menu rendering engine
├── firmware/                 # Device-specific configs (gitignored binaries)
└── docs/
```

## Key Concepts

- **Menu Engine**: Parses JSON menu definitions, renders to OLED, handles rotary input
- **MQTT-Driven**: Menus arrive via retained MQTT messages
- **No Reflash**: Change menus by publishing new JSON; device updates immediately

## Status

🚧 **Stub** — Components to be added.

See [protocols/menu/](../protocols/menu/) for the menu protocol specification.
