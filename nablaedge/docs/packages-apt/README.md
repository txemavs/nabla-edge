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
- **CLIs** in PATH: `nabla-config`, `nabla-net`, `vpn-mode`, `nabla-image`
- Systemd services for network modes and accessories

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

## Publishing a Release

Use the publish script to build and deploy a new version:

```bash
# From repo root
./tools/publish-nabla-edge.sh
```

### Publish Script Options

```bash
./tools/publish-nabla-edge.sh                    # Patch bump (0.9.0 → 0.9.1)
./tools/publish-nabla-edge.sh --bump minor       # Minor bump (0.9.0 → 0.10.0)
./tools/publish-nabla-edge.sh --bump major       # Major bump (0.9.0 → 1.0.0)
./tools/publish-nabla-edge.sh --version 1.0.0    # Explicit version
./tools/publish-nabla-edge.sh --dry-run          # Preview without building
```

### What the Script Does

1. **Bumps version** in `packages/nabla-edge/DEBIAN/control` and `nabla-config`
2. **Builds** `nabla-edge_<ver>_all.deb` and `nabla-edge.tar.gz`
3. **Regenerates apt indexes** (Packages, Packages.gz, Release)
4. **Copies to Coco** (if `COCO_APT` and `COCO_PACKAGES` env vars are set)

### Manual Deployment (No Coco Access)

If you don't have direct Coco access, the script produces artifacts in `build/`:

```bash
./tools/publish-nabla-edge.sh
# Outputs:
#   build/nabla-edge_0.9.1_all.deb
#   build/nabla-edge.tar.gz
#   build/nabla-edge_0.9.1.tar.gz
```

Copy these to Coco manually:

| Artifact | Destination |
|----------|-------------|
| `.deb` | `\\coco\nabla.net\apt\pool\main\n\nabla-edge\` |
| `.tar.gz` | `\\coco\nabla.net\packages\` |

Then regenerate apt indexes on Coco:

```bash
cd /path/to/apt
apt-ftparchive packages pool/main > dists/stable/main/binary-arm64/Packages
gzip -kf dists/stable/main/binary-arm64/Packages
apt-ftparchive release dists/stable > dists/stable/Release
```

### Release Checklist

- [ ] Test changes locally on a Pi
- [ ] Run `./tools/publish-nabla-edge.sh` (bumps version + builds)
- [ ] Verify `.deb` installs: `sudo dpkg -i build/nabla-edge_*.deb`
- [ ] Copy to Coco (script does this if env vars set, else manual)
- [ ] Verify apt works: `curl -fsSL https://coco.nabla.net/apt/dists/stable/Release`
- [ ] Test upgrade on a Pi: `sudo apt update && sudo apt upgrade nabla-edge`
- [ ] Commit version bump and push

Details on package metadata live in [`../../../packages/`](../../../packages/).

---

## How Pis Update

Pis can update nabla-edge via two methods:

### 1. Via nabla-config Menu (Recommended)

```bash
sudo nabla-config
# → Update → Check for updates
```

The Update menu:
- Ensures `/etc/apt/sources.list.d/nabla.list` exists
- Runs `apt update` and shows available version
- Offers to upgrade if newer version available

This works even on Pis you can't SSH into — just access the local console.

### 2. Via apt Command Line

```bash
sudo apt update
sudo apt upgrade nabla-edge
```

Or upgrade everything:

```bash
sudo apt update && sudo apt upgrade
```

### Fresh Install: APT Source Auto-Installed

Every fresh install (via APT, .deb, or tarball) now configures the APT source automatically:

```
/etc/apt/sources.list.d/nabla.list
```

This means:
- **New Pis** can `apt upgrade` without manual source setup
- **Existing Pis** get the source added when they upgrade to 0.9.0+
- **Offline Pis** get the source from firstboot, enabling future upgrades when they connect

### Devices Without SSH Access

For Pis deployed without SSH (e.g., behind NAT, mesh-only):

1. **Console access**: Run `sudo nabla-config` → Update
2. **Automatic updates**: Set up unattended-upgrades (optional)
3. **Physical access**: Connect keyboard/monitor, run nabla-config

The APT source is always installed, so any network connectivity enables upgrades.

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
