# nabla.menu/v1 Protocol Specification

Version: 1.0.0-draft

---

## 1. Overview

The `nabla.menu` protocol enables dynamic, MQTT-driven menus for edge devices with rotary encoders and OLED displays.

### Design Principles

1. **YAML-First Authoring** — Menus are hand-edited as YAML, then converted to JSON for transmission
2. **MQTT Transport** — Retained JSON messages; devices receive updates immediately
3. **Firmware = Engine Only** — Devices render menus and execute actions; no menu logic in firmware
4. **No Reflash Updates** — Menu changes by publishing new JSON; firmware stays the same
5. **Backend-Agnostic** — Home Assistant is one option; MQTT and internal actions work without HA

---

## 2. MQTT Topics

Base prefix: `nabla/menu/v1/{site}/`

| Topic | Retained | Direction | Description |
|-------|----------|-----------|-------------|
| `config` | Yes | Server → Device | Full menu definition (JSON) |
| `version` | Yes | Server → Device | Menu version metadata |
| `cmd/{device}` | No | Server → Device | Commands to specific device |
| `hello` | No | Device → Server | Device announces itself |

### Optional Device Override

For per-device menu customization:

```
nabla/menu/v1/{site}/device/{device_id}/config
```

Device checks device-specific topic first, falls back to site config.

### Example Topics

```
nabla/menu/v1/demo/config           # Site "demo" menu
nabla/menu/v1/demo/version          # Version info
nabla/menu/v1/demo/cmd/oled01       # Command to device "oled01"
nabla/menu/v1/demo/hello            # Device hello messages
nabla/menu/v1/demo/device/oled01/config  # Override for oled01
```

---

## 3. Menu Structure

### 3.1 Root Object

