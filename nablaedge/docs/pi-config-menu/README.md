# Pi Config Menu — nabla-config

The `nabla-config` tool: a whiptail-based configuration menu for Raspberry Pi edge nodes.

---

## Installation

`nabla-config` is part of the `nabla-edge` package. Install via APT:

```bash
echo 'deb [trusted=yes] https://coco.nabla.net/apt/ stable main' | \
  sudo tee /etc/apt/sources.list.d/nabla.list
sudo apt update && sudo apt install nabla-edge
```

See [../packages-apt/](../packages-apt/) for full installation details.

---

## What is nabla-config?

`nabla-config` is an interactive terminal menu (using whiptail/dialog) that configures:

- **Network** — Nabla Net modes, uplink settings
- **Media** — USB/SD imaging for Nabla Pi OS
- **Accessories** — OLED, rotary encoder, large display flags
- **Camera** — Camera module settings
- **Voice Satellite** — Linux Voice Assistant for HA Assist

---

## Running nabla-config

```bash
# Interactive mode (default)
sudo nabla-config

# Show help
nabla-config --help

# Direct submenu access
sudo nabla-config network
sudo nabla-config accessories
sudo nabla-config voice
```

---

## Menu Tree

```
nabla-config (Main Menu)
├── Network
│   ├── Status            → Show current network status
│   ├── CABLE             → eth LAN + Tailscale
│   ├── AP                → SSID Nabla Net
│   ├── CABLE-AP          → eth + wlan1 AP
│   └── OFF               → Disable networking
│
├── Media (USB/SD)
│   ├── Nabla Pi OS full  → Write desktop image to USB/SD
│   ├── Nabla Pi OS lite  → Write lite image to USB/SD
│   ├── OTP enabler       → Pi 3B USB boot enabler
│   ├── List disks        → Show available drives
│   └── Download image    → Cache base image
│
├── Accessories
│   ├── Small I2C OLED    → Enable/disable
│   ├── Rotary encoder    → Enable/disable
│   ├── Large SPI display → Enable/disable
│   ├── Apply OLED now    → Enable OLED service
│   └── View profile      → Show accessories.conf
│
├── Camera
│   └── go2rtc            → Camera helper
│
└── Voice Satellite
    ├── Install / update  → Install LVA via Docker
    ├── Mode              → button (HA) / wake (continuous)
    ├── Satellite name    → Name for HA entity
    ├── Wake word         → hey_jarvis, ok_nabu, etc.
    ├── ESPHome port      → Default 6053
    ├── Start / Stop      → Control LVA container
    ├── View status       → Show LVA status
    └── HA Instructions   → ESPHome + dashboard button setup
```

---

## Configuration Files

### /etc/nabla-net/accessories.conf

Accessory flags file — controls which hardware is enabled:

```ini
# Accessories configuration
# Edit via nabla-config or manually

display_oled=1          # 1=enabled, 0=disabled
rotary=1                # Rotary encoder enabled
display_large=0         # Large SPI display (disabled by default)
```

### /etc/nabla-edge/voice.conf

Voice satellite configuration:

```ini
# Voice configuration (Linux Voice Assistant)

MODE=button             # button | wake
SATELLITE_NAME=demo     # HA entity name
PORT=6053               # ESPHome port
WAKE_WORD=hey_jarvis    # Wake word
```

---

## How nabla-config Works

```mermaid
flowchart TD
    Start[nabla-config] --> Menu[Whiptail Main Menu]
    Menu --> |Network| Network[Network Submenu]
    Menu --> |Accessories| Accessories[Accessories Submenu]
    Menu --> |Voice| Voice[Voice Submenu]
    
    Network --> |Mode| SetMode[Run vpn-mode]
    
    Accessories --> |OLED| SetOLED[Write accessories.conf]
    SetOLED --> RestartOLED[systemctl restart nabla-oled]
    
    Voice --> |Install| InstallLVA[Docker Compose up]
```

1. User selects menu option via whiptail
2. Script validates input
3. Writes to appropriate config file
4. Restarts relevant service or container

---

## USB Hotplug Dialog

When a USB drive is inserted, nabla-config can trigger a dialog:

| Option | Action |
|--------|--------|
| **Write OS** | Launch nabla-image to write to the drive |
| **OTP Enable** | Write OTP bit for USB boot (Pi 3B only) |
| **Open Files** | Mount and browse the drive |
| **Nothing** | Ignore the drive |

---

## Command Line Reference

```
nabla-config [OPTIONS]

OPTIONS:
  --help, -h          Show this help message
  network             Jump to network submenu
  media               Jump to media submenu
  accessories         Jump to accessories submenu
  voice               Jump to voice submenu
  oled                Enable OLED directly
```

---

## Related

- [../accessories/](../accessories/) — Hardware flags detail
- [../network-modes/](../network-modes/) — Network mode concepts
- [../voice-satellite/](../voice-satellite/) — Voice satellite setup (LVA)
