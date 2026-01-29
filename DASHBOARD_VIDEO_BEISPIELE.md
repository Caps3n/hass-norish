# Dashboard-Beispiele mit Video-Unterstützung

## 🎥 Videos in Home Assistant anzeigen

Norish unterstützt jetzt sowohl Bilder als auch Videos für Rezepte!

---

## Option 1: Conditional Card (Bild ODER Video)

Zeigt automatisch das richtige Medium an:

```yaml
type: vertical-stack
cards:
  # Zeige Video wenn vorhanden
  - type: conditional
    conditions:
      - condition: state
        entity: sensor.norish_mittagessen
        attribute: media_type
        state: "video"
    card:
      type: custom:video-card
      entity: sensor.norish_mittagessen
      url: "{{ state_attr('sensor.norish_mittagessen', 'video_url') }}"
      poster: "{{ state_attr('sensor.norish_mittagessen', 'video_thumbnail') }}"
      autoplay: true
      muted: true
      loop: true
  
  # Zeige Bild wenn kein Video
  - type: conditional
    conditions:
      - condition: state
        entity: sensor.norish_mittagessen
        attribute: media_type
        state: "image"
    card:
      type: picture-entity
      entity: sensor.norish_mittagessen
      show_name: true
      show_state: true
  
  # Details
  - type: entities
    entities:
      - sensor.norish_mittagessen
```

---

## Option 2: HTML5 Video (ohne Custom Card)

Nutzt Standard-Markdown Card:

```yaml
type: markdown
content: |
  ## 🍽️ {{ states('sensor.norish_mittagessen') }}
  
  {% if state_attr('sensor.norish_mittagessen', 'video_url') %}
  <video 
    width="100%" 
    autoplay 
    muted 
    loop 
    playsinline
    poster="{{ state_attr('sensor.norish_mittagessen', 'video_thumbnail') }}"
  >
    <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
  </video>
  {% elif state_attr('sensor.norish_mittagessen', 'image') %}
  ![Rezept]({{ state_attr('sensor.norish_mittagessen', 'image') }})
  {% else %}
  Kein Bild oder Video verfügbar
  {% endif %}
  
  {% if state_attr('sensor.norish_mittagessen', 'description') %}
  {{ state_attr('sensor.norish_mittagessen', 'description') }}
  {% endif %}
```

---

## Option 3: Media Player Entity (NEU!)

Nutzt die neue Media Player Integration:

```yaml
type: media-control
entity: media_player.norish_mittagessen_video
```

**Oder volle Kontrolle:**

```yaml
type: vertical-stack
cards:
  - type: media-control
    entity: media_player.norish_mittagessen_video
  
  - type: entities
    entities:
      - entity: media_player.norish_mittagessen_video
        type: attribute
        attribute: recipe_name
        name: Rezept
      - entity: media_player.norish_mittagessen_video
        type: attribute
        attribute: cooking_time
        name: Zubereitungszeit
      - entity: media_player.norish_mittagessen_video
        type: attribute
        attribute: servings
        name: Portionen
```

---

## Option 4: Picture Elements mit Video

Interaktive Überlagerung:

```yaml
type: picture-elements
image: "{{ state_attr('sensor.norish_mittagessen', 'video_thumbnail') or state_attr('sensor.norish_mittagessen', 'image') }}"
elements:
  - type: state-label
    entity: sensor.norish_mittagessen
    style:
      top: 5%
      left: 50%
      color: white
      background: rgba(0,0,0,0.6)
      padding: 10px
      border-radius: 5px
  
  # Play-Button wenn Video vorhanden
  - type: conditional
    conditions:
      - entity: sensor.norish_mittagessen
        attribute: media_type
        state: "video"
    elements:
      - type: icon
        icon: mdi:play-circle
        style:
          top: 50%
          left: 50%
          font-size: 80px
          color: white
          opacity: 0.8
        tap_action:
          action: navigate
          navigation_path: "#video-popup"
```

---

## Option 5: Iframe Card (für externe Videos)

Falls Videos auf externem Server liegen:

```yaml
type: iframe
url: "{{ state_attr('sensor.norish_mittagessen', 'video_url') }}"
aspect_ratio: 16:9
```

