# Pi Config Menu — nabla-config

The `nabla-config` whiptail panel (v0.7): interactive configuration for Raspberry Pi edge nodes.

---

## Overview

`nabla-config` is a terminal-based configuration tool using whiptail dialogs:

```
┌─────────────── nabla-config v0.7 ───────────────┐
│                                                  │
│  NablaEdge Configuration                         │
│                                                  │
│    Red          Network mode and WiFi settings   │
│    Medios       Audio and video output           │
│    Accesorios   OLED, rotary encoder, displays   │
│    Cámara       Camera module settings           │
│    Voz          Voice satellite (HA Assist)      │
│    Info         System information               │
│    Salir        Exit configuration               │
│                                                  │
│         <Ok>            <Cancel>                 │
└──────────────────────────────────────────────────┘
```

---

## Running nabla-config

```bash
# Interactive mode (main menu)
sudo nabla-config

# Jump to specific submenu
sudo nabla-config --network
sudo nabla-config --accessories

# Non-interactive status
nabla-config --status

# Help
nabla-config --help
```

---

## Menu Tree

```
nabla-config (Main)
│
├── Red (Network)
│   ├── Modo        → Set mode: cable | ap | cable-ap | off
│   ├── WiFi        → Configure AP SSID and password
│   ├── Estado      → Show current network status
│   └── Reiniciar   → Restart networking services
│
├── Medios (Media)
│   ├── Audio       → HDMI / 3.5mm / USB
│   └── Video       → HDMI / composite / none
│
├── Accesorios (Accessories)
│   ├── OLED        → Toggle OLED display [ON/OFF]
│   ├── Rotary      → Toggle rotary encoder [ON/OFF]
│   ├── TFT         → Toggle large SPI display [ON/OFF]
│   ├── Ver         → Show current configuration
│   └── Guardar     → Save and apply changes
│
├── Cámara (Camera)
│   ├── Enable      → Enable camera module
│   ├── Test        → Capture test image
│   └── Stream      → Configure streaming (go2rtc)
│
├── Voz (Voice)
│   ├── Enable      → Enable voice satellite
│   ├── WakeWord    → Configure wake word
│   └── Test        → Test microphone
│
└── Info
    └── (shows hostname, IP, kernel, uptime, temp)
```

---

## Configuration Files

### /etc/nabla-net/accessories.conf

Controls which hardware accessories are enabled:

```ini
# NablaEdge Accessories Configuration
# Managed by nabla-config

# OLED Display (SSD1306 I2C)
display_oled=1

# Rotary Encoder (GPIO 17/27/22)
rotary=1

# Large SPI Display (optional TFT)
display_large=0
```

**Flags:**

| Flag | Values | Effect |
|------|--------|--------|
| `display_oled` | 0/1 | Enable OLED service |
| `rotary` | 0/1 | Enable rotary encoder input |
| `display_large` | 0/1 | Enable SPI TFT display |

### /etc/nabla-net/network.conf

Current network mode:

```ini
# NablaEdge Network Configuration
network_mode=cable
```

### ~/.config/nabla-net-ap.env

WiFi AP credentials (user-specific, not in git):

```bash
# WARNING: Contains secrets
AP_SSID="NablaNet"
AP_PASSWORD="CHANGE_ME"
```

---

## USB Hotplug Dialog

When a USB drive is inserted, `nabla-config --usb-dialog` can be triggered:

```
┌─────────── USB Drive Detected ───────────┐
│                                           │
│  Drive: /dev/sdb (16GB)                   │
│                                           │
│    WriteOS    Write NablaEdge image       │
│    OTP        Enable USB boot (Pi 3B)     │
│    Open       Mount and browse files      │
│    Nothing    Ignore this drive           │
│                                           │
└───────────────────────────────────────────┘
```

**Protected Drives**: Drives labeled `NABLA-DATA*` or `PROTECTED*` skip the dialog automatically — they won't be accidentally overwritten.

---

## Command Line Reference

```
nabla-config v0.7 — NablaEdge Configuration Panel

USAGE:
    nabla-config [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    -v, --version       Show version
    --network           Jump to network menu
    --accessories       Jump to accessories menu
    --media             Jump to media menu
    --camera            Jump to camera menu
    --voice             Jump to voice menu
    --status            Print current configuration (non-interactive)
    --usb-dialog DEV    Show USB hotplug dialog for device

CONFIGURATION FILES:
    /etc/nabla-net/accessories.conf   Accessories flags
    /etc/nabla-net/network.conf       Network mode
    ~/.config/nabla-net-ap.env        WiFi AP credentials

EXAMPLES:
    sudo nabla-config                  # Interactive menu
    sudo nabla-config --accessories    # Jump to accessories
    nabla-config --status              # Show current config

SEE ALSO:
    nabla-net(1), nabla-image(1)
```

---

## How to Edit nabla-config

The script lives at [`../../scripts/nabla-config`](../../scripts/nabla-config).

### Adding a Menu Option

1. Find the relevant `*_menu()` function
2. Add entry to whiptail `--menu` list
3. Add case handler

```bash
# Example: Add new accessory toggle
accessories_menu() {
    # ... existing code ...
    CHOICE=$(whiptail --menu "..." \
        "NewThing" "Toggle new accessory [$status]" \
        # ...
    )
    case "$CHOICE" in
        "NewThing") toggle_new_thing ;;
    esac
}

toggle_new_thing() {
    # Toggle logic, update accessories.conf
}
```

### Adding a Configuration Flag

1. Add default in `load_accessories()`
2. Add to `save_accessories()` output
3. Add toggle function
4. Add menu entry

### Reinstalling After Changes

```bash
# Copy to system location
sudo cp nabla-config /usr/local/bin/

# Or reinstall edge package
sudo apt reinstall nabla-edge
```

---

## Related

- [`../../scripts/nabla-config`](../../scripts/nabla-config) — Full script source
- [../accessories/](../accessories/) — Hardware flags detail
- [../network-modes/](../network-modes/) — Network mode concepts
- [../voice-satellite/](../voice-satellite/) — Voice configuration
