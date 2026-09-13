# NablaEdge docs (learning map)

One folder per topic so you can open it, see how it works, and change it.

| Folder | What you learn |
|--------|----------------|
| [architecture/](architecture/) | Big picture: Edge node, Nabla Net, Tailscale mesh (generic) |
| [pi-config-menu/](pi-config-menu/) | Pi whiptail panel (`nabla-config`): Red / Medios / Accesorios |
| [network-modes/](network-modes/) | `cable` · `ap` · `cable-ap` · `off` — see also `pdf/` |
| [imaging/](imaging/) | Fetch Pi OS → first-boot → write USB/SD · OTP |
| [accessories/](accessories/) | OLED / rotary / large SPI · pinouts in `pdf/` · UI in `oled-ui/` |
| [ble-mesh/](ble-mesh/) | BLE presence / contagion (no real secrets) |
| [packages-apt/](packages-apt/) | Publishing `.deb` / HTTP apt |
| [voice-satellite/](voice-satellite/) | Voice Assist satellite (stub) |
| [manuals/](manuals/) | PDF catalog · private list stays off git |

Paint tokens/layout live in [`../ui/ssd/`](../ui/ssd/). Menu **protocol** (MQTT JSON) lives in [`../../protocols/menu/`](../../protocols/menu/).
