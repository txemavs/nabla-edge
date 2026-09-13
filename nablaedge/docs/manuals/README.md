# Manuals — PDF Catalog

Classification of NablaEdge PDFs: what's public, what's private, and where each belongs.

---

## Classification Key

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ **Public** | Already sanitized, safe to commit | In topic `pdf/` folder |
| 🔄 **Light scrub** | Generic content, remove site names | Clean then commit |
| 🔄 **Heavy scrub** | Useful content buried in private data | Extract generic portions |
| 🔒 **Private** | Core content is private | Stays on NAS only |

---

## Full PDF Catalog

### Already Public (committed)

| Filename | Location | Content |
|----------|----------|---------|
| `nabla-edge-ejemplos.pdf` | [network-modes/pdf/](../network-modes/pdf/) | Two connection ways: WiFi-in/cable-out, cable-in/WiFi-out |
| `nabla-accesorios-lista-y-pines.pdf` | [accessories/pdf/](../accessories/pdf/) | Accessory → GPIO / physical pin mapping |
| `nabla-edge-esquema-pinout.pdf` | [accessories/pdf/](../accessories/pdf/) | Mounting overview diagram |
| `nabla-pegatinas-accesorios.pdf` | [accessories/pdf/](../accessories/pdf/) | Accessory label sticker sheet |
| `nabla-pegatinas-pi4.pdf` | [accessories/pdf/](../accessories/pdf/) | Pi 4 case labels |
| `nabla-pegatinas-zero.pdf` | [accessories/pdf/](../accessories/pdf/) | Pi Zero / W case labels |

---

### Can Become Public (light scrub needed)

| Filename | Target Folder | Scrub Notes |
|----------|---------------|-------------|
| *(examples above already committed)* | | |

All generic product copy PDFs have been committed. Additional PDFs would need review.

---

### Can Become Public (heavy scrub needed)

| Filename | Target Folder | Content | Scrub Notes |
|----------|---------------|---------|-------------|
| `nabla-net-informe-ingenieria.pdf` | [architecture/](../architecture/) | Engineering report | Remove: real sites, Tailscale layout. Keep: generic 3-layer LAN/mesh/edge diagrams |

**After scrub**: Public version would show conceptual architecture without revealing specific site topology.

---

### Private — Do NOT Commit

| Filename | Why Private | Contains |
|----------|-------------|----------|
| `nabla-edge.pdf` | Site names, private IPs | Villaloba/Nave references, full network details |
| `nabla-infraestructura-privada-global.pdf` | Core content is infrastructure map | Full private network topology |
| `nabla-home-assistant-voz.pdf` | HA URLs, device paths | Site-specific voice setup |
| `nabla-edge-veronica-esp32.pdf` | Internal pitch | Agent/ops references, could scrub or keep private |

**Note**: `nabla-home-assistant-voz (1).pdf` is a duplicate — ignore it.

---

## PDF Locations

```
nablaedge/docs/
├── network-modes/
│   └── pdf/
│       └── nabla-edge-ejemplos.pdf         ✅
├── accessories/
│   └── pdf/
│       ├── nabla-accesorios-lista-y-pines.pdf  ✅
│       ├── nabla-edge-esquema-pinout.pdf       ✅
│       ├── nabla-pegatinas-accesorios.pdf      ✅
│       ├── nabla-pegatinas-pi4.pdf             ✅
│       └── nabla-pegatinas-zero.pdf            ✅
├── architecture/
│   └── pdf/                                (future: scrubbed engineering docs)
└── manuals/
    └── private/
        └── README.md                       Index of NAS-only PDFs
```

---

## Sanitization Checklist

Before committing any PDF, verify it contains **none** of:

- [ ] Real WiFi SSIDs or passwords
- [ ] Private IPs: `10.x.x.x`, `192.168.x.x`, `172.16-31.x.x`
- [ ] Tailscale IPs: `100.x.x.x`
- [ ] Real hostnames: `monitor*`, `pi*`, `coco`, `villaloba`, `nave`, `alarma`, etc.
- [ ] Real Home Assistant entity_ids
- [ ] API keys, tokens, secrets
- [ ] Personal names or addresses

### Scrubbing Process

1. **Export editable version** from source app
2. **Find and replace**:
   - Real IPs → `192.0.2.x` (documentation range)
   - Real hostnames → `example.local`, `node1.example.local`
   - Real SSIDs → `CHANGE_ME` or `NablaNet`
   - Real entity_ids → `switch.example_light`
3. **Re-export PDF**
4. **Text check** (if PDF is text-based):
   ```bash
   pdftotext file.pdf - | grep -iE '10\.[0-9]+\.|192\.168\.|monitor|villaloba|coco'
   ```
5. **Visual review** — check diagrams for hostnames/IPs

---

## Related

- [private/README.md](private/README.md) — Private PDF index
- [../../AGENTS.md](../../../AGENTS.md) — Sanitization rules
