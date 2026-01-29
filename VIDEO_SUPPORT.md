# 🎥 Norish Video-Unterstützung

## Übersicht

Die Norish Integration unterstützt jetzt sowohl **Bilder** als auch **Videos** für Rezepte!

### Unterstützte Video-Formate

- ✅ **YouTube** (automatische Erkennung + Embed)
- ✅ **Vimeo** (automatische Erkennung)
- ✅ **Direkte Video-URLs** (MP4, WebM, etc.)
- ✅ **Video-Thumbnails** (automatisch von YouTube oder manuell)

---

## 📊 Video-Daten in Sensoren

### Verfügbare Attribute

Jeder Mahlzeiten-Sensor enthält jetzt zusätzliche Video-Informationen:

```yaml
# Beispiel Sensor-Attribute
sensor.norish_mittagessen:
  state: "Spaghetti Carbonara"
  attributes:
    # Video-URLs
    video_url: "https://www.youtube.com/watch?v=ABC123"
    video_type: "youtube"  # youtube, vimeo, oder direct
    video_thumbnail: "https://img.youtube.com/vi/ABC123/maxresdefault.jpg"
    
    # YouTube-spezifisch
    youtube_id: "ABC123"
    youtube_embed_url: "https://www.youtube.com/embed/ABC123"
    
    # Listen
    videos:
      - name: "Spaghetti Carbonara"
        type: "Lunch"
        url: "https://www.youtube.com/watch?v=ABC123"
        video_type: "youtube"
        youtube_id: "ABC123"
        thumbnail: "https://..."
    
    # Status-Flags
    has_video: true
    has_image: true
```

---

## 🎬 Dashboard-Karten für Videos

### 1. YouTube Video einbetten

**Webpage Card (Custom Component erforderlich):**
```yaml
type: custom:webpage-card
url: >-
  {{ state_attr('sensor.norish_mittagessen', 'youtube_embed_url') }}
aspect_ratio: 56%
```

**Installation Webpage Card:**
Via HACS → Frontend → "Webpage Card"

---

### 2. Video-Link mit Thumbnail

**Picture Entity Card mit Link:**
```yaml
type: picture-entity
entity: sensor.norish_mittagessen
show_name: true
show_state: true
tap_action:
  action: url
  url_path: >-
    {{ state_attr('sensor.norish_mittagessen', 'video_url') }}
```

---

### 3. Markdown Card mit Video

```yaml
type: markdown
content: |
  ## 🍽️ {{ states('sensor.norish_mittagessen') }}
  
  {% set video_url = state_attr('sensor.norish_mittagessen', 'video_url') %}
  {% set youtube_id = state_attr('sensor.norish_mittagessen', 'youtube_id') %}
  
  {% if youtube_id %}
  ### 🎥 Rezept-Video
  <iframe width="100%" height="315" 
    src="https://www.youtube.com/embed/{{ youtube_id }}" 
    frameborder="0" 
    allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" 
    allowfullscreen>
  </iframe>
  {% elif video_url %}
  [📺 Video ansehen]({{ video_url }})
  {% endif %}
```

---

### 4. Custom Button Card mit Video

```yaml
type: custom:button-card
entity: sensor.norish_mittagessen
name: "Mittagessen"
show_entity_picture: true
tap_action:
  action: url
  url_path: >-
    [[[ return entity.attributes.video_url || '#'; ]]]
styles:
  card:
    - height: 200px
  img_cell:
    - position: relative
  custom_fields:
    video_icon:
      - position: absolute
      - top: 10px
      - right: 10px
      - color: white
      - font-size: 30px
custom_fields:
  video_icon: >
    [[[ 
      if (entity.attributes.has_video) {
        return '<ha-icon icon="mdi:play-circle"></ha-icon>';
      }
    ]]]
```

---

### 5. Komplettes Video-Dashboard

