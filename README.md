# IPX800 v3 to MQTT Bridge

Dockerized bridge to connect an IPX800 v3 domotics card to HomeAssistant via MQTT.

## Features

- **Push notifications** : Instant state change reception via HTTP
- **Polling** : Periodic retrieval (30s by default) to ensure consistency
- **Auto-discovery** : Automatic detection by HomeAssistant
- **32 relays** : ON/OFF command with real-time state
- **32 digital inputs** : Input state monitoring

## Quick Start

```bash
# 1. Clone and start
docker-compose up -d

# 2. Check logs
docker-compose logs -f

# 3. Configure IPX800 push (optional but recommended)
# See "IPX800 Push Configuration" section below

# 4. HomeAssistant will auto-discover all 64 entities
```

## Configuration

### Environment Variables

**Note:** This bridge requires an **external MQTT broker** (e.g., Mosquitto, RabbitMQ, or your HomeAssistant MQTT addon). Configure the broker host below.

| Variable | Description | Default |
|----------|-------------|---------|
| `IPX800_HOST` | IP of the IPX800 | 192.168.1.12 |
| `IPX800_PORT` | HTTP port of the IPX800 | 80 |
| `IPX800_USERNAME` | IPX800 username | your_username |
| `IPX800_PASSWORD` | IPX800 password | - |
| `MQTT_BROKER_HOST` | MQTT broker host | 192.168.1.24 |
| `MQTT_BROKER_PORT` | MQTT port | 1883 |
| `MQTT_USERNAME` | MQTT username (optional) | - |
| `MQTT_PASSWORD` | MQTT password (optional) | - |
| `MQTT_TOPIC_PREFIX` | MQTT topic prefix | ipx800 |
| `POLLING_INTERVAL` | Polling interval (s) | 30 |
| `LOG_LEVEL` | Log level (DEBUG/INFO/WARNING/ERROR) | INFO |

### Docker Compose Configuration

Configuration is passed via environment variables in `docker-compose.yml`:

```yaml
services:
  ipx800-mqtt:
    ports:
      - "8080:8080"  # HOST:CONTAINER (container port is always 8080)
    environment:
      - IPX800_HOST=192.168.1.12
      - IPX800_PASSWORD=your_password
      - MQTT_BROKER_HOST=192.168.1.24
```

Or use an `.env` file to customize the exposed port (optional):
```bash
# Create .env file with your values
echo "IPX800_PASSWORD=secret" > .env
echo "HTTP_PORT=9090" >> .env  # Changes host port only, container stays on 8080
docker-compose up -d
```

### IPX800 Push Configuration

The bridge supports **real-time notifications** via HTTP push from the IPX800. This provides instant state updates without waiting for the next polling cycle.

#### Step 1: Find the Docker Host IP

Find the IP address of the machine running Docker:

```bash
# On macOS
ipconfig getifaddr en0

# On Linux
ip addr show | grep "inet " | head -1
```

Example: `192.168.1.12` (replace with your actual IP)

#### Step 2: Configure IPX800 Push Notifications

In the IPX800 web interface:

1. Navigate to **M2M → Push**
2. In the section **"Send data on events"**, configure the push notification with these settings:

The IPX800 uses 3 separate fields for the URL:

| Field | Value | Example |
|-------|-------|---------|
| **Server** | IP of your Docker host | `<docker-host-ip>` |
| **Port** | `8080` | `8080` |
| **Path** | `/api/ipx/push?mac=$M&inputs=$I&outputs=$O` | `/api/ipx/push?mac=$M&inputs=$I&outputs=$O` |

**Important:** Don't forget the leading `/` in the Path field!

3. **Enable the notification** on the desired events:
   - Check **"On Input Change"** to get instant updates when inputs change
   - The bridge updates immediately when an input or output changes

4. **Save and apply** the configuration

#### Step 3: Test the Configuration

Activate an input on the IPX800 and verify in the bridge logs:

```bash
docker-compose logs -f ipx800-mqtt
```

You should see:
```json
{"event": "push_processed", "mac": "00:1E:C0:XX:XX:XX", "changed_inputs": 1, "changed_outputs": 0}
```

#### Available Tags

The IPX800 supports these substitution tags:

