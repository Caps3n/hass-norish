# 📅 Norish Wochenplan mit Bildern & Videos

## Übersicht

Zeige den kompletten Wochenplan mit Bildern oder Videos für alle 7 Tage!

---

## 🎯 Lösung 1: Grid-Layout (Desktop)

### Basis-Wochenplan

```yaml
type: custom:layout-card
layout_type: custom:grid-layout
layout:
  grid-template-columns: repeat(7, 1fr)
  grid-gap: 10px
cards:
  # Montag
  - type: custom:state-switch
    entity: sensor.norish_wochenplan
    default: default
    states:
      default:
        type: vertical-stack
        cards:
          - type: markdown
            content: |
              <div style="text-align: center; padding: 10px; background: #1a1a1a; border-radius: 8px 8px 0 0;">
                <strong style="color: white;">Montag</strong>
              </div>
          - type: markdown
            content: |
              {% set monday = state_attr('sensor.norish_wochenplan', 'mo') %}
              {% if monday and monday.meals %}
                {% for meal in monday.meals %}
                  <div style="position: relative; margin-bottom: 10px; border-radius: 8px; overflow: hidden;">
                    {% if meal.video %}
                      <video autoplay loop muted playsinline 
                             style="width: 100%; height: 150px; object-fit: cover;">
                        <source src="{{ meal.video }}" type="video/mp4">
                      </video>
                    {% elif meal.image %}
                      <img src="{{ meal.image }}" 
                           style="width: 100%; height: 150px; object-fit: cover;">
                    {% endif %}
                    <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                                background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); 
                                padding: 10px; color: white; font-size: 11px;">
                      <strong>{{ meal.type }}</strong><br>
                      {{ meal.name }}
                    </div>
                  </div>
                {% endfor %}
              {% else %}
                <div style="padding: 20px; text-align: center; color: #666;">
                  Nicht geplant
                </div>
              {% endif %}
  
  # Dienstag bis Sonntag (gleiche Struktur, nur Tag ändern)
  # ... (Code für Di, Mi, Do, Fr, Sa, So)
```

---

## 🚀 Lösung 2: Horizontal Scroll (Mobile)

### Swipeable Wochenplan

**Installation: Swipe Card**
```
HACS → Frontend → "Swipe Card"
```

**Dashboard:**
```yaml
type: custom:swipe-card
parameters:
  spaceBetween: 8
  centeredSlides: false
  slidesPerView: auto
cards:
  # Tag 0 (Heute)
  - type: vertical-stack
    cards:
      - type: markdown
        content: |
          <div style="text-align: center; padding: 15px; background: #ff6b6b; color: white; border-radius: 12px 12px 0 0;">
            <h3 style="margin: 0;">HEUTE</h3>
            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">
              {{ now().strftime('%A, %d. %B') }}
            </p>
          </div>
      
      - type: markdown
        content: |
          <!-- Frühstück -->
          {% if state_attr('sensor.norish_fruhstuck', 'video_url') %}
            <div style="position: relative; margin: 10px; border-radius: 12px; overflow: hidden;">
              <video autoplay loop muted playsinline 
                     style="width: 100%; height: 200px; object-fit: cover;">
                <source src="{{ state_attr('sensor.norish_fruhstuck', 'video_url') }}" type="video/mp4">
              </video>
              <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                          background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); 
                          padding: 15px; color: white;">
                <span style="background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 4px; font-size: 11px;">
                  🌅 Frühstück
                </span>
                <h3 style="margin: 8px 0 0 0; font-size: 16px;">
                  {{ states('sensor.norish_fruhstuck') }}
                </h3>
              </div>
            </div>
          {% endif %}
          
          <!-- Mittagessen -->
          {% if state_attr('sensor.norish_mittagessen', 'video_url') or state_attr('sensor.norish_mittagessen', 'image') %}
            <div style="position: relative; margin: 10px; border-radius: 12px; overflow: hidden;">
              {% if state_attr('sensor.norish_mittagessen', 'video_url') %}
                <video autoplay loop muted playsinline 
                       style="width: 100%; height: 200px; object-fit: cover;">
                  <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
                </video>
              {% else %}
                <img src="{{ state_attr('sensor.norish_mittagessen', 'image') }}" 
                     style="width: 100%; height: 200px; object-fit: cover;">
              {% endif %}
              <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                          background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); 
                          padding: 15px; color: white;">
                <span style="background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 4px; font-size: 11px;">
                  ☀️ Mittagessen
                </span>
                <h3 style="margin: 8px 0 0 0; font-size: 16px;">
                  {{ states('sensor.norish_mittagessen') }}
                </h3>
              </div>
            </div>
          {% endif %}
          
          <!-- Abendessen -->
          {% if state_attr('sensor.norish_abendessen', 'video_url') or state_attr('sensor.norish_abendessen', 'image') %}
            <div style="position: relative; margin: 10px; border-radius: 12px; overflow: hidden;">
              {% if state_attr('sensor.norish_abendessen', 'video_url') %}
                <video autoplay loop muted playsinline 
                       style="width: 100%; height: 200px; object-fit: cover;">
                  <source src="{{ state_attr('sensor.norish_abendessen', 'video_url') }}" type="video/mp4">
                </video>
              {% else %}
                <img src="{{ state_attr('sensor.norish_abendessen', 'image') }}" 
                     style="width: 100%; height: 200px; object-fit: cover;">
              {% endif %}
              <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                          background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); 
                          padding: 15px; color: white;">
                <span style="background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 4px; font-size: 11px;">
                  🌙 Abendessen
                </span>
                <h3 style="margin: 8px 0 0 0; font-size: 16px;">
                  {{ states('sensor.norish_abendessen') }}
                </h3>
              </div>
            </div>
          {% endif %}
```

