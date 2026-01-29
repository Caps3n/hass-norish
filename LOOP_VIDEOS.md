# 🎬 Norish Loop-Videos in Home Assistant

## Übersicht

So werden Videos genau wie in Norish angezeigt:
- ✅ Automatisch abspielen
- ✅ Stumm (ohne Ton)
- ✅ Dauerschleife
- ✅ Vollbild-Ansicht
- ✅ Kein Player-Interface

---

## 🎯 Lösung 1: Markdown Card (Empfohlen)

### Einfache Version

```yaml
type: markdown
content: |
  <video 
    autoplay 
    loop 
    muted 
    playsinline 
    style="width: 100%; height: auto; object-fit: cover; border-radius: 8px;">
    <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
  </video>
```

### Vollbild-Version

```yaml
type: markdown
content: |
  <video 
    autoplay 
    loop 
    muted 
    playsinline 
    style="width: 100%; height: 400px; object-fit: cover; border-radius: 8px;">
    <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
  </video>
```

### Mit Rezept-Name Overlay

```yaml
type: markdown
content: |
  <div style="position: relative; width: 100%; height: 400px; border-radius: 8px; overflow: hidden;">
    <video 
      autoplay 
      loop 
      muted 
      playsinline 
      style="width: 100%; height: 100%; object-fit: cover;">
      <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
    </video>
    <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); 
                padding: 20px; color: white;">
      <h2 style="margin: 0; font-size: 24px;">{{ states('sensor.norish_mittagessen') }}</h2>
      <p style="margin: 5px 0 0 0; opacity: 0.9;">
        ⏱️ {{ state_attr('sensor.norish_mittagessen', 'cooking_time') }} Min. | 
        👥 {{ state_attr('sensor.norish_mittagessen', 'servings') }} Portionen
      </p>
    </div>
  </div>
```

---

## 🎨 Lösung 2: Webpage Card (Für komplexe Layouts)

### Installation

```
HACS → Frontend → "Webpage Card"
```

### Dashboard-Code

```yaml
type: custom:webpage-card
url: !include norish_video_player.html
aspect_ratio: 56%
```

**Datei: `www/norish_video_player.html`**

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body {
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #000;
    }
    video {
      width: 100%;
      height: 100vh;
      object-fit: cover;
    }
    .overlay {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
      padding: 20px;
      color: white;
    }
  </style>
</head>
<body>
  <video autoplay loop muted playsinline id="recipeVideo">
    <source src="" type="video/mp4">
  </video>
  <div class="overlay">
    <h2 id="recipeName">Lädt...</h2>
  </div>
  
  <script>
    // Hole Daten von Home Assistant
    const videoUrl = window.parent.hass?.states['sensor.norish_mittagessen']?.attributes?.video_url;
    const recipeName = window.parent.hass?.states['sensor.norish_mittagessen']?.state;
    
    if (videoUrl) {
      document.getElementById('recipeVideo').src = videoUrl;
    }
    if (recipeName) {
      document.getElementById('recipeName').textContent = recipeName;
    }
  </script>
</body>
</html>
```

---

## 🚀 Lösung 3: Picture Elements Card

### Mit Video-Hintergrund

```yaml
type: picture-elements
image: >-
  {{ state_attr('sensor.norish_mittagessen', 'video_thumbnail') or 
     state_attr('sensor.norish_mittagessen', 'image') }}
elements:
  - type: custom:hui-element
    card_type: markdown
    content: |
      <video 
        autoplay 
        loop 
        muted 
        playsinline 
        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; z-index: -1;">
        <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
      </video>
    style:
      top: 0
      left: 0
      width: 100%
      height: 100%
  
  - type: state-label
    entity: sensor.norish_mittagessen
    style:
      bottom: 20px
      left: 20px
      color: white
      font-size: 24px
      text-shadow: 0 2px 4px rgba(0,0,0,0.8)
