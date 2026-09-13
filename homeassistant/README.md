# NablaNet Home Assistant Integration

Home Assistant integration for the NablaNet ecosystem.

---

## Overview

This is a **separate concern** from the edge protocol. Home Assistant is one possible backend for `nabla.menu` actions, but the protocol itself is backend-agnostic.

## Planned Structure

```
homeassistant/
├── custom_components/
│   └── nablanet/            # HA custom component
├── packages/                 # HA package YAML configs
├── automations/             # Example automations
└── dashboards/              # Lovelace examples
```

## Relationship to nabla.menu

The `ha_service` action kind in nabla.menu calls Home Assistant services. But nabla.menu also supports:

- `mqtt` — Direct MQTT publish (no HA needed)
- `nabla` — Internal NablaEdge commands

Non-HA entities work fine via MQTT actions.

## Status

🚧 **Stub** — Integration to be added.

See [protocols/menu/PROTOCOL.md](../protocols/menu/PROTOCOL.md) for action kinds.
