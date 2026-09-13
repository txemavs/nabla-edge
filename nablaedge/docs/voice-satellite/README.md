# Voice satellite

A Nabla Edge Pi can become a **conversation point**: mic + speakers (+ optional USB camera), HDMI to a TV, talking to Home Assistant Assist (e.g. Whisper).

![Voice satellite](diagrams/voice-satellite-generic.jpg)

## Split of concerns

- **Voice path** — Assist / Wyoming-style pipeline (mic → intent → HA).
- **Camera path** — separate (often go2rtc); do not conflate with the voice stack.

## Status

Design/ready notes; full install steps land as the package matures. No site-specific entity names here.
