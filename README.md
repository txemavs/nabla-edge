# Nabla Edge

Public repository for **NablaEdge** (edge stack), **NablaNet** Home Assistant integration, and shared protocols.

No secrets, credentials, private IPs, or production entity IDs. See [AGENTS.md](AGENTS.md) for contribution rules.

---

## Repository Structure

```
nabla-edge/
├── nablaedge/        # NablaEdge - Dom's edge system (ESPHome components, firmware)
├── homeassistant/    # NablaNet - Home Assistant integration (separate concern)
├── protocols/        # Backend-agnostic protocols (nabla.menu, etc.)
│   └── menu/         # nabla.menu/v1 - rotary/OLED menu protocol
├── packages/         # Apt package metadata (binaries via Releases/CI)
├── dist/             # HTTP serving configuration (apt repo, artifacts)
└── examples/         # Fictional placeholder examples
```

---

## Components

### NablaEdge (`nablaedge/`)

The edge stack: ESPHome custom components for rotary encoders, OLEDs, and the menu engine. Devices receive menu definitions over MQTT and render them locally—no firmware reflash needed for menu updates.

### NablaNet Home Assistant (`homeassistant/`)

Home Assistant integration for NablaNet. This is a **separate concern** from the edge protocol; HA is one possible backend, not a requirement.

### Protocols (`protocols/`)

Backend-agnostic protocol specifications. The `nabla.menu` protocol defines how menus are structured, transmitted, and executed. Actions can target:

- `ha_service` — Home Assistant service calls
- `mqtt` — Direct MQTT publish
- `nabla` — Internal NablaEdge commands

Non-HA entities are fully supported via MQTT or nabla actions.

### Packages (`packages/`)

Apt repository metadata for Debian packages. Heavy binaries are **not** stored in git; they're distributed via GitHub Releases or CI artifacts.

### Dist (`dist/`)

Configuration and notes for serving the apt repository and artifacts over HTTP. Works with any reverse proxy or static file server.

---

## Quick Links

- [AGENTS.md](AGENTS.md) — Contribution and sanitization rules
- [protocols/menu/PROTOCOL.md](protocols/menu/PROTOCOL.md) — nabla.menu/v1 specification
- [protocols/menu/schema/menu.schema.json](protocols/menu/schema/menu.schema.json) — JSON Schema

---

## License

See individual component directories for licensing information.
