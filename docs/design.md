# IPX800 v3 to MQTT - Design Document

Date: 2026-03-28
Status: draft

---

## Problem Statement

Créer un bridge MQTT pour l'IPX800 v3 afin de l'intégrer à HomeAssistant.
L'IPX800 est une carte domotique avec 32 relais et 32 entrées digitales.

---

## Constraints

- Container Docker
- Language: Python 3.11+
- Protocole push (HTTP) + polling (API REST) pour la récupération des états
- Auto-discovery HomeAssistant MQTT
- Authentification IPX800 via user/password
- Gestion des relais (ON/OFF) et entrées digitales uniquement

---

## Architecture

Architecture monolithique asyncio avec les composants suivants:

1. **HTTP Server** - Reçoit les push de l'IPX800
2. **MQTT Client** - Connexion au broker + publish/subscribe
3. **State Manager** - Stockage et synchronisation des états
4. **Polling Task** - Récupération périodique via API REST
5. **Auto-Discovery Publisher** - Configuration HomeAssistant

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

**Paramètres attendus:**
- `mac` : Adresse MAC de l'IPX800
- `inputs` : 32 caractères (0/1) représentant l'état des entrées
- `outputs` : 32 caractères (0/1) représentant l'état des sorties

**Format URL configurée dans l'IPX800:**
```
http://container:8080/api/ipx/push?mac=$M&inputs=$I&outputs=$O
```

### 2. MQTT Client

**Topics de publication:**
- `ipx800/{mac}/relay/{n}/state` : État des relais (ON/OFF)
- `ipx800/{mac}/input/{n}/state` : État des entrées digitales (ON/OFF)
- `ipx800/{mac}/availability` : Online/offline

**Topics de souscription:**
- `ipx800/{mac}/relay/{n}/set` : Commandes HomeAssistant (ON/OFF)

**Auto-discovery topics:**
- `homeassistant/switch/ipx800_{mac}_{n}/config`
- `homeassistant/binary_sensor/ipx800_{mac}_{n}/config`

### 3. State Manager

- Stockage en mémoire avec `asyncio.Lock`
- Détection des changements
- Synchronisation push ↔ polling

### 4. Polling Task

**Intervalle:** Configurable (défaut 30s)

**Sources de données:**
- `http://ipx800/globalstatus.xml` - XML avec état complet
- `http://ipx800/api/xdevices.json?cmd=10` - Entrées (JSON)
- `http://ipx800/api/xdevices.json?cmd=20` - Sorties (JSON)

**Authentification:** Basic Auth (user:password)

### 5. Auto-Discovery Publisher

Publié au démarrage pour chaque relais et entrée:
- Unique ID basé sur MAC
- Friendly name configurable
- Device info (fabricant, modèle)

---

## Configuration

### Variables d'environnement

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

| Composant | Erreur | Stratégie |
|-----------|--------|-----------|
| MQTT | Déconnexion | Retry exponential backoff (max 60s) |
| HTTP Server | Exception | Log + continue |
| Polling | Timeout/Auth fail | Retry 3x + log warning |
| IPX800 API | 4xx/5xx | Log error + skip cycle |

---

## Testing Strategy

1. **Tests unitaires** - Mock MQTT et HTTP
2. **Tests d'intégration** - Docker Compose avec Mosquitto
3. **Tests E2E** - Simulation IPX800 avec mock serveur

---

## Open Questions

- Nombre de relais/entrées à exposer (configurable ou fixe 32?) → **Fixe 32 pour MVP**
- Gestion des entrées analogiques? → **Non, hors scope**
- Format de log (JSON ou texte)? → **Texte structuré**
