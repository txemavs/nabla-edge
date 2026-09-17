# NablaEdge Scripts

Sanitized copies of Edge node tools. These are the readable/editable source for how the tools work.

| Script | Role | Install Path |
|--------|------|--------------|
| [`nabla-config`](nabla-config) | Whiptail panel: network, imaging, accessories, voice | `/usr/local/bin/nabla-config` |
| [`vpn-mode`](vpn-mode) | Private LAN gateway + Tailscale (cable/ap/cable-ap/off) | `/usr/local/bin/vpn-mode` |

Private site packages and installs live on the private package share; this tree is the **readable** source.

---

## vpn-mode

Golden reference script for Nabla Net gateway mode. Verified on production gateway Pis.

**Modes:**

- `cable` — WiFi uplink, eth0 gateway (10.100.N.1/24), DHCP for client Pis
- `ap` — Ethernet uplink, WiFi AP mode (Nabla Net SSID)
- `cable-ap` — WiFi uplink, eth0 + wlan1 AP bridged (same subnet)
- `off` — Disable gateway mode
- `status` — Show current configuration

**Quick usage:**

```bash
# Cable mode (most common for gateway Pis)
sudo vpn-mode cable

# Check status
vpn-mode status
```

**Installation to new Pi:**

```bash
# Copy from repo
sudo cp vpn-mode /usr/local/bin/vpn-mode
sudo chmod +x /usr/local/bin/vpn-mode

# Or via nabla-edge package
sudo apt install nabla-edge
```

**Key features:**

- Auto-detects interfaces (eth0, wlan0)
- Subnet octet from hostname pattern (gateway1 → .1, gateway2 → .2)
- dnsmasq with `bind-dynamic` for boot resilience
- systemd drop-in: `Restart=on-failure` for reliability
- Tailscale subnet advertisement

See [`../docs/network-modes/`](../docs/network-modes/) for detailed documentation.

---

## nabla-config

Interactive whiptail menu for Pi configuration. Wraps `vpn-mode` for network operations.

See [`../docs/pi-config-menu/`](../docs/pi-config-menu/) for the narrative.

---

## Installation

These scripts are installed by the `nabla-edge` package:

```bash
echo 'deb [trusted=yes] https://coco.nabla.net/apt/ stable main' | \
  sudo tee /etc/apt/sources.list.d/nabla.list
sudo apt update && sudo apt install nabla-edge
```

Or for first-boot imaging, see [`../docs/imaging/`](../docs/imaging/).
