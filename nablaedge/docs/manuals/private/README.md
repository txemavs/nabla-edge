# Private PDFs — NAS Only

Index of private PDFs that must **not** be committed to git.

---

## Location

These files exist on the private NAS:

```
/nas/docs/nabla/private/
```

---

## Private PDF Index

| Filename | Content | Why Private |
|----------|---------|-------------|
| `nabla-edge.pdf` | Main edge documentation | Real hostnames (Villaloba, Nave), private IPs |
| `nabla-infraestructura-privada-global.pdf` | Global infrastructure map | Full network topology — core content is private |
| `nabla-home-assistant-voz.pdf` | Voice satellite setup | HA instance URLs, device paths |
| `nabla-edge-veronica-esp32.pdf` | ESP32 device docs | Agent/ops internal pitch |
| `nabla-net-informe-ingenieria.pdf` | Engineering report | Private network details (could be scrubbed) |

### Duplicates (ignore)

- `nabla-home-assistant-voz (1).pdf` — duplicate of `nabla-home-assistant-voz.pdf`

---

## Scrub Candidates

Some PDFs could become public with sanitization work:

| PDF | Effort | Public Value |
|-----|--------|--------------|
| `nabla-net-informe-ingenieria.pdf` | High | 3-layer architecture diagrams |
| `nabla-edge-veronica-esp32.pdf` | Medium | ESP32 patterns (already in esphome-patterns/) |
| `nabla-home-assistant-voz.pdf` | Medium | Voice setup guide |

### Not Worth Scrubbing

| PDF | Why |
|-----|-----|
| `nabla-edge.pdf` | Too many real values throughout |
| `nabla-infraestructura-privada-global.pdf` | Core purpose is private topology |

---

## Rule

**Never commit binaries from this list to git.**

If you need content from these PDFs in public docs:
1. Extract the relevant section
2. Sanitize per [../README.md](../README.md) checklist
3. Add to appropriate topic README as text/diagrams
