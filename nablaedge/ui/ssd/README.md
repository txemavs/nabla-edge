# SSD OLED UI Paint Layer

Shared visual style definitions for small monochrome OLED displays (SSD1306, SSD1309, etc.) used across NablaEdge devices.

## Contents

| File | Description |
|------|-------------|
| [LAYOUT.md](LAYOUT.md) | Screen regions, coordinate system, platform integration |
| [tokens.yaml](tokens.yaml) | Design tokens: colors, fonts, spacing, selection |
| [profiles/128x64.yaml](profiles/128x64.yaml) | Concrete layout for 128×64 displays |

## Scope

This folder defines **paint and layout only**:
- Where regions appear on screen
- Font sizes and colors
- Spacing and margins

Menu navigation logic lives in [`protocols/menu`](../../protocols/menu/) (coming soon).

## Supported Hardware

- **Raspberry Pi**: luma.oled with SSD1306 (I2C)
- **ESP32**: ESPHome display component with SSD1309 (SPI)

Same profile, different drivers.

## Quick Reference

```
128×64 Layout:
┌──────────────────────────────────────┐ y=0
│ Status Bar (icons + clock)           │ 10px
├──────────────────────────────────────┤
│ Title (large, centered)              │ 22px
├──────────────────────────────────────┤
│ Subtitle                             │ 12px
├──────────────────────────────────────┤
│ Body / Menu                          │ 20px
└──────────────────────────────────────┘ y=64
```