---

## Option 6: Grid mit allen Mahlzeiten (Video + Bild)

```yaml
type: grid
columns: 2
square: false
cards:
  # Frühstück
  - type: vertical-stack
    cards:
      - type: markdown
        content: |
          {% if state_attr('sensor.norish_fruhstuck', 'video_url') %}
          <video width="100%" autoplay muted loop playsinline>
            <source src="{{ state_attr('sensor.norish_fruhstuck', 'video_url') }}" type="video/mp4">
          </video>
          {% elif state_attr('sensor.norish_fruhstuck', 'image') %}
          ![]({{ state_attr('sensor.norish_fruhstuck', 'image') }})
          {% endif %}
      - type: entity
        entity: sensor.norish_fruhstuck
  
  # Mittagessen
  - type: vertical-stack
    cards:
      - type: markdown
        content: |
          {% if state_attr('sensor.norish_mittagessen', 'video_url') %}
          <video width="100%" autoplay muted loop playsinline>
            <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
          </video>
          {% elif state_attr('sensor.norish_mittagessen', 'image') %}
          ![]({{ state_attr('sensor.norish_mittagessen', 'image') }})
          {% endif %}
      - type: entity
        entity: sensor.norish_mittagessen
  
  # Abendessen
  - type: vertical-stack
    cards:
      - type: markdown
        content: |
          {% if state_attr('sensor.norish_abendessen', 'video_url') %}
          <video width="100%" autoplay muted loop playsinline>
            <source src="{{ state_attr('sensor.norish_abendessen', 'video_url') }}" type="video/mp4">
          </video>
          {% elif state_attr('sensor.norish_abendessen', 'image') %}
          ![]({{ state_attr('sensor.norish_abendessen', 'image') }})
          {% endif %}
      - type: entity
        entity: sensor.norish_abendessen
  
  # Snack
  - type: vertical-stack
    cards:
      - type: markdown
        content: |
          {% if state_attr('sensor.norish_snack', 'video_url') %}
          <video width="100%" autoplay muted loop playsinline>
            <source src="{{ state_attr('sensor.norish_snack', 'video_url') }}" type="video/mp4">
          </video>
          {% elif state_attr('sensor.norish_snack', 'image') %}
          ![]({{ state_attr('sensor.norish_snack', 'image') }})
          {% endif %}
      - type: entity
        entity: sensor.norish_snack
```

---

## Option 7: Custom Video Card (wenn installiert)

