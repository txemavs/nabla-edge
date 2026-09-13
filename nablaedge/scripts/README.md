# NablaEdge Scripts

Sanitized reference copies of NablaEdge command-line tools for learning and modification.

---

## Scripts

| Script | Description |
|--------|-------------|
| [nabla-config](nabla-config) | Whiptail configuration panel (v0.7) |
| [nabla-net](nabla-net) | Network mode manager (vpn-mode) |
| [nabla-image](nabla-image) | SD/USB imaging with first-boot injection |

---

## Usage

These scripts are **reference copies** — the installed versions live in `/usr/local/bin/` on edge nodes.

To test locally:

```bash
# Make executable
chmod +x nabla-config

# Run (requires whiptail, sudo for some operations)
sudo ./nabla-config
```

---

## Modifying Scripts

1. Edit the script in this folder
2. Test on a dev Pi
3. Update the edge package (`packages/nabla-edge/`)
4. Rebuild and deploy

---

## Sanitization

All scripts use placeholder values:

- Hostnames: `example.local`, `node1.example.local`
- IPs: `192.0.2.x` (documentation range)
- Secrets: `CHANGE_ME`, `YOUR_SECRET_HERE`
- SSIDs: `NablaNet`, `CHANGE_ME`

Real values are configured at runtime via `/etc/nabla-net/` files.