---

## 📱 Lösung 3: Kompakte Liste (Ohne Custom Components)

### Vertikale Wochenliste

```yaml
type: vertical-stack
cards:
  # Header
  - type: markdown
    content: |
      <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white;">
        <h1 style="margin: 0; font-size: 28px;">📅 Wochenplan</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">
          {{ now().strftime('KW %W • %B %Y') }}
        </p>
      </div>
  
  # Heute (hervorgehoben)
  - type: markdown
    content: |
      <div style="background: #1a1a1a; border-radius: 12px; padding: 15px; margin: 10px 0;">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
          <div style="background: #ff6b6b; color: white; padding: 8px 12px; border-radius: 8px; font-weight: bold; margin-right: 10px;">
            HEUTE
          </div>
          <div style="color: white; font-size: 18px; font-weight: bold;">
            {{ now().strftime('%A, %d. %B') }}
          </div>
        </div>
        
        <!-- Mahlzeiten von heute -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
          {% for sensor in ['fruhstuck', 'mittagessen', 'abendessen', 'snack'] %}
            {% set entity = 'sensor.norish_' ~ sensor %}
            {% if states(entity) != 'Kein Plan' %}
              <div style="position: relative; border-radius: 8px; overflow: hidden; height: 120px;">
                {% if state_attr(entity, 'video_url') %}
                  <video autoplay loop muted playsinline 
                         style="width: 100%; height: 100%; object-fit: cover;">
                    <source src="{{ state_attr(entity, 'video_url') }}" type="video/mp4">
                  </video>
                {% elif state_attr(entity, 'image') %}
                  <img src="{{ state_attr(entity, 'image') }}" 
                       style="width: 100%; height: 100%; object-fit: cover;">
                {% endif %}
                <div style="position: absolute; inset: 0; 
                            background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
                            display: flex; align-items: flex-end; padding: 10px;">
                  <span style="color: white; font-size: 12px; font-weight: bold;">
                    {{ states(entity) }}
                  </span>
                </div>
              </div>
            {% endif %}
          {% endfor %}
        </div>
      </div>
  
  # Morgen
  - type: markdown
    content: |
      <div style="background: #2a2a2a; border-radius: 12px; padding: 15px; margin: 10px 0;">
        <div style="color: white; font-size: 16px; font-weight: bold; margin-bottom: 10px;">
          {{ (now() + timedelta(days=1)).strftime('%A, %d. %B') }}
        </div>
        <!-- TODO: Template für Morgen -->
        <p style="color: #999;">Noch nicht implementiert - benötigt Kalender-Daten</p>
      </div>
```

---

## 🎨 Lösung 4: Premium Wochenplan (Vollversion)

### Mit allen Features

