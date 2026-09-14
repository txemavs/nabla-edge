# Custom Wake Words

Custom wake word models for Linux Voice Assistant (LVA) on Nabla Edge.

---

## Overview

Custom wake words let you trigger voice assistants with personalized phrases like "Oye Veronica" instead of generic wake words like "ok_nabu".

**Key facts:**
- Training happens on **GPU hosts** (Suprim/Nemo), not on Raspberry Pis
- Trained models are packaged on Coco NAS for deployment
- Pis run inference only — drop `.tflite` + `.json` into LVA's wake folder

---

## Available Custom Wake Words

| Wake Word | Status | Model Path (Coco) |
|-----------|--------|-------------------|
| **Oye Veronica** | Ready (first-pass) | `\\coco\nabla.net\packages\wakewords\oye_veronica\` |

Future wake words follow the same layout: `packages/wakewords/<id>/`.

---

## Package Contents

Each wake word package contains:

```
packages/wakewords/oye_veronica/
├── oye_veronica.tflite    # TensorFlow Lite model
└── oye_veronica.json      # Model metadata (threshold, labels)
```

---

## Deploying to LVA

### Step 1: Copy Model Files

Copy the `.tflite` and `.json` from Coco to the Pi:

```bash
# On the Pi, create the custom wake words directory
sudo mkdir -p /app/wakewords/custom

# Copy from Coco (example using SMB mount)
sudo cp /mnt/coco/nabla.net/packages/wakewords/oye_veronica/oye_veronica.* \
    /app/wakewords/custom/
```

Or via SCP from a host with Coco access:

```bash
scp oye_veronica.tflite oye_veronica.json user@pi-host:/tmp/
ssh user@pi-host "sudo mv /tmp/oye_veronica.* /app/wakewords/custom/"
```

### Step 2: Configure LVA

Edit `/etc/nabla-edge/voice.conf`:

```bash
MODE=wake
WAKE_WORD=oye_veronica
WAKE_WORD_PATH=/app/wakewords/custom
```

### Step 3: Restart LVA

```bash
cd /opt/nabla-edge/voice/lva
docker compose restart
```

---

## Training Custom Wake Words

> **Train on GPU hosts (Suprim/Nemo), not on Raspberry Pis.**
> 
> Pis lack the GPU memory and compute for training. Use a host with NVIDIA GPU (RTX 3090/4090 recommended).

### Prerequisites

- NVIDIA GPU with CUDA support
- Python 3.10+
- 8GB+ GPU VRAM (RTX 3090/4090 recommended)

### Setup (GPU Host)

```bash
# Clone microWakeWord
git clone https://github.com/kahrendt/microWakeWord.git
cd microWakeWord

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Known Pitfalls

#### 1. Missing `layers/` Directory

The microWakeWord pip wheel does **not** include the required `layers/` directory. You must use the Git clone:

```bash
# WRONG: pip install microwakeword  # Missing layers/

# CORRECT: Clone from GitHub
git clone https://github.com/kahrendt/microWakeWord.git
```

#### 2. WSL CUDA Setup

On WSL2, TensorFlow needs explicit CUDA configuration:

```bash
# Install TensorFlow with CUDA support
pip install tensorflow[and-cuda]

# Create gpu.env for the training environment
cat > gpu.env << 'EOF'
LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
CUDA_VISIBLE_DEVICES=0
TF_FORCE_GPU_ALLOW_GROWTH=true
EOF

# Source before training
source gpu.env
```

#### 3. Train on Suprim, Not on HA

Do not attempt training on Home Assistant hosts or low-power devices. Training requires:
- Significant GPU memory (6GB+ for small models, 12GB+ recommended)
- Hours of compute time
- Large dataset storage

Use dedicated GPU hosts: **Suprim** (RTX 4090) or **Nemo** (RTX 3090).

### Training Workflow

1. **Prepare positive samples** — Record 100+ utterances of the wake phrase
2. **Prepare negative samples** — Background audio, similar-sounding phrases
3. **Train the model** — Follow microWakeWord training guide
4. **Export to TFLite** — Generate `.tflite` and `.json` files
5. **Package on Coco** — Copy to `\\coco\nabla.net\packages\wakewords/<id>/`

### Example Training Command

```bash
source venv/bin/activate
source gpu.env

python train.py \
    --wake-word "oye veronica" \
    --positive-samples ./data/positive/ \
    --negative-samples ./data/negative/ \
    --output ./output/oye_veronica/
```

---

## File Locations Summary

| Location | Purpose |
|----------|---------|
| `\\coco\nabla.net\packages\wakewords\<id>\` | Packaged models (source of truth) |
| `/app/wakewords/custom/` | LVA custom wake word deployment path |
| `/opt/nabla-edge/voice/lva/` | LVA Docker Compose installation |
| `/etc/nabla-edge/voice.conf` | LVA configuration |

---

## Adding New Wake Words

To add a new custom wake word:

1. **Train** on GPU host following the workflow above
2. **Package** in `\\coco\nabla.net\packages\wakewords/<new_id>/`:
   - `<new_id>.tflite`
   - `<new_id>.json`
3. **Document** in this README (add to Available Custom Wake Words table)
4. **Deploy** to target Pis following the deployment steps

---

## Troubleshooting

### Wake word not triggering

```bash
# Check LVA logs for wake word loading
cd /opt/nabla-edge/voice/lva
docker compose logs | grep -i wake

# Verify model files exist
ls -la /app/wakewords/custom/

# Check file permissions
sudo chmod 644 /app/wakewords/custom/*.tflite
sudo chmod 644 /app/wakewords/custom/*.json
```

### Training fails with CUDA errors

```bash
# Verify CUDA is available
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

# Check CUDA version
nvcc --version
nvidia-smi
```

### Model too sensitive / not sensitive enough

Adjust the threshold in the `.json` metadata file:

```json
{
  "wake_word": "oye_veronica",
  "threshold": 0.5
}
```

- Lower threshold (0.3) = more sensitive, more false positives
- Higher threshold (0.7) = less sensitive, fewer false positives

---

## See Also

- [Voice Satellite README](../README.md) — LVA installation and configuration
- [microWakeWord](https://github.com/kahrendt/microWakeWord) — Training framework
- [Coco docs mirror](file://coco/docs/voice-satellite/custom-wake-words/) — Original reference
