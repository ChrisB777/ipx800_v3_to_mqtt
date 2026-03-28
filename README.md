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
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IPX800_HOST` | IP of the IPX800 | 192.168.1.100 |
| `IPX800_PORT` | HTTP port of the IPX800 | 80 |
| `IPX800_USERNAME` | IPX800 username | admin |
| `IPX800_PASSWORD` | IPX800 password | - |
| `MQTT_BROKER_HOST` | MQTT broker host | mosquitto |
| `MQTT_BROKER_PORT` | MQTT port | 1883 |
| `MQTT_USERNAME` | MQTT username (optional) | - |
| `MQTT_PASSWORD` | MQTT password (optional) | - |
| `MQTT_TOPIC_PREFIX` | MQTT topic prefix | ipx800 |
| `HTTP_PORT` | HTTP server port | 8080 |
| `POLLING_INTERVAL` | Polling interval (s) | 30 |
| `LOG_LEVEL` | Log level (DEBUG/INFO/WARNING/ERROR) | INFO |

### Docker Compose Configuration

Configuration is passed via environment variables in `docker-compose.yml`:

```yaml
services:
  ipx800-mqtt:
    environment:
      - IPX800_HOST=192.168.1.100
      - IPX800_PASSWORD=your_password
      - MQTT_BROKER_HOST=mosquitto
```

Or use an `.env` file with docker-compose (optional):
```bash
# Create .env file with your values
echo "IPX800_PASSWORD=secret" > .env
docker-compose up -d
```

### IPX800 Configuration

In the IPX800 web interface, configure a push notification:

**URL**: `http://<container-ip>:8080/api/ipx/push?mac=$M&inputs=$I&outputs=$O`

Replace `<container-ip>` with the IP of the container or Docker host.

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

```
┌─────────────┐      HTTP Push      ┌──────────────┐
│   IPX800    │ ──────────────────> │  HTTP Server │
│    v3       │                     │   (Push)     │
└─────────────┘                     └──────┬───────┘
                                           │
                                           v
┌─────────────┐      Polling      ┌──────────────┐     State update     ┌─────────────┐
│   IPX800    │ <──────────────── │  Polling     │ ───────────────────> │   State     │
│    v3       │    (API REST)     │   Task       │                      │   Manager   │
└─────────────┘                   └──────────────┘                      └──────┬───────┘
                                                                               │
                               ┌───────────────────────────────────────────────┘
                               v
                     ┌─────────────────┐
                     │  MQTT Client    │
                     │  (Publish)      │
                     └────────┬────────┘
                              │
                              v
                     ┌─────────────────┐
                     │   HomeAssistant │
                     │  (Auto-discover)│
                     └─────────────────┘
```

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
