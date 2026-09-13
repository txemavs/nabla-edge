# OLED UI (under Accessories)

Shared monochrome layout: status bar + title + subtitle.

Source of truth for paint tokens/profiles:

- [`../../../ui/ssd/`](../../../ui/ssd/) — `LAYOUT.md`, `tokens.yaml`, `profiles/128x64.yaml`

Drivers (same 128×64 profile):

- Pi: `ssd1306` I2C (luma.oled)
- ESP: e.g. `ssd1309` SPI — same layout profile, different driver
