# Norish Integration - Bilder für Mahlzeiten anzeigen

## Übersicht

Es gibt **zwei Möglichkeiten**, um Bilder von Rezepten in Home Assistant anzuzeigen:

### Option 1: Sensor mit `entity_picture` (Empfohlen)
- ✅ Einfacher zu implementieren
- ✅ Funktioniert direkt in allen Dashboard-Karten
- ✅ Zeigt Bild automatisch in Entity Card, Picture Entity Card, etc.
- ✅ Geringer Overhead

### Option 2: Camera Entity
- ✅ Maximale Kontrolle über Bilddarstellung
- ✅ Nutzt Home Assistant's Camera-Infrastruktur
- ✅ Kann in Picture Glance Card verwendet werden
- ⚠️ Komplexer zu implementieren

---

## Option 1: Sensor mit entity_picture (Empfohlen)

### Installation

1. **Ersetze die `sensor.py` Datei:**
   ```bash
   cp sensor_with_images.py custom_components/norish/sensor.py
   ```

2. **Starte Home Assistant neu**

3. **Das war's!** Die Sensoren zeigen jetzt automatisch Bilder an.

### Verfügbare Sensoren

Nach der Installation hast du mehrere Sensoren:

- **Norish Mahlzeiten Heute** - Zeigt alle Mahlzeiten
- **Norish Frühstück** - Nur Frühstück
- **Norish Mittagessen** - Nur Mittagessen  
- **Norish Abendessen** - Nur Abendessen
- **Norish Snack** - Nur Snacks

### Dashboard-Verwendung

#### Variante A: Picture Entity Card (Großes Bild)
```yaml
type: picture-entity
entity: sensor.norish_mittagessen
show_name: true
show_state: true
```

#### Variante B: Entity Card (Mit kleinem Bild)
```yaml
type: entities
entities:
  - entity: sensor.norish_mittagessen
    secondary_info: last-changed
  - entity: sensor.norish_abendessen
    secondary_info: last-changed
```

#### Variante C: Picture Glance (Mehrere Mahlzeiten)
```yaml
type: picture-glance
title: Heute auf dem Speiseplan
entities:
  - sensor.norish_fruhstuck
  - sensor.norish_mittagessen
  - sensor.norish_abendessen
camera_image: sensor.norish_mittagessen
```

#### Variante D: Custom Card mit Template
```yaml
type: markdown
content: |
  ## 🍽️ Essen Heute
  
  {% set lunch = states.sensor.norish_mittagessen %}
  {% if lunch.attributes.image %}
  ![{{ lunch.state }}]({{ lunch.attributes.image }})
  {% endif %}
  
  **{{ lunch.state }}**
  
  {% if lunch.attributes.description %}
  {{ lunch.attributes.description }}
  {% endif %}
```

---

## Option 2: Camera Entity

### Installation

1. **Kopiere die `camera.py` Datei:**
   ```bash
   cp camera.py custom_components/norish/camera.py
   ```

2. **Aktualisiere `__init__.py`:**
   ```python
   # Füge "camera" zur PLATFORMS Liste hinzu:
   PLATFORMS = ["sensor", "todo", "calendar", "camera"]
   ```

3. **Aktualisiere `manifest.json`:**
   ```json
   {
     "version": "0.0.5",
     "dependencies": ["camera"]
   }
   ```

4. **Starte Home Assistant neu**

### Verfügbare Kameras

- **Norish Frühstück Bild**
- **Norish Mittagessen Bild**
- **Norish Abendessen Bild**
- **Norish Snack Bild**

### Dashboard-Verwendung

#### Picture Glance Card
```yaml
type: picture-glance
camera_image: camera.norish_mittagessen_bild
entities:
  - sensor.norish_mittagessen
title: Mittagessen Heute
```

#### Picture Entity Card
```yaml
type: picture-entity
entity: camera.norish_mittagessen_bild
show_name: true
show_state: false
```

---

## Datenstruktur-Anforderungen

Damit Bilder angezeigt werden, muss die Norish API folgende Felder liefern:

### In der Calendar API Response:
```json
{
  "date": "2026-01-29T00:00:00.000Z",
  "type": "LUNCH",
  "recipe": {
    "id": "123",
    "name": "Spaghetti Carbonara",
    "image": "https://your-server.com/images/carbonara.jpg",
    // Alternative Feldnamen die auch funktionieren:
    // "imageUrl": "...",
    // "picture": "...",
    // "photo": "...",
    // "thumbnail": "..."
    "description": "Klassisches italienisches Pasta-Gericht",
    "cookingTime": 30,
    "servings": 4
  }
}
```

### Oder direkt im Event:
```json
{
  "date": "2026-01-29T00:00:00.000Z",
  "type": "LUNCH",
  "recipeName": "Spaghetti Carbonara",
  "image": "https://your-server.com/images/carbonara.jpg"
}
```

---

## Troubleshooting

### Problem: Kein Bild wird angezeigt

**Prüfe die Logs:**
```bash
grep -i "norish.*bild" /config/home-assistant.log
```

**Debugging aktivieren:**
```yaml
# In configuration.yaml
logger:
  default: info
  logs:
    custom_components.norish: debug
```

**Mögliche Ursachen:**