```yaml
type: vertical-stack
cards:
  # Titel
  - type: markdown
    content: |
      # 🎬 Heute Kochen
      {{ states('sensor.norish_mittagessen') }}
  
  # Video-Thumbnail mit Play-Button
  - type: picture-entity
    entity: sensor.norish_mittagessen
    show_name: false
    show_state: false
    tap_action:
      action: url
      url_path: >-
        {{ state_attr('sensor.norish_mittagessen', 'video_url') }}
  
  # Video eingebettet (wenn YouTube)
  - type: conditional
    conditions:
      - entity: sensor.norish_mittagessen
        state_not: "Kein Plan"
    card:
      type: custom:webpage-card
      url: >-
        {% if state_attr('sensor.norish_mittagessen', 'youtube_embed_url') %}
        {{ state_attr('sensor.norish_mittagessen', 'youtube_embed_url') }}
        {% endif %}
      aspect_ratio: 56%
  
  # Rezept-Details
  - type: entities
    entities:
      - entity: sensor.norish_mittagessen
        type: attribute
        attribute: cooking_time
        name: "Zubereitungszeit"
        suffix: " Min."
      - entity: sensor.norish_mittagessen
        type: attribute
        attribute: servings
        name: "Portionen"
```

---

## 🔧 API-Datenformat

### Minimale Anforderungen

**Nur Video:**
```json
{
  "date": "2026-01-29T00:00:00.000Z",
  "type": "LUNCH",
  "recipe": {
    "name": "Spaghetti Carbonara",
    "video": "https://www.youtube.com/watch?v=ABC123"
  }
}
```

**Video + Thumbnail:**
```json
{
  "date": "2026-01-29T00:00:00.000Z",
  "type": "LUNCH",
  "recipe": {
    "name": "Spaghetti Carbonara",
    "video": "https://www.youtube.com/watch?v=ABC123",
    "videoThumbnail": "https://example.com/thumb.jpg"
  }
}
```

**Vollständig (Bild + Video):**
```json
{
  "date": "2026-01-29T00:00:00.000Z",
  "type": "LUNCH",
  "recipe": {
    "name": "Spaghetti Carbonara",
    "image": "https://example.com/carbonara.jpg",
    "video": "https://www.youtube.com/watch?v=ABC123",
    "videoThumbnail": "https://example.com/video-thumb.jpg",
    "description": "Klassisches italienisches Pasta-Gericht",
    "cookingTime": 30,
    "servings": 4
  }
}
```

### Unterstützte Feldnamen

**Für Videos:**
- `video` (empfohlen)
- `videoUrl`
- `video_url`
- `youtubeUrl`
- `youtube_url`

**Für Video-Thumbnails:**
- `videoThumbnail` (empfohlen)
- `video_thumbnail`

Wenn kein Thumbnail angegeben ist und die URL YouTube ist, wird automatisch das YouTube-Thumbnail verwendet.

---

## 🎨 Styling-Tipps

### Play-Button Overlay

Mit **card-mod** kannst du ein Play-Icon über dem Thumbnail anzeigen:

```yaml
type: picture-entity
entity: sensor.norish_mittagessen
card_mod:
  style: |
    ha-card {
      position: relative;
    }
    ha-card::after {
      content: "▶";
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 60px;
      color: white;
      text-shadow: 0 0 10px rgba(0,0,0,0.5);
      pointer-events: none;
    }
```

---

## 🚀 Erweiterte Funktionen

### Template Sensor für Video-Status

```yaml
template:
  - sensor:
      - name: "Mittagessen Video Status"
        state: >-
          {% if state_attr('sensor.norish_mittagessen', 'has_video') %}
            Video verfügbar
          {% else %}
            Kein Video
          {% endif %}
        attributes:
          video_url: >-
            {{ state_attr('sensor.norish_mittagessen', 'video_url') }}
          video_type: >-
            {{ state_attr('sensor.norish_mittagessen', 'video_type') }}
```

### Automation: Benachrichtigung mit Video

```yaml
automation:
  - alias: "Mittags-Video Erinnerung"
    trigger:
      - platform: time
        at: "11:00:00"
    condition:
      - condition: template
        value_template: >-
          {{ state_attr('sensor.norish_mittagessen', 'has_video') }}
    action:
      - service: notify.mobile_app
        data:
          title: "🍽️ Mittagessen"
          message: >-
            Heute: {{ states('sensor.norish_mittagessen') }}
          data:
            url: >-
              {{ state_attr('sensor.norish_mittagessen', 'video_url') }}
            image: >-
              {{ state_attr('sensor.norish_mittagessen', 'video_thumbnail') }}
```

