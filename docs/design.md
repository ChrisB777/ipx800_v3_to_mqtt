# IPX800 v3 to MQTT - Design Document

Date: 2026-03-28
Status: draft

---

## Problem Statement

Create an MQTT bridge for the IPX800 v3 to integrate it with HomeAssistant.
The IPX800 is a domotics card with 32 relays and 32 digital inputs.

---

## Constraints

- Docker container
- Language: Python 3.11+
- Push protocol (HTTP) + polling (API REST) for state retrieval
- HomeAssistant MQTT auto-discovery
- IPX800 authentication via user/password
- Management of relays (ON/OFF) and digital inputs only

---

## Architecture

Monolithic asyncio architecture with the following components:

1. **HTTP Server** - Receives push notifications from IPX800
2. **MQTT Client** - Connection to broker + publish/subscribe
3. **State Manager** - State storage and synchronization
4. **Polling Task** - Periodic retrieval via REST API
5. **Auto-Discovery Publisher** - HomeAssistant configuration

---

## Data Flow

```
IPX800 v3 --(HTTP Push)--> HTTP Server ---> State Manager
     ^                                            |
     |----(XML/JSON Polling)----< Polling Task <---|
                                                  |
                                            MQTT Client
                                                  |
                                                  v
                                          HomeAssistant
```

---

## Components

### 1. HTTP Server (Push Receiver)

**Endpoint:** `POST /api/ipx/push`

**Expected parameters:**
- `mac` : MAC address of the IPX800
- `inputs` : 32 characters (0/1) representing input states
- `outputs` : 32 characters (0/1) representing output states

**URL format configured in IPX800:**
```
http://container:8080/api/ipx/push?mac=$M&inputs=$I&outputs=$O
```

### 2. MQTT Client

**Publication topics:**
- `ipx800/{mac}/relay/{n}/state` : Relay state (ON/OFF)
- `ipx800/{mac}/input/{n}/state` : Digital input state (ON/OFF)
- `ipx800/{mac}/availability` : Online/offline

**Subscription topics:**
- `ipx800/{mac}/relay/{n}/set` : HomeAssistant commands (ON/OFF)

**Auto-discovery topics:**
- `homeassistant/switch/ipx800_{mac}_{n}/config`
- `homeassistant/binary_sensor/ipx800_{mac}_{n}/config`

### 3. State Manager

- In-memory storage with `asyncio.Lock`
- Change detection
- Push ↔ polling synchronization

### 4. Polling Task

**Interval:** Configurable (default 30s)

**Data sources:**
- `http://ipx800/globalstatus.xml` - XML with complete state
- `http://ipx800/api/xdevices.json?cmd=10` - Inputs (JSON)
- `http://ipx800/api/xdevices.json?cmd=20` - Outputs (JSON)

**Authentication:** Basic Auth (user:password)

### 5. Auto-Discovery Publisher

Published at startup for each relay and input:
- Unique ID based on MAC
- Configurable friendly name
- Device info (manufacturer, model)

---

## Configuration

### Environment Variables

```env
# IPX800 Configuration
IPX800_HOST=192.168.1.100
IPX800_PORT=80
IPX800_USERNAME=admin
IPX800_PASSWORD=secret

# MQTT Configuration
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=ipx800-bridge

# Bridge Configuration
HTTP_PORT=8080
POLLING_INTERVAL=30
LOG_LEVEL=INFO
```

---

## Error Handling

| Component | Error | Strategy |
|-----------|-------|----------|
| MQTT | Disconnection | Exponential backoff retry (max 60s) |
| HTTP Server | Exception | Log + continue |
| Polling | Timeout/Auth fail | Retry 3x + log warning |
| IPX800 API | 4xx/5xx | Log error + skip cycle |

---

## Testing Strategy

1. **Unit tests** - Mock MQTT and HTTP
2. **Integration tests** - Docker Compose with Mosquitto
3. **E2E tests** - IPX800 simulation with mock server

---

## Open Questions

- Number of relays/inputs to expose (configurable or fixed 32?) → **Fixed 32 for MVP**
- Analog input management? → **No, out of scope**
- Log format (JSON or text)? → **Structured text**
