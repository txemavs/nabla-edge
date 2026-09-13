# Voice Satellite

A Nabla Edge Pi can become a **conversation point**: mic + speakers talking to Home Assistant Assist via the Wyoming protocol.

![Voice satellite](diagrams/voice-satellite-generic.jpg)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Nabla Edge Pi                            │
│  ┌─────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │   USB Mic   │───▶│ wyoming-satellite │◀───│  USB Speaker  │  │
│  └─────────────┘    │   :10700          │    └───────────────┘  │
│                     └────────┬──────────┘                       │
│                              │                                  │
│  ┌─────────────┐             │                                  │
│  │ GPIO Button │─────────────┤  (button mode)                   │
│  └─────────────┘             │                                  │
│                              │                                  │
│  ┌─────────────────┐         │                                  │
│  │ openWakeWord    │─────────┘  (wake mode, Docker)             │
│  │ :10400          │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ Wyoming protocol (TCP)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Home Assistant                              │
│  ┌──────────────┐   ┌────────────┐   ┌────────────┐             │
│  │ Wyoming      │   │ Whisper    │   │ Piper TTS  │             │
│  │ Integration  │──▶│ (STT)      │──▶│            │             │
│  │              │   └────────────┘   └────────────┘             │
│  │ assist_      │         │                │                    │
│  │ satellite.*  │◀────────┴────────────────┘                    │
│  └──────────────┘                                               │
│          │                                                      │
│          ▼                                                      │
│  ┌──────────────┐                                               │
│  │ Assist       │  Intent recognition + action execution        │
│  │ Pipeline     │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Split of Concerns

| Component | Location | Role |
|-----------|----------|------|
| Microphone + Speaker | Edge Pi | Audio I/O only |
| Wake detection | Edge (button/wake) | Trigger conversation start |
| Wyoming satellite | Edge Pi :10700 | Bridge audio ↔ Wyoming protocol |
| STT (Whisper) | Home Assistant | Speech-to-text |
| TTS (Piper) | Home Assistant | Text-to-speech |
| Assist pipeline | Home Assistant | Intent recognition + execution |

**Camera is a separate concern** — do not conflate go2rtc (video) with voice.

---

## Two Modes

### Button Mode (Recommended for Pi)

A **physical GPIO button** triggers Assist conversations. No continuous audio processing on the Pi.

```
[GPIO Button] ──press──▶ [nabla-voice-ptt] ──Wyoming event──▶ [satellite] ──▶ HA starts listening
```

**Why button mode for Pi?**

- Pi 3B cannot run continuous wake-word detection (CPU too slow)
- Even Pi 4 sees high CPU load with local openWakeWord
- Remote wake-word over Tailscale was tried and rejected (fragile, latency issues)
- Physical button is reliable, zero CPU overhead, tactile feedback

**Wiring:**

```
GPIO17 ───┬─── Button ─── GND
          │
       (internal pull-up enabled)
```

Any GPIO pin works (17, 27, 22 common). Configure in `/etc/nabla-edge/voice.conf`.

### Wake Mode (Desktop / Powerful Hosts)

Local **openWakeWord** (Docker) listens continuously and triggers the satellite.

```
[Mic] ──continuous──▶ [openWakeWord :10400] ──detection──▶ [satellite :10700] ──▶ HA pipeline
```

**Requirements:**

- Docker running
- Sufficient CPU (not Pi 3; Pi 4 marginal; desktop recommended)
- `rhasspy/wyoming-openwakeword` container on `127.0.0.1:10400`

**Setup Docker openWakeWord:**

```bash
docker run -d --name openwakeword \
  --restart unless-stopped \
  -p 127.0.0.1:10400:10400 \
  rhasspy/wyoming-openwakeword \
  --preload-model hey_jarvis \
  --threshold 0.3
```

Available wake words: `hey_jarvis`, `ok_nabu`, `alexa`, `hey_mycroft`

---

## Installation

### Via nabla-config (Recommended)

```bash
sudo nabla-config
# → Satélite de voz → Instalar
```

The menu lets you:

- Choose mode (button/wake)
- Set satellite name
- Configure GPIO pin
- Start/stop services
- View status

### Manual Installation

```bash
# Run the installer
sudo /opt/nabla-edge/voice/install-voice-satellite.sh --mode button

# Or for wake mode:
sudo /opt/nabla-edge/voice/install-voice-satellite.sh --mode wake
```

The installer:

1. Creates Python venv at `/opt/nabla-edge/voice/venv`
2. Installs `wyoming-satellite` via pip
3. Creates systemd user services
4. Writes config to `/etc/nabla-edge/voice.conf`

---

## Configuration

**Config file:** `/etc/nabla-edge/voice.conf`

```bash
# Mode: button (GPIO PTT) or wake (local openWakeWord)
MODE=button

# Satellite name (appears in HA as assist_satellite.<name>)
SATELLITE_NAME=demo

# Home Assistant connection (for button mode REST fallback)
HA_URL=https://example.invalid
HA_TOKEN_FILE=/etc/nabla-edge/ha-token

# GPIO pin for PTT button (BCM numbering)
GPIO_PIN=17

# Wake word name (wake mode only)
WAKE_WORD=hey_jarvis

# Wyoming satellite port
PORT=10700

# Audio devices (auto-detected if empty)
MIC_DEVICE=
SPK_DEVICE=

# Wake word server URI (wake mode)
WAKE_URI=tcp://127.0.0.1:10400
```

