# ESPHome patterns (how to build mounts)

A real fleet may keep many device YAMLs privately. **This folder teaches the patterns** so you can recreate mounts yourself — fictional names only (`demo-oled-encoder`), no site SSIDs or production entities.

## Pattern: OLED + rotary menu

Inspired by phone-style encoder remotes:

1. **Display** — SPI SSD1309/SSD1306 or I2C SSD1306; often rotated 180° if mounted upside-down.
2. **Input** — `rotary_encoder` (A/B) + push switch; invert direction in software if the knob feels backwards.
3. **State** — globals such as `menu_level` and `menu_idx`; home screen vs inside-menu layout differ.
4. **Paint** — today often lambdas that draw a list + selection caret; target architecture moves content to [`protocols/menu`](../../../protocols/menu/) (MQTT JSON) and paint to [`ui/ssd`](../../ui/ssd/).
5. **Home chrome** — optional status icons (radio / Wi-Fi / MQTT / BLE count) + clock; inside menus, list only.
6. **Actions** — IR, MQTT publish, or HA services — keep allowlists tight.

See [`examples/demo-oled-encoder.yaml`](examples/demo-oled-encoder.yaml) (skeleton).

## Pattern: BLE mesh helpers

- Presence advertisement on an interval (order of ~60s).
- “Need Wi-Fi” cry faster (~20s) when orphaned.
- Optional Phase-2: connectable ADV + GATT; a provisioned neighbour pushes fleet Wi-Fi using a shared `CHANGE_ME` secret (never put real passwords on MQTT/ADV).

Details: [`../ble-mesh/`](../ble-mesh/).

## Pattern: MQTT prefix

Devices often use a prefix like `nabla/esp/{device_id}/…` for telemetry; menu config uses `nabla/menu/v1/{site}/…`.

## What stays private

Exact zone lists, SSIDs, API keys, and per-person device YAMLs stay on the private package/docs share — not in this repo.