```

---

## 📱 Lösung 4: Vollständiges Dashboard

### Norish-Style Video-Dashboard

```yaml
type: vertical-stack
cards:
  # Video-Player
  - type: markdown
    content: |
      <div style="position: relative; width: 100%; height: 500px; 
                  border-radius: 12px; overflow: hidden; background: #000;">
        {% if state_attr('sensor.norish_mittagessen', 'video_url') %}
        <video 
          autoplay 
          loop 
          muted 
          playsinline 
          style="width: 100%; height: 100%; object-fit: cover;">
          <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
        </video>
        {% else %}
        <img src="{{ state_attr('sensor.norish_mittagessen', 'image') }}" 
             style="width: 100%; height: 100%; object-fit: cover;">
        {% endif %}
        
        <!-- Gradient Overlay -->
        <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                    background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); 
                    padding: 30px 20px 20px 20px;">
          <h1 style="margin: 0; color: white; font-size: 28px; font-weight: bold;">
            {{ states('sensor.norish_mittagessen') }}
          </h1>
          <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
            ⏱️ {{ state_attr('sensor.norish_mittagessen', 'cooking_time') }} Minuten
            &nbsp;&nbsp;|&nbsp;&nbsp;
            👥 {{ state_attr('sensor.norish_mittagessen', 'servings') }} Portionen
          </p>
        </div>
        
        <!-- Video-Indikator -->
        {% if state_attr('sensor.norish_mittagessen', 'has_video') %}
        <div style="position: absolute; top: 15px; right: 15px; 
                    background: rgba(0,0,0,0.6); border-radius: 20px; 
                    padding: 8px 12px; color: white; font-size: 14px;">
          🎬 Video
        </div>
        {% endif %}
      </div>
  
  # Rezept-Details
  - type: entities
    title: Details
    entities:
      - entity: sensor.norish_mittagessen
        name: Gericht
      - type: attribute
        entity: sensor.norish_mittagessen
        attribute: description
        name: Beschreibung
      - type: attribute
        entity: sensor.norish_mittagessen
        attribute: prep_time
        name: Vorbereitungszeit
        suffix: " Min."
```

---

## 🎯 Lösung 5: Grid mit allen Mahlzeiten

### Video-Grid

```yaml
type: grid
columns: 2
square: false
cards:
  # Frühstück
  - type: markdown
    content: |
      <div style="position: relative; height: 250px; border-radius: 8px; overflow: hidden;">
        <video autoplay loop muted playsinline 
               style="width: 100%; height: 100%; object-fit: cover;">
          <source src="{{ state_attr('sensor.norish_fruhstuck', 'video_url') }}" type="video/mp4">
        </video>
        <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                    background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); 
                    padding: 15px; color: white;">
          <h3 style="margin: 0;">🌅 Frühstück</h3>
          <p style="margin: 5px 0 0 0; font-size: 14px;">
            {{ states('sensor.norish_fruhstuck') }}
          </p>
        </div>
      </div>
  
  # Mittagessen
  - type: markdown
    content: |
      <div style="position: relative; height: 250px; border-radius: 8px; overflow: hidden;">
        <video autoplay loop muted playsinline 
               style="width: 100%; height: 100%; object-fit: cover;">
          <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
        </video>
        <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                    background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); 
                    padding: 15px; color: white;">
          <h3 style="margin: 0;">☀️ Mittagessen</h3>
          <p style="margin: 5px 0 0 0; font-size: 14px;">
            {{ states('sensor.norish_mittagessen') }}
          </p>
        </div>
      </div>
  
  # Abendessen
  - type: markdown
    content: |
      <div style="position: relative; height: 250px; border-radius: 8px; overflow: hidden;">
        <video autoplay loop muted playsinline 
               style="width: 100%; height: 100%; object-fit: cover;">
          <source src="{{ state_attr('sensor.norish_abendessen', 'video_url') }}" type="video/mp4">
        </video>
        <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                    background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); 
                    padding: 15px; color: white;">
          <h3 style="margin: 0;">🌙 Abendessen</h3>
          <p style="margin: 5px 0 0 0; font-size: 14px;">
            {{ states('sensor.norish_abendessen') }}
          </p>
        </div>
      </div>
  
  # Snack
  - type: markdown
    content: |
      <div style="position: relative; height: 250px; border-radius: 8px; overflow: hidden;">
        <video autoplay loop muted playsinline 
               style="width: 100%; height: 100%; object-fit: cover;">
          <source src="{{ state_attr('sensor.norish_snack', 'video_url') }}" type="video/mp4">
        </video>
        <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                    background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); 
                    padding: 15px; color: white;">
          <h3 style="margin: 0;">🍪 Snack</h3>
          <p style="margin: 5px 0 0 0; font-size: 14px;">
            {{ states('sensor.norish_snack') }}
          </p>
        </div>
      </div>
```

---

## 🔧 Relative URLs handhaben

### Problem: Relative Video-URLs

Wenn die API relative URLs liefert:
```
/recipes/ff8d4877.../video-1768689166978.mp4
```

### Lösung: Vollständige URL im Template

```yaml
type: markdown
content: |
  {% set video_path = state_attr('sensor.norish_mittagessen', 'video_url') %}
  {% set base_url = 'https://norish.deinedomain.com' %}
  {% if video_path and video_path.startswith('/') %}
    {% set full_url = base_url + video_path %}
  {% else %}
    {% set full_url = video_path %}
  {% endif %}
  
  <video autoplay loop muted playsinline 
         style="width: 100%; height: 400px; object-fit: cover;">
    <source src="{{ full_url }}" type="video/mp4">
  </video>
