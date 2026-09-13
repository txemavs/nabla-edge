# Packages

Apt package metadata for Debian packages in the NablaEdge ecosystem.

---

## Overview

This directory contains **metadata only**:

- Package definitions
- Control files
- Build scripts

## No Heavy Binaries

Heavy binaries (`.deb` files, compiled artifacts) are **not** stored in git. They are distributed via:

- **GitHub Releases** — Tagged releases include binary assets
- **CI Artifacts** — Built and uploaded by GitHub Actions

## Structure

```
packages/
├── nabla-menu-tools/        # CLI tools for menu management
│   ├── DEBIAN/
│   │   └── control
│   └── build.sh
└── README.md
```

## Building

Packages are built via CI. To build locally:

```bash
# Example (when implemented)
./packages/nabla-menu-tools/build.sh
```

Output `.deb` files go to a gitignored `build/` directory.

## Apt Repository

The apt repository is served via HTTP. See [dist/README.md](../dist/README.md) for serving configuration.
