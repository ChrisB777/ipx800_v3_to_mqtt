# IPX800 v3 to MQTT Bridge

Dockerized bridge to connect an IPX800 v3 domotics card to HomeAssistant via MQTT with auto-discovery.

## Features

- **🚀 Real-time push notifications** - Instant state updates via HTTP push from IPX800
- **🔄 Hybrid architecture** - Push for speed + polling for reliability
- **🏠 HomeAssistant auto-discovery** - 64 entities automatically detected
- **⚡ 32 relays** - ON/OFF control with real-time state
- **🔌 32 digital inputs** - State monitoring
- **📡 MQTT commands** - Control relays from any MQTT client

## Quick Start

```yaml
# docker-compose.yml
version: '3.8'
services:
  ipx800-mqtt:
    image: chrisb777/ipx800_v3_to_mqtt:v1.0.0
    container_name: ipx800-mqtt
    ports:
      - "8080:8080"
    environment:
      - IPX800_HOST=192.168.1.12
      - IPX800_USERNAME=your_username
      - IPX800_PASSWORD=your_password
      - MQTT_BROKER_HOST=192.168.1.24
      - MQTT_USERNAME=your_mqtt_user
      - MQTT_PASSWORD=your_mqtt_password
    restart: unless-stopped
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IPX800_HOST` | IP of the IPX800 | 192.168.1.12 |
| `IPX800_PORT` | HTTP port | 80 |
| `IPX800_USERNAME` | IPX800 username | - |
| `IPX800_PASSWORD` | IPX800 password | - |
| `MQTT_BROKER_HOST` | MQTT broker host | 192.168.1.24 |
| `MQTT_BROKER_PORT` | MQTT port | 1883 |
| `MQTT_USERNAME` | MQTT username | - |
| `MQTT_PASSWORD` | MQTT password | - |
| `MQTT_TOPIC_PREFIX` | Topic prefix | ipx800 |
| `POLLING_INTERVAL` | Polling interval (s) | 30 |
| `LOG_LEVEL` | Log level | INFO |

## IPX800 Push Configuration

For real-time updates, configure HTTP push in your IPX800:

**Menu**: M2M → Push → "Send data on events"

| Field | Value |
|-------|-------|
| Server | `<docker-host-ip>` |
| Port | `8080` |
| Path | `/api/ipx/push?mac=$M&inputs=$I&outputs=$O` |

## MQTT Topics

**Published:**
- `ipx800/{mac}/relay/{n}/state` - Relay state (ON/OFF)
- `ipx800/{mac}/input/{n}/state` - Input state (ON/OFF)
- `ipx800/{mac}/availability` - Bridge status

**Commands:**
- `ipx800/{mac}/relay/{n}/set` - Send ON/OFF to control relay

**Auto-discovery:**
- `homeassistant/switch/ipx800_{mac}_{n}/config`
- `homeassistant/binary_sensor/ipx800_{mac}_{n}/config`

## Links

- [GitHub Repository](https://github.com/ChrisB777/ipx800_v3_to_mqtt)
- [Documentation](https://github.com/ChrisB777/ipx800_v3_to_mqtt#readme)
- [Releases](https://github.com/ChrisB777/ipx800_v3_to_mqtt/releases)

## Tags

- `v1.0.0`, `latest` - Stable release

## License

MIT License
