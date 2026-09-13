# Private PDFs — NAS Only

Index of private PDFs that contain sensitive data and must **not** be committed to git.

---

## Location

These files exist on the private NAS only:

```
/nas/docs/nabla/private/
```

---

## Private PDF Index

| Filename | Content | Why Private |
|----------|---------|-------------|
| `nabla-edge.pdf` | Main edge documentation | Real hostnames, IPs |
| `nabla-infraestructura-privada-global.pdf` | Global infrastructure | Full network topology |
| `nabla-home-assistant-voz.pdf` | Voice satellite setup | HA instance URLs |
| `nabla-edge-veronica-esp32.pdf` | ESP32 device docs | Real device names |
| `nabla-net-informe-ingenieria.pdf` | Engineering report | Private network details |

---

## Can These Become Public?

Some may be sanitized for public release:

| PDF | Sanitization Effort |
|-----|---------------------|
| `nabla-edge.pdf` | High — many real values throughout |
| `nabla-infraestructura-privada-global.pdf` | Not feasible — core content is private |
| `nabla-home-assistant-voz.pdf` | Medium — replace HA URLs, device paths |
| `nabla-edge-veronica-esp32.pdf` | Medium — replace device names |
| `nabla-net-informe-ingenieria.pdf` | High — extensive network details |

See [../README.md](../README.md) for the sanitization process.

---

## Rule

**Never commit binaries from this list to git.**

If you need content from these PDFs in public docs, extract and sanitize the relevant sections manually.
