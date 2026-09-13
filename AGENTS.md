# AGENTS.md — Contribution & Sanitization Rules

Guidelines for humans and AI agents contributing to this repository.

---

## Golden Rule

**Never commit secrets, credentials, or identifying production data.**

---

## Forbidden Content

Do NOT include:

- Secrets, API keys, tokens, passwords
- WiFi SSIDs or passwords
- Real production `entity_id` values from actual deployments
- Private/internal IP addresses (10.x, 192.168.x, 172.16-31.x)
- Tailscale hostnames or IPs
- Personal names, addresses, or identifying information
- Internal hostnames or domain names

---

## Required Placeholders

When examples need values, use these patterns:

| Type | Placeholder Example |
|------|---------------------|
| Secrets/passwords | `CHANGE_ME`, `YOUR_SECRET_HERE` |
| Entity IDs | `switch.example_light`, `scene.example_night`, `sensor.example_temp` |
| Site names | `demo`, `example`, `test` |
| Hostnames | `example.local`, `mqtt.example.local` |
| IPs (if needed) | `192.0.2.x` (documentation range) or `example.local` |

---

## MQTT Topic Prefixes

Standard prefixes for this project:

```
nabla/esp/...           # ESP device telemetry and commands
nabla/menu/v1/...       # Menu protocol v1 topics
```

Examples:
```
nabla/menu/v1/demo/config      # Menu config for site "demo"
nabla/menu/v1/demo/version     # Version info
nabla/esp/oled01/hello         # Device hello message
```

---

## File Hygiene

### .gitignore Enforcement

The repository `.gitignore` blocks common secret patterns:
- `*.pem`, `*.key`, `*.crt`
- `.env`, `secrets.yaml`, `*_secrets.yaml`
- `credentials.json`

### Before Committing

1. Grep for private IPs: `grep -rE '10\.[0-9]+\.[0-9]+\.[0-9]+|192\.168\.' .`
2. Grep for real entity patterns: `grep -rE 'entity_id:.*[a-z]+_[a-z]+_[a-z]+' .`
3. Check for SSIDs/passwords in YAML
4. Verify no Tailscale references

---

## Example Validation

Good:
```yaml
site: demo
entity_id: switch.example_light
```

Bad:
```yaml
site: villaloba          # Real site name
entity_id: switch.garage_door_opener  # Looks like real entity
ip: 10.0.1.50           # Private IP
```

---

## AI Agent Instructions

When generating code or examples for this repository:

1. Always use placeholder values from the table above
2. Never infer or guess real entity IDs from context
3. Use `demo` as the default site name
4. Use `example_*` pattern for all entity IDs
5. Verify no private IPs slip into generated content
6. When in doubt, use `CHANGE_ME`