### HA Token

For button mode REST fallback, create a long-lived access token in HA:

1. HA → Profile → Long-Lived Access Tokens → Create Token
2. Save token to `/etc/nabla-edge/ha-token`

```bash
echo 'your-long-lived-token' | sudo tee /etc/nabla-edge/ha-token
sudo chmod 600 /etc/nabla-edge/ha-token
```

---

## Home Assistant Setup

### Prerequisites

Install these add-ons in Home Assistant:

1. **Whisper** — Speech-to-text (local or Faster Whisper)
2. **Piper** — Text-to-speech
3. **Wyoming protocol** — Already part of core HA

### Add the Satellite

1. **Settings → Devices & Services → Add Integration**
2. Search **Wyoming**
3. **Host:** `<Pi-IP-or-hostname>` (e.g., `edge01.local` or `192.0.2.10`)
4. **Port:** `10700`

The satellite appears as `assist_satellite.<name>` (e.g., `assist_satellite.demo`).

### Configure Assist Pipeline

1. **Settings → Voice assistants**
2. Create or edit a pipeline
3. Set **Conversation agent**, **Speech-to-text** (Whisper), **Text-to-speech** (Piper)
4. Assign the pipeline to the satellite device

---

## Services

Services run as **systemd user units** (not system services).

```bash
# Start satellite
systemctl --user start wyoming-satellite

# Start PTT watcher (button mode)
systemctl --user start nabla-voice-ptt

# Check status
systemctl --user status wyoming-satellite
systemctl --user status nabla-voice-ptt

# View logs
journalctl --user -u wyoming-satellite -f
journalctl --user -u nabla-voice-ptt -f

# Enable at boot
systemctl --user enable wyoming-satellite
systemctl --user enable nabla-voice-ptt

# Services persist across reboots via loginctl linger
loginctl enable-linger $USER
```

---

## Troubleshooting

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

### Button not working

```bash
# Test GPIO (requires gpiozero)
python3 -c "from gpiozero import Button; b=Button(17); print('Press button...'); b.wait_for_press(); print('OK')"

# Check PTT service logs
journalctl --user -u nabla-voice-ptt -f
```

### Satellite not connecting

```bash
# Check satellite is listening
ss -tlnp | grep 10700

# Test Wyoming connection (from HA host or another machine)
nc -zv <pi-ip> 10700

# Check firewall
sudo ufw status
sudo ufw allow 10700/tcp
```

### Wake word not detecting (wake mode)

```bash
# Check openWakeWord container
docker logs openwakeword

# Test wake word server
nc -zv 127.0.0.1 10400

# Lower threshold if too sensitive
docker run ... --threshold 0.2
```

---

## Hardware Recommendations

### USB Audio

Recommended USB audio adapters (mic + speaker):

- **Jabra Speak 510** — Good mic, speaker, mute button
- **Generic USB sound card** + lavalier mic + powered speaker
- **ReSpeaker USB Array** — 4-mic array, good for far-field

### GPIO Button

Any momentary push button works:

- Connect between GPIO pin and GND
- Internal pull-up is enabled (no external resistor needed)
- Debounce handled in software (200ms)

Common GPIO pins: 17, 27, 22, 23, 24

---

## Resource Notes

| Mode | CPU (Pi 3B) | CPU (Pi 4) | Notes |
|------|-------------|------------|-------|
| Button | ~0% idle | ~0% idle | PTT watcher negligible |
| Wake | **Not recommended** | 15-30% | openWakeWord is heavy |
| Satellite active | 5-15% | 2-5% | During conversation only |

**Pi 3B:** Use button mode only. Wake-word detection is too heavy.

**Pi 4:** Button mode recommended. Wake mode possible but impacts other tasks.

**Desktop/NUC:** Wake mode works well.

---

## Files

| Path | Description |
|------|-------------|
| `/etc/nabla-edge/voice.conf` | Configuration |
| `/etc/nabla-edge/ha-token` | HA long-lived access token |
| `/opt/nabla-edge/voice/venv/` | Python virtual environment |
| `/opt/nabla-edge/voice/nabla-voice-ptt` | GPIO PTT script |
| `~/.config/systemd/user/wyoming-satellite.service` | Satellite service |
| `~/.config/systemd/user/nabla-voice-ptt.service` | PTT service |

---

## Known Limitations

1. **No webrtc/silero by default** — These extras can cause SIGILL on older CPUs. Install manually if needed: `pip install wyoming-satellite[webrtc]`

2. **User services, not system** — Services run under the logged-in user, not root. This avoids audio permission issues but requires `loginctl enable-linger`.

3. **No continuous streaming to remote wake-word** — Streaming mic audio over Tailscale to a remote openWakeWord was tried and rejected (fragile, latency). Use local button or local Docker wake.

---

## See Also

- [`../../voice/`](../../voice/) — Voice module scripts
- [`../pi-config-menu/`](../pi-config-menu/) — nabla-config usage
- [Wyoming Satellite docs](https://github.com/rhasspy/wyoming-satellite)
- [Home Assistant Assist](https://www.home-assistant.io/voice_control/)