---

## 📱 Mobile App

### Action Button für Video

```yaml
type: entities
entities:
  - entity: sensor.norish_mittagessen
  - type: button
    name: "📺 Video ansehen"
    tap_action:
      action: url
      url_path: >-
        {{ state_attr('sensor.norish_mittagessen', 'video_url') }}
```

---

## 🔍 Troubleshooting

### Video wird nicht erkannt

1. **Prüfe Sensor-Attribute:**
   ```yaml
   Entwicklertools → Zustände → sensor.norish_mittagessen
   ```
   Sollte `video_url` Attribut haben

2. **Debug-Logging:**
   ```yaml
   logger:
     logs:
       custom_components.norish.sensor: debug
   ```

3. **Unterstützte Feldnamen prüfen:**
   - API sollte `video`, `videoUrl` oder `video_url` liefern

### YouTube-Video lädt nicht

1. **Embed-URL prüfen:**
   Sollte sein: `https://www.youtube.com/embed/VIDEO_ID`

2. **Cookies akzeptieren:**
   Manche Browser blockieren YouTube-Embeds ohne Cookie-Consent

3. **Alternative nutzen:**
   Verwende tap_action mit direktem Link statt Embed

### Vimeo-Video

Vimeo erfordert oft zusätzliche Parameter:
```
https://player.vimeo.com/video/VIDEO_ID?autoplay=0
```

---

## 🎯 Best Practices

### 1. Priorisierung
- Nutze Bilder für `entity_picture` (bessere Performance)
- Video-Thumbnail als Fallback
- Video-URL in Attributen für tap_action

### 2. Performance
- Videos nicht auto-play im Dashboard
- Nutze Thumbnails statt Embeds wo möglich
- Lazy-Loading für eingebettete Videos

### 3. Benutzererfahrung
- Zeige Play-Icon Overlay für Videos
- Öffne Videos in neuem Tab/Fenster
- Biete beide an: Embed + Link

---

## 📦 Benötigte Custom Components

Für die besten Ergebnisse:

1. **webpage-card** - Für Video-Embeds
   ```
   HACS → Frontend → Suche "Webpage Card"
   ```

2. **button-card** - Für erweiterte Buttons
   ```
   HACS → Frontend → Suche "Button Card"
   ```

3. **card-mod** - Für Custom Styling
   ```
   HACS → Frontend → Suche "Card Mod"
   ```

Alle optional, aber empfohlen!

---

## 🆕 Was ist neu?

### Version 1.1.0

- ✅ Video-URL Unterstützung
- ✅ Automatische YouTube-Erkennung
- ✅ Automatische Thumbnail-Extraktion
- ✅ Vimeo-Support
- ✅ Video-Type Detection
- ✅ Neue Sensor-Attribute: `has_video`, `video_type`, `youtube_id`
- ✅ Dashboard-Beispiele für Videos

---

## 💡 Beispiel-Workflows

### Rezept mit Video kochen

1. **Morgens:** Dashboard zeigt Mittagessen mit Video-Thumbnail
2. **Klick:** Öffnet YouTube-Video in App
3. **Kochen:** Video auf Tablet/Phone während dem Kochen
4. **Fertig:** Rezept in Norish als "gekocht" markieren

### Video-Playlist erstellen

```yaml
# Template für alle heutigen Videos
{% set videos = namespace(list=[]) %}
{% for meal in ['breakfast', 'lunch', 'dinner', 'snack'] %}
  {% set sensor = 'sensor.norish_' ~ meal %}
  {% if state_attr(sensor, 'video_url') %}
    {% set videos.list = videos.list + [state_attr(sensor, 'video_url')] %}
  {% endif %}
{% endfor %}

Videos heute: {{ videos.list | join(', ') }}
```

---

**Viel Spaß mit Video-Rezepten! 🎬👨‍🍳**
