# Installation Guide - Norish Home Assistant Integration

## Voraussetzungen

- Home Assistant 2024.1.0 oder neuer
- Norish Server mit API-Zugang
- API-Schlüssel für deinen Norish Account

## Installationsmethoden

### Methode 1: HACS (Empfohlen) 🌟

HACS (Home Assistant Community Store) ist die einfachste Methode zur Installation und ermöglicht automatische Updates.

#### Schritt 1: HACS installieren (falls noch nicht vorhanden)

Falls du HACS noch nicht installiert hast, folge der [offiziellen HACS Installationsanleitung](https://hacs.xyz/docs/setup/download).

#### Schritt 2: Norish Repository hinzufügen

1. Öffne Home Assistant
2. Gehe zu **HACS** im Seitenmenü
3. Klicke auf **Integrationen**
4. Klicke auf die **drei Punkte** (⋮) oben rechts
5. Wähle **Benutzerdefinierte Repositories**
6. Füge folgende Informationen ein:
   - **Repository**: `https://github.com/Caps3n/hass-norish`
   - **Kategorie**: `Integration`
7. Klicke auf **Hinzufügen**

#### Schritt 3: Integration installieren

1. Suche in HACS nach **"Norish"**
2. Klicke auf die Integration
3. Klicke auf **Herunterladen**
4. Wähle die neueste Version
5. Klicke auf **Herunterladen**
6. **Starte Home Assistant neu**

#### Schritt 4: Integration konfigurieren

1. Gehe zu **Einstellungen** → **Geräte & Dienste**
2. Klicke auf **+ Integration hinzufügen**
3. Suche nach **"Norish"**
4. Gib deine Daten ein:
   - **Server URL**: z.B. `https://norish.deinedomain.com`
   - **API-Schlüssel**: Dein persönlicher API-Key
5. Klicke auf **Absenden**

✅ Fertig! Die Integration ist nun einsatzbereit.

---

### Methode 2: Manuelle Installation

#### Schritt 1: Integration herunterladen

1. Gehe zu den [GitHub Releases](https://github.com/Caps3n/hass-norish/releases)
2. Lade die neueste Version herunter (ZIP-Datei)
3. Entpacke die Datei

#### Schritt 2: Dateien kopieren

1. Öffne deinen Home Assistant Konfigurationsordner
   - Standard-Pfad: `/config/`
   - Bei Docker oft: `/usr/share/hassio/homeassistant/`

2. Erstelle den Ordner `custom_components`, falls er nicht existiert:
   ```bash
   mkdir -p custom_components
   ```

3. Kopiere den `norish` Ordner:
   ```bash
   cp -r norish custom_components/
   ```

4. Die Struktur sollte so aussehen:
   ```
   config/
   └── custom_components/
       └── norish/
           ├── __init__.py
           ├── calendar.py
           ├── camera.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── manifest.json
           ├── sensor.py
           ├── strings.json
           ├── todo.py
           └── translations/
               ├── de.json
               ├── en.json
               ├── es.json
               ├── fr.json
               └── it.json
   ```

#### Schritt 3: Home Assistant neu starten

Starte Home Assistant neu über:
- **Einstellungen** → **System** → **Neustart**
- Oder per CLI: `ha core restart`

#### Schritt 4: Integration konfigurieren

Siehe [Schritt 4 bei HACS-Installation](#schritt-4-integration-konfigurieren)

---

## Konfiguration

### Server URL finden

1. Öffne deine Norish-Instanz im Browser
2. Die URL in der Adressleiste ist deine Server-URL
3. Beispiele:
   - `https://norish.example.com`
   - `http://192.168.1.100:3000`
   - `https://my-norish.dyndns.org`

**Wichtig:** 
- Verwende die vollständige URL inklusive `https://` oder `http://`
- Bei lokalen Installationen: stelle sicher, dass Home Assistant den Server erreichen kann

### API-Schlüssel erhalten

Der API-Schlüssel wird in deinem Norish Account generiert:

1. Melde dich bei Norish an
2. Gehe zu **Einstellungen** → **API**
3. Klicke auf **Neuen API-Schlüssel erstellen**
4. Kopiere den Schlüssel (er wird nur einmal angezeigt!)
5. Verwende diesen Schlüssel in der Home Assistant Konfiguration

### Optionale Einstellungen

Nach der Installation kannst du zusätzliche Optionen konfigurieren:

1. Gehe zu **Einstellungen** → **Geräte & Dienste**
2. Finde die **Norish** Integration
3. Klicke auf **Konfigurieren**
4. Passe folgende Optionen an:
   - ☐ Frühstück anzeigen
   - ☐ Mittagessen anzeigen
   - ☐ Abendessen anzeigen
   - ☐ Snacks anzeigen

---

## Verifizierung

Nach erfolgreicher Installation solltest du folgende Entitäten sehen:

### Im Entwickler-Tools → Status

Suche nach `norish`:

- `sensor.norish_mahlzeiten_heute`
- `sensor.norish_fruhstuck`
- `sensor.norish_mittagessen`
- `sensor.norish_abendessen`
- `sensor.norish_snack`
- `calendar.norish_speiseplan`
- `todo.norish_unsortiert`
- `camera.norish_fruhstuck_bild`
- `camera.norish_mittagessen_bild`
- `camera.norish_abendessen_bild`
- `camera.norish_snack_bild`

### Erste Schritte

1. **Teste einen Sensor:**
   - Gehe zu **Entwickler-Tools** → **Zustände**
   - Suche nach `sensor.norish_mittagessen`
   - Der Status sollte den Namen des heutigen Mittagessens zeigen

2. **Prüfe den Kalender:**
   - Öffne **Kalender** im Menü
   - Du solltest deine Essensplanung sehen

3. **Teste die Einkaufsliste:**
   - Erstelle eine Todo-List Card
   - Füge einen Artikel hinzu
   - Er sollte in Norish erscheinen

---

## Troubleshooting

### Integration erscheint nicht in der Liste

**Lösung:**
1. Prüfe, ob der `custom_components/norish` Ordner existiert
2. Überprüfe die Dateirechte (müssen lesbar sein)
3. Schaue in die Logs: `grep -i norish /config/home-assistant.log`
4. Starte Home Assistant neu

### "Verbindung fehlgeschlagen"

**Mögliche Ursachen:**

1. **Falsche URL:**
   - Prüfe Schreibweise
   - Teste URL im Browser
   - Stelle sicher, dass `https://` oder `http://` dabei ist

2. **Netzwerk-Problem:**
   - Kann Home Assistant den Server erreichen?
   - Bei Docker: ist das Netzwerk richtig konfiguriert?
   - Firewall-Regeln prüfen

3. **SSL-Zertifikat-Problem:**
   - Bei selbst-signierten Zertifikaten kann es Probleme geben
   - Verwende ggf. `http://` für lokale Tests

### "Ungültiger API-Schlüssel"

**Lösungen:**
1. Generiere einen neuen API-Schlüssel in Norish
2. Kopiere ihn komplett (keine Leerzeichen)
3. Lösche die Integration und richte sie neu ein

### Keine Bilder werden angezeigt

**Prüfe:**
1. Liefert deine Norish-API Bild-URLs?
2. Sind die URLs erreichbar?
3. Aktiviere Debug-Logging (siehe unten)

### Debug-Logging aktivieren

Füge zu `configuration.yaml` hinzu:

```yaml
logger:
  default: info
  logs:
    custom_components.norish: debug
```

Starte Home Assistant neu und prüfe die Logs:

```bash
tail -f /config/home-assistant.log | grep norish
```

---

## Updates

### Via HACS (automatisch)

HACS zeigt verfügbare Updates automatisch an:

1. Öffne **HACS** → **Integrationen**
2. Bei verfügbaren Updates erscheint eine Benachrichtigung
3. Klicke auf **Aktualisieren**
4. Starte Home Assistant neu

### Manuelle Updates

1. Lade die neue Version von GitHub herunter
2. Ersetze den `custom_components/norish` Ordner
3. Starte Home Assistant neu
4. Prüfe das [CHANGELOG](CHANGELOG.md) für Breaking Changes

---

## Deinstallation

### Integration entfernen

1. Gehe zu **Einstellungen** → **Geräte & Dienste**
2. Finde **Norish**
3. Klicke auf die **drei Punkte** (⋮)
4. Wähle **Löschen**
5. Bestätige

### Dateien entfernen

**Bei HACS-Installation:**
1. Öffne **HACS** → **Integrationen**
2. Finde **Norish**
3. Klicke auf **Entfernen**

**Bei manueller Installation:**
```bash
rm -rf /config/custom_components/norish
```

---

## Nächste Schritte

Nach erfolgreicher Installation:

1. 📖 Lies die [Dashboard-Beispiele](DASHBOARD_BEISPIELE.yaml)
2. 🎨 Passe die Anzeige nach deinen Wünschen an
3. 🔔 Erstelle Automationen basierend auf deinem Essensplan
4. 💡 Teile deine Dashboards in der Community!

---

## Support

Bei Problemen:

- 🐛 [Issue auf GitHub erstellen](https://github.com/Caps3n/hass-norish/issues)
- 💬 [Diskussionen](https://github.com/Caps3n/hass-norish/discussions)
- 📖 [README lesen](README.md)

---

Viel Erfolg mit deiner Norish Integration! 🎉
