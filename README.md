# Nabla Edge

Public repository for **NablaEdge** (edge stack), **NablaNet** Home Assistant integration, and shared protocols.

No secrets, credentials, private IPs, or production entity IDs. See [AGENTS.md](AGENTS.md) for contribution rules.

---

## What Is This?

**NablaEdge** is an edge-device system for home automation. Devices (ESP32, Raspberry Pi) receive menu definitions over MQTT and render them locally—no firmware reflash needed for menu changes.

Key ideas:

- **MQTT-driven menus**: Publish a JSON menu; devices update instantly.
- **Backend-agnostic protocol**: The `nabla.menu` protocol works with Home Assistant, pure MQTT, or internal commands.
- **Home Assistant optional**: NablaNet integrates with HA, but edge devices don't require it.
- **Apt distribution**: Debian packages for Pi tools, served via the included apt repo config.

---

## Repository Structure

```
nabla-edge/
├── nablaedge/        # Edge stack (ESPHome components, voice satellite, config tools)
├── homeassistant/    # NablaNet Home Assistant integration (optional backend)
├── protocols/        # Backend-agnostic protocols
│   └── menu/         # nabla.menu/v1 specification + schema + examples
├── packages/         # Apt package metadata (binaries via Releases/CI)
├── dist/             # HTTP serving configuration (apt repo, artifacts)
└── examples/         # Sanitized placeholder examples (see Examples section)
```

---

## Components

### Protocols (`protocols/`)

Backend-agnostic protocol specifications. The `nabla.menu` protocol defines how menus are structured, transmitted, and executed. Actions can target:

- `ha_service` — Home Assistant service calls
- `mqtt` — Direct MQTT publish
- `nabla` — Internal NablaEdge commands

See [protocols/menu/README.md](protocols/menu/README.md) for the full spec, JSON schema, and working examples.

### NablaEdge (`nablaedge/`)

The edge stack: ESPHome custom components for rotary encoders, menu engine, voice satellite support, and configuration tools. Devices receive menu definitions over MQTT and render them locally.

- **Menu engine**: MQTT-driven menus, EC11 encoder input
- **Voice satellite**: LVA installer for Raspberry Pi (Home Assistant Assist)
- **Config tools**: Interactive `nabla-config` menu for Pi setup
- **UI components**: Optional OLED display support (SSD1306/SSD1309)

### NablaNet Home Assistant (`homeassistant/`)

Home Assistant integration for NablaNet. This is a **separate concern** from the edge protocol; HA is one possible backend, not a requirement.

### Packages (`packages/`)

Apt repository metadata for Debian packages. Heavy binaries are **not** stored in git; they're distributed via GitHub Releases or CI artifacts.

### Dist (`dist/`)

Configuration and notes for serving the apt repository and artifacts over HTTP. Works with any reverse proxy or static file server.

---

## Examples

Examples are split by purpose:

| Location | Contents |
|----------|----------|
| [`protocols/menu/examples/`](protocols/menu/examples/) | Protocol examples: menu YAML source and generated JSON |
| [`examples/`](examples/) | Usage examples: how to adapt protocol definitions for deployment |
| [`nablaedge/docs/esphome-patterns/examples/`](nablaedge/docs/esphome-patterns/examples/) | ESPHome device skeletons |

All examples use **sanitized placeholder values** (`demo` site, `example_*` entity IDs) per [AGENTS.md](AGENTS.md). They demonstrate structure and syntax; replace placeholders with your actual configuration before deployment.

See [examples/README.md](examples/README.md) for guidance on adapting these to your setup.

---

## Quick Links

- [AGENTS.md](AGENTS.md) — Contribution and sanitization rules
- [protocols/menu/PROTOCOL.md](protocols/menu/PROTOCOL.md) — nabla.menu/v1 specification
- [protocols/menu/schema/menu.schema.json](protocols/menu/schema/menu.schema.json) — JSON Schema
- [nablaedge/docs/](nablaedge/docs/) — Learning map and documentation

---

## License

See individual component directories for licensing information.
