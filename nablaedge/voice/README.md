# Voice Satellite Module

Linux Voice Assistant (LVA) for Home Assistant Assist integration.

> **Do NOT use Wyoming Satellite.** It is deprecated. Use LVA.

## Trigger Modes

| Mode | Trigger | Recommended For |
|------|---------|-----------------|
| **button** (default) | HA `start_conversation` or GPIO | Wall-mounted Pi, low-power |
| **wake** | Continuous wake word | Desktop, hands-free |

## Why LVA over Wyoming Satellite?

| Feature | LVA | Wyoming Satellite |
|---------|-----|-------------------|
| Protocol | ESPHome (:6053) | Wyoming (:10700) |
| start_conversation | **Yes** (features=3) | No (features=1) |
| announce | Yes | Yes |
| Wake word | Built-in (microWakeWord) | Separate container |
| Status | **Active** (OHF-Voice) | **Deprecated** |

## Components

| File | Description |
|------|-------------|
| [`voice.conf.example`](voice.conf.example) | Configuration template with documented options |
| [`install-lva.sh`](install-lva.sh) | Docker Compose installer |

## Quick Start

```bash
# Via nabla-config (recommended):
sudo nabla-config
# → Voice Satellite → Install / update LVA

# Or manually:
sudo /opt/nabla-edge/voice/install-lva.sh
```

## HA Dashboard Button

Add a button to trigger `start_conversation`:

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

Config: `/etc/nabla-edge/voice.conf`

```bash
# Trigger mode (default: button)
MODE=button              # button | wake

# Satellite identity
SATELLITE_NAME=demo      # → assist_satellite.demo_satellite_assist
PORT=6053                # ESPHome native API port

# Wake word (only active when MODE=wake)
WAKE_WORD=hey_jarvis     # hey_jarvis, ok_nabu, alexa, hey_mycroft

# GPIO button (optional physical trigger)
GPIO_PIN=17              # BCM pin number
```

## Custom Wake Word (Coming Soon)

"Oye Veronica" microWakeWord model is training. Once ready:
- Place `.tflite` + `.json` in `/opt/nabla-edge/voice/wake/`
- Update config to use custom model

## See Also

- [../docs/voice-satellite/](../docs/voice-satellite/) — Full documentation
- [../scripts/nabla-config](../scripts/nabla-config) — Interactive menu
- [OHF-Voice/linux-voice-assistant](https://github.com/OHF-Voice/linux-voice-assistant)
