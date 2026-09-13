# Imaging — nabla-image

How to create bootable SD/USB media with first-boot injection for NablaEdge nodes.

---

## Overview

`nabla-image` prepares Raspberry Pi boot media:

```mermaid
flowchart LR
    Fetch[Fetch Pi OS] --> Extract[Extract .xz]
    Extract --> Inject[Inject first-boot]
    Inject --> Write[Write to media]
    Write --> Boot[First boot<br/>auto-configures]
```

---

## Quick Start

```bash
# List available drives
nabla-image --list

# Write to USB drive (example device)
sudo nabla-image --target /dev/sdX --site demo

# With verification
sudo nabla-image --target /dev/sdX --site demo --verify
```

**Warning:** This erases all data on the target drive.

---

## The Imaging Flow

### 1. Fetch Raspberry Pi OS

Downloads official Pi OS Lite (64-bit) if not cached:

```
Source: https://downloads.raspberrypi.org/raspios_lite_arm64_latest
Cache:  ~/.cache/nabla-image/raspios.img.xz
```

Custom images can be specified with `--image URL`.

### 2. Extract Image

Decompresses `.xz` to raw `.img`:

```bash
xz -dk raspios.img.xz
```

### 3. Inject First-Boot

Mounts boot partition and adds:

```
/boot/
├── firstboot.d/           # Scripts run once on first boot
│   ├── 01-expand-filesystem.sh
│   ├── 02-set-hostname.sh
│   ├── 03-install-packages.sh
│   ├── 04-enable-services.sh
│   └── 99-cleanup.sh
├── firstboot.txt          # Trigger file (deleted after run)
└── nabla/
    ├── site.conf          # Site identifier
    └── packages.tar.gz    # Pre-staged .deb packages (optional)
```

### 4. Write to Media

Uses `dd` with progress:

```bash
dd if=image.img of=/dev/sdX bs=4M status=progress conv=fsync
```

### 5. First Boot

On first power-up, the Pi:

1. **Expands filesystem** to fill SD/USB
2. **Sets hostname** based on site + serial
3. **Installs packages** from staged tarball
4. **Enables services** (nabla-net, nabla-oled)
5. **Cleans up** first-boot scripts

---

## Package Sources

### Current: Tarball Install

Packages pre-staged in `/boot/nabla/packages.tar.gz`:

```bash
# On imaging machine, create tarball
tar czf packages.tar.gz *.deb

# Tarball placed in image, extracted on first boot
dpkg -i /tmp/*.deb
```

### Future: Apt from HTTP Mirror

Target architecture:

```bash
# First-boot adds apt source
echo "deb [trusted=yes] https://apt.example.local/nabla stable main" \
    > /etc/apt/sources.list.d/nabla.list

# Then installs via apt
apt update && apt install nabla-edge
```

See [../packages-apt/](../packages-apt/) for mirror setup.

---

## OTP USB Boot (Pi 3B)

The Raspberry Pi 3B requires a **one-time programmable (OTP) bit** to boot from USB.

### Why OTP?

- Pi 3B doesn't boot from USB by default
- Setting OTP permanently enables USB boot capability
- Cannot be undone — it's fused into the chip
- Only needs to be done once per physical Pi

### Checking OTP Status

```bash
# On a running Pi 3B
vcgencmd otp_dump | grep 17:
# Not set: 17:1020000a
# Set:     17:3020000a
```

### Enabling OTP

```bash
# Method 1: Via nabla-image (on the Pi to enable)
sudo nabla-image --enable-otp

# Method 2: Manual
echo program_usb_boot_mode=1 | sudo tee -a /boot/config.txt
sudo reboot
# After reboot, remove the line from config.txt
```

### Pi 4/5

Pi 4 and Pi 5 support USB boot **natively** — no OTP needed.

---

## Command Reference

```
nabla-image v0.4 — NablaEdge SD/USB Imaging Tool

USAGE:
    sudo nabla-image [OPTIONS]

OPTIONS:
    -h, --help              Show help
    -v, --version           Show version
    -l, --list              List available target devices
    -t, --target DEVICE     Target device (e.g., /dev/sdb)
    -s, --site NAME         Site identifier (default: demo)
    -i, --image URL         Custom image URL
    --verify                Verify after writing
    --enable-otp            Enable USB boot OTP on Pi 3B
    --dry-run               Show what would be done

EXAMPLES:
    sudo nabla-image --list
    sudo nabla-image --target /dev/sdb
    sudo nabla-image -t /dev/mmcblk0 -s demo --verify
```

---

## Safety Features

1. **Removable-only**: Refuses to write to non-removable drives
2. **Confirmation**: Shows device info, requires explicit confirmation
3. **Dry-run**: Preview with `--dry-run`
4. **Verification**: Optional checksum verification

---

## First-Boot Scripts

Located in `/boot/firstboot.d/` on the image:

### 01-expand-filesystem.sh
```bash
#!/bin/bash
raspi-config --expand-rootfs
```

### 02-set-hostname.sh
```bash
#!/bin/bash
SITE="demo"
SERIAL=$(cat /proc/cpuinfo | grep Serial | tail -c 9)
hostnamectl set-hostname "edge-${SERIAL}"
```

### 03-install-packages.sh
```bash
#!/bin/bash
if [[ -f /boot/nabla/packages.tar.gz ]]; then
    cd /tmp
    tar xzf /boot/nabla/packages.tar.gz
    dpkg -i *.deb || apt-get install -f -y
fi
```

### 04-enable-services.sh
```bash
#!/bin/bash
systemctl enable nabla-net
systemctl enable nabla-oled
```

### 99-cleanup.sh
```bash
#!/bin/bash
rm -rf /boot/firstboot.d
rm -f /boot/nabla/packages.tar.gz
```

---

## How to Change This

1. **Add first-boot step**: Create numbered script in `firstboot.d/`
2. **Change package source**: Modify `03-install-packages.sh`
3. **Add configuration**: Place files in `/boot/nabla/`

---

## Related

- [`../../scripts/nabla-image`](../../scripts/nabla-image) — Full imaging script
- [../packages-apt/](../packages-apt/) — Apt repository setup
- [../pi-config-menu/](../pi-config-menu/) — USB hotplug dialog
