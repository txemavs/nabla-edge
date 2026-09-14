# NablaEdge scripts (learning mirrors)

Sanitized copies of Edge node tools so you can read and edit them here.

| Script | Role |
|--------|------|
| [`nabla-config`](nabla-config) | Whiptail panel: network, imaging media, accessories (v0.7+) |
| [`nabla-image`](nabla-image) | SD/USB imaging tool: write-usb, write-otp, fetch-base |
| [`otp-enabler/`](otp-enabler/) | Tiny OTP enabler image builder for Pi 3B USB boot |

## nabla-image

Main imaging tool for creating bootable Nabla Pi OS media:

```bash
# Write Nabla OS to USB/SD
sudo nabla-image write-usb /dev/sdX --lite --hostname mypi

# Write OTP enabler for Pi 3B
sudo nabla-image write-otp /dev/sdX
```

## OTP Enabler

The OTP enabler creates a tiny (~50MB) bootable SD that:
- Shows diagnostic text on HDMI (no more black screen)
- Displays Pi model, serial, hardware info
- Scans USB drives for Nabla OS
- Burns the Pi 3B USB-boot OTP fuse

See [`otp-enabler/README.md`](otp-enabler/README.md) for details.

---

Private site packages and installs still live on the private package share; this tree is the **readable** source for how the tools work.

See [`../docs/pi-config-menu/`](../docs/pi-config-menu/) for the narrative.
