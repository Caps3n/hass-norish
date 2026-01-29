# 🚀 Norish Integration - Quick Start

## Installation in 3 Schritten

### 1️⃣ Integration installieren

**Via HACS (empfohlen):**
1. HACS öffnen → Integrationen
2. ⋮ (3 Punkte) → Benutzerdefinierte Repositories
3. Repository hinzufügen: `https://github.com/Caps3n/hass-norish`
4. "Norish" suchen und installieren
5. Home Assistant neu starten

**Manuell:**
1. [Release herunterladen](https://github.com/Caps3n/hass-norish/releases)
2. `norish` Ordner nach `/config/custom_components/` kopieren
3. Home Assistant neu starten

---

### 2️⃣ Integration einrichten

1. **Einstellungen** → **Geräte & Dienste** → **+ Integration hinzufügen**
2. "Norish" suchen
3. Eingeben:
   - **Server URL**: `https://deine-norish-url.com`
   - **API-Schlüssel**: Dein API-Key aus Norish
4. **Absenden** klicken

✅ Fertig!

---

### 3️⃣ Dashboard erstellen

Einfaches Dashboard mit Bildern:

```yaml
type: vertical-stack
cards:
  # Heutiges Mittagessen mit Bild
  - type: picture-entity
    entity: sensor.norish_mittagessen
    show_name: true
    show_state: true
  
  # Alle Mahlzeiten des Tages
  - type: entities
    title: Heute
    entities:
      - sensor.norish_fruhstuck
      - sensor.norish_mittagessen
      - sensor.norish_abendessen
      - sensor.norish_snack
  
  # Einkaufsliste
  - type: todo-list
    entity: todo.norish_unsortiert
```

---

## 🎨 Verfügbare Entitäten

Nach der Installation stehen bereit:

### Sensoren
- `sensor.norish_mahlzeiten_heute` - Alle Mahlzeiten
- `sensor.norish_fruhstuck` - Frühstück
- `sensor.norish_mittagessen` - Mittagessen
- `sensor.norish_abendessen` - Abendessen  
- `sensor.norish_snack` - Snack

### Kalender
- `calendar.norish_speiseplan` - Wöchentlicher Essensplan

### Todo-Listen
- `todo.norish_unsortiert` - Einkaufsliste
- `todo.norish_<geschaeft>` - Pro Geschäft

### Kameras (optional)
- `camera.norish_fruhstuck_bild`
- `camera.norish_mittagessen_bild`
- `camera.norish_abendessen_bild`
- `camera.norish_snack_bild`

---

## 🖼️ Bilder anzeigen

Die Sensoren zeigen automatisch Rezeptbilder an, wenn diese in der API vorhanden sind.

**Dashboard-Karten mit Bildunterstützung:**
- Picture Entity Card (empfohlen)
- Picture Glance Card
- Entity Card (kleines Bild)

---

## ⚙️ Optionen

Konfiguriere welche Mahlzeiten angezeigt werden:

1. **Einstellungen** → **Geräte & Dienste**
2. **Norish** → **Konfigurieren**
3. Optionen anpassen:
   - ☑ Frühstück anzeigen
   - ☑ Mittagessen anzeigen
   - ☑ Abendessen anzeigen
   - ☑ Snacks anzeigen

---

## 🔍 Troubleshooting

### Keine Verbindung?
- Server-URL korrekt? (mit `https://` oder `http://`)
- API-Key gültig?
- Firewall-Regeln prüfen

### Keine Bilder?
- API liefert Bild-URLs? (in Entwicklertools → Zustände prüfen)
- URLs erreichbar?
- Debug-Logging aktivieren (siehe [INSTALLATION.md](INSTALLATION.md))

### Integration wird nicht gefunden?
- Home Assistant neugestartet?
- Dateien in `/config/custom_components/norish/`?
- Logs prüfen: `grep norish /config/home-assistant.log`

---

## 📚 Weitere Ressourcen

- [Vollständige Installation](INSTALLATION.md)
- [Dashboard-Beispiele](DASHBOARD_BEISPIELE.yaml)
- [Bild-Anleitung](BILDER_ANLEITUNG.md)
- [Changelog](CHANGELOG.md)

---

## 🆘 Support

- 🐛 [Bug Report](https://github.com/Caps3n/hass-norish/issues)
- 💡 [Feature Request](https://github.com/Caps3n/hass-norish/issues)
- 💬 [Diskussion](https://github.com/Caps3n/hass-norish/discussions)

---

**Viel Spaß mit Norish! 🎉**
