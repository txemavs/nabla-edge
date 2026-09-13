# nabla.menu Protocol

Backend-agnostic menu protocol for edge devices with rotary encoders and OLED displays.

---

## Overview

The `nabla.menu` protocol defines how menus are:

1. **Authored** — Hand-edited YAML files
2. **Transmitted** — MQTT retained JSON messages
3. **Rendered** — Firmware displays and handles input
4. **Executed** — Actions trigger services, MQTT, or internal commands

## Key Principle

**Firmware is a rendering engine only.** Menu content updates without reflashing devices.

## Documentation

| Document | Description |
|----------|-------------|
| [PROTOCOL.md](PROTOCOL.md) | Full nabla.menu/v1 specification |
| [device/CONTRACT.md](device/CONTRACT.md) | Firmware implementation contract |
| [schema/menu.schema.json](schema/menu.schema.json) | JSON Schema for validation |

## Examples

| File | Description |
|------|-------------|
| [examples/demo.menu.yaml](examples/demo.menu.yaml) | Human-editable source (site: demo) |
| [examples/demo.menu.json](examples/demo.menu.json) | Generated JSON for MQTT |

## Quick Start

1. Write menu in YAML (see examples)
2. Convert to JSON
3. Publish to MQTT: `nabla/menu/v1/{site}/config`
4. Device receives and renders

## Action Kinds

| Kind | Target | HA Required? |
|------|--------|--------------|
| `ha_service` | Home Assistant service | Yes |
| `mqtt` | MQTT topic publish | No |
| `nabla` | Internal NablaEdge command | No |

Non-HA entities work via `mqtt` or `nabla` actions.

## Related

- [nablaedge/](../../nablaedge/) — Edge device firmware
- [homeassistant/](../../homeassistant/) — HA integration (optional backend)
