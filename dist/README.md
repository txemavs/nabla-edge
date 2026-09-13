# Dist

HTTP serving configuration for the apt repository and release artifacts.

---

## Overview

This directory contains configuration and documentation for serving:

- Apt package repository
- Release artifacts
- Static files

## Serving Options

The apt repo can be served by any HTTP server or reverse proxy:

- **Nginx** — Static file serving with directory listing
- **Apache** — Traditional hosting
- **Caddy** — Automatic HTTPS
- **Synology Web Station** — NAS-based hosting
- **GitHub Pages** — For smaller repos
- **Any static file server**

## Repository Structure

```
/apt/
├── dists/
│   └── stable/
│       └── main/
│           └── binary-amd64/
│               └── Packages.gz
└── pool/
    └── main/
        └── *.deb
```

## Client Configuration

Add to `/etc/apt/sources.list.d/nabla.list`:

```
deb [trusted=yes] https://your-server.example/apt stable main
```

Replace `your-server.example` with your actual hostname.

## Signing (Optional)

For production, sign packages with GPG:

```bash
# Generate repo metadata with signing
apt-ftparchive packages pool/main > dists/stable/main/binary-amd64/Packages
gzip -k dists/stable/main/binary-amd64/Packages
apt-ftparchive release dists/stable > dists/stable/Release
gpg --armor --sign --detach-sign -o dists/stable/Release.gpg dists/stable/Release
```

## Notes

- No private hostnames or IPs in this repo
- See [AGENTS.md](../AGENTS.md) for sanitization rules
