# Voice Satellite

A Nabla Edge Pi can become a **wall-mounted conversation point**: mic + speakers talking to Home Assistant Assist via the Wyoming protocol.

![Voice satellite](diagrams/voice-satellite-generic.jpg)

---

## Primary Trigger: HA Dashboard Button

The Pi is typically **wall-mounted** — users shouldn't need to walk up to press a button. The primary way to trigger listening is from your phone:

```
[Phone / HA Companion]  →  tap "Listen" button  →  [HA rest_command]  →  [Pi HTTP endpoint]  →  Satellite starts listening
```

An HTTP endpoint on the Pi (`nabla-voice-listen` on port 10701) accepts triggers from:
- Home Assistant dashboard buttons
- HA Companion app on your phone
- Automations (presence-based, NFC tags, etc.)

**GPIO button** on the Pi is available as an **optional secondary trigger** — handy if your phone isn't out.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Nabla Edge Pi (wall-mounted)                 │
│  ┌─────────────┐    ┌──────────────────┐    ┌───────────────┐       │
│  │   USB Mic   │───▶│ wyoming-satellite │◀───│  USB Speaker  │       │
│  └─────────────┘    │   :10700          │    └───────────────┘       │
│                     └────────┬──────────┘                            │
│                              │                                       │
│  ┌─────────────────┐         │                                       │
│  │ nabla-voice-    │─────────┤  ← HTTP trigger from HA dashboard     │
│  │ listen :10701   │         │                                       │
│  └─────────────────┘         │                                       │
│                              │                                       │
│  ┌─────────────┐             │                                       │
│  │ GPIO Button │─────────────┘  (optional secondary trigger)         │
│  └─────────────┘                                                     │
│                                                                      │
│  ┌─────────────────┐                                                 │
│  │ openWakeWord    │  (optional, desktop only, NOT for Pi)           │
│  │ :10400          │                                                 │
│  └─────────────────┘                                                 │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               │ Wyoming protocol (TCP)
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       Home Assistant                                  │
│  ┌──────────────┐   ┌────────────┐   ┌────────────┐                  │
│  │ Wyoming      │   │ Whisper    │   │ Piper TTS  │                  │
│  │ Integration  │──▶│ (STT)      │──▶│            │                  │
│  │              │   └────────────┘   └────────────┘                  │
│  │ assist_      │         │                │                         │
│  │ satellite.*  │◀────────┴────────────────┘                         │
│  └──────────────┘                                                    │
│          │                                                           │
│          ▼                                                           │
│  ┌──────────────┐                                                    │
│  │ Assist       │  Intent recognition + action execution             │
│  │ Pipeline     │                                                    │
│  └──────────────┘                                                    │
└──────────────────────────────────────────────────────────────────────┘
```

### Split of Concerns

| Component | Location | Role |
|-----------|----------|------|
| Microphone + Speaker | Edge Pi | Audio I/O only |
| HTTP listen endpoint | Edge Pi :10701 | Receives trigger from HA dashboard |
| Wyoming satellite | Edge Pi :10700 | Bridge audio ↔ Wyoming protocol |
| STT (Whisper) | Home Assistant | Speech-to-text |
| TTS (Piper) | Home Assistant | Text-to-speech |
| Assist pipeline | Home Assistant | Intent recognition + execution |

**Camera is a separate concern** — do not conflate go2rtc (video) with voice.

---

## Triggering Methods

### 1. HA Dashboard Button (Primary — Recommended)

Add a button to your HA dashboard that you can tap from your phone.

**Step 1: Add rest_command to `configuration.yaml`:**

```yaml
rest_command:
  voice_satellite_listen:
    url: "http://192.0.2.10:10701/listen"
    method: POST
```

Replace `192.0.2.10` with your Pi's IP or hostname.

**Step 2: Create a button card on your dashboard:**

```yaml
type: button
name: "Listen"
icon: mdi:microphone
tap_action:
  action: call-service
  service: rest_command.voice_satellite_listen
```

Now tap the button from anywhere (phone, tablet, wall tablet) to make the Pi start listening.

### 2. GPIO Button (Optional Secondary)

If you also want a physical button on the Pi (handy when phone isn't out):

- Wire a momentary button between GPIO pin and GND
- Enable the PTT service: `systemctl --user enable --now nabla-voice-ptt`

### 3. Wake Word (Desktop Only)

On powerful hosts (not Pi), you can use local openWakeWord for hands-free activation. **Not recommended for Pi 3/4** due to CPU load.

### 4. Presence-Based Automation (Future/Optional)

You could create an automation that shows/enables the listen button only when you're home:

```yaml
# Example automation idea (not auto-enabled)
automation:
  - alias: "Show voice button when home"
    trigger:
      - platform: state
        entity_id: person.txema
        to: "home"
    action:
      - service: input_boolean.turn_on
        entity_id: input_boolean.show_voice_button
