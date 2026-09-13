# Accessories

Hardware profile toggled from `nabla-config` → Accesorios:

- `display_oled` — small I2C SSD1306 (128×64)
- `rotary` — EC11 / KY-040 rotary encoder
- `display_large` — SPI TFT (ILI9341 / ST7789)

Config file: `/etc/nabla-net/accessories.conf`

```ini
# Example accessories.conf
display_oled=1
rotary=1
display_large=0
```

---

## Subfolders

| Folder | Content |
|--------|---------|
| [oled-ui/](oled-ui/) | 128×64 paint layer (links to `ui/ssd`) |
| [pdf/](pdf/) | Pinout tables, mounting diagrams, stickers |
| [diagrams/](diagrams/) | Wiring photos (OLED I2C, encoder, etc.) |

---

## GPIO Reference

### OLED Display (I2C SSD1306)

| Function | GPIO | Physical Pin | Notes |
|----------|------|--------------|-------|
| SDA | GPIO2 | Pin 3 | I2C data |
| SCL | GPIO3 | Pin 5 | I2C clock |
| VCC | — | Pin 1 | 3.3V |
| GND | — | Pin 6 | Ground |

I2C address: `0x3C` (sometimes `0x3D`)

### Rotary Encoder (KY-040 / EC11)

| Function | GPIO | Physical Pin | Notes |
|----------|------|--------------|-------|
| CLK (A) | GPIO17 | Pin 11 | Rotation signal A |
| DT (B) | GPIO27 | Pin 13 | Rotation signal B |
| SW | GPIO22 | Pin 15 | Push button |
| + | — | Pin 1 | 3.3V |
| GND | — | Pin 9 | Ground |

### Mode Selector Switch

| Function | GPIO | Physical Pin | Notes |
|----------|------|--------------|-------|
| Position 1 | GPIO5 | Pin 29 | Input with pullup |
| Position 2 | GPIO6 | Pin 31 | Input with pullup |

### Large SPI Display (optional)

| Function | GPIO | Physical Pin | Notes |
|----------|------|--------------|-------|
| MOSI | GPIO10 | Pin 19 | SPI data |
| SCLK | GPIO11 | Pin 23 | SPI clock |
| CE0 | GPIO8 | Pin 24 | Chip select |
| DC | GPIO24 | Pin 18 | Data/command |
| RST | GPIO25 | Pin 22 | Reset |
| BL | GPIO12 | Pin 32 | Backlight (PWM) |

---

## Public PDFs

| File | Content |
|------|---------|
| [nabla-accesorios-lista-y-pines.pdf](pdf/nabla-accesorios-lista-y-pines.pdf) | Accessory → GPIO / physical pin mapping |
| [nabla-edge-esquema-pinout.pdf](pdf/nabla-edge-esquema-pinout.pdf) | Mounting overview diagram |
| [nabla-pegatinas-accesorios.pdf](pdf/nabla-pegatinas-accesorios.pdf) | Accessory label sticker sheet |
| [nabla-pegatinas-pi4.pdf](pdf/nabla-pegatinas-pi4.pdf) | Pi 4 case labels |
| [nabla-pegatinas-zero.pdf](pdf/nabla-pegatinas-zero.pdf) | Pi Zero / W case labels |

---

## Wiring Diagrams

See [diagrams/](diagrams/) for wiring photos:

- OLED I2C connection to Pi
- Rotary encoder wiring
- Combined accessory setup

*(Photos being added by Dom)*

---

## Related

- [oled-ui/](oled-ui/) — OLED paint layer details
- [../esphome-patterns/](../esphome-patterns/) — ESP32 OLED+encoder patterns
- [../../ui/ssd/](../../ui/ssd/) — Layout profiles and tokens
- [../../scripts/nabla-config](../../scripts/nabla-config) — Configuration tool
