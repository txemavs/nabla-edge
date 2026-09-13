# Voice Satellite Module

Wyoming-based voice satellite for Home Assistant Assist integration.

## Primary Trigger: HA Dashboard Button

The Pi is typically **wall-mounted** — users trigger listening from their phone via an HA dashboard button, not by walking up to the Pi.

```
[Phone tap "Listen"]  →  [HA rest_command]  →  [nabla-voice-listen :10701]  →  Satellite starts listening
```

GPIO button on the Pi is an **optional secondary trigger**.

## Components

| File | Role |
|------|------|
| [`voice.conf.example`](voice.conf.example) | Configuration template |
| [`install-voice-satellite.sh`](install-voice-satellite.sh) | Installer: venv, deps, systemd units |
| [`nabla-voice-listen`](nabla-voice-listen) | HTTP endpoint for remote trigger (primary) |
| [`nabla-voice-ptt`](nabla-voice-ptt) | GPIO push-to-talk (optional secondary) |
| [`wyoming-satellite.service`](wyoming-satellite.service) | Systemd unit template |

## Trigger Methods

| Method | Port | Use Case |
|--------|------|----------|
| HTTP endpoint | 10701 | **Primary** — HA dashboard button, phone, automations |
| GPIO button | — | Optional secondary — physical button on Pi |
| Wake word | 10400 | Desktop only — continuous listening (NOT for Pi) |

## Quick Start

```bash
# Install voice satellite
sudo /opt/nabla-edge/voice/install-voice-satellite.sh

# Or via nabla-config:
sudo nabla-config
# → Satélite de voz → Instalar

# Start services
systemctl --user start wyoming-satellite
systemctl --user start nabla-voice-listen
```

## HA Dashboard Button Setup

**1. Add to `configuration.yaml`:**

```yaml
rest_command:
  voice_satellite_listen:
    url: "http://192.0.2.10:10701/listen"
    method: POST
```

**2. Add button card to dashboard:**

```yaml
type: button
name: "Listen"
icon: mdi:microphone
tap_action:
  action: call-service
  service: rest_command.voice_satellite_listen
```

## Configuration

Config file: `/etc/nabla-edge/voice.conf`

```bash
MODE=button              # button | wake
SATELLITE_NAME=demo      # Shows in HA as assist_satellite.<name>
PORT=10700               # Wyoming satellite port
LISTEN_HTTP_PORT=10701   # HTTP trigger port (primary)
GPIO_PIN=17              # Optional physical button pin
WAKE_WORD=hey_jarvis     # Wake word (desktop mode only)
```

## See Also

- [../docs/voice-satellite/](../docs/voice-satellite/) — Full documentation
- [../scripts/nabla-config](../scripts/nabla-config) — Interactive menu
