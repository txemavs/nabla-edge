# NablaEdge scripts

Edge node CLI tools. Install via `../install.sh` or the `nabla-edge` .deb package.

| Script | Role |
|--------|------|
| [`nabla-config`](nabla-config) | Whiptail panel: network, imaging media, accessories, voice (v0.8+) |
| [`nabla-image`](nabla-image) | SD/USB imaging tool for Nabla Pi OS |

## Installation

After installation (via `install.sh` or .deb), tools are available system-wide:

```bash
sudo nabla-config     # Interactive menu
sudo nabla-image --help
```

Tools are installed to `/usr/local/bin/` so `sudo` works (root PATH includes `/usr/local/bin`).

### Manual install

```bash
cd /path/to/nablaedge
sudo ./install.sh
```

### Via APT (recommended)

```bash
sudo apt install nabla-edge
```

See [`../docs/packages-apt/`](../docs/packages-apt/) for APT setup.

## Documentation

- [`../docs/pi-config-menu/`](../docs/pi-config-menu/) — nabla-config menu reference
- [`../docs/imaging/`](../docs/imaging/) — nabla-image usage
