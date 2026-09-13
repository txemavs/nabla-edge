# Packages and Apt Repository

How NablaEdge packages are built and distributed via apt.

---

## Overview

NablaEdge uses Debian packages (`.deb`) distributed via a self-hosted apt repository:

```mermaid
flowchart LR
    Source[Package Source] --> Build[Build .deb]
    Build --> Repo[Apt Repository]
    Repo --> HTTP[HTTP Server]
    HTTP --> Pi[Edge Nodes]
```

---

## Repository Structure

See [packages/](../../../packages/) for package metadata and [dist/](../../../dist/) for HTTP serving config.

```
/apt/
├── dists/
│   └── stable/
│       └── main/
│           └── binary-arm64/
│               └── Packages.gz
└── pool/
    └── main/
        ├── nabla-edge_1.0.0_arm64.deb
        ├── nabla-net_1.0.0_arm64.deb
        ├── nabla-oled_1.0.0_arm64.deb
        └── nabla-config_1.0.0_arm64.deb
```

---

## Packages

| Package | Description |
|---------|-------------|
| `nabla-edge` | Core edge system, dependencies |
| `nabla-net` | Network management service |
| `nabla-oled` | OLED display service |
| `nabla-config` | Configuration tool (whiptail) |
| `nabla-menu-tools` | CLI tools for menu management |

---

## Client Configuration

On edge nodes, add the repository:

```bash
# Add repository
echo "deb [trusted=yes] https://apt.example.local/nabla stable main" \
    | sudo tee /etc/apt/sources.list.d/nabla.list

# Update and install
sudo apt update
sudo apt install nabla-edge
```

Replace `apt.example.local` with your actual mirror hostname.

---

## Hosting Options

The apt repository can be served by any HTTP server:

| Server | Notes |
|--------|-------|
| Nginx | Static file serving, directory listing |
| Caddy | Automatic HTTPS |
| Apache | Traditional hosting |
| Synology Web Station | NAS-based |
| GitHub Releases | For public packages |

### Nginx Example

```nginx
server {
    listen 80;
    server_name apt.example.local;
    
    root /var/www/apt;
    autoindex on;
    
    location / {
        try_files $uri $uri/ =404;
    }
}
```

---

## Building Packages

Packages are built via CI/CD. The metadata lives in git, binaries are distributed via releases.

### Package Metadata

In [packages/](../../../packages/):

```
packages/
├── nabla-edge/
│   ├── DEBIAN/
│   │   ├── control
│   │   ├── postinst
│   │   └── prerm
│   └── build.sh
└── nabla-config/
    └── ...
```

### Control File Example

```
Package: nabla-edge
Version: 1.0.0
Architecture: arm64
Maintainer: NablaEdge Team <team@example.local>
Depends: python3, python3-pip
Description: NablaEdge core system
 Edge computing system for home automation.
```

### Building Locally

```bash
cd packages/nabla-edge
./build.sh
# Output: build/nabla-edge_1.0.0_arm64.deb
```

---

## Repository Management

### Adding a Package

```bash
# Copy to pool
cp nabla-edge_1.0.0_arm64.deb /var/www/apt/pool/main/

# Regenerate index
cd /var/www/apt
apt-ftparchive packages pool/main > dists/stable/main/binary-arm64/Packages
gzip -k dists/stable/main/binary-arm64/Packages

# Generate Release file
apt-ftparchive release dists/stable > dists/stable/Release
```

### Signing (Optional)

For production, sign the repository:

```bash
gpg --armor --sign --detach-sign -o dists/stable/Release.gpg dists/stable/Release
gpg --clearsign -o dists/stable/InRelease dists/stable/Release
```

Clients then need the GPG key:

```bash
curl -fsSL https://apt.example.local/nabla.gpg | sudo apt-key add -
```

---

## First-Boot Integration

`nabla-image` can pre-stage packages for offline installation:

1. Packages downloaded during image creation
2. Placed in `/var/cache/apt/archives/`
3. First-boot script runs `dpkg -i` to install

See [../imaging/](../imaging/) for details.

---

## Binary Storage

**Heavy binaries are NOT stored in git.**

Distribution methods:
- **GitHub Releases** — Tagged releases include binary assets
- **CI Artifacts** — Built by GitHub Actions
- **Private mirror** — Self-hosted HTTP server

The git repo contains only:
- Package metadata (control files)
- Build scripts
- Documentation

---

## How to Change This

1. Package metadata: Edit files in `packages/`
2. Build process: Modify `build.sh` scripts
3. Repository structure: Update `dist/` configs
4. Documentation: Update this README

---

## Related

- [../../../packages/](../../../packages/) — Package metadata
- [../../../dist/](../../../dist/) — HTTP serving config
- [../imaging/](../imaging/) — First-boot package installation
