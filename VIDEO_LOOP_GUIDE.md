# 🔄 Norish Videos mit Auto-Loop (wie in Norish App)

## Übersicht

Videos werden genau wie in der Norish-App angezeigt:
- ✅ **Automatisch abgespielt** (autoplay)
- ✅ **In Endlosschleife** (loop)
- ✅ **Stumm** (muted)
- ✅ **Kein Ton-Button** (playsinline)

---

## 🎬 Media Player Entities

Die Integration erstellt automatisch Media Player für jede Mahlzeit:

- `media_player.norish_fruhstuck_video`
- `media_player.norish_mittagessen_video`
- `media_player.norish_abendessen_video`
- `media_player.norish_snack_video`

### Status:
- **PLAYING** - Wenn Video vorhanden
- **OFF** - Wenn kein Video

---

## 📺 Dashboard-Karten

### Option 1: Iframe Card (Empfohlen - Genau wie Norish App)

```yaml
type: custom:html-card
content: |
  <video 
    loop 
    autoplay 
    muted 
    playsinline 
    style="width: 100%; height: auto; object-fit: cover;"
    src="{{ state_attr('media_player.norish_mittagessen_video', 'video_source') }}">
  </video>
```

**Benötigt:** [html-card](https://github.com/PiotrMachowski/lovelace-html-card) via HACS

---

### Option 2: Webpage Card mit HTML

```yaml
type: custom:webpage-card
url: >-
  data:text/html;charset=utf-8,
  <html>
    <body style="margin:0; overflow:hidden; background:#000;">
      <video 
        loop 
        autoplay 
        muted 
        playsinline 
        style="width:100vw; height:100vh; object-fit:cover;"
        src="{{ state_attr('media_player.norish_mittagessen_video', 'video_source') }}">
      </video>
    </body>
  </html>
aspect_ratio: 56%
```

**Benötigt:** [webpage-card](https://github.com/Sese-Schneider/ha-webview-card) via HACS

---

### Option 3: Picture Glance Card (Fallback ohne Custom Component)

```yaml
type: picture-glance
camera_image: media_player.norish_mittagessen_video
entities:
  - sensor.norish_mittagessen
title: Mittagessen
tap_action:
  action: more-info
```

**Hinweis:** Zeigt nur Thumbnail, kein Video

---

### Option 4: Vollbild Video-Dashboard (Norish-Style)

```yaml
type: vertical-stack
cards:
  # Video in voller Breite
  - type: custom:html-card
    content: |
      <style>
        .video-container {
          position: relative;
          width: 100%;
          padding-top: 56.25%; /* 16:9 Aspect Ratio */
          background: #000;
          overflow: hidden;
        }
        .video-container video {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      </style>
      <div class="video-container">
        <video 
          loop 
          autoplay 
          muted 
          playsinline
          src="{{ state_attr('media_player.norish_mittagessen_video', 'video_source') }}">
        </video>
      </div>
  
  # Rezept-Info unten
  - type: markdown
    content: |
      ## {{ state_attr('media_player.norish_mittagessen_video', 'media_title') }}
      
      **Zubereitungszeit:** {{ state_attr('sensor.norish_mittagessen', 'cooking_time') }} Min.
      **Portionen:** {{ state_attr('sensor.norish_mittagessen', 'servings') }}
```

---

## 🎨 Erweiterte Styling-Optionen

### Mit Overlay-Buttons

```yaml
type: custom:html-card
content: |
  <style>
    .video-wrapper {
      position: relative;
      width: 100%;
      height: 400px;
      overflow: hidden;
    }
    .video-wrapper video {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .recipe-title {
      position: absolute;
      bottom: 20px;
      left: 20px;
      color: white;
      font-size: 24px;
      font-weight: bold;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }
  </style>
  <div class="video-wrapper">
    <video 
      loop 
      autoplay 
      muted 
      playsinline
      src="{{ state_attr('media_player.norish_mittagessen_video', 'video_source') }}">
    </video>
    <div class="recipe-title">
      {{ state_attr('media_player.norish_mittagessen_video', 'media_title') }}
    </div>
  </div>
```

---

### Mobile-optimiert

```yaml
type: custom:html-card
content: |
  <video 
    loop 
    autoplay 
    muted 
    playsinline 
    style="
      width: 100%; 
      max-height: 300px; 
      object-fit: cover;
      border-radius: 12px;
    "
    src="{{ state_attr('media_player.norish_mittagessen_video', 'video_source') }}">
  </video>
```

---

## 📱 Conditional Card (Zeige nur wenn Video vorhanden)

```yaml
type: conditional
conditions:
  - entity: media_player.norish_mittagessen_video
    state: "playing"
card:
  type: custom:html-card
  content: |
    <video 
      loop 
      autoplay 
      muted 
      playsinline 
      style="width: 100%; border-radius: 8px;"
      src="{{ state_attr('media_player.norish_mittagessen_video', 'video_source') }}">
    </video>
```

---

## 🔧 Video-URLs

### Relative Pfade (wie in deinem Beispiel)

Wenn die API relative Pfade liefert:
```json
{
  "video": "/recipes/ff8d4877.../video-123.mp4"
}
```

Der Media Player kombiniert diese automatisch mit der Server-URL:
```
https://norish.deine-domain.com/recipes/ff8d4877.../video-123.mp4
```

**Attribut:** `video_source` enthält die vollständige URL

### Absolute URLs

Wenn die API vollständige URLs liefert:
```json
{
  "video": "https://norish.example.com/videos/recipe-123.mp4"
}
```

Werden direkt verwendet.

---

## 🎯 Grid mit mehreren Videos

```yaml
type: grid
columns: 2
square: false
cards:
  - type: custom:html-card
    content: |
      <div style="position: relative;">
        <video 
          loop autoplay muted playsinline 
          style="width:100%; border-radius:8px;"
          src="{{ state_attr('media_player.norish_fruhstuck_video', 'video_source') }}">
        </video>
        <div style="
          position: absolute;
          bottom: 10px;
          left: 10px;
          color: white;
          font-weight: bold;
          text-shadow: 1px 1px 2px black;
        ">Frühstück</div>
      </div>
  
  - type: custom:html-card
    content: |
      <div style="position: relative;">
        <video 
          loop autoplay muted playsinline 
          style="width:100%; border-radius:8px;"
          src="{{ state_attr('media_player.norish_mittagessen_video', 'video_source') }}">
        </video>
        <div style="
          position: absolute;
          bottom: 10px;
          left: 10px;
          color: white;
          font-weight: bold;
          text-shadow: 1px 1px 2px black;
        ">Mittagessen</div>
      </div>
  
  - type: custom:html-card
    content: |
      <div style="position: relative;">
        <video 
          loop autoplay muted playsinline 
          style="width:100%; border-radius:8px;"
          src="{{ state_attr('media_player.norish_abendessen_video', 'video_source') }}">
        </video>
        <div style="
          position: absolute;
          bottom: 10px;
          left: 10px;
          color: white;
          font-weight: bold;
          text-shadow: 1px 1px 2px black;
        ">Abendessen</div>
      </div>
  
  - type: custom:html-card
    content: |
      <div style="position: relative;">
        <video 
          loop autoplay muted playsinline 
          style="width:100%; border-radius:8px;"
          src="{{ state_attr('media_player.norish_snack_video', 'video_source') }}">
        </video>
        <div style="
          position: absolute;
          bottom: 10px;
          left: 10px;
          color: white;
          font-weight: bold;
          text-shadow: 1px 1px 2px black;
        ">Snack</div>
      </div>
```

---

## 📊 Attribute des Media Players

```yaml
media_player.norish_mittagessen_video:
  state: "playing"
  attributes:
    loop: true
    muted: true
    autoplay: true
    controls: true
    video_url: "/recipes/abc/video.mp4"
    video_source: "https://norish.example.com/recipes/abc/video.mp4"
    media_title: "Spaghetti Carbonara"
    media_content_type: "video"
```

---

## 🚀 Performance-Tipps

### 1. Lazy Loading

```yaml
type: conditional
conditions:
  - entity: sensor.norish_mittagessen
    state_not: "Kein Plan"
card:
  type: custom:html-card
  content: |
    <video 
      loop autoplay muted playsinline 
      loading="lazy"
      src="...">
    </video>
```

### 2. Mehrere Videos

Nutze `swipe-card` für bessere Performance:

```yaml
type: custom:swipe-card
parameters:
  spaceBetween: 8
cards:
  - type: custom:html-card
    content: |
      <video loop autoplay muted playsinline src="..."></video>
  
  - type: custom:html-card
    content: |
      <video loop autoplay muted playsinline src="..."></video>
```

### 3. Preload

```yaml
<video 
  loop autoplay muted playsinline 
  preload="metadata"
  src="...">
</video>
```

---

## 🔍 Troubleshooting

### Video lädt nicht

1. **Prüfe URL:**
   ```yaml
   Entwicklertools → Zustände → media_player.norish_mittagessen_video
   ```
   Schaue nach `video_source` Attribut

2. **Prüfe CORS:**
   Norish-Server muss CORS-Header senden:
   ```
   Access-Control-Allow-Origin: *
   ```

3. **Prüfe Netzwerk:**
   - Ist Home Assistant mit Norish-Server verbunden?
   - Firewall-Regeln korrekt?

### Video spielt nicht automatisch ab

**Browser-Einschränkungen:**
- Chrome/Safari blockieren autoplay ohne User-Interaktion
- Lösung: `muted` muss gesetzt sein

**Mobil:**
- iOS Safari: Nutze `playsinline`
- Android: Sollte funktionieren

### Video-Format nicht unterstützt

**Unterstützte Formate:**
- MP4 (H.264) - **Beste Kompatibilität**
- WebM (VP8/VP9)
- OGG (Theora)

**Empfehlung:** Konvertiere Videos zu MP4 H.264

---

## 📦 Benötigte Custom Components

Für die beste Erfahrung:

1. **html-card** (Empfohlen)
   ```
   HACS → Frontend → "HTML Template card"
   ```

2. **webpage-card** (Alternative)
   ```
   HACS → Frontend → "Webpage Card"
   ```

3. **swipe-card** (Optional für Multiple Videos)
   ```
   HACS → Frontend → "Swipe Card"
   ```

---

## 🎬 Vergleich: Norish App vs Home Assistant

| Feature | Norish App | Home Assistant |
|---------|-----------|----------------|
| Auto-Play | ✅ | ✅ |
| Loop | ✅ | ✅ |
| Muted | ✅ | ✅ |
| Playsinline | ✅ | ✅ |
| Thumbnail | ✅ | ✅ |
| Controls | ❌ | ⚙️ Optional |
| Fullscreen | ❌ | ⚙️ Optional |

---

## 💡 Best Practice

```yaml
# Vollständiges Norish-Style Dashboard
type: vertical-stack
cards:
  # Video (genau wie in App)
  - type: conditional
    conditions:
      - entity: media_player.norish_mittagessen_video
        state: "playing"
    card:
      type: custom:html-card
      content: |
        <video 
          loop 
          autoplay 
          muted 
          playsinline 
          style="
            width: 100%; 
            height: auto; 
            display: block;
            object-fit: cover;
          "
          src="{{ state_attr('media_player.norish_mittagessen_video', 'video_source') }}">
        </video>
  
  # Fallback: Bild wenn kein Video
  - type: conditional
    conditions:
      - entity: media_player.norish_mittagessen_video
        state: "off"
    card:
      type: picture-entity
      entity: sensor.norish_mittagessen
  
  # Rezept-Details
  - type: entities
    entities:
      - entity: sensor.norish_mittagessen
      - type: attribute
        entity: sensor.norish_mittagessen
        attribute: cooking_time
        name: "Zeit"
      - type: attribute
        entity: sensor.norish_mittagessen
        attribute: servings
        name: "Portionen"
```

---

**Jetzt hast du Videos genau wie in der Norish App! 🎬**
