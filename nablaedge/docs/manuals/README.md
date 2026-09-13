# Manuals — PDF Catalog

Reference PDFs for NablaEdge: what's public, what's private, and how to sanitize.

---

## Public vs Private

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ **Public** | Safe to commit | Add to topic `pdf/` folder |
| 🔒 **Private** | Contains sensitive data | Stays on NAS only |
| 🔄 **Needs Scrub** | Can be public after sanitization | Clean then commit |

---

## Public PDFs (Safe to Commit)

These PDFs contain no private data and can be committed:

| Filename | Topic Folder | Content |
|----------|--------------|---------|
| `nabla-edge-ejemplos.pdf` | [network-modes/pdf/](../network-modes/pdf/) | Network configuration examples |
| `nabla-accesorios-lista-y-pines.pdf` | [accessories/pdf/](../accessories/pdf/) | Accessory list with pinouts |
| `nabla-edge-esquema-pinout.pdf` | [accessories/pdf/](../accessories/pdf/) | Pi pinout diagram |
| `nabla-pegatinas-accesorios.pdf` | [accessories/pdf/](../accessories/pdf/) | Accessory labels/stickers |
| `nabla-pegatinas-pi4.pdf` | [accessories/pdf/](../accessories/pdf/) | Pi 4 case labels |
| `nabla-pegatinas-zero.pdf` | [accessories/pdf/](../accessories/pdf/) | Pi Zero case labels |

**TODO**: Binary PDFs to be committed by Dom via direct push.

---

## Private PDFs (DO NOT Commit)

These contain sensitive data and must stay on the NAS:

| Filename | Why Private |
|----------|-------------|
| `nabla-edge.pdf` | Contains real hostnames, IPs |
| `nabla-infraestructura-privada-global.pdf` | Full private infrastructure map |
| `nabla-home-assistant-voz.pdf` | HA URLs, device paths |
| `nabla-edge-veronica-esp32.pdf` | Real device names, configs |
| `nabla-net-informe-ingenieria.pdf` | Private network details |

See [private/README.md](private/README.md) for the private PDF index.

---

## Sanitization Checklist

Before committing any PDF, verify it contains **none** of:

- [ ] Real WiFi SSIDs or passwords
- [ ] Private IPs (10.x, 192.168.x, 172.16-31.x)
- [ ] Tailscale IPs (100.x)
- [ ] Real hostnames (monitor*, pi*, coco, villaloba, nave, alarma, etc.)
- [ ] Real Home Assistant entity_ids
- [ ] API keys, tokens, secrets
- [ ] Personal names or addresses

### How to Sanitize

1. **Export editable version** — Open in source app
2. **Find and replace**:
   - Real IPs → `192.0.2.x`
   - Real hostnames → `example.local`, `node1.example.local`
   - Real SSIDs → `CHANGE_ME`
   - Real entity_ids → `switch.example_light`
3. **Re-export PDF**
4. **Grep check** (if text-based):
   ```bash
   pdftotext file.pdf - | grep -E '10\.[0-9]+\.|192\.168\.|monitor|villaloba'
   ```
5. **Visual review** — Check diagrams for hostnames

---

## PDF Folder Structure

```
nablaedge/docs/
├── network-modes/
│   └── pdf/
│       └── nabla-edge-ejemplos.pdf
├── accessories/
│   └── pdf/
│       ├── nabla-accesorios-lista-y-pines.pdf
│       ├── nabla-edge-esquema-pinout.pdf
│       ├── nabla-pegatinas-accesorios.pdf
│       ├── nabla-pegatinas-pi4.pdf
│       └── nabla-pegatinas-zero.pdf
└── manuals/
    ├── README.md          ← You are here
    └── private/
        └── README.md      # Index of private PDFs (no binaries)
```

---

## Adding a New PDF

1. **Check if public** — Use sanitization checklist above
2. **Choose topic folder** — Place in relevant topic's `pdf/` subfolder
3. **Update catalog** — Add entry to this README
4. **Commit** — Binary via direct push (not text API)

---

## Related

- [../../AGENTS.md](../../../AGENTS.md) — Sanitization rules
- [private/README.md](private/README.md) — Private PDF index
