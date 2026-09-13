# Architecture

NablaEdge system architecture: three network layers, edge node roles, and component relationships.

---

## The Three Layers

NablaEdge operates across three conceptual network layers:

```mermaid
flowchart TB
    subgraph Layer1["Layer 1: Site LAN"]
        Router[Site Router]
        Switch[Switch]
        Devices[LAN Devices]
        Router --- Switch --- Devices
    end
    
    subgraph Layer2["Layer 2: Mesh VPN Overlay"]
        TS1[Tailscale Node A]
        TS2[Tailscale Node B]
        TS3[Tailscale Node C]
        TS1 <-..-> TS2 <-..-> TS3
    end
    
    subgraph Layer3["Layer 3: Nabla Net (Edge LAN)"]
        Edge[Edge Node<br/>Gateway]
        OLED[OLED Device]
        Sensor[Sensor Node]
        ESP[ESP32 BLE]
        Edge --- OLED
        Edge --- Sensor
        Edge --- ESP
    end
    
    Layer1 --> Layer2
    Layer2 --> Layer3
    
    style Layer1 fill:#e3f2fd
    style Layer2 fill:#fff3e0
    style Layer3 fill:#e8f5e9
```

### Layer 1: Site LAN

The existing local network at a location:
- Standard home/office router
- Ethernet switches
- Existing WiFi
- Internet uplink

Edge nodes connect to this layer for upstream connectivity.

### Layer 2: Mesh VPN Overlay (Conceptual)

A virtual network connecting nodes across sites:
- Encrypted tunnels between locations
- Allows edge nodes at different sites to communicate
- Optional — single-site deployments don't need this

**Note**: Implementation details (Tailscale, WireGuard, etc.) are site-specific and not documented here.

### Layer 3: Nabla Net (Edge LAN)

The local network created by edge nodes for IoT devices:
- Created by edge node in `ap` or `cable-ap` mode
- Isolates edge devices from main LAN
- Runs MQTT broker for device communication
- Devices that can't join main WiFi connect here

---

## Edge Node Roles

A Raspberry Pi edge node can serve multiple roles:

```mermaid
flowchart LR
    subgraph EdgeNode["Edge Node (Pi)"]
        Gateway[Gateway<br/>Mode]
        Imaging[Imaging<br/>Parent]
        Display[Display<br/>+ Menu]
        Camera[Camera<br/>Satellite]
        Voice[Voice<br/>Satellite]
        BLE[BLE<br/>Helper]
    end
    
    Gateway --> |creates| NablaNet[Nabla Net<br/>WiFi/LAN]
    Imaging --> |writes| Media[SD/USB<br/>Images]
    Display --> |renders| OLED[OLED<br/>128×64]
    Camera --> |streams| Video[go2rtc<br/>Stream]
    Voice --> |connects| HA[Home Assistant<br/>Assist]
    BLE --> |detects| Presence[BLE<br/>Presence]
```

### Gateway Mode

Creates and manages Nabla Net:
- Runs `nabla-net` service
- Provides DHCP for Nabla Net clients
- Routes traffic to upstream network
- Runs MQTT broker (optional)

### Imaging Parent

Prepares boot media for new nodes:
- Runs `nabla-image` tool
- Downloads and customizes Pi OS
- Injects first-boot scripts
- Writes to SD/USB media

### Display + Menu

Interactive OLED interface:
- 128×64 OLED (SSD1306 I2C)
- Rotary encoder for navigation
- Receives menus via MQTT
- Executes actions (HA, MQTT, internal)

### Camera Satellite

Video streaming node:
- Pi Camera Module or USB cam
- Streams via go2rtc
- Separate from voice (can combine)

### Voice Satellite

Home Assistant Assist endpoint:
- USB microphone + speaker
- Wake word detection (local)
- Speech-to-text via HA Wyoming
- Text-to-speech response

### BLE Helper

Bluetooth presence and mesh:
- Detects BLE beacons
- Reports presence to MQTT
- Participates in BLE mesh
- Can provision orphaned nodes

---

## Data Flow

### Menu System

```mermaid
sequenceDiagram
    participant Author as Menu Author
    participant MQTT as MQTT Broker
    participant Pi as Pi Edge Node
    participant ESP as ESP32 Device
    
    Author->>Author: Edit menu.yaml
    Author->>Author: Convert to JSON
    Author->>MQTT: Publish retained
    
    par Pi receives
        MQTT-->>Pi: Menu JSON
        Pi->>Pi: Parse & render
    and ESP receives
        MQTT-->>ESP: Menu JSON
        ESP->>ESP: Parse & render
    end
    
    Note over Pi,ESP: User interacts
    
    Pi->>MQTT: Action (toggle light)
    ESP->>MQTT: Action (call scene)
```

### Presence Detection

```mermaid
sequenceDiagram
    participant Phone as Phone (BLE)
    participant Edge as Edge Node
    participant MQTT as MQTT Broker
    participant HA as Home Assistant
    
    Phone->>Edge: BLE advertisement
    Edge->>Edge: Detect presence
    Edge->>MQTT: Publish presence event
    MQTT->>HA: Presence update
    HA->>HA: Trigger automation
```

---

## Component Map

```
nabla-edge/
├── nablaedge/
│   ├── docs/           ← You are here
│   ├── scripts/        ← CLI tools (nabla-config, nabla-net, nabla-image)
│   └── ui/ssd/         ← OLED paint layer
│
├── protocols/
│   └── menu/           ← Menu JSON protocol (backend-agnostic)
│
├── homeassistant/      ← HA integration (optional backend)
├── packages/           ← Apt package metadata
└── dist/               ← HTTP serving config
```

---

## Protocol References

| Protocol | Location | Purpose |
|----------|----------|---------|
| nabla.menu/v1 | [protocols/menu/](../../../protocols/menu/) | MQTT JSON menus |
| OLED Layout | [ui/ssd/](../../ui/ssd/) | 128×64 paint profiles |
| BLE Mesh | [ble-mesh/](../ble-mesh/) | Presence, provisioning |

---

## How to Change This

1. **Add a role**: Create service, add to `nabla-config` menu
2. **Change network**: Modify `nabla-net` modes
3. **New protocol**: Add to `protocols/` with schema
4. **Update docs**: Edit this file, keep diagrams current

---

## Related

- [../network-modes/](../network-modes/) — How Nabla Net modes work
- [../imaging/](../imaging/) — Creating boot images
- [../esphome-patterns/](../esphome-patterns/) — ESP32 device patterns
