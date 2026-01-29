# Norish Integration für Home Assistant

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Caps3n/hass-norish)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Lizenz](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Home Assistant Integration für das Norish Rezept- und Essensplanungssystem.

[🇬🇧 English Version](README.md) | [🇫🇷 Version Française](README_FR.md) | [🇪🇸 Versión Española](README_ES.md)

## Funktionen

- 📅 **Essensplan-Kalender** - Zeige deinen Wochenplan an
- 🍳 **Mehrere Mahlzeiten-Sensoren** - Separate Sensoren für Frühstück, Mittagessen, Abendessen und Snacks
- 🖼️ **Rezept-Bilder** - Zeige Rezeptfotos in deinem Dashboard
- 🛒 **Einkaufslisten** - Verwalte Einkaufslisten nach Geschäft
- 📷 **Kamera-Entitäten** - Alternative Bildanzeige über die Kamera-Plattform
- 🌍 **Mehrsprachig** - Verfügbar auf Deutsch, Englisch, Französisch, Spanisch und Italienisch

## Installation

### Option 1: HACS (Empfohlen)

1. Öffne HACS in Home Assistant
2. Klicke auf "Integrationen"
3. Klicke auf die drei Punkte oben rechts
4. Wähle "Benutzerdefinierte Repositories"
5. Füge `https://github.com/Caps3n/hass-norish` als Repository hinzu
6. Kategorie: "Integration"
7. Klicke "Hinzufügen"
8. Suche nach "Norish" in HACS
9. Klicke "Installieren"
10. Starte Home Assistant neu

### Option 2: Manuelle Installation

1. Lade die neueste Version von [GitHub](https://github.com/Caps3n/hass-norish/releases) herunter
2. Entpacke den `norish` Ordner in dein `custom_components` Verzeichnis
3. Starte Home Assistant neu

## Konfiguration

1. Gehe zu **Einstellungen** > **Geräte & Dienste**
2. Klicke auf **+ Integration hinzufügen**
3. Suche nach "Norish"
4. Gib deine Norish Server-URL und deinen API-Schlüssel ein
5. Klicke auf **Absenden**

### Konfigurationsoptionen

- **Server URL**: Die URL deiner Norish-Instanz (z.B. `https://norish.deinedomain.de`)
- **API-Schlüssel**: Dein Norish API-Schlüssel (zu finden in deinen Norish-Kontoeinstellungen)

### Optionen

Nach der Installation kannst du konfigurieren, welche Mahlzeiten-Typen angezeigt werden sollen:

- Frühstück anzeigen
- Mittagessen anzeigen
- Abendessen anzeigen
- Snacks anzeigen

## Entitäten

Die Integration erstellt folgende Entitäten:

### Sensoren

- `sensor.norish_mahlzeiten_heute` - Alle Mahlzeiten für heute
- `sensor.norish_fruhstuck` - Frühstück
- `sensor.norish_mittagessen` - Mittagessen
- `sensor.norish_abendessen` - Abendessen
- `sensor.norish_snack` - Snacks

Jeder Sensor enthält:
- Aktuellen Mahlzeitennamen als Status
- Rezeptbild (falls verfügbar)
- Zubereitungszeit
- Portionen
- Beschreibung

### Kalender

- `calendar.norish_speiseplan` - Wöchentlicher Essenskalender

### Todo-Listen

- `todo.norish_unsortiert` - Unsortierte Einkaufsartikel
- `todo.norish_<geschaeft_name>` - Einkaufsliste pro Geschäft

### Kameras (Optional)

- `camera.norish_fruhstuck_bild` - Frühstücks-Rezeptbild
- `camera.norish_mittagessen_bild` - Mittagessen-Rezeptbild
- `camera.norish_abendessen_bild` - Abendessen-Rezeptbild
- `camera.norish_snack_bild` - Snack-Rezeptbild

## Dashboard-Beispiele

### Einfache Picture Entity Card

```yaml
type: picture-entity
entity: sensor.norish_mittagessen
show_name: true
show_state: true
```

### Grid-Layout

```yaml
type: grid
columns: 2
cards:
  - type: picture-entity
    entity: sensor.norish_fruhstuck
  - type: picture-entity
    entity: sensor.norish_mittagessen
  - type: picture-entity
    entity: sensor.norish_abendessen
  - type: picture-entity
    entity: sensor.norish_snack
```

### Mit Einkaufsliste

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: sensor.norish_mittagessen
  - type: todo-list
    entity: todo.norish_unsortiert
```

Mehr Beispiele in [DASHBOARD_BEISPIELE.yaml](DASHBOARD_BEISPIELE.yaml)

## Fehlerbehebung

### Keine Bilder werden angezeigt

1. Prüfe, ob deine API Bild-URLs zurückgibt
2. Verifiziere, dass die Bild-URLs erreichbar sind
3. Prüfe die Logs: `grep -i norish /config/home-assistant.log`

### Verbindungsfehler

1. Überprüfe, ob die Server-URL korrekt ist
2. Prüfe deinen API-Schlüssel
3. Stelle sicher, dass Home Assistant deinen Norish-Server erreichen kann
4. Prüfe Firewall-Regeln

### Debug-Logging aktivieren

Füge zu `configuration.yaml` hinzu:

```yaml
logger:
  default: info
  logs:
    custom_components.norish: debug
```

## Mitwirken

Beiträge sind willkommen! Bitte:

1. Forke das Repository
2. Erstelle einen Feature-Branch
3. Mache deine Änderungen
4. Füge Tests hinzu, falls zutreffend
5. Reiche einen Pull Request ein

## Änderungsprotokoll

### Version 1.0.0 (29.01.2026)

- ✨ Erste Veröffentlichung
- 📅 Kalender-Integration
- 🍳 Mahlzeiten-Sensoren mit Bildern
- 🛒 Einkaufslisten-Unterstützung
- 📷 Kamera-Entitäten
- 🌍 Mehrsprachige Unterstützung (DE, EN, ES, FR, IT)
- ⚡ Verbesserte Fehlerbehandlung
- 🔄 Retry-Logik für API-Aufrufe
- 🎨 Bessere Bild-Unterstützung

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE)-Datei für Details.

## Danksagungen

- Erstellt von [@Caps3n](https://github.com/Caps3n)
- Inspiriert vom Norish Essensplanungssystem
- Gebaut für die Home Assistant Community

## Support

- 🐛 [Einen Fehler melden](https://github.com/Caps3n/hass-norish/issues)
- 💡 [Eine Funktion vorschlagen](https://github.com/Caps3n/hass-norish/issues)
- 💬 [Diskussionen](https://github.com/Caps3n/hass-norish/discussions)

---

Mit ❤️ für die Home Assistant Community erstellt
