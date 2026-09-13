# Voice Satellite Module

Linux Voice Assistant (LVA) for Home Assistant Assist integration.

## Primary Trigger: HA start_conversation

Wall-mounted Pi: users trigger listening from their phone via HA dashboard button calling `assist_satellite.start_conversation`.

```
[Phone tap "Listen"]  →  [HA service call]  →  [LVA :6053]  →  Satellite starts listening
```

Wake word is available on capable hosts but not required.

## Why LVA over Wyoming Satellite?

| Feature | LVA | Wyoming Satellite |
|---------|-----|-------------------|
| Protocol | ESPHome (:6053) | Wyoming (:10700) |
| start_conversation | Yes (features=3) | No (features=1) |
| announce | Yes | Yes |
| Wake word | Built-in | Separate container |
| Status | Active (OHF-Voice) | Deprecated |

## Components

| File | Role |
|------|------|
| [`voice.conf.example`](voice.conf.example) | Configuration template |
| [`install-lva.sh`](install-lva.sh) | Docker Compose installer |

## Quick Start

```bash
# Via nabla-config (recommended):
sudo nabla-config
# → Voice Satellite → Install / update LVA

# Or manually:
sudo /opt/nabla-edge/voice/install-lva.sh
```

## HA Dashboard Button Setup

LVA exposes `assist_satellite.<name>_satellite_assist` with `supported_features: 3`.

**Add button to dashboard:**

```yaml
type: button
name: Listen
icon: mdi:microphone
tap_action:
  action: call-service
  service: assist_satellite.start_conversation
  target:
    entity_id: assist_satellite.demo_satellite_assist
  data:
    start_message: ""
```

## Configuration

Config file: `/etc/nabla-edge/voice.conf`

```bash
MODE=button              # button | wake
SATELLITE_NAME=demo      # Shows in HA as assist_satellite.<name>_satellite_assist
PORT=6053                # ESPHome port
WAKE_WORD=hey_jarvis     # hey_jarvis, ok_nabu, alexa, hey_mycroft
GPIO_PIN=17              # Optional physical button pin
```

## See Also

- [../docs/voice-satellite/](../docs/voice-satellite/) — Full documentation
- [../scripts/nabla-config](../scripts/nabla-config) — Interactive menu
- [OHF-Voice/linux-voice-assistant](https://github.com/OHF-Voice/linux-voice-assistant)