```

This is just an example pattern — implement based on your needs. **Do not auto-listen without explicit user action.**

---

## Installation

### Via nabla-config (Recommended)

```bash
sudo nabla-config
# → Satélite de voz → Instalar
```

The menu lets you:

- Install the satellite
- Set satellite name and ports
- Start/stop services
- View HA setup instructions

### Manual Installation

```bash
# Run the installer
sudo /opt/nabla-edge/voice/install-voice-satellite.sh

# For desktop wake mode (optional):
sudo /opt/nabla-edge/voice/install-voice-satellite.sh --mode wake
```

The installer:

1. Creates Python venv at `/opt/nabla-edge/voice/venv`
2. Installs `wyoming-satellite` via pip
3. Creates systemd user services:
   - `wyoming-satellite.service` — the satellite itself
   - `nabla-voice-listen.service` — HTTP endpoint (primary trigger)
   - `nabla-voice-ptt.service` — GPIO button (optional, not auto-enabled)
4. Writes config to `/etc/nabla-edge/voice.conf`

---

## Configuration

**Config file:** `/etc/nabla-edge/voice.conf`

```bash
# Mode: button (with optional GPIO) or wake (desktop only)
MODE=button

# Satellite name (appears in HA as assist_satellite.<name>)
SATELLITE_NAME=demo

# Wyoming satellite port
PORT=10700

# HTTP listen endpoint port (primary trigger)
LISTEN_HTTP_PORT=10701

# GPIO pin for optional physical button (BCM numbering)
GPIO_PIN=17

# Wake word name (wake mode only, desktop)
WAKE_WORD=hey_jarvis

# Audio devices (auto-detected if empty)
MIC_DEVICE=
SPK_DEVICE=

# Wake word server URI (wake mode only)
WAKE_URI=tcp://127.0.0.1:10400
```

---

## Home Assistant Setup

### Prerequisites

Install these add-ons in Home Assistant:

1. **Whisper** — Speech-to-text (local or Faster Whisper)
2. **Piper** — Text-to-speech
3. **Wyoming protocol** — Already part of core HA

### Step 1: Add the Satellite

1. **Settings → Devices & Services → Add Integration**
2. Search **Wyoming**
3. **Host:** `<Pi-IP-or-hostname>` (e.g., `edge01.local` or `192.0.2.10`)
4. **Port:** `10700`

The satellite appears as `assist_satellite.<name>` (e.g., `assist_satellite.demo`).

### Step 2: Add the Listen Button (Primary Trigger)

**In `configuration.yaml`:**

```yaml
rest_command:
  voice_satellite_listen:
    url: "http://192.0.2.10:10701/listen"
    method: POST
```

Restart HA, then add a button to your dashboard:

```yaml
type: button
name: "Listen"
icon: mdi:microphone
show_name: true
show_icon: true
tap_action:
  action: call-service
  service: rest_command.voice_satellite_listen
```

**Alternative: shell_command** (if rest_command doesn't work):

```yaml
shell_command:
  voice_satellite_listen: "curl -X POST http://192.0.2.10:10701/listen"
```

### Step 3: Configure Assist Pipeline

1. **Settings → Voice assistants**
2. Create or edit a pipeline
3. Set **Conversation agent**, **Speech-to-text** (Whisper), **Text-to-speech** (Piper)
4. Assign the pipeline to the satellite device

---

## Services

Services run as **systemd user units** (not system services).

```bash
# Start services
systemctl --user start wyoming-satellite
systemctl --user start nabla-voice-listen

# Optional: enable GPIO button
systemctl --user enable --now nabla-voice-ptt

# Check status
systemctl --user status wyoming-satellite
systemctl --user status nabla-voice-listen

# View logs
journalctl --user -u wyoming-satellite -f
journalctl --user -u nabla-voice-listen -f

# Enable at boot
systemctl --user enable wyoming-satellite
systemctl --user enable nabla-voice-listen

# Services persist across reboots via loginctl linger
loginctl enable-linger $USER
```

---

## Testing the HTTP Endpoint

```bash
# From any machine on your network:
curl http://192.0.2.10:10701/listen

