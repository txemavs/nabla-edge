# Firmware Contract — nabla.menu/v1

Implementation requirements for devices supporting the nabla.menu protocol.

---

## 1. Overview

The device firmware is a **rendering engine**. It:

1. Connects to MQTT broker
2. Subscribes to menu config topics
3. Parses JSON menu definitions
4. Renders menus on display
5. Handles rotary encoder input
6. Executes actions

**Firmware does NOT contain menu content.** Menus are delivered via MQTT.

---

## 2. MQTT Requirements

### 2.1 Connection

- Connect to configured MQTT broker on startup
- Reconnect automatically on disconnect (exponential backoff)
- Support TLS (optional but recommended)

### 2.2 Subscriptions

On connect, subscribe to:

```
nabla/menu/v1/{site}/config              # Site menu (retained)
nabla/menu/v1/{site}/version             # Version info (retained)
nabla/menu/v1/{site}/cmd/{device_id}     # Device commands
nabla/menu/v1/{site}/device/{device_id}/config  # Device override (optional)
```

### 2.3 Publications

On connect, publish hello:

```
Topic: nabla/menu/v1/{site}/hello
QoS: 0
Retain: false
```

Payload: See PROTOCOL.md §9.

---

## 3. Menu Parsing

### 3.1 JSON Parsing

- Parse full JSON menu on receipt
- Validate against expected structure
- Handle missing optional fields gracefully

### 3.2 Fallback Behavior

If parsing fails:
1. Log error
2. Load `emergency_menu` if present
3. Otherwise, display built-in minimal menu

### 3.3 Memory Management

- Support menus up to at least 8KB
- Stream-parse if memory constrained
- Discard previous menu before loading new

---

## 4. Display Rendering

### 4.1 Item Rendering

| Type | Display |
|------|---------|
| `submenu` | Label with ">" indicator |
| `button` | Label (press to execute) |
| `toggle` | Label + ON/OFF state |
| `number` | Label + value + unit |
| `info` | Label + value (read-only) |
| `back` | Label (typically "← Back") |

### 4.2 Navigation

- Rotary CW: Next item
- Rotary CCW: Previous item
- Button press: Select/execute
- Long press: Optional (back, or menu)

### 4.3 State Display

For items with `state_topic`:
- Subscribe to topic
- Update display when state changes
- Show "?" if state unknown

---

## 5. Action Execution

### 5.1 `ha_service`

If device has Home Assistant integration:

1. Validate domain against allowlist
2. Call HA service via configured method (REST, WebSocket, MQTT)
3. Handle errors gracefully

**Domain Allowlist (recommended):**
```
light, switch, scene, script, input_boolean, input_number,
input_select, automation, cover, fan, climate, media_player
```

### 5.2 `mqtt`

1. Validate topic format
2. Process `payload_template` if present (substitute `{{ value }}`)
3. Publish to topic with specified QoS and retain

### 5.3 `nabla`

Internal commands:

| Command | Action |
|---------|--------|
| `reboot` | Restart device |
| `refresh_menu` | Re-fetch menu from MQTT |
| `factory_reset` | Clear config, restart |

---

## 6. Capabilities

### 6.1 Reporting

In hello message, report capabilities:

```json
{
  "caps": ["ha_service", "mqtt"]
}
```

### 6.2 Filtering

When rendering menu:
- Check each item's `caps` array
- Skip items requiring capabilities device lacks

Example: If device lacks `ha_service`, skip items with:
```json
{ "caps": ["ha_service"] }
```

---

## 7. Error Handling

### 7.1 Network Errors

- Retry MQTT connection with backoff
- Cache last known menu in flash
- Operate from cache if broker unreachable

### 7.2 Action Errors

- Display brief error feedback
- Do not block UI
- Log errors for debugging

### 7.3 Parse Errors

- Fall back to emergency menu
- Publish error to status topic (optional)

---

## 8. Configuration

Device must be configurable with:

| Parameter | Required | Description |
|-----------|----------|-------------|
| `mqtt_host` | Yes | Broker hostname |
| `mqtt_port` | No | Default: 1883 (8883 for TLS) |
| `mqtt_user` | No | MQTT username |
| `mqtt_pass` | No | MQTT password |
| `site` | Yes | Site identifier |
| `device_id` | Yes | Unique device ID |

Configuration via:
- Compile-time defines
- Runtime AP config portal
- MQTT config topic

---

## 9. Version Compatibility

### 9.1 Protocol Version

- Parse `version` field from menu
- Major version mismatch: Log warning, attempt parse anyway
- Minor version mismatch: OK, new features may not render

### 9.2 Firmware Version

Include in hello message for server-side tracking.

---

## 10. Testing

### 10.1 Minimal Test Menu

Device should render correctly:

```json
{
  "version": "1.0.0",
  "site": "test",
  "menu": {
    "type": "submenu",
    "label": "Test",
    "items": [
      { "type": "info", "label": "Status", "state_topic": "test/status" },
      { "type": "button", "label": "Reboot", "action": { "kind": "nabla", "command": "reboot" } },
      { "type": "back", "label": "Back" }
    ]
  }
}
```

### 10.2 Edge Cases

Test:
- Empty `items` array
- Missing optional fields
- Unknown item types (should skip gracefully)
- Very long labels (truncate or scroll)
- Deep nesting (at least 5 levels)
