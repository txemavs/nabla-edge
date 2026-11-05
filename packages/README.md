# Packages

Debian package source and metadata for the nabla-edge package.

---

## Overview

This directory contains:

- `nabla-edge/DEBIAN/` — Debian control files (control, postinst, prerm)
- `nabla-edge/etc/` — Configuration files installed by the package
- `nabla-edge/opt/` — Firstboot scripts and package assets

## Structure

```
packages/
├── nabla-edge/
│   ├── DEBIAN/
│   │   ├── control           # Package metadata
│   │   ├── postinst          # Post-install script
│   │   └── prerm             # Pre-remove script
│   ├── etc/
│   │   └── apt/sources.list.d/
│   │       └── nabla.list    # APT source for updates
│   └── opt/nabla-edge/
│       └── firstboot/
│           └── 04-install-packages.sh
└── README.md
```

## Building

Use the publish script from the repo root:

```bash
./tools/publish-nabla-edge.sh
```

This:
1. Bumps the version (patch by default)
2. Builds `nabla-edge_<ver>_all.deb` in `build/`
3. Builds `nabla-edge.tar.gz` in `build/`
4. Deploys to Coco (if `COCO_APT`/`COCO_PACKAGES` env vars set)

### Build Options

```bash
./tools/publish-nabla-edge.sh --bump minor      # 0.9.0 → 0.10.0
./tools/publish-nabla-edge.sh --version 1.0.0   # Explicit version
./tools/publish-nabla-edge.sh --dry-run         # Preview only
```

## No Heavy Binaries in Git

`.deb` and `.tar.gz` files are gitignored. They are:

- Built locally via `publish-nabla-edge.sh`
- Distributed via Coco apt repo: https://coco.nabla.net/apt/

## What Gets Built

The `.deb` package includes:

| Path | Source |
|------|--------|
| `/opt/nabla-edge/bin/nabla-config` | `nablaedge/scripts/nabla-config` |
| `/opt/nabla-edge/voice/install-lva.sh` | `nablaedge/voice/install-lva.sh` |
| `/opt/nabla-edge/firstboot/*.sh` | `packages/nabla-edge/opt/nabla-edge/firstboot/` |
| `/etc/apt/sources.list.d/nabla.list` | `packages/nabla-edge/etc/apt/sources.list.d/nabla.list` |
| `/opt/nabla-edge/VERSION` | Generated |

Post-install creates symlinks in `/usr/local/bin/` for CLIs.

## APT Repository

The apt repository is served at https://coco.nabla.net/apt/

See:
- [nablaedge/docs/packages-apt/](../nablaedge/docs/packages-apt/) — Full APT/install docs
- [dist/README.md](../dist/README.md) — Serving configuration
