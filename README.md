# IPX800 v3 to MQTT Bridge

Bridge Dockerisé pour connecter une carte IPX800 v3 à HomeAssistant via MQTT.

## Fonctionnalités

- **Push notifications** : Réception instantanée des changements d'état via HTTP
- **Polling** : Récupération périodique (30s par défaut) pour garantir la cohérence
- **Auto-discovery** : Détection automatique par HomeAssistant
- **32 relais** : Commande ON/OFF avec état en temps réel
- **32 entrées digitales** : État des entrées

## Quick Start

```bash
docker-compose up -d
```

## Configuration

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `IPX800_HOST` | IP de l'IPX800 | 192.168.1.100 |
| `IPX800_PORT` | Port HTTP de l'IPX800 | 80 |
| `IPX800_USERNAME` | Utilisateur IPX800 | admin |
| `IPX800_PASSWORD` | Mot de passe IPX800 | - |
| `MQTT_BROKER_HOST` | Host du broker MQTT | mosquitto |
| `MQTT_BROKER_PORT` | Port MQTT | 1883 |
| `MQTT_USERNAME` | Utilisateur MQTT (optionnel) | - |
| `MQTT_PASSWORD` | Mot de passe MQTT (optionnel) | - |
| `HTTP_PORT` | Port du serveur HTTP | 8080 |
| `POLLING_INTERVAL` | Intervalle de polling (s) | 30 |
| `LOG_LEVEL` | Niveau de log (DEBUG/INFO/WARNING/ERROR) | INFO |

### Créer un fichier .env

```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

### Configuration IPX800

Dans l'interface web de l'IPX800, configurer une notification push :

**URL**: `http://<container-ip>:8080/api/ipx/push?mac=$M&inputs=$I&outputs=$O`

Remplacez `<container-ip>` par l'IP du conteneur ou du host Docker.

## Utilisation

### Docker Compose

```bash
# Lancer
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

### HomeAssistant

Les entités sont automatiquement découvertes sous le préfixe `ipx800_`.

**Relais** (switch):
- Entity ID: `switch.ipx800_XXXXXXXXXXXX_relay_X`
- Commande: ON/OFF
- État: Temps réel

**Entrées** (binary_sensor):
- Entity ID: `binary_sensor.ipx800_XXXXXXXXXXXX_input_X`
- État: ON/OFF

## Architecture

```
┌─────────────┐      HTTP Push      ┌──────────────┐
│   IPX800    │ ──────────────────> │  HTTP Server │
│    v3       │                     │   (Push)     │
└─────────────┘                     └──────┬───────┘
                                           │
                                           v
┌─────────────┐      Polling      ┌──────────────┐     Mise à jour     ┌─────────────┐
│   IPX800    │ <──────────────── │  Polling     │ ─────────────────> │   State     │
│    v3       │    (API REST)     │   Task       │      état          │   Manager   │
└─────────────┘                   └──────────────┘                    └──────┬───────┘
                                                                             │
                              ┌──────────────────────────────────────────────┘
                              v
                    ┌─────────────────┐
                    │  MQTT Client    │
                    │  (Publication)  │
                    └────────┬────────┘
                             │
                             v
                    ┌─────────────────┐
                    │   HomeAssistant │
                    │  (Auto-discover)│
                    └─────────────────┘
```

## Topics MQTT

### Publication (sans action requise)

- `ipx800/{mac}/relay/{n}/state` - État des relais (ON/OFF)
- `ipx800/{mac}/input/{n}/state` - État des entrées (ON/OFF)
- `ipx800/{mac}/availability` - Online/offline

### Commande (publié par HomeAssistant)

- `ipx800/{mac}/relay/{n}/set` - Commander un relais (ON/OFF)

### Auto-Discovery (publié au démarrage)

- `homeassistant/switch/ipx800_{mac}_{n}/config` - Configuration relais
- `homeassistant/binary_sensor/ipx800_{mac}_{n}/config` - Configuration entrées

## Développement

### Tests

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer les tests
python -m pytest tests/ -v

# Avec couverture
python -m pytest tests/ -v --cov=src
```

### Structure du projet

```
ipx800-v3-mqtt/
├── src/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée
│   ├── config.py            # Configuration
│   ├── state_manager.py     # Gestion d'état
│   ├── ipx800_client.py     # Client API IPX800
│   ├── mqtt_client.py       # Client MQTT
│   ├── http_server.py       # Serveur HTTP push
│   └── auto_discovery.py    # Auto-discovery HA
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
