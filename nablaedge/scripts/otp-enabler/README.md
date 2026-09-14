# Nabla OTP Enabler

Minimal bootable SD image (~50-100MB) that programs the Pi 3B USB-boot OTP fuse and provides hardware diagnostics.

---

## Overview

The Raspberry Pi 3B requires a one-time programmable (OTP) fuse to enable USB boot. This tool creates a small diagnostic SD card that:

- Fits on a **256MB SD card** (~50-100MB actual)
- Displays diagnostic text on HDMI
- Shows Pi model, serial number, and hardware info
- Scans USB drives for Nabla OS
- Programs the OTP fuse automatically
- Halts safely after countdown

The previous method used a full Pi OS image (~2.7GB) with no display output. This version provides visible confirmation that the Pi is working and the fuse is programmed.

---

## Quick Start

### Build the image

```bash
# Requires root for losetup/mount
sudo ./build-otp-image --output otp-enabler.img
```

### Write to SD card

```bash
sudo dd if=otp-enabler.img of=/dev/sdX bs=4M status=progress
sync
```

### Or use nabla-image

```bash
sudo nabla-image write-otp /dev/sdX
```

### Boot the Pi 3B

1. Insert SD into Pi 3B
2. Connect HDMI monitor
3. Power on
4. The diagnostic display shows:

```
    NABLA OTP ENABLER
    Programming USB boot fuse (Pi 3B)

    ─────────────────────────────────

    Hardware
    Model:    Raspberry Pi 3 Model B Rev 1.2
    Serial:   00000000abcd1234
    Revision: a02082

    OTP Status
    OK USB boot fuse programmed by GPU firmware

    This Pi 3B will boot from USB after power-off.
    Verify with: vcgencmd otp_dump | grep 17:
    Expected:    17:3020000a

    USB Storage
    /dev/sda: 32GB SanDisk Cruzer
    USB: Nabla OS detected on /dev/sda1

    ─────────────────────────────────

    Next Steps
    1. Wait for countdown to complete
    2. Power off when finished
    3. Remove this SD card
    4. Insert Nabla OS USB drive
    5. Power on to boot from USB

    System will halt in 120 seconds
    Press Enter to halt now
    Remaining:  85 seconds
```

5. Wait for countdown or press Enter
6. Power off when finished, then remove this SD to boot from USB

---

## What Gets Detected

### USB Nabla OS Markers

The scan looks for these files on mounted USB partitions:

| Marker | Description |
|--------|-------------|
| `nabla-edge.tar.gz` | Edge package tarball |
| `nabla-firstboot` | First-boot trigger file |
| `firstboot.d/04-install-packages.sh` | First-boot scripts |
| `nabla/` directory | Site configuration folder |
| `nabla-*.tar.gz` | Any Nabla package tarball |

If found, displays:
```
USB: Nabla OS detected on /dev/sda1
```

If no Nabla OS is found:
```
USB: no Nabla OS found
```

If no USB drive is connected:
```
USB: no USB disk
```

### Hardware Info

From `/proc/cpuinfo` and `/proc/device-tree/model`:
- Model name (e.g., "Raspberry Pi 3 Model B Rev 1.2")
- Serial number
- Revision code

---

## Verifying OTP After Boot

After the OTP fuse is burned, verify on any running Pi OS:

```bash
vcgencmd otp_dump | grep 17:
```

**Expected output:**
```
17:3020000a
```

The `3020000a` value indicates USB boot is enabled. If you see `17:1020000a`, the fuse was not programmed.

---

## Image Contents

The image contains only essential boot files (~15-20MB total):

```
/
├── bootcode.bin          # GPU bootloader (~50KB)
├── start.elf             # GPU firmware (~3MB)
├── fixup.dat             # GPU memory fixup
├── kernel8.img           # 64-bit Linux kernel (~8MB)
├── bcm2710-rpi-3-b.dtb   # Device tree for Pi 3B
├── bcm2710-rpi-3-b-plus.dtb
├── initramfs8            # Compressed initramfs with busybox (~2MB)
├── config.txt            # Boot config with program_usb_boot_mode=1
├── cmdline.txt           # Kernel command line
└── nabla-otp.txt         # Marker file
```

### config.txt (critical)

```ini
# Burns OTP fuse to enable USB boot on Pi 3B
program_usb_boot_mode=1

# 64-bit mode for kernel8.img
arm_64bit=1

# Load our initramfs
initramfs initramfs8 followkernel

# HDMI always on
hdmi_force_hotplug=1
```

---

## Build Requirements

The build script requires:

- Root access (for losetup, mount, mknod)
- `curl` — download firmware and busybox
- `dd` — create image file
- `parted` — create partition table
- `mkfs.vfat` — format FAT32
- `losetup` — set up loop devices
- `cpio` — create initramfs

### Build Options

```bash
./build-otp-image [OPTIONS]

OPTIONS:
    -o, --output FILE    Output image file (default: otp-enabler.img)
    -c, --cache-dir DIR  Cache directory (default: ~/.cache/nabla-otp)
    -s, --size MB        Image size in MB (default: 128)
    --clean              Remove cached files before building
    -h, --help           Show help
```

### Cached Downloads

The builder caches these in `~/.cache/nabla-otp/`:

| Item | Source | Size |
|------|--------|------|
| GPU firmware | github.com/raspberrypi/firmware | ~3MB |
| kernel8.img | github.com/raspberrypi/firmware | ~8MB |
| Device trees | github.com/raspberrypi/firmware | ~30KB each |
| BusyBox (aarch64) | busybox.net | ~1MB |

---

## Troubleshooting

### Black screen (no output)

1. Check HDMI cable connection
2. Try a different HDMI port (Pi 3B has one port)
3. Connect before power-on
4. Verify SD card is properly seated

### "USB: no USB disk"

- Wait 5-10 seconds after boot for USB enumeration
- Try a different USB port
- Verify the USB drive is functional

### OTP not programmed (17:1020000a)

The firmware reads `config.txt` very early. If `program_usb_boot_mode=1` isn't seen:

1. Re-flash the SD card
2. Verify `config.txt` on the SD contains the line
3. Boot again — the fuse burns on GPU firmware init

### Pi still won't boot from USB after OTP

1. Verify OTP: `vcgencmd otp_dump | grep 17:` → should show `3020000a`
2. Check USB drive:
   - Must have valid boot partition
   - Try a known-good USB drive
   - Some USB adapters don't work
3. Power supply — USB boot needs more current

---

## How It Works

### Boot Sequence

1. **GPU bootloader** (`bootcode.bin`) loads from SD
2. **GPU firmware** (`start.elf`) reads `config.txt`
3. `program_usb_boot_mode=1` triggers OTP fuse programming
4. **Kernel** (`kernel8.img`) loads with initramfs
5. **init script** runs from initramfs:
   - Mounts proc/sys/dev
   - Displays diagnostics to HDMI
   - Scans USB block devices
   - Counts down and halts

### Why initramfs?

We don't need a full root filesystem. The initramfs contains:
- BusyBox (static ARM64 binary, ~1MB)
- Device nodes (console, null, tty)
- Init script (bash-like shell script)

This keeps the image tiny while providing full diagnostic capability.

---

## Related

- [`../nabla-image`](../nabla-image) — Main imaging tool
- [`../../docs/imaging/`](../../docs/imaging/) — Imaging documentation
- [Pi 3B USB Boot OTP](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#usb-mass-storage-boot) — Official docs
