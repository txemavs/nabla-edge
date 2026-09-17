# NablaEdge Scripts

Edge node tools for configuration and imaging.

| Script | Role |
|--------|------|
| [`nabla-config`](nabla-config) | Whiptail panel: network, imaging media, accessories, voice |
| [`nabla-image`](nabla-image) | Pi OS media writer with fleet defaults (ES keyboard, Wi-Fi injection) |

## Imaging Support Files

```
image/
├── firstboot/
│   ├── nabla-firstboot.sh      # First-boot setup script
│   └── nabla-firstboot.service # Systemd unit
├── otp-enabler/
│   └── config.txt.append       # OTP bit for Pi 3B USB boot
└── wifi.env.example            # Wi-Fi credentials template
```

## Wi-Fi Credentials (Flasher Machine)

Before running `nabla-image`, create `~/.config/nabla/wifi.env` with your fleet Wi-Fi credentials. See [`image/wifi.env.example`](image/wifi.env.example) for the template.

**Security**: Never commit real credentials. The example uses `CHANGE_ME` placeholders.

## Related Documentation

- [`../docs/imaging/`](../docs/imaging/) — Full imaging workflow
- [`../docs/pi-config-menu/`](../docs/pi-config-menu/) — nabla-config reference
- [`../docs/network-modes/`](../docs/network-modes/) — Network configuration