1. **Keine Bild-URL in API-Daten**
   - Prüfe: `Developer Tools > States > sensor.norish_mittagessen`
   - Schaue in `attributes.raw_data`
   - Sollte ein `image` Feld enthalten

2. **CORS-Probleme** (bei externen Bildern)
   - Norish Server muss CORS-Header senden
   - Oder: Bilder über lokalen Proxy laden

3. **Bild-URL nicht erreichbar**
   - Teste die URL direkt im Browser
   - Prüfe Firewall/Netzwerk

4. **Falsches Feld in API**
   ```python
   # In sensor_with_images.py kannst du weitere Feldnamen hinzufügen:
   image_url = (
       recipe.get("image") or
       recipe.get("imageUrl") or
       recipe.get("picture") or
       recipe.get("deinFeldName")  # <-- Hier eigenen Feldnamen eintragen
   )
   ```

---

## Erweiterte Konfiguration

### Custom Fallback-Bild

Wenn kein Bild vorhanden ist, zeige ein Standard-Bild:

```python
# In sensor_with_images.py, in der entity_picture Property:
@property
def entity_picture(self) -> Optional[str]:
    meals = self._get_filtered_meals()
    
    if not meals:
        return "/local/norish/no-meal.png"  # Fallback
    
    first_meal = meals[0]
    image_url = first_meal.get('image')
    
    if image_url:
        return image_url
    
    # Standard-Bild je nach Mahlzeit-Typ
    fallback_images = {
        "BREAKFAST": "/local/norish/breakfast-default.png",
        "LUNCH": "/local/norish/lunch-default.png",
        "DINNER": "/local/norish/dinner-default.png",
        "SNACK": "/local/norish/snack-default.png",
    }
    
    return fallback_images.get(
        first_meal['type'].upper(), 
        "/local/norish/meal-default.png"
    )
```

### Bilder lokal cachen (Performance)

Für bessere Performance kannst du Bilder lokal cachen:

```python
import hashlib
from pathlib import Path

async def _download_and_cache_image(self, url: str) -> Optional[str]:
    """Lade Bild herunter und cache es lokal."""
    # Hash der URL als Dateiname
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_dir = Path("/config/www/norish_cache")
    cache_dir.mkdir(exist_ok=True, parents=True)
    
    cache_file = cache_dir / f"{url_hash}.jpg"
    
    # Wenn gecacht, gib lokale URL zurück
    if cache_file.exists():
        return f"/local/norish_cache/{url_hash}.jpg"
    
    # Ansonsten: Download
    try:
        async with self.coordinator.api_data["session"].get(url) as resp:
            if resp.status == 200:
                data = await resp.read()
                cache_file.write_bytes(data)
                return f"/local/norish_cache/{url_hash}.jpg"
    except Exception as e:
        _LOGGER.error(f"Cache-Fehler: {e}")
    
    # Fallback: Original-URL
    return url
```

---

## Beispiel-Dashboard

### Vollständiges Mahlzeiten-Dashboard

```yaml
title: 🍽️ Speiseplan
type: vertical-stack
cards:
  # Großes Bild des Hauptgerichts
  - type: picture-entity
    entity: sensor.norish_mittagessen
    show_name: true
    show_state: true
    
  # Details zu allen Mahlzeiten
  - type: entities
    title: Heute
    entities:
      - entity: sensor.norish_fruhstuck
        secondary_info: last-changed
      - entity: sensor.norish_mittagessen
        secondary_info: last-changed
      - entity: sensor.norish_abendessen
        secondary_info: last-changed
      - entity: sensor.norish_snack
        secondary_info: last-changed
  
  # Kompakte Übersicht mit Bildern
  - type: horizontal-stack
    cards:
      - type: picture-entity
        entity: sensor.norish_fruhstuck
        show_name: true
        show_state: false
      - type: picture-entity
        entity: sensor.norish_mittagessen
        show_name: true
        show_state: false
      - type: picture-entity
        entity: sensor.norish_abendessen
        show_name: true
        show_state: false
```

---

## API-Änderungen erforderlich?

**Nein!** Die Integration funktioniert mit verschiedenen Datenstrukturen:

✅ Funktioniert mit: `image`, `imageUrl`, `picture`, `photo`, `thumbnail`
✅ Funktioniert mit: Bild im `recipe`-Objekt ODER direkt im Event
✅ Graceful degradation: Wenn kein Bild → zeigt nur Text

**Aber:** Wenn deine API aktuell **gar keine** Bild-URLs liefert, musst du das Backend erweitern.

---

## Empfehlung

**Starte mit Option 1 (Sensor mit entity_picture)**
- Einfacher
- Funktioniert sofort
- Deckt 95% der Use Cases ab

**Wechsle zu Option 2 (Camera) nur wenn:**
- Du spezielle Bildverarbeitung brauchst
- Du die Camera-Infrastruktur von HA nutzen willst
- Du Bilder in Picture Glance Cards brauchst

---

## Nächste Schritte

1. Prüfe, ob deine Norish API Bild-URLs liefert
2. Installiere `sensor_with_images.py`
3. Teste mit einer Picture Entity Card
4. Bei Problemen: Debug-Logs prüfen
5. Dashboard nach Wunsch anpassen
