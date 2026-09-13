# Accessories

Hardware accessories for NablaEdge: OLED displays, rotary encoders, large SPI displays.

---

## Overview

NablaEdge supports optional hardware accessories configured via `nabla-config`:

| Accessory | Flag | Description |
|-----------|------|-------------|
| OLED display | `display_oled` | 128×64 I2C OLED (SSD1306/SSD1309) |
| Rotary encoder | `rotary` | Knob with push button for menu navigation |
| Large SPI display | `display_large` | Larger SPI-connected display |

---

## Configuration

### Via nabla-config

```bash
sudo nabla-config --accessories
```

Menu options:
- Enable/disable each accessory
- Configure I2C addresses and GPIO pins
- View current configuration

### Configuration File

Stored in `/etc/nabla-net/accessories.conf`:

```ini
# Accessories configuration
# Managed by nabla-config

# OLED Display (SSD1306/SSD1309)
display_oled=1
oled_i2c_address=0x3C
oled_i2c_bus=1

# Rotary Encoder
rotary=1
rotary_clk=17
rotary_dt=27
rotary_sw=22

# Large SPI Display
display_large=0
```

---

## OLED Display

### Supported Hardware

| Chip | Resolution | Interface | Typical Use |
|------|------------|-----------|-------------|
| SSD1306 | 128×64 | I2C | Raspberry Pi |
| SSD1309 | 128×64 | SPI | ESP32 |

Both use the same 128×64 pixel layout profile.

### Wiring (I2C)

| OLED Pin | Pi Pin | Description |
|----------|--------|-------------|
| VCC | 3.3V (Pin 1) | Power |
| GND | GND (Pin 6) | Ground |
| SDA | GPIO 2 (Pin 3) | I2C Data |
| SCL | GPIO 3 (Pin 5) | I2C Clock |

### Enabling

```bash
# Via nabla-config
sudo nabla-config --accessories
# Select "OLED display" → Enable

# Or manually
sudo sed -i 's/display_oled=0/display_oled=1/' /etc/nabla-net/accessories.conf
sudo systemctl restart nabla-oled
```

### Deep Dive

See [oled-ui/](oled-ui/) for:
- Paint layer and layout profiles
- Pi luma.oled vs ESP ESPHome drivers
- 128×64 profile specification

---

## Rotary Encoder

### Supported Hardware

Standard rotary encoder with push button (KY-040 or similar).

### Wiring

| Encoder Pin | Pi GPIO | Description |
|-------------|---------|-------------|
| CLK | GPIO 17 | Clock/A signal |
| DT | GPIO 27 | Data/B signal |
| SW | GPIO 22 | Switch (button) |
| + | 3.3V | Power |
| GND | GND | Ground |

### Enabling

```bash
sudo nabla-config --accessories
# Select "Rotary encoder" → Enable
```

### GPIO Customization

To use different pins, edit `accessories.conf`:

```ini
rotary=1
rotary_clk=17    # Change to your CLK pin
rotary_dt=27     # Change to your DT pin
rotary_sw=22     # Change to your SW pin
```

---

## Large SPI Display

### Overview

For larger displays (2.4", 3.5" TFT) connected via SPI. Currently **experimental**.

### Enabling

```bash
sudo nabla-config --accessories
# Select "Large SPI display" → Enable
```

This sets `display_large=1` in accessories.conf.

---

## Stickers and Labels

Reference PDFs for labeling accessories and Pi boards:

| PDF | Content |
|-----|---------|
| `nabla-accesorios-lista-y-pines.pdf` | Accessory list with pinouts |
| `nabla-edge-esquema-pinout.pdf` | Pi pinout diagram |
| `nabla-pegatinas-accesorios.pdf` | Accessory labels |
| `nabla-pegatinas-pi4.pdf` | Pi 4 case labels |
| `nabla-pegatinas-zero.pdf` | Pi Zero case labels |

See [pdf/](pdf/) *(binaries to be committed separately)*.

---

## Service Management

```bash
# OLED service
sudo systemctl status nabla-oled
sudo systemctl restart nabla-oled

# View logs
journalctl -u nabla-oled -f
```

---

## Troubleshooting

### OLED not displaying

1. Check I2C is enabled: `sudo raspi-config` → Interface → I2C
2. Scan I2C bus: `i2cdetect -y 1`
3. Verify address matches config (0x3C or 0x3D)

### Rotary not responding

1. Check GPIO pins are correct
2. Verify no conflicts with other services
3. Test with `gpio readall` or `gpioinfo`

### Display shows garbage

1. Check power supply (weak power causes issues)
2. Verify correct driver (SSD1306 vs SSD1309)
3. Check I2C/SPI connections

---

## How to Change This

1. Edit `accessories.conf` format in nabla-config source
2. Add new accessory types following existing pattern
3. Update this README and [oled-ui/](oled-ui/) docs
4. Test on actual hardware before documenting

---

## Related

- [oled-ui/](oled-ui/) — OLED paint layer details
- [../pi-config-menu/](../pi-config-menu/) — Configuration tool
- [../../ui/ssd/](../../ui/ssd/) — Layout profiles and tokens