```json
{
  "version": "1.0.0",
  "site": "demo",
  "generated_at": "2024-01-15T10:30:00Z",
  "menu": { ... },
  "emergency_menu": { ... }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `version` | Yes | Protocol version (semver) |
| `site` | Yes | Site identifier |
| `generated_at` | No | ISO 8601 timestamp |
| `menu` | Yes | Root menu item |
| `emergency_menu` | No | Fallback if main menu fails |

### 3.2 Menu Item

Every menu item has:

```json
{
  "type": "submenu",
  "label": "Kitchen",
  "icon": "lightbulb",
  "tags": ["lighting"],
  "caps": ["ha_service"],
  "items": [ ... ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Item type (see §4) |
| `label` | Yes | Display text |
| `icon` | No | Icon name (device-dependent) |
| `tags` | No | Categorization tags |
| `caps` | No | Required device capabilities |

---

## 4. Item Types

### 4.1 `submenu`

Container for nested items.

```json
{
  "type": "submenu",
  "label": "Kitchen",
  "items": [
    { "type": "button", "label": "Light On", ... }
  ]
}
```

### 4.2 `button`

Single-press action trigger.

```json
{
  "type": "button",
  "label": "Light On",
  "action": {
    "kind": "ha_service",
    "service": "light.turn_on",
    "data": { "entity_id": "switch.example_light" }
  }
}
```

### 4.3 `toggle`

Binary on/off control with state feedback.

```json
{
  "type": "toggle",
  "label": "Main Light",
  "state_topic": "nabla/esp/demo/light/state",
  "action_on": {
    "kind": "mqtt",
    "topic": "nabla/esp/demo/light/set",
    "payload": "ON"
  },
  "action_off": {
    "kind": "mqtt",
    "topic": "nabla/esp/demo/light/set",
    "payload": "OFF"
  }
}
```

### 4.4 `number`

Numeric value with range.

```json
{
  "type": "number",
  "label": "Brightness",
  "min": 0,
  "max": 100,
  "step": 5,
  "unit": "%",
  "state_topic": "nabla/esp/demo/brightness/state",
  "action": {
    "kind": "mqtt",
    "topic": "nabla/esp/demo/brightness/set",
    "payload_template": "{{ value }}"
  }
}
```

### 4.5 `info`

Read-only display item.

```json
{
  "type": "info",
  "label": "Temperature",
  "state_topic": "nabla/esp/demo/temp/state",
  "unit": "°C"
}
```

### 4.6 `back`

Navigation to parent menu.

```json
{
  "type": "back",
  "label": "← Back"
}
```

---

## 5. Actions

### 5.1 Action Object

```json
{
  "kind": "ha_service | mqtt | nabla",
  ...kind-specific fields...
}
```

### 5.2 `ha_service` — Home Assistant Service Call

```json
{
  "kind": "ha_service",
  "service": "light.turn_on",
  "data": {
    "entity_id": "switch.example_light",
    "brightness": 255
  }
}
```

**Domain Allowlist:** For security, firmware SHOULD restrict callable domains:

```
light, switch, scene, script, input_boolean, input_number,
input_select, automation, cover, fan, climate, media_player
```

### 5.3 `mqtt` — Direct MQTT Publish

```json
{
  "kind": "mqtt",
  "topic": "nabla/esp/demo/relay/set",
  "payload": "ON",
  "retain": false,
  "qos": 0
}
```

For non-HA entities or direct device control.

### 5.4 `nabla` — Internal Command

```json
{
  "kind": "nabla",
  "command": "reboot"
}
```

Reserved commands:
- `reboot` — Restart device
- `refresh_menu` — Re-fetch menu config
- `factory_reset` — Reset to defaults

---

## 6. Tags and Capabilities

### 6.1 Tags

Categorize items for filtering or device selection:

```json
{
  "tags": ["lighting", "kitchen", "favorite"]
}
```

### 6.2 Capabilities (`caps`)

Declare required device features:

```json
{
  "caps": ["ha_service", "rgb"]
}
```

Devices skip items requiring capabilities they lack.

Standard capabilities:
- `ha_service` — Can call Home Assistant
- `mqtt` — Can publish MQTT
- `rgb` — Has color display
- `audio` — Has audio output

---

## 7. Versioning

### 7.1 Version Topic

Publish to `nabla/menu/v1/{site}/version`:

```json
{
  "menu_version": "1.2.3",
  "protocol_version": "1.0.0",
  "updated_at": "2024-01-15T10:30:00Z",
  "checksum": "sha256:abc123..."
}
```

### 7.2 Protocol Version

Follows semver:
- **Major**: Breaking changes (devices may not understand)
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes

---

## 8. Emergency Menu

Fallback menu if main menu parsing fails:

```json
{
  "emergency_menu": {
    "type": "submenu",
    "label": "Emergency",
    "items": [
      {
        "type": "button",
        "label": "Reboot",
        "action": { "kind": "nabla", "command": "reboot" }
      },
      {
        "type": "button",
        "label": "Refresh Menu",
        "action": { "kind": "nabla", "command": "refresh_menu" }
      }
    ]
  }
}
```

---

## 9. Device Hello

Device announces presence on connect:

```
Topic: nabla/menu/v1/{site}/hello
```

```json
{
  "device_id": "oled01",
  "firmware_version": "2.1.0",
  "protocol_version": "1.0.0",
  "caps": ["ha_service", "mqtt"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 10. Extensibility

### 10.1 Custom Action Kinds

Additional action kinds can be added:

```json
{
  "kind": "custom_integration",
  "custom_field": "value"
}
```

Devices ignore unknown kinds gracefully.

### 10.2 Custom Item Types

Unknown types render as info with label only.

---

## 11. Security Considerations

1. **No Secrets in Menu** — Never include credentials in menu JSON
2. **Domain Allowlist** — Restrict ha_service to safe domains
3. **Topic Validation** — Validate MQTT topics before publish
4. **Rate Limiting** — Devices should rate-limit action execution

---

## 12. YAML to JSON Workflow

1. Edit `{site}.menu.yaml` (human-friendly)
2. Convert: `yaml2json {site}.menu.yaml > {site}.menu.json`
3. Publish: `mosquitto_pub -t nabla/menu/v1/{site}/config -r -f {site}.menu.json`

Or automate via CI/CD pipeline.