```

---

## 📱 Mobile-Optimiert

### Responsive Video-Card

```yaml
type: markdown
content: |
  <div style="position: relative; width: 100%; 
              padding-top: 56.25%; /* 16:9 Aspect Ratio */ 
              border-radius: 12px; overflow: hidden;">
    <video 
      autoplay 
      loop 
      muted 
      playsinline 
      style="position: absolute; top: 0; left: 0; 
             width: 100%; height: 100%; object-fit: cover;">
      <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
    </video>
  </div>
```

---

## ⚙️ Video-Attribute

### HTML5 Video-Tag Attribute erklärt

```html
<video 
  autoplay       <!-- Startet automatisch -->
  loop           <!-- Dauerschleife -->
  muted          <!-- Stumm -->
  playsinline    <!-- Spielt inline (wichtig für Mobile) -->
  preload="auto" <!-- Lädt Video im Voraus -->
  style="...">   <!-- CSS-Styling -->
```

### Object-Fit Optionen

```css
object-fit: cover;    /* Füllt Container, schneidet ab */
object-fit: contain;  /* Zeigt alles, schwarze Balken */
object-fit: fill;     /* Streckt Video -->
object-fit: none;     /* Original-Größe -->
```

---

## 🎨 Styling-Optionen

### Mit Schatten

```css
style="
  width: 100%; 
  height: 400px; 
  object-fit: cover; 
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
"
```

### Mit Border

```css
style="
  width: 100%; 
  height: 400px; 
  object-fit: cover; 
  border: 3px solid #333;
  border-radius: 8px;
"
```

### Abgerundete Ecken (wie Norish)

```css
style="
  width: 100%; 
  height: 400px; 
  object-fit: cover; 
  border-radius: 12px;
"
```

---

## 🚨 Troubleshooting

### Video lädt nicht

1. **Prüfe URL:**
   ```yaml
   Entwicklertools → Zustände → sensor.norish_mittagessen
   ```
   Attribut `video_url` sollte vorhanden sein

2. **Relative URL?**
   - Nutze Template mit Base-URL (siehe oben)

3. **CORS-Problem?**
   - Server muss CORS-Header senden
   - Teste URL direkt im Browser

### Video spielt nicht automatisch

**Lösung:** Füge `muted` hinzu
```html
<video autoplay loop muted playsinline>
```

Browser blockieren Autoplay ohne `muted`!

### Video zu groß/klein

**Lösung:** Passe `height` an
```css
style="height: 300px;"  <!-- Kleiner -->
style="height: 600px;"  <!-- Größer -->
```

### Performance-Probleme

**Lösung:** Preload steuern
```html
<video preload="metadata">  <!-- Nur Metadaten -->
<video preload="none">      <!-- Nichts vorladen -->
<video preload="auto">      <!-- Alles vorladen (Standard) -->
```

---

## 💡 Best Practices

### 1. Fallback für fehlende Videos

```yaml
type: markdown
content: |
  {% set video = state_attr('sensor.norish_mittagessen', 'video_url') %}
  {% set image = state_attr('sensor.norish_mittagessen', 'image') %}
  
  {% if video %}
    <video autoplay loop muted playsinline 
           style="width: 100%; height: 400px; object-fit: cover;">
      <source src="{{ video }}" type="video/mp4">
    </video>
  {% elif image %}
    <img src="{{ image }}" 
         style="width: 100%; height: 400px; object-fit: cover;">
  {% else %}
    <div style="width: 100%; height: 400px; background: #ccc; 
                display: flex; align-items: center; justify-content: center;">
      <p>Kein Medien verfügbar</p>
    </div>
  {% endif %}
```

### 2. Loading-Indikator

```yaml
type: markdown
content: |
  <div style="position: relative;">
    <video autoplay loop muted playsinline 
           onloadstart="this.nextElementSibling.style.display='flex'"
           oncanplay="this.nextElementSibling.style.display='none'"
           style="width: 100%; height: 400px; object-fit: cover;">
      <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
    </video>
    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 400px;
                background: rgba(0,0,0,0.8); display: none; 
                align-items: center; justify-content: center; color: white;">
      Lädt...
    </div>
  </div>
```

### 3. Tap to Pause

```yaml
type: markdown
content: |
  <video 
    id="recipeVideo"
    autoplay 
    loop 
    muted 
    playsinline 
    onclick="this.paused ? this.play() : this.pause()"
    style="width: 100%; height: 400px; object-fit: cover; cursor: pointer;">
    <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
  </video>
```

---

## 🎯 Empfehlung

**Für die meisten Fälle:** Nutze **Lösung 1 (Markdown Card)**
- ✅ Einfach
- ✅ Keine Custom Components nötig
- ✅ Funktioniert überall
- ✅ Genau wie Norish

**Für komplexe Layouts:** Nutze **Lösung 4 (Vollständiges Dashboard)**
- ✅ Professionell
- ✅ Alle Features
- ✅ Overlay mit Infos
- ✅ Responsive

---

**Viel Spaß mit Loop-Videos! 🎬**
