# Examples

This folder contains usage examples showing how to adapt the `nabla.menu` protocol for real deployments.

---

## Example Locations

| Location | Purpose |
|----------|---------|
| [`protocols/menu/examples/`](../protocols/menu/examples/) | **Protocol reference**: Complete menu YAML and generated JSON demonstrating all item types, action kinds, and structure. Start here to understand the protocol. |
| [`nablaedge/docs/esphome-patterns/examples/`](../nablaedge/docs/esphome-patterns/examples/) | **Device skeletons**: ESPHome YAML templates for encoder + display hardware. |
| This folder | **Adaptation guidance**: How to replace placeholders with your actual configuration. |

---

## What the Protocol Examples Demonstrate

The files in [`protocols/menu/examples/`](../protocols/menu/examples/) show a complete menu with:

- **Submenus**: Kitchen, Garage, Scenes, System
- **Item types**: `button`, `toggle`, `number`, `info`, `back`
- **Action kinds**:
  - `ha_service` — Home Assistant service calls
  - `mqtt` — Direct MQTT publish (no HA required)
  - `nabla` — Internal device commands (`refresh_menu`, `reboot`)
- **State topics**: Binding MQTT state to toggle/info items
- **Emergency menu**: Fallback if main menu fails to load

**YAML source**: [`demo.menu.yaml`](../protocols/menu/examples/demo.menu.yaml) — Human-editable, with comments.

**JSON output**: [`demo.menu.json`](../protocols/menu/examples/demo.menu.json) — Publish this to MQTT.

---

## Placeholder Values

All examples use **sanitized placeholders** (see [AGENTS.md](../AGENTS.md)):

| Placeholder | Replace With |
|-------------|--------------|
| `site: demo` | Your site name (e.g., `site: home`) |
| `switch.example_light` | Your actual entity ID |
| `scene.example_night` | Your actual scene |
| `nabla/esp/demo/...` | Your MQTT topic prefix |
| `example.local` | Your actual hostname |

---

## Adapting for Your Setup

### 1. Copy the YAML source

```bash
cp protocols/menu/examples/demo.menu.yaml my-site.menu.yaml
```

### 2. Replace placeholders

```yaml
# Before
site: demo
entity_id: switch.example_light
state_topic: nabla/esp/demo/kitchen/light/state

# After
site: myhouse
entity_id: switch.kitchen_ceiling
state_topic: nabla/esp/myhouse/kitchen/light/state
```

### 3. Convert to JSON

```bash
# Using yq
yq -o=json my-site.menu.yaml > my-site.menu.json

# Or Python
python3 -c "import yaml, json, sys; print(json.dumps(yaml.safe_load(open(sys.argv[1])), indent=2))" my-site.menu.yaml > my-site.menu.json
```

### 4. Publish to MQTT

```bash
mosquitto_pub -h mqtt.example.local -t "nabla/menu/v1/myhouse/config" -r -f my-site.menu.json
```

The device receives the retained message and renders the menu immediately.

---

## Schema Validation

Validate your menu against the JSON Schema before publishing:

```bash
# Using ajv-cli
ajv validate -s protocols/menu/schema/menu.schema.json -d my-site.menu.json
```

See [protocols/menu/schema/](../protocols/menu/schema/) for the schema.

---

## Related Documentation

- [protocols/menu/PROTOCOL.md](../protocols/menu/PROTOCOL.md) — Full protocol specification
- [protocols/menu/device/CONTRACT.md](../protocols/menu/device/CONTRACT.md) — Firmware implementation contract
- [nablaedge/docs/](../nablaedge/docs/) — Edge device documentation