| Tag | Description | Example |
|-----|-------------|---------|
| `$M` | MAC address | `00:1E:C0:XX:XX:XX` |
| `$I` | All 32 input states | `10000000000000000000000000000000` |
| `$O` | All 32 output states | `00000000000000000000000000000000` |

#### Troubleshooting

**No push received?**

1. **Check firewall** on the Docker host:
   ```bash
   # macOS
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   # If enabled, temporarily disable for testing
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
   ```

2. **Verify connectivity** from IPX800 to Docker host:
   - From your phone/browser, test: `http://<docker-ip>:8080/`
   - You should see: **"IPX800 Bridge OK"**

3. **Check logs** for incoming requests:
   ```bash
   docker-compose logs -f ipx800-mqtt | grep push
   ```

4. **Save and restart IPX800**: After configuring the push notification, go to **Configuration → System** and click **Reboot** for changes to take effect

5. **Test an input**: After reboot, activate an input on the IPX800 (e.g., press a button) and check the bridge logs for `push_processed` events

## Usage

### Docker Compose

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### HomeAssistant

Entities are automatically discovered under the `ipx800_` prefix.

**Relays** (switch):
- Entity ID: `switch.ipx800_XXXXXXXXXXXX_relay_X`
- Command: ON/OFF
- State: Real-time

**Inputs** (binary_sensor):
- Entity ID: `binary_sensor.ipx800_XXXXXXXXXXXX_input_X`
- State: ON/OFF

## Architecture

The bridge uses a **hybrid approach** for maximum reliability:

```
                         ┌─────────────────────────────────────┐
                         │      IPX800 v3 Configuration       │
                         │  Push: HTTP → <docker-host-ip>:8080 │
                         └──────────────────┬──────────────────┘
                                            │
              ┌─────────────────────────────┴─────────────────────────┐
              │                           │                           │
              ▼                           ▼                           ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   HTTP Push         │    │   Polling           │    │   MQTT Commands     │
│   (Real-time)       │    │   (30s interval)    │    │   (HomeAssistant)   │
│                     │    │                     │    │                     │
│  Input/Output       │    │  Period sync        │    │  Relay control      │
│  state changes      │    │  for consistency    │    │  ON/OFF commands    │
└──────────┬──────────┘    └──────────┬──────────┘    └─────────┬───────────┘
           │                          │                         │
           ▼                          ▼                         │
┌────────────────────────────────────────────────────────────┐  │
│                      State Manager                          │  │
│              (Tracks all 32 inputs/outputs)                 │◄─┘
└──────────────────────────┬─────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│  MQTT Publish  │ │  Auto-discovery│ │  Availability  │
│  relay/X/state │ │  (HomeAssistant)│ │  online/offline│
│  input/X/state │ │                │ │                │
└────────┬───────┘ └────────────────┘ └────────────────┘
         │
         ▼
┌─────────────────┐
│   HomeAssistant │
│  (Auto-discover)│
└─────────────────┘
```

### Why Hybrid?

- **Push**: Instant updates when states change (fast, efficient)
- **Polling**: Periodic sync to catch missed updates (reliable)
- **Result**: Real-time + never out-of-sync

## MQTT Topics

### Published (no action required)

- `ipx800/{mac}/relay/{n}/state` - Relay state (ON/OFF)
- `ipx800/{mac}/input/{n}/state` - Input state (ON/OFF)
- `ipx800/{mac}/availability` - Online/offline

### Commands (published by HomeAssistant)

- `ipx800/{mac}/relay/{n}/set` - Command a relay (ON/OFF)

### Auto-Discovery (published at startup)

- `homeassistant/switch/ipx800_{mac}_{n}/config` - Relay configuration
- `homeassistant/binary_sensor/ipx800_{mac}_{n}/config` - Input configuration

## Development

### Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=src
```

### Project Structure

```
ipx800-v3-mqtt/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration
│   ├── state_manager.py     # State management
│   ├── ipx800_client.py     # IPX800 API client
│   ├── mqtt_client.py       # MQTT client
│   ├── http_server.py       # HTTP push server
│   └── auto_discovery.py    # HA auto-discovery
├── tests/
│   ├── test_config.py
│   ├── test_state_manager.py
│   ├── test_ipx800_client.py
│   ├── test_mqtt_client.py
│   ├── test_auto_discovery.py
│   └── test_http_server.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## License

MIT License
