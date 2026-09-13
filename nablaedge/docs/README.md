# NablaEdge docs (learning map)

One folder per topic so you can open it, see how it works, and change it.

| Folder | What you learn |
|--------|----------------|
| [architecture/](architecture/) | Big picture: Edge node, Nabla Net, Tailscale mesh (generic) |
| [pi-config-menu/](pi-config-menu/) | Pi whiptail panel (`nabla-config`): Red / Medios / Accesorios |
| [network-modes/](network-modes/) | `cable` · `ap` · `cable-ap` · `off` — see also `pdf/` |
| [imaging/](imaging/) | Fetch Pi OS → first-boot → write USB/SD · OTP |
| [accessories/](accessories/) | OLED / rotary / large SPI · pinouts in `pdf/` · wiring in `diagrams/` |
| [esphome-patterns/](esphome-patterns/) | ESP32 OLED+encoder menu · BLE mesh protocol patterns |
| [ble-mesh/](ble-mesh/) | BLE presence / contagion (no real secrets) |
| [packages-apt/](packages-apt/) | Publishing `.deb` / HTTP apt |
| [voice-satellite/](voice-satellite/) | Voice Assist satellite (stub) |
| [manuals/](manuals/) | PDF catalog · private list stays off git |

---

## How to Use This Manual

1. **Start with [architecture/](architecture/)** to understand the layers
2. **Pick a topic folder** — each has a README explaining how it works
3. **Scripts live in [`../scripts/`](../scripts/)** — sanitized reference copies of `nabla-config`, `nabla-net`, `nabla-image`
4. **Edit and experiment** — docs are designed to be modified

---

## Related Resources

| Location | Content |
|----------|---------|
| [`../scripts/`](../scripts/) | Sanitized CLI tools for learning |
| [`../ui/ssd/`](../ui/ssd/) | OLED paint layer (layout, tokens, profiles) |
| [`../../protocols/menu/`](../../protocols/menu/) | Menu JSON protocol (MQTT) |
| [`../../packages/`](../../packages/) | Apt package metadata |
| [`../../dist/`](../../dist/) | HTTP serving configuration |
