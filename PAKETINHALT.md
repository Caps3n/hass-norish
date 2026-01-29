# 📦 Norish Integration v1.0.0 - Paketinhalt

## 🎯 Was ist enthalten?

Komplette Home Assistant Integration für Norish mit Mehrsprachigkeit und Bildunterstützung.

---

## 📂 Ordnerstruktur

```
norish_v1.0.0/
├── custom_components/norish/          # Haupt-Integration
│   ├── __init__.py                    # Setup & Initialisierung
│   ├── config_flow.py                 # Konfigurations-UI mit Validierung
│   ├── const.py                       # Alle Konstanten zentral
│   ├── coordinator.py                 # Daten-Koordinator mit Retry-Logik
│   ├── sensor.py                      # Mahlzeiten-Sensoren mit Bildern
│   ├── calendar.py                    # Kalender-Integration
│   ├── todo.py                        # Einkaufslisten
│   ├── camera.py                      # Kamera-Entities für Bilder
│   ├── manifest.json                  # Integration-Metadaten
│   ├── strings.json                   # Standard-Übersetzungen (EN)
│   └── translations/                  # Mehrsprachigkeit
│       ├── de.json                    # 🇩🇪 Deutsch
│       ├── en.json                    # 🇬🇧 English
│       ├── es.json                    # 🇪🇸 Español
│       ├── fr.json                    # 🇫🇷 Français
│       └── it.json                    # 🇮🇹 Italiano
│
├── README.md                          # Haupt-Dokumentation (EN)
├── README_DE.md                       # Deutsche Dokumentation
├── QUICKSTART.md                      # Schnellstart-Anleitung
├── INSTALLATION.md                    # Detaillierte Installationsanleitung
├── CHANGELOG.md                       # Versionshistorie
├── LICENSE                            # MIT Lizenz
├── hacs.json                          # HACS-Konfiguration
├── .gitignore                         # Git-Ignore-Datei
├── DASHBOARD_BEISPIELE.yaml           # 10+ Dashboard-Vorlagen
└── BILDER_ANLEITUNG.md                # Anleitung für Bild-Integration
```

---

## 🌟 Hauptfunktionen

### ✅ Bereits implementiert

1. **Mahlzeiten-Sensoren**
   - 5 Sensoren (Alle, Frühstück, Mittag, Abend, Snack)
   - Automatische Bildanzeige
   - Rezept-Details als Attribute
   - Zubereitungszeit, Portionen, Beschreibung

2. **Kalender-Integration**
   - Wöchentliche Essensplanung
   - Unterschiedliche Uhrzeiten pro Mahlzeit
   - Vollständige Event-Details

3. **Einkaufslisten**
   - Todo-Listen pro Geschäft
   - Erstellen, Bearbeiten, Löschen
   - Mengen und Einheiten

4. **Bild-Unterstützung**
   - Via Sensor (entity_picture)
   - Via Camera-Entities
   - Automatisches Caching

5. **Mehrsprachigkeit**
   - 5 Sprachen komplett übersetzt
   - Automatische Spracherkennung

6. **Robustheit**
   - Retry-Logik bei Netzwerkfehlern
   - Timeout-Protection
   - Defensive Datenvalidierung
   - Ausführliches Logging

---

## 📥 Installationsoptionen

### Option A: HACS (Empfohlen)
1. HACS öffnen
2. Benutzerdefiniertes Repository hinzufügen
3. Installation mit einem Klick
4. Automatische Updates

### Option B: Manuell
1. `custom_components/norish` nach `/config/custom_components/` kopieren
2. Home Assistant neu starten
3. Integration hinzufügen

---

## 🎨 Dashboard-Vorlagen

**10 vorgefertigte Layouts:**
1. Einfache Bild-Karte
2. Kompakte Übersicht
3. Ohne Custom Components
4. Grid-Layout
5. Mit Rezept-Details
6. Wochenübersicht
7. Mit Einkaufsliste
8. Mobile-optimiert
9. Conditional Cards
10. Glance Card

Alle Vorlagen in `DASHBOARD_BEISPIELE.yaml`

