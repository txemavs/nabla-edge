# Packages and APT Repository

How to install ∇ NablaEdge from the public APT repository, and how the release pipeline works.

---

## Quick Install (APT)

NablaEdge is published to a Debian APT repository at **https://coco.nabla.net/apt/**.

### 1. Add the Repository

```bash
# Add the Nabla APT source
echo 'deb [trusted=yes] https://coco.nabla.net/apt/ stable main' | \
  sudo tee /etc/apt/sources.list.d/nabla.list
```

### 2. Update and Install

```bash
sudo apt update
sudo apt install nabla-edge
```

That's it. The package installs:

- **Tools** under `/opt/nabla-edge/`
- **CLIs** to `/usr/local/bin/`: `nabla-config`, `nabla-image` (and `nabla-net`, `vpn-mode` when present)
- Systemd services for network modes and accessories

The tools are installed to `/usr/local/bin/` so they work with `sudo`:

```bash
sudo nabla-config     # Works — root PATH includes /usr/local/bin
```

---

## What Gets Installed

| Component | Description |
|-----------|-------------|
| `/opt/nabla-edge/` | Core tools, scripts, and configuration |
| `nabla-config` | Interactive whiptail menu for system setup |
| `nabla-net` | Network mode management (cable, ap, cable-ap, off) |
| `vpn-mode` | Mesh overlay network integration |
| `nabla-image` | SD/USB imaging tool for new nodes |
| Systemd units | `nabla-net.service`, `nabla-oled.service`, etc. |

### Optional Full Provision

After installing the package, you can run the full provision script:

```bash
sudo /opt/nabla-edge/install.sh
```

This applies site-specific configuration, enables services, and completes the initial setup beyond the base package install.

---

## APT Repository Details

| Property | Value |
|----------|-------|
| Base URL | `https://coco.nabla.net/apt/` |
| Suite | `stable` |
| Component | `main` |
| Architecture | `arm64` (Raspberry Pi), `amd64` |
| GPG signing | Not yet — use `[trusted=yes]` |

Source line:

```
deb [trusted=yes] https://coco.nabla.net/apt/ stable main
```

Repository structure:

```
/apt/
├── dists/
│   └── stable/
│       ├── main/
│       │   └── binary-arm64/
│       │       └── Packages
│       └── Release
└── pool/
    └── main/
        └── nabla-edge_*.deb
```

Verify the repository is reachable:

```bash
curl -fsSL https://coco.nabla.net/apt/dists/stable/Release
```

---

## Tarball (Legacy / Manual Install)

A tarball is also published for manual installs, first-boot injection, or environments where APT isn't available:

```
https://coco.nabla.net/nabla.net/pkgs/nabla-edge.tar.gz
```

### Manual Tarball Install

```bash
curl -fsSL -o nabla-edge.tar.gz \
  https://coco.nabla.net/nabla.net/pkgs/nabla-edge.tar.gz
tar xzf nabla-edge.tar.gz
cd nabla-edge && sudo ./install.sh
```

### TAR vs APT

| Method | Use Case |
|--------|----------|
| **APT** | Preferred for install and upgrades; `apt upgrade` keeps nodes current |
| **Tarball** | First-boot injection (imaging), offline installs, legacy scripts |

**Release policy**: every release ships both a `.deb` to the APT pool and a `.tar.gz` to the pkgs folder.

---

## Publishing Checklist (Maintainers)

High-level steps to publish a new release:

1. **Build the `.deb`** — run the package build script (CI or local)
2. **Add to pool** — place `.deb` in `pool/main/`
3. **Regenerate metadata**:
   ```bash
   apt-ftparchive packages pool/main > dists/stable/main/binary-arm64/Packages
   gzip -k dists/stable/main/binary-arm64/Packages
   apt-ftparchive release dists/stable > dists/stable/Release
   ```
4. **Sync to HTTP** — push the `apt/` tree to the coco HTTP server
5. **Verify** — confirm `Release` file is accessible:
   ```bash
   curl -I https://coco.nabla.net/apt/dists/stable/Release
   ```
6. **Update tarball** — build and upload `nabla-edge.tar.gz` to `/nabla.net/pkgs/`

Details on package metadata live in [`../../../packages/`](../../../packages/).

---

## Upgrading

Once installed via APT, upgrades are standard Debian:

```bash
sudo apt update
sudo apt upgrade nabla-edge
```

Or upgrade everything:

```bash
sudo apt update && sudo apt upgrade
```

---

## Troubleshooting

### "Repository does not have a Release file"

Check the URL is correct and reachable:

```bash
curl -v https://coco.nabla.net/apt/dists/stable/Release
```

### "The following packages cannot be authenticated"

The repo currently uses `[trusted=yes]` (no GPG). Ensure your source line includes this:

```
deb [trusted=yes] https://coco.nabla.net/apt/ stable main
```

### Package Not Found

Ensure you ran `apt update` after adding the source:

```bash
sudo apt update
apt-cache search nabla
```

---

## Related

- [../imaging/](../imaging/) — SD/USB imaging with first-boot injection
- [../../../packages/](../../../packages/) — Package metadata and build scripts
- [../../../dist/](../../../dist/) — HTTP serving configuration
- GitHub: [https://github.com/txemavs/nabla-edge](https://github.com/txemavs/nabla-edge)
