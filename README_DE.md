# Norish Integration für Home Assistant

[![Version](https://img.shields.io/github/v/release/Caps3n/hass-norish?label=version&color=blue)](https://github.com/Caps3n/hass-norish/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.6%2B-blue.svg)](https://www.home-assistant.io/)
[![Lizenz](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Validate](https://github.com/Caps3n/hass-norish/actions/workflows/validate.yaml/badge.svg)](https://github.com/Caps3n/hass-norish/actions/workflows/validate.yaml)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-caps3n-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/caps3n)

[🇬🇧 English Version](README.md)

Eine vollständige Home Assistant Integration für [Norish](https://github.com/norish-recipes/norish) — die Open-Source-App für Rezepte und Essensplanung.

> Verbindet deine Norish-Instanz mit Home Assistant: Mahlzeiten-Sensoren, Einkaufsliste, Kalender, Rezeptbilder und Video-Unterstützung — alles in einer Integration.

---

## ✨ Funktionen

### 🍳 Mahlzeiten-Sensoren
- **6 Sensoren**: Alle Mahlzeiten heute, Frühstück, Mittagessen, Abendessen, Snack, Wochenplan
- Automatische **Rezeptbild**-Anzeige über `entity_picture`
- **Video-Unterstützung** — Autoplay, Loop, stumm (genau wie in der Norish App)
- Attribute: Rezeptname, Typ, Bild-URL, Rezept-ID

### 📅 Wochenplan-Sensor
- 7-Tage-Übersicht aller geplanten Mahlzeiten
- Tages-Attribute: `mo`, `tu`, `we`, `th`, `fr`, `sa`, `su`
- Heute und Wochenenden werden hervorgehoben
- Sortiert nach Mahlzeit-Typ (Frühstück → Mittagessen → Abendessen → Snack)
- **Vergangene Mahlzeiten werden automatisch ausgeblendet** — 30 Minuten nach dem Standard-Zeitfenster

### 📆 Kalender
- Nativer Home Assistant Kalender
- Ein Eintrag pro Mahlzeit mit korrekten Zeitfenstern

### 🛒 Einkaufsliste
- Native Home Assistant Todo-Listen-Entität
- Artikel mit Menge und Einheit
- Erstellen, aktualisieren und löschen

### 📷 Kamera-Entitäten
- Eine Kamera pro Mahlzeit-Typ
- Lokal gecachte Bilder für schnelle Anzeige

### 🎬 Media Player Entitäten
- Ein Media Player pro Mahlzeit-Typ
- Zeigt das Rezeptvideo, wenn verfügbar

### 🌍 Mehrsprachig
- 5 Sprachen: 🇩🇪 Deutsch · 🇬🇧 English · 🇫🇷 Français · 🇪🇸 Español · 🇮🇹 Italiano

---

## 🚀 Installation

### Option 1: HACS (Empfohlen)

1. **HACS** in Home Assistant öffnen
2. **Integrationen** → ⋮ oben rechts → **Benutzerdefinierte Repositories**
3. URL hinzufügen: `https://github.com/Caps3n/hass-norish` → Kategorie: `Integration`
4. Nach **"Norish"** suchen und **Installieren** klicken
5. Home Assistant neu starten

### Option 2: Manuell

1. Die [neueste Version](https://github.com/Caps3n/hass-norish/releases) herunterladen
2. Den `norish`-Ordner in `config/custom_components/` kopieren
3. Home Assistant neu starten

---

## ⚙️ Konfiguration

1. **Einstellungen → Geräte & Dienste**
2. **+ Integration hinzufügen**
3. Nach **"Norish"** suchen
4. Eingeben:
   - **Server-URL** — z.B. `https://norish.deinedomain.de`
   - **API-Key** — zu finden in den Norish-Einstellungen unter **API-Schlüssel**
5. **Absenden** klicken

### API-Key aktualisieren

Wenn der API-Key abläuft, zeigt Home Assistant automatisch eine **„Neu konfigurieren"**-Benachrichtigung an. Über das ⋮-Menü auf der Integrations-Karte → **Neu konfigurieren** kann der Key aktualisiert werden — ohne die Integration zu löschen.

---

## 📊 Entitäten

### Sensoren

| Entität | Beschreibung |
|---------|--------------|
| `sensor.norish_meals_today` | Alle Mahlzeiten heute |
| `sensor.norish_breakfast` | Frühstück heute |
| `sensor.norish_lunch` | Mittagessen heute |
| `sensor.norish_dinner` | Abendessen heute |
| `sensor.norish_snack` | Snack heute |
| `sensor.norish_week_planner` | 7-Tage-Mahlzeitenübersicht |

### Kalender

| Entität | Beschreibung |
|---------|--------------|
| `calendar.norish_meal_plan` | Wöchentlicher Mahlzeiten-Kalender |

### Todo

| Entität | Beschreibung |
|---------|--------------|
| `todo.norish_shopping_list` | Einkaufsliste |

### Kameras

| Entität | Beschreibung |
|---------|--------------|
| `camera.norish_breakfast_image` | Frühstücks-Rezeptbild |
| `camera.norish_lunch_image` | Mittagessen-Rezeptbild |
| `camera.norish_dinner_image` | Abendessen-Rezeptbild |
| `camera.norish_snack_image` | Snack-Rezeptbild |

### Media Player

| Entität | Beschreibung |
|---------|--------------|
| `media_player.norish_breakfast_video` | Frühstücks-Rezeptvideo |
| `media_player.norish_lunch_video` | Mittagessen-Rezeptvideo |
| `media_player.norish_dinner_video` | Abendessen-Rezeptvideo |
| `media_player.norish_snack_video` | Snack-Rezeptvideo |

---

## 🎨 Dashboard-Beispiele

### Einfache Bild-Karte

```yaml
type: picture-entity
entity: sensor.norish_lunch
show_name: true
show_state: true
```

### 2×2 Mahlzeiten-Grid

```yaml
type: grid
columns: 2
cards:
  - type: picture-entity
    entity: sensor.norish_breakfast
  - type: picture-entity
    entity: sensor.norish_lunch
  - type: picture-entity
    entity: sensor.norish_dinner
  - type: picture-entity
    entity: sensor.norish_snack
```

### Wochenübersicht (mit Heute-Hervorhebung)

```yaml
type: markdown
content: |
  {% set week = state_attr('sensor.norish_week_planner', 'week_data') %}
  {% for day in week %}
  <div style="background:{% if day.is_today %}#1e3a5f{% else %}#1c1c1c{% endif %};
              border-radius:10px;padding:12px;margin:6px 0;">
    <strong style="color:white;">{{ day.weekday }} · {{ day.date_formatted }}</strong>
    <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">
    {% for meal in day.meals %}
      <div style="flex:1;min-width:80px;height:70px;border-radius:6px;overflow:hidden;position:relative;">
        {% if meal.image %}
          <img src="{{ meal.image }}" style="width:100%;height:100%;object-fit:cover;">
        {% endif %}
        <div style="position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,.5);
                    color:white;font-size:10px;padding:2px 4px;">{{ meal.type }}</div>
      </div>
    {% endfor %}
    </div>
  </div>
  {% endfor %}
```

Weitere Beispiele in [DASHBOARD_BEISPIELE.yaml](DASHBOARD_BEISPIELE.yaml)

---

## 🔧 Fehlerbehebung

**Integration zeigt „Einrichtungsfehler" / hört nach einigen Stunden auf zu funktionieren**
- Der API-Key ist abgelaufen. **Einstellungen → Geräte & Dienste → Norish → ⋮ → Neu konfigurieren** und einen neuen Key aus den Norish-Einstellungen unter **API-Schlüssel** eingeben.
- Die Integration toleriert bis zu 2 kurzzeitige Auth-Fehler automatisch, bevor sie sich deaktiviert.

**Keine Mahlzeiten angezeigt / „No meals planned"**
- Prüfen, ob die Integration aktiv ist (kein Einrichtungsfehler)
- Vergangene Mahlzeiten werden automatisch ausgeblendet: Frühstück nach 08:30, Mittagessen nach 12:30, Snack nach 15:30, Abendessen nach 18:30
- Zukünftige Tage zeigen immer alle Mahlzeiten

**Keine Bilder angezeigt**
- Prüfen, ob die Norish-Instanz Bild-URLs zurückgibt
- Sicherstellen, dass die Bilder von Home Assistant erreichbar sind

**Verbindungsfehler beim Einrichten**
- Server-URL von Home Assistant aus erreichbar?
- API-Key korrekt? (Norish-Einstellungen → API-Schlüssel)
- Firewall / Reverse-Proxy-Einstellungen prüfen

**Debug-Logging aktivieren**

In `configuration.yaml` hinzufügen:

```yaml
logger:
  default: info
  logs:
    custom_components.norish: debug
```

---

## 🆕 Neu in v1.6.9

- **Automatische API-Key-Erneuerung** — wenn der Key erschöpft ist, erstellt die Integration automatisch einen neuen mit den gespeicherten Norish-Zugangsdaten. Kein manuelles "Neu konfigurieren" nötig.
- **Optionale Zugangsdaten** — E-Mail + Passwort im Setup- oder Reconfigure-Formular eintragen, um die Auto-Erneuerung zu aktivieren. Das Passwort wird als maskiertes Feld gespeichert.
- **Fallback** — ohne Zugangsdaten bleibt das bisherige Verhalten: nach 3 aufeinanderfolgenden 401-Fehlern zeigt HA die "Neu konfigurieren"-Benachrichtigung.
- **Exponentielles Reconnect-Backoff** (v1.6.8) — 1. Fehler → 60 s, 2. → 5 min, 3.+ → 10 min; stellt sich nach Erfolg automatisch wieder her.

Vollständige Versionshistorie in [CHANGELOG.md](CHANGELOG.md)

---

## 🤝 Mitwirken

Beiträge sind willkommen!

1. Repository forken
2. Feature-Branch erstellen (`git checkout -b feature/mein-feature`)
3. Änderungen committen
4. Pull Request öffnen

---

## 📄 Lizenz

MIT-Lizenz — siehe [LICENSE](LICENSE) für Details.

---

## 🙏 Danksagungen

- Erstellt von [@Caps3n](https://github.com/Caps3n)
- Gebaut für [Norish](https://github.com/norish-recipes/norish)
- Mit ❤️ für die Home Assistant Community