---

## 🔧 API-Anforderungen

### Minimale Anforderungen

**Calendar Endpoint:**
```json
{
  "date": "2026-01-29T00:00:00.000Z",
  "type": "LUNCH",
  "recipe": {
    "name": "Rezeptname"
  }
}
```

**Optimal mit Bildern:**
```json
{
  "date": "2026-01-29T00:00:00.000Z",
  "type": "LUNCH",
  "recipe": {
    "name": "Spaghetti Carbonara",
    "image": "https://example.com/image.jpg",
    "description": "Leckere Pasta",
    "cookingTime": 30,
    "servings": 4
  }
}
```

**Groceries Endpoint:**
```json
{
  "id": "123",
  "name": "Tomaten",
  "amount": 2,
  "unit": "kg",
  "isDone": false,
  "storeId": "1"
}
```

---

## 🚀 Erste Schritte nach Installation

1. **Integration einrichten**
   - Einstellungen → Geräte & Dienste
   - Norish hinzufügen
   - URL und API-Key eingeben

2. **Dashboard erstellen**
   - Vorlagen aus `DASHBOARD_BEISPIELE.yaml` nutzen
   - Mit Picture Entity Card starten

3. **Anpassen**
   - Optionen konfigurieren
   - Gewünschte Mahlzeiten auswählen

4. **Testen**
   - Sensoren in Entwicklertools prüfen
   - Kalender öffnen
   - Todo-Liste testen

---

## 📊 Technische Details

### Performance
- Update-Intervall: 5 Minuten (konfigurierbar)
- Store-Cache: 24 Stunden
- Bild-Cache: Session-basiert
- Connection Pooling: Aktiviert

### Sicherheit
- API-Key Validierung beim Setup
- Verschlüsselte Speicherung
- Timeout-Protection (10s)
- HTTPS empfohlen

### Kompatibilität
- Home Assistant: 2024.1.0+
- Python: 3.11+
- aiohttp: 3.9.0+

---

## 🆘 Support & Hilfe

### Dokumentation
- `README.md` - Übersicht & Features
- `QUICKSTART.md` - Schnelleinstieg
- `INSTALLATION.md` - Detaillierte Anleitung
- `BILDER_ANLEITUNG.md` - Bild-Integration
- `DASHBOARD_BEISPIELE.yaml` - Layout-Vorlagen

### Bei Problemen
1. Logs prüfen: `grep norish /config/home-assistant.log`
2. Debug aktivieren (siehe INSTALLATION.md)
3. [Issue erstellen](https://github.com/Caps3n/hass-norish/issues)
4. [Diskussion starten](https://github.com/Caps3n/hass-norish/discussions)

---

## 🔄 Updates

### Via HACS
- Automatische Update-Benachrichtigungen
- Ein-Klick-Update
- Changelog wird angezeigt

### Manuell
- Neue Version herunterladen
- Dateien ersetzen
- Home Assistant neu starten
- Changelog prüfen

---

## 🎯 Nächste Schritte

1. ✅ Installation abschließen
2. 📖 QUICKSTART.md lesen
3. 🎨 Dashboard erstellen
4. ⚙️ Optionen anpassen
5. 🎉 Genießen!

---

## 📝 Changelog

### Version 1.0.0 (29.01.2026)
- 🎉 Erste Veröffentlichung
- 📅 Kalender-Integration
- 🍳 Mahlzeiten-Sensoren mit Bildern
- 🛒 Einkaufslisten
- 📷 Kamera-Entities
- 🌍 5 Sprachen
- ⚡ Verbesserte Performance & Fehlerbehandlung

---

## 📄 Lizenz

MIT License - Siehe `LICENSE` Datei

---

## 👨‍💻 Entwickler

- **Erstellt von:** [@Caps3n](https://github.com/Caps3n)
- **Repository:** https://github.com/Caps3n/hass-norish
- **Issues:** https://github.com/Caps3n/hass-norish/issues

---

**Viel Erfolg mit deiner Norish Integration! 🎉**

Bei Fragen oder Problemen: Einfach ein Issue erstellen!