Falls du die [video-card](https://github.com/custom-cards/video-card) installiert hast:

```yaml
type: custom:video-card
entity: sensor.norish_mittagessen
url: "{{ state_attr('sensor.norish_mittagessen', 'video_url') }}"
poster: "{{ state_attr('sensor.norish_mittagessen', 'video_thumbnail') }}"
title: "{{ states('sensor.norish_mittagessen') }}"
autoplay: true
muted: true
loop: true
preload: metadata
controls: true
```

---

## Option 8: Vollständiges Video-Dashboard

```yaml
type: vertical-stack
cards:
  # Header
  - type: markdown
    content: |
      # 🎥 Rezept-Videos
      {{ now().strftime('%A, %d. %B %Y') }}
  
  # Video-Player
  - type: conditional
    conditions:
      - entity: sensor.norish_mittagessen
        attribute: media_type
        state: "video"
    card:
      type: markdown
      content: |
        ## {{ states('sensor.norish_mittagessen') }}
        
        <video 
          width="100%" 
          controls 
          autoplay 
          muted 
          loop 
          playsinline
          poster="{{ state_attr('sensor.norish_mittagessen', 'video_thumbnail') }}"
        >
          <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
        </video>
        
        {% if state_attr('sensor.norish_mittagessen', 'description') %}
        ### Beschreibung
        {{ state_attr('sensor.norish_mittagessen', 'description') }}
        {% endif %}
        
        {% if state_attr('sensor.norish_mittagessen', 'cooking_time') %}
        ⏱️ **Zubereitungszeit:** {{ state_attr('sensor.norish_mittagessen', 'cooking_time') }} Min.
        {% endif %}
        
        {% if state_attr('sensor.norish_mittagessen', 'servings') %}
        👥 **Portionen:** {{ state_attr('sensor.norish_mittagessen', 'servings') }}
        {% endif %}
  
  # Fallback wenn nur Bild
  - type: conditional
    conditions:
      - entity: sensor.norish_mittagessen
        attribute: media_type
        state: "image"
    card:
      type: picture-entity
      entity: sensor.norish_mittagessen
      show_name: true
      show_state: true
  
  # Weitere Mahlzeiten als Liste
  - type: entities
    title: Weitere Mahlzeiten
    entities:
      - sensor.norish_fruhstuck
      - sensor.norish_abendessen
      - sensor.norish_snack
```

---

## 🎬 Video-Eigenschaften

Die Videos werden standardmäßig so abgespielt:
- ✅ **Autoplay**: Startet automatisch
- ✅ **Muted**: Ohne Ton (wie gewünscht)
- ✅ **Loop**: Wiederholt sich endlos
- ✅ **Playsinline**: Spielt inline auf Mobile (kein Fullscreen)

### HTML5 Video Attribute

```html
<video 
  width="100%"           <!-- Volle Breite -->
  autoplay               <!-- Auto-Start -->
  muted                  <!-- Ohne Ton -->
  loop                   <!-- Endlos-Schleife -->
  playsinline            <!-- Inline auf Mobile -->
  controls               <!-- Zeige Controls (optional) -->
  poster="thumbnail.jpg" <!-- Vorschaubild -->
>
  <source src="video.mp4" type="video/mp4">
</video>
```

---

## 📱 Mobile Optimierung

Für beste Mobile-Erfahrung:

```yaml
type: markdown
content: |
  <video 
    width="100%" 
    autoplay 
    muted 
    loop 
    playsinline
    style="border-radius: 15px; max-height: 400px; object-fit: cover;"
    poster="{{ state_attr('sensor.norish_mittagessen', 'video_thumbnail') }}"
  >
    <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
  </video>
```

---

## 🔍 Template für Media-Typ-Erkennung

Nutze dies in Templates:

```yaml
# Prüfe ob Video vorhanden
{% if state_attr('sensor.norish_mittagessen', 'media_type') == 'video' %}
  Es gibt ein Video!
{% elif state_attr('sensor.norish_mittagessen', 'media_type') == 'image' %}
  Es gibt nur ein Bild.
{% else %}
  Keine Medien vorhanden.
{% endif %}

# Direkter Zugriff auf Video-URL
{{ state_attr('sensor.norish_mittagessen', 'video_url') }}

# Video-Thumbnail
{{ state_attr('sensor.norish_mittagessen', 'video_thumbnail') }}

# Alle Videos des Tages
{{ state_attr('sensor.norish_mahlzeiten_heute', 'videos') }}
```

---

## 🎯 Empfohlene Konfiguration

**Für beste Ergebnisse:**

1. **Option 2 (HTML5 Video in Markdown)** - Funktioniert ohne Custom Cards
2. **Option 8 (Vollständiges Dashboard)** - Professionell mit Fallbacks
3. **Option 3 (Media Player)** - Wenn du die neue Entity nutzen möchtest

**Starter-Template:**

```yaml
type: markdown
content: |
  {% set meal = states.sensor.norish_mittagessen %}
  
  # 🍽️ {{ meal.state }}
  
  {% if meal.attributes.video_url %}
  <video width="100%" autoplay muted loop playsinline controls>
    <source src="{{ meal.attributes.video_url }}" type="video/mp4">
  </video>
  {% elif meal.attributes.image %}
  ![Rezept]({{ meal.attributes.image }})
  {% endif %}
  
  {{ meal.attributes.description or '' }}
```

---

## ⚙️ Unterstützte Video-Formate

- MP4 (empfohlen)
- WebM
- OGG

**API-Feldnamen die erkannt werden:**
- `video`
- `videoUrl`
- `video_url`
- `mp4`
- `media`

**Thumbnail-Feldnamen:**
- `videoThumbnail`
- `video_thumbnail`
- `poster`

---

Viel Spaß mit den Video-Rezepten! 🎥🍳
