# Voice Satellite Module

Wyoming-based voice satellite for Home Assistant Assist integration.

## Components

| File | Role |
|------|------|
| [`voice.conf.example`](voice.conf.example) | Configuration template |
| [`install-voice-satellite.sh`](install-voice-satellite.sh) | Installer: venv, deps, systemd unit |
| [`nabla-voice-ptt`](nabla-voice-ptt) | GPIO push-to-talk trigger (Pi button mode) |
| [`wyoming-satellite.service`](wyoming-satellite.service) | Systemd user unit template |

## Modes

| Mode | Use case | Wake detection |
|------|----------|----------------|
| `button` | Raspberry Pi 3/4 (default) | GPIO physical button triggers Assist |
| `wake` | Desktop / powerful host | Local openWakeWord Docker container |

Button mode is recommended for Pi (continuous wake-word is too heavy on Pi 3).

## Quick Start

```bash
# Install voice satellite
sudo /opt/nabla-edge/voice/install-voice-satellite.sh

# Or via nabla-config:
sudo nabla-config
# → Satélite de voz → Instalar
```

## Configuration

Config file: `/etc/nabla-edge/voice.conf`

```bash
MODE=button              # button | wake
SATELLITE_NAME=edge01    # Shows in HA as assist_satellite.<name>
HA_URL=https://example.invalid
HA_TOKEN_FILE=/etc/nabla-edge/ha-token
GPIO_PIN=17              # Button pin (BCM numbering, button mode)
WAKE_WORD=hey_jarvis     # Wake word name (wake mode)
PORT=10700               # Wyoming satellite port
```

## See Also

- [../docs/voice-satellite/](../docs/voice-satellite/) — Full documentation
- [../scripts/nabla-config](../scripts/nabla-config) — Interactive menu