```yaml
type: vertical-stack
cards:
  # Header mit Wochenübersicht
  - type: markdown
    content: |
      <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  border-radius: 12px; padding: 20px; color: white; margin-bottom: 15px;">
        <h1 style="margin: 0; font-size: 32px;">📅 Wochenplan</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">
          {{ now().strftime('Kalenderwoche %W • %B %Y') }}
        </p>
      </div>
  
  # Heute - Groß hervorgehoben
  - type: vertical-stack
    cards:
      - type: markdown
        content: |
          <div style="background: #ff6b6b; border-radius: 12px 12px 0 0; 
                      padding: 15px; text-align: center;">
            <h2 style="margin: 0; color: white; font-size: 24px; text-transform: uppercase;">
              Heute • {{ now().strftime('%A') }}
            </h2>
            <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.9);">
              {{ now().strftime('%d. %B %Y') }}
            </p>
          </div>
      
      # Grid mit heutigen Mahlzeiten
      - type: grid
        columns: 2
        square: false
        cards:
          # Frühstück
          - type: markdown
            content: |
              {% if states('sensor.norish_fruhstuck') != 'Kein Plan' %}
                <div style="position: relative; height: 200px; border-radius: 12px; overflow: hidden;">
                  {% if state_attr('sensor.norish_fruhstuck', 'video_url') %}
                    <video autoplay loop muted playsinline 
                           style="width: 100%; height: 100%; object-fit: cover;">
                      <source src="{{ state_attr('sensor.norish_fruhstuck', 'video_url') }}" type="video/mp4">
                    </video>
                  {% elif state_attr('sensor.norish_fruhstuck', 'image') %}
                    <img src="{{ state_attr('sensor.norish_fruhstuck', 'image') }}" 
                         style="width: 100%; height: 100%; object-fit: cover;">
                  {% else %}
                    <div style="width: 100%; height: 100%; background: #333; display: flex; align-items: center; justify-content: center; color: #666;">
                      Kein Bild
                    </div>
                  {% endif %}
                  
                  <div style="position: absolute; top: 10px; left: 10px; 
                              background: rgba(255,255,255,0.9); color: #333; 
                              padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                    🌅 Frühstück
                  </div>
                  
                  <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                              background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); 
                              padding: 15px; color: white;">
                    <h3 style="margin: 0; font-size: 16px;">
                      {{ states('sensor.norish_fruhstuck') }}
                    </h3>
                    {% if state_attr('sensor.norish_fruhstuck', 'cooking_time') %}
                      <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.9;">
                        ⏱️ {{ state_attr('sensor.norish_fruhstuck', 'cooking_time') }} Min.
                      </p>
                    {% endif %}
                  </div>
                </div>
              {% else %}
                <div style="height: 200px; background: #1a1a1a; border-radius: 12px; 
                            display: flex; flex-direction: column; align-items: center; 
                            justify-content: center; color: #666;">
                  <span style="font-size: 40px; margin-bottom: 10px;">🌅</span>
                  <span>Kein Frühstück geplant</span>
                </div>
              {% endif %}
          
          # Mittagessen
          - type: markdown
            content: |
              {% if states('sensor.norish_mittagessen') != 'Kein Plan' %}
                <div style="position: relative; height: 200px; border-radius: 12px; overflow: hidden;">
                  {% if state_attr('sensor.norish_mittagessen', 'video_url') %}
                    <video autoplay loop muted playsinline 
                           style="width: 100%; height: 100%; object-fit: cover;">
                      <source src="{{ state_attr('sensor.norish_mittagessen', 'video_url') }}" type="video/mp4">
                    </video>
                  {% elif state_attr('sensor.norish_mittagessen', 'image') %}
                    <img src="{{ state_attr('sensor.norish_mittagessen', 'image') }}" 
                         style="width: 100%; height: 100%; object-fit: cover;">
                  {% endif %}
                  
                  <div style="position: absolute; top: 10px; left: 10px; 
                              background: rgba(255,255,255,0.9); color: #333; 
                              padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                    ☀️ Mittagessen
                  </div>
                  
                  <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                              background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); 
                              padding: 15px; color: white;">
                    <h3 style="margin: 0; font-size: 16px;">
                      {{ states('sensor.norish_mittagessen') }}
                    </h3>
                    {% if state_attr('sensor.norish_mittagessen', 'cooking_time') %}
                      <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.9;">
                        ⏱️ {{ state_attr('sensor.norish_mittagessen', 'cooking_time') }} Min.
                      </p>
                    {% endif %}
                  </div>
                </div>
              {% else %}
                <div style="height: 200px; background: #1a1a1a; border-radius: 12px; 
                            display: flex; flex-direction: column; align-items: center; 
                            justify-content: center; color: #666;">
                  <span style="font-size: 40px; margin-bottom: 10px;">☀️</span>
                  <span>Kein Mittagessen geplant</span>
                </div>
              {% endif %}
          
          # Abendessen
          - type: markdown
            content: |
              {% if states('sensor.norish_abendessen') != 'Kein Plan' %}
                <div style="position: relative; height: 200px; border-radius: 12px; overflow: hidden;">
                  {% if state_attr('sensor.norish_abendessen', 'video_url') %}
                    <video autoplay loop muted playsinline 
                           style="width: 100%; height: 100%; object-fit: cover;">
                      <source src="{{ state_attr('sensor.norish_abendessen', 'video_url') }}" type="video/mp4">
                    </video>
                  {% elif state_attr('sensor.norish_abendessen', 'image') %}
                    <img src="{{ state_attr('sensor.norish_abendessen', 'image') }}" 
                         style="width: 100%; height: 100%; object-fit: cover;">
                  {% endif %}
                  
                  <div style="position: absolute; top: 10px; left: 10px; 
                              background: rgba(255,255,255,0.9); color: #333; 
                              padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                    🌙 Abendessen
                  </div>
                  
                  <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                              background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); 
                              padding: 15px; color: white;">
                    <h3 style="margin: 0; font-size: 16px;">
                      {{ states('sensor.norish_abendessen') }}
                    </h3>
                    {% if state_attr('sensor.norish_abendessen', 'cooking_time') %}
                      <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.9;">
                        ⏱️ {{ state_attr('sensor.norish_abendessen', 'cooking_time') }} Min.
                      </p>
                    {% endif %}
                  </div>
                </div>
              {% else %}
                <div style="height: 200px; background: #1a1a1a; border-radius: 12px; 
                            display: flex; flex-direction: column; align-items: center; 
                            justify-content: center; color: #666;">
                  <span style="font-size: 40px; margin-bottom: 10px;">🌙</span>
                  <span>Kein Abendessen geplant</span>
                </div>
              {% endif %}
          
          # Snack
          - type: markdown
            content: |
              {% if states('sensor.norish_snack') != 'Kein Plan' %}
                <div style="position: relative; height: 200px; border-radius: 12px; overflow: hidden;">
                  {% if state_attr('sensor.norish_snack', 'video_url') %}
                    <video autoplay loop muted playsinline 
                           style="width: 100%; height: 100%; object-fit: cover;">
                      <source src="{{ state_attr('sensor.norish_snack', 'video_url') }}" type="video/mp4">
                    </video>
                  {% elif state_attr('sensor.norish_snack', 'image') %}
                    <img src="{{ state_attr('sensor.norish_snack', 'image') }}" 
                         style="width: 100%; height: 100%; object-fit: cover;">
                  {% endif %}
                  
                  <div style="position: absolute; top: 10px; left: 10px; 
                              background: rgba(255,255,255,0.9); color: #333; 
                              padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                    🍪 Snack
                  </div>
                  
                  <div style="position: absolute; bottom: 0; left: 0; right: 0; 
                              background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); 
                              padding: 15px; color: white;">
                    <h3 style="margin: 0; font-size: 16px;">
                      {{ states('sensor.norish_snack') }}
                    </h3>
                  </div>
                </div>
              {% else %}
                <div style="height: 200px; background: #1a1a1a; border-radius: 12px; 
                            display: flex; flex-direction: column; align-items: center; 
                            justify-content: center; color: #666;">
                  <span style="font-size: 40px; margin-bottom: 10px;">🍪</span>
                  <span>Kein Snack geplant</span>
                </div>
              {% endif %}
  
  # Restliche Woche (kompakt)
  - type: markdown
    content: |
      <div style="background: #1a1a1a; border-radius: 12px; padding: 20px; margin-top: 15px;">
        <h3 style="margin: 0 0 15px 0; color: white;">Restliche Woche</h3>
        <p style="color: #999; text-align: center; padding: 20px;">
          Kalender-Integration kommt bald...<br>
          Nutze vorerst den Kalender-Tab
        </p>
      </div>
```

---

## 🎯 Empfehlung

**Für die meisten Nutzer:** 
→ **Lösung 4 (Premium Wochenplan)** für "Heute"
→ Kombiniert mit Kalender-View für restliche Woche

**Für Mobile:**
→ **Lösung 2 (Horizontal Scroll)** mit Swipe Card

**Einfachste Lösung:**
→ **Lösung 3 (Kompakte Liste)** - keine Custom Components

---

**Vollständige Wochenansicht kommt in nächster Version!** 🚀
