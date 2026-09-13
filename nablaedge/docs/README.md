# ∇ NablaEdge Documentation

**Learn HOW to build your own edge network — not where ours are.**

This documentation teaches you to build NablaEdge from scratch. Every concept is explained, every script is readable, every example uses placeholders you replace with your own values.

One folder per topic. Open it, understand how it works, modify it yourself.

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

```
Start here ──► architecture/     Understand the 3-layer model
         │
         ├──► imaging/           Create your first boot image
         │
         ├──► pi-config-menu/    Configure your node
         │
         ├──► accessories/       Wire OLED, encoder, etc.
         │
         └──► protocols/menu/    Write menus for your devices
```

1. **Read [architecture/](architecture/)** — understand the layers before building
2. **Follow the build path** — imaging → config → accessories → menus
3. **Use the scripts** in [`../scripts/`](../scripts/) as reference or copy them
4. **Replace placeholders** — `CHANGE_ME`, `192.0.2.x`, `example.local` become your values

### What's NOT Here

- Real IP addresses, hostnames, or SSIDs
- Site names or locations
- Credentials or secrets
- Private infrastructure details

You learn the **method**; you supply the **specifics**.

---

## Related Resources

| Location | Content |
|----------|---------|
| [`../scripts/`](../scripts/) | Sanitized CLI tools for learning |
| [`../ui/ssd/`](../ui/ssd/) | OLED paint layer (layout, tokens, profiles) |
| [`../../protocols/menu/`](../../protocols/menu/) | Menu JSON protocol (MQTT) |
| [`../../packages/`](../../packages/) | Apt package metadata |
| [`../../dist/`](../../dist/) | HTTP serving configuration |
