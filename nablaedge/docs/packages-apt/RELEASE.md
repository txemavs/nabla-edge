# NablaEdge Release Workflow

**Mandatory** release process for publishing NablaEdge updates to the fleet.

---

## Overview

Every NablaEdge release that adds features Pis should receive **must** be published to:

1. **APT repository** — Fleet updates via `apt upgrade`
2. **Tarball** — Manual installs and first-boot injection

This is not optional. APT is the fleet update mechanism. All production Pis pull from `https://coco.nabla.net/apt/`.

---

## Release Checklist

### 1. Bump Version

Update the version in the Debian control file:

```
Package: nabla-edge
Version: X.Y.Z
Architecture: arm64
...
```

Keep a parallel control file for `amd64` if shipping multi-arch.

### 2. Build the .deb

Build the package from the runtime payload (`/opt/nabla-edge/` layout):

```bash
# Structure
nabla-edge_X.Y.Z_arm64/
├── DEBIAN/
│   └── control
└── opt/
    └── nabla-edge/
        ├── bin/
        ├── install.sh
        └── ...

# Build
dpkg-deb --build nabla-edge_X.Y.Z_arm64
```

Output: `nabla-edge_X.Y.Z_arm64.deb`

### 3. Update APT Pool

Copy the `.deb` to the pool directory:

```
\\coco\nabla.net\apt\pool\main\nabla-edge_X.Y.Z_arm64.deb
```

Keep previous versions for rollback capability.

### 4. Regenerate Repository Metadata

On the APT server, regenerate `Packages` and `Release`:

```bash
cd /path/to/apt

# Generate package index
apt-ftparchive packages pool/main > dists/stable/main/binary-arm64/Packages
gzip -kf dists/stable/main/binary-arm64/Packages

# Generate release metadata
apt-ftparchive release dists/stable > dists/stable/Release
```

Helper scripts available at `\\coco\nabla.net\tools\rebuild-apt-repo.sh`.
See also `COMO-APT.txt` under `apt/` for historical notes.

### 5. Sync to Web Mirror

Sync the APT tree to the HTTP server:

```
Source: \\coco\nabla.net\apt\
Target: \\coco\web\apt\
```

This makes the repo available at `https://coco.nabla.net/apt/`.

### 6. Update Tarball

Build and copy the tarball for manual/offline installs:

```bash
# Create tarball from the same payload
tar czf nabla-edge.tar.gz nabla-edge/

# Copy to packages directory
cp nabla-edge.tar.gz "\\coco\nabla.net\packages\nabla-edge.tar.gz"

# Keep a dated copy for history
cp nabla-edge.tar.gz "\\coco\nabla.net\packages\nabla-edge-X.Y.Z.tar.gz"
```

### 7. Verify Release

Confirm the release is live:

```bash
# Check Release file is accessible
curl -fsSL https://coco.nabla.net/apt/dists/stable/Release

# Check package is listed (from any machine)
curl -fsSL https://coco.nabla.net/apt/dists/stable/main/binary-arm64/Packages | grep -A5 "Package: nabla-edge"
```

### 8. Test on a Pi

On a target Pi:

```bash
sudo apt update
apt policy nabla-edge
# Should show the new version as candidate

sudo apt upgrade nabla-edge
# Verify installation
nabla-config --version  # or equivalent
```

---

## Repository Layout

```
\\coco\nabla.net\apt\           # APT truth (master)
├── dists/
│   └── stable/
│       ├── main/
│       │   └── binary-arm64/
│       │       ├── Packages
│       │       └── Packages.gz
│       └── Release
└── pool/
    └── main/
        ├── nabla-edge_0.7.0_arm64.deb
        └── nabla-edge_0.8.0_arm64.deb   # current

\\coco\web\apt\                 # HTTP mirror → https://coco.nabla.net/apt/

\\coco\nabla.net\packages\      # Tarballs
├── nabla-edge.tar.gz           # Latest (symlink or copy)
├── nabla-edge-0.7.0.tar.gz
└── nabla-edge-0.8.0.tar.gz     # current
```

---

## Client Setup Reference

For new Pis, add the APT source:

```bash
echo 'deb [trusted=yes] https://coco.nabla.net/apt/ stable main' | \
  sudo tee /etc/apt/sources.list.d/nabla.list

sudo apt update
sudo apt install nabla-edge
```

---

## Release History

| Version | Date | Notes |
|---------|------|-------|
| 0.8.0 | 2026-09 | OLED menu: Reloj+Config (PR #20) |

---

## Do Not

- **Do not** ship Pi-only copies without publishing to APT and tarball
- **Do not** skip the web mirror sync (Pis can't reach the SMB share)
- **Do not** forget the dated tarball copy (history/rollback)
- **Do not** commit `.deb` files to git (too large)

---

## Related

- [README.md](README.md) — Installation and APT details
- [../../../packages/](../../../packages/) — Package metadata
- [../../../AGENTS.md](../../../AGENTS.md) — Contribution rules