# Check health:
curl http://192.0.2.10:10701/health

# Expected response:
# {"success": true, "message": "Satellite triggered - listening started"}
```

---

## Troubleshooting

### Listen button doesn't work

```bash
# Check HTTP endpoint is running
curl http://pi-ip:10701/health

# Check satellite is running
systemctl --user status wyoming-satellite

# Check firewall allows ports
sudo ufw allow 10700/tcp
sudo ufw allow 10701/tcp
```

### No audio

```bash
# List audio devices
arecord -L
aplay -L

# Test mic
arecord -d 5 -r 16000 -c 1 -f S16_LE test.wav
aplay test.wav

# Set specific device in voice.conf
MIC_DEVICE=plughw:1,0
SPK_DEVICE=plughw:1,0
```

### GPIO button not working (optional secondary trigger)

```bash
# Ensure service is enabled
systemctl --user enable --now nabla-voice-ptt

# Test GPIO
python3 -c "from gpiozero import Button; b=Button(17); print('Press button...'); b.wait_for_press(); print('OK')"

# Check logs
journalctl --user -u nabla-voice-ptt -f
```

### Satellite not connecting to HA

```bash
# Check satellite is listening
ss -tlnp | grep 10700

# Test Wyoming connection (from HA host)
nc -zv <pi-ip> 10700
```

---

## Hardware Recommendations

### USB Audio

Recommended USB audio adapters (mic + speaker):

- **Jabra Speak 510** — Good mic, speaker, mute button
- **Generic USB sound card** + lavalier mic + powered speaker
- **ReSpeaker USB Array** — 4-mic array, good for far-field

### GPIO Button (Optional)

Any momentary push button works:

- Connect between GPIO pin and GND
- Internal pull-up is enabled (no external resistor needed)
- Common GPIO pins: 17, 27, 22, 23, 24

---

## Why No Continuous Wake Word on Pi?

| Mode | CPU (Pi 3B) | CPU (Pi 4) | Notes |
|------|-------------|------------|-------|
| HTTP trigger | ~0% idle | ~0% idle | Waiting for request |
| GPIO PTT | ~0% idle | ~0% idle | Waiting for button |
| Wake word | **Not viable** | 15-30% | openWakeWord is too heavy |
| Satellite active | 5-15% | 2-5% | During conversation only |

**Pi 3B:** Cannot run continuous wake-word detection. Use HTTP trigger (primary) + optional GPIO button.

**Pi 4:** HTTP trigger recommended. Wake mode possible but impacts other tasks.

**Desktop/NUC:** Wake mode works well if hands-free is needed.

Streaming mic audio over Tailscale to a remote openWakeWord was tried and rejected (fragile, latency issues). Use local triggers instead.

---

## Files

| Path | Description |
|------|-------------|
| `/etc/nabla-edge/voice.conf` | Configuration |
| `/opt/nabla-edge/voice/venv/` | Python virtual environment |
| `/opt/nabla-edge/voice/nabla-voice-listen` | HTTP listen endpoint |
| `/opt/nabla-edge/voice/nabla-voice-ptt` | GPIO PTT script (optional) |
| `~/.config/systemd/user/wyoming-satellite.service` | Satellite service |
| `~/.config/systemd/user/nabla-voice-listen.service` | HTTP endpoint service |
| `~/.config/systemd/user/nabla-voice-ptt.service` | PTT service (optional) |

---

## Known Limitations

1. **Wyoming doesn't support `assist_satellite.start_conversation`** — The HA service exists but Wyoming satellite never implemented it. We work around this by sending a Wyoming detection event via our HTTP endpoint.

2. **No webrtc/silero by default** — These extras can cause SIGILL on older CPUs. Install manually if needed: `pip install wyoming-satellite[webrtc]`

3. **User services, not system** — Services run under the logged-in user, not root. This avoids audio permission issues but requires `loginctl enable-linger`.

---

## See Also

- [`../../voice/`](../../voice/) — Voice module scripts
- [`../pi-config-menu/`](../pi-config-menu/) — nabla-config usage
- [Wyoming Satellite docs](https://github.com/rhasspy/wyoming-satellite)
- [Linux Voice Assistant](https://github.com/OHF-Voice/linux-voice-assistant) — Wyoming successor with native `start_conversation` support
- [Home Assistant Assist](https://www.home-assistant.io/voice_control/)
