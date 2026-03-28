# API IPX800 – Commandes M2M et HTTP

**Auteur :** Patrick Gorce / Lionel Février  
**Original :** 28/11/2011  
**Mise à jour :** 18/07/2012  

> Compte tenu de l'évolution constante des produits, certaines commandes peuvent être sans effet.  
> Support : 0811034813  
> Email : support@gce-electronics.com  

---

## Protocole de communication M2M IPX800 (mode serveur)

Les ordres sont envoyés par trame TCP/IP sur le port **9870** (modifiable via l’interface web).

---

### Commander une sortie : `Set`

**Syntaxe :**
```text
Setxxy
```

- `xx` : numéro de sortie (01 à 32)  
- `y` : état (0 = OFF, 1 = ON)

**Exemples :**
```text
Set011    # Relais 1 ON
Set011p   # Mode impulsionnel (nécessite Ta et Tb configurés)
```

---

### Commander les sorties simultanément : `Bit=`

Permet de définir l’état des 32 sorties en une seule commande.

**Exemples :**
```text
Bit=0000  # Toutes les sorties OFF
Bit=1111  # Toutes les sorties ON
```

---

### Obtenir l’état d’une entrée : `GetIn`

```text
GetInx
```

- `x` : entrée (1 à 32)

**Exemple :**
```text
GetIn1 → GetIn1=0
```

---

### Obtenir toutes les entrées : `GetInputs`

```text
GetInputs → GetInputs=0000
```

> Le dernier caractère correspond à l’entrée 32.

---

### Entrée analogique : `GetAn`

```text
GetAnx
```

- `x` : entrée analogique (1 à 4)

**Exemple :**
```text
GetAn1 → GetAn1=512 (0 à 1023)
```

---

### Compteur : `GetCount`

```text
GetCountx
```

- `x` : compteur (1 à 3)

**Exemple :**
```text
GetCount1 → GetCount1=0
```

---

### État d’une sortie : `GetOut`

```text
GetOutx
```

**Exemple :**
```text
GetOut1 → GetOut1=1
```

---

### Toutes les sorties : `GetOutputs`

```text
GetOutputs → GetOutputs=0000
```

---

### Reset compteur : `ResetCount`

```text
ResetCountx
```

**Exemple :**
```text
ResetCount1 → Success
```

---

### Reset système : `Reset`

```text
Reset
```

→ Redémarre l’IPX800

---

# Commandes HTTP

> Certaines commandes peuvent varier selon firmware.

---

### Simuler une entrée

```text
http://IPX800_V3/leds.cgi?led-x
```

- `x` : 100 à 131

---

### Réinitialiser un timer

```text
http://IPX800_V3/protect/timers/timer1.htm?erase-x
```

- `x` : 0 à 127

---

### Programmer un timer

```text
http://IPX800_V3/protect/timers/timer1.htm?
```

**Paramètres :**
- `timer-x` : numéro (0 à 127)
- `day-x` :
  - 0–6 : lundi → dimanche
  - 7 : tous les jours
  - 8 : semaine
  - 9 : week-end
- `time-HH%3AMM`
- `relay-x` : sortie (0 à 31) ou compteur (32 à 34)
- `action-x` :
  - 0 = off
  - 1 = on
  - 2 = inversion
  - 3 = impulsion
  - 4 = annulation
  - 7 = reset compteur

---

### Commander une sortie (impulsion possible)

```text
http://IPX800_V3/leds.cgi?led-x
```

- `x` : 0 à 31

---

### Commander une sortie (forcé ON/OFF)

```text
http://IPX800_V3/preset.htm?setx-1
http://IPX800_V3/preset.htm?setx-0
```

---

### Gestion des compteurs

```text
http://IPX800_V3/protect/assignio/counter.htm?
```

- `counternamex=NOM`
- `counterx=valeur`

---

### Configuration sortie

```text
http://IPX800_V3/protect/settings/output1.htm?
```

**Paramètres :**
- `output-x` : 1 à 32
- `relayname-NOM`
- `delayon-x` (Ta)
- `delayoff-y` (Tb)

---

### Configuration entrée digitale

```text
http://IPX800_V3/protect/assignio/assign1.htm?
```

**Paramètres :**
- `input-x` : 0 à 31
- `inputname-NOM`
- `lx-1` : sortie assignée
- `mode-x` :
  - 0 = on/off
  - 1 = switch
  - 2 = VR
  - 3 = ON
  - 4 = OFF
- `inv-1` : inversion

---

### Configuration entrée analogique

```text
http://IPX800_V3/protect/assignio/analog1.htm?
```

**Paramètres :**
- `analog-x` : 0 à 3
- `name-NOM`
- `selectinput-x` :
  - 0 = brut
  - 1 = tension
  - 2 = TC4012
  - 3 = lumière
  - 4 = température
  - 5 = humidité
- `hi-x`, `lo-x` : seuils
- `mhi`, `mlo` : actions
- `lkax-1` : sortie assignée

---

### Ping watchdog

```text
http://IPX800_V3/protect/settings/ping.htm?
```

**Paramètres :**
- `pingip-xxx.xxx.xxx.xxx`
- `pingtime-x`
- `pingretry-x`
- `prelay-x`

---

## XML Status

```text
http://ipx800_v3/status.xml
```

→ Retourne l’état complet des entrées/sorties
