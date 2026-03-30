# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.1] - 2026-03-30

### Changed — Clean Rewrite
- 🏗️ **Rewritten coordinator** — `NorishCoordinator` (formerly `NorishListCoordinator`) with clean architecture. `config_entry` properly passed to `DataUpdateCoordinator` so HA correctly triggers reauth on 401 errors.
- ⚡ **30-second polling** — Reduced from 2 minutes for near-real-time updates.
- 🔐 **API key validation on setup** — Quick check during `async_setup_entry` that the API key works before creating the coordinator.
- 🔄 **Reauth flow** — Added `async_step_reauth` and `async_step_reauth_confirm` so HA shows "Reconfigure" when the API key expires, and the user can enter a new one without deleting the integration.
- 🔁 **Retry with exponential backoff** — Server errors (5xx) and timeouts are retried up to 3 times before giving up.
- 🗂️ **Simplified data structure** — `hass.data[DOMAIN][entry_id]` stores the coordinator directly instead of a nested dict.
- 🌍 **Updated all translations** — `strings.json`, `en.json`, `de.json`, `fr.json`, `es.json`, `it.json` updated with reauth_confirm and reconfigure steps.

## [1.5.8] - 2026-03-30

### Fixed
- 🔑 **config_entry now passed to DataUpdateCoordinator** – The root cause of "Neu konfigurieren" never appearing. Without `config_entry`, HA's coordinator silently swallowed `ConfigEntryAuthFailed` on scheduled polls instead of triggering `async_start_reauth`. The counter reached 3/3 but nothing happened; then it reset and started over. Now `config_entry` is passed to `super().__init__()`, so HA correctly triggers the reauth notification.
- 🛑 **Permanent auth-fail flag** – Once the sliding-window threshold (3 failures in 10 min) is reached, a `_auth_permanently_failed` flag is set. Every subsequent poll immediately raises `ConfigEntryAuthFailed` instead of resetting the counter and starting over. This guarantees the "reconfigure" notification even if HA doesn't stop polling after the first auth failure.
- 🔄 **Fixed infinite restart loop in `__init__.py`** – `ConfigEntryNotReady` is no longer re-raised during setup, preventing HA from recreating the coordinator and resetting the counter.
- 🔇 **Recipe 401s isolated from core data** – `recipes.get` returning 401 is caught and logged as a warning without affecting core data loading.

## [1.5.7] - 2026-03-29

### Fixed
- 🔐 **Sliding-window auth failure detection** – Replaced the consecutive-failure counter with a time-based sliding window (3 failures within 10 minutes → disable). The old counter was reset to 0 on every successful poll, so intermittent 401s could never reach the threshold.
- 🔄 **Fixed infinite restart loop in `__init__.py`** – The root cause of the "counter stuck at 1/3" bug. When `_async_update_data` raised `UpdateFailed` (auth count < threshold), HA's `async_config_entry_first_refresh` converted it to `ConfigEntryNotReady`. The old code re-raised `ConfigEntryNotReady`, causing HA to call `async_setup_entry` again — creating a **new coordinator** and resetting the sliding-window to zero. Now `ConfigEntryNotReady` is caught and the integration loads with empty data instead of restarting. The coordinator persists across polls, allowing the counter to accumulate correctly.
- 🔇 **Recipe 401s no longer block the integration** – `recipes.get` returning 401 is caught and logged as a warning. Core data (calendar, groceries) loads normally.

## [1.5.2] - 2026-03-26

### Changed
- 📝 **README.md** vollständig auf v1.5.x aktualisiert — What's New, Troubleshooting (API-Key-Ablauf, vergangene Mahlzeiten), Reconfigure-Anleitung
- 📝 **README_DE.md** komplett neu geschrieben — war noch auf v1.0.0 mit veralteten Entity-Namen, jetzt deckungsgleich mit der englischen Version

## [1.5.1] - 2026-03-26

### Fixed
- 🔁 **Integration bleibt bei kurzzeitigen 401-Fehlern aktiv** – Ein einzelner 401-Fehler (z.B. durch einen Norish-Server-Neustart oder kurzzeitige Netzwerkprobleme) deaktiviert die Integration nicht mehr sofort.
  - Die Integration toleriert jetzt bis zu 2 aufeinanderfolgende 401-Fehler (`UpdateFailed`, Retry beim nächsten Poll)
  - Erst beim **3. aufeinanderfolgenden** 401 wird `ConfigEntryAuthFailed` ausgelöst → HA zeigt „Neu konfigurieren" an
  - Bei erfolgreichem Update wird der Fehlerzähler automatisch zurückgesetzt

## [1.5.0] - 2026-03-25

### Added
- 🔄 **API-Key Ablauf automatisch erkennen** – Die Integration zeigt jetzt eine HA-Benachrichtigung an, wenn der API-Key abläuft (HTTP 401), statt still zu scheitern.
  - Nutzt `ConfigEntryAuthFailed` → Home Assistant deaktiviert automatisch den Polling und zeigt im UI „Neu konfigurieren" an
  - Betrifft sowohl GET- als auch POST-Anfragen
- 🔑 **„Neu konfigurieren"-Schritt** (`async_step_reconfigure`) – API-Key kann über das Drei-Punkte-Menü der Integration aktualisiert werden, ohne die Integration zu löschen
  - Neue Seite im Config Flow mit URL + API-Key Feldern
  - Validierung gegen beide Endpunkte (`groceries.list` + `calendar.listItems`)
  - Deutsche Übersetzungen für alle neuen Texte
- ⏰ **Wochenplaner: vergangene Mahlzeiten ausblenden** – Heute werden Mahlzeiten automatisch ausgeblendet, wenn ihr Zeitfenster um mehr als 30 Minuten überschritten ist
  - Standard-Zeiten: Frühstück 08:00, Mittagessen 12:00, Snack 15:00, Abendessen 18:00
  - Gilt für alle `NorishMealSensor`-Entities und den `NorishWeekPlannerSensor`
  - Zukünftige Tage sind nicht betroffen – dort bleiben alle Mahlzeiten sichtbar
  - Verwendet `dt_util.now()` mit korrekter HA-Zeitzone

### Changed
- ⚡ **Polling-Intervall** von 5 Minuten auf **2 Minuten** reduziert – die Integration synchronisiert sich häufiger mit der Norish API
- 🔁 **Verbindungsresilienz** verbessert – bei unterbrochenen Verbindungen (`ServerDisconnectedError`, `ClientConnectorError`) wird jetzt automatisch mit exponentiellem Backoff wiederholt, statt direkt zu scheitern

### Fixed
- 🐛 `ConfigEntryAuthFailed` wurde durch einen zu breiten `except Exception`-Block verschluckt – jetzt korrekt weitergegeben, damit HA die Re-Auth-Benachrichtigung anzeigt

## [1.4.0] - 2026-03-23

### Added
- 🔄 **GitHub Actions CI/CD** - Automatische Validierung bei jedem Push
  - HACS-Validierung (`hacs/action`)
  - Home Assistant hassfest-Validierung
  - Läuft bei Push auf `main`/`master` und bei Pull Requests
- 📋 **HACS Default Repository Vorbereitung**
  - `codeowners` in manifest.json gesetzt (`@Caps3n`)
  - `integration_type: "service"` hinzugefügt (HA 2024.x Anforderung)
  - Minimum HA-Version auf `2024.6.0` gesetzt
  - `media_player` zu `hacs.json` domains hinzugefügt

### Changed
- ⬆️ **Home Assistant Kompatibilität** auf HA 2024.6.0+ aktualisiert
- 🧹 **Code-Qualität** – Alle Plattform-Dateien mit modernen Typ-Annotationen
  - `from __future__ import annotations` in allen Plattform-Dateien
  - `async_setup_entry` mit vollständigen Typ-Signaturen (`HomeAssistant`, `ConfigEntry`, `AddEntitiesCallback`)
  - `Dict`, `List`, `Optional` von `typing` durch native Python-Typen ersetzt
- 🔧 **`__init__.py`** verbessert
  - `ConfigEntryNotReady` wird jetzt korrekt weitergegeben
  - `entry.async_on_unload` für sauberes Entladen bei Options-Änderungen
  - Verbesserte Log-Messages
- 🔧 **`config_flow.py`** modernisiert
  - Rückgabetyp `FlowResult` hinzugefügt
  - `aiohttp` Timeout explizit gesetzt
  - `User-Agent` Header in Validierung hinzugefügt
- 📦 **`requirements`** – `aiohttp>=3.9.0` mit Mindestversion spezifiziert

## [1.3.0] - 2026-01-29

### Added
- 📅 **Wochenplan-Sensor** - Komplette Wochenübersicht
  - Neuer Sensor `sensor.norish_wochenplan`
  - Zeigt Planung für die nächsten 7 Tage
  - Attribute für jeden Tag (Mo, Di, Mi, Do, Fr, Sa, So)
  - Alle Mahlzeiten pro Tag mit Bildern/Videos
  - Status: "X Tage geplant" oder "Woche vollständig geplant"
- 🎨 **Wochenplan Dashboard-Vorlagen** (WOCHENPLAN_DASHBOARDS.md)
  - Grid-Layout für Desktop (7 Tage nebeneinander)
  - Horizontal Scroll für Mobile (Swipe Card)
  - Kompakte Listen-Ansicht
  - Premium-Version mit allen Features
  - Heute hervorgehoben
  - Weekend-Markierung
- 📊 **Wochenplan-Attribute**
  - `week_data`: Array mit allen 7 Tagen
  - `mo`, `di`, `mi`, `do`, `fr`, `sa`, `so`: Tag-spezifische Daten
  - `days_planned`: Anzahl geplanter Tage
  - `total_meals`: Gesamtzahl Mahlzeiten der Woche
  - Pro Tag: `date`, `weekday`, `meals`, `is_today`, `is_weekend`

### Changed
- Sensor-Setup erweitert um Wochenplan-Sensor
- Kalender-Daten werden für 7 Tage ausgewertet
- Verbesserte Datums-Verarbeitung

### Technical
- Neue Klasse `NorishWeekPlannerSensor` in sensor.py
- 7-Tage-Loop für Datenextraktion
- Deutsche Wochentage
- Meal-Type Sortierung (Breakfast → Lunch → Dinner → Snack)

## [1.2.0] - 2026-01-29

### Added
- 🎬 **Media Player Entities für Video-Loop-Wiedergabe**
  - Neue Platform: `media_player`
  - 4 neue Entities: Frühstück, Mittagessen, Abendessen, Snack Videos
  - Videos werden automatisch in Endlosschleife abgespielt
  - Stumm (muted) und autoplay wie in Norish App
  - State: PLAYING wenn Video vorhanden, OFF wenn kein Video
- 📺 **Video-Loop Dashboard-Support**
  - Videos genau wie in Norish App angezeigt
  - HTML `<video>` Tag mit loop, autoplay, muted, playsinline
  - Automatische URL-Konvertierung (relative → absolute Pfade)
  - `video_source` Attribut mit vollständiger URL
- 📚 **VIDEO_LOOP_GUIDE.md** - Komplette Anleitung
  - Dashboard-Beispiele für Video-Loop
  - HTML-Card Konfigurationen
  - Grid-Layouts mit mehreren Videos
  - Performance-Tipps
  - Troubleshooting

### Changed
- Media Player kombiniert automatisch relative Pfade mit Server-URL
- `video_source` Attribut enthält immer vollständige URL
- Thumbnails werden als Vorschaubilder verwendet

### Technical
- Neue Datei: `media_player.py`
- Media Player State-Management
- Automatische URL-Normalisierung
- Support für relative und absolute Video-Pfade

## [1.2.0] - 2026-01-29

### Added
- 🔄 **Loop-Video Unterstützung** - Videos wie in Norish App
  - Automatische Konvertierung relativer URLs zu absoluten URLs
  - Bilder, Videos und Thumbnails werden automatisch korrigiert
  - Support für lokale Norish-Video-URLs (z.B. `/recipes/xxx/video.mp4`)
  - Dashboard-Vorlagen für autoplay + loop + muted Videos
  - HTML5 Video-Player Konfigurationen
- 📚 Umfassende Loop-Video-Dokumentation (LOOP_VIDEOS.md)
  - 5 verschiedene Implementierungs-Methoden
  - Markdown Card Lösungen (kein Custom Component nötig)
  - Webpage Card Lösungen
  - Picture Elements Card Beispiele
  - Vollständige Dashboard-Vorlagen
  - Grid-Layout mit allen Mahlzeiten
- 🎨 Norish-Style Video-Overlays mit Gradient
- 📱 Mobile-optimierte Video-Layouts

### Changed
- Sensor konvertiert jetzt automatisch relative URLs (`/recipes/...`) zu absoluten URLs
- Bild-URLs werden ebenfalls bei Bedarf konvertiert
- Video-Thumbnail-URLs werden bei Bedarf konvertiert
- Verbesserte URL-Verarbeitung mit Base-URL vom Coordinator

### Fixed
- Relative Video-URLs werden jetzt korrekt aufgelöst
- Relative Bild-URLs werden jetzt korrekt aufgelöst
- Video-Thumbnails mit relativen Pfaden funktionieren jetzt

### Technical
- Neue URL-Konvertierungslogik in `sensor.py`
- Base-URL Nutzung vom Coordinator API-Data
- Debug-Logging für URL-Konvertierungen

## [1.1.0] - 2026-01-29

### Added
- 🎥 **Video-Unterstützung für Rezepte**
  - Automatische Erkennung von YouTube-URLs mit ID-Extraktion
  - Automatische Erkennung von Vimeo-URLs  
  - Unterstützung für direkte Video-URLs (MP4, WebM, etc.)
  - Automatische YouTube-Thumbnail-Extraktion
  - Video-Typ-Erkennung (youtube, vimeo, direct)
  - Neue Sensor-Attribute: 
    - `video_url` - Direkte Video-URL
    - `video_type` - Art des Videos (youtube/vimeo/direct)
    - `youtube_id` - YouTube Video-ID (falls YouTube)
    - `youtube_embed_url` - Fertige Embed-URL für YouTube
    - `video_thumbnail` - Thumbnail-URL für das Video
  - Neue Status-Flags: `has_video`, `has_image`
  - `videos` Array mit allen Videos des Tages
- 📚 Umfassende Video-Dokumentation (VIDEO_SUPPORT.md)
- 🎨 Dashboard-Beispiele für Video-Integration
  - YouTube-Embeds
  - Video-Links mit Thumbnails
  - Play-Button Overlays
  - Mobile-optimierte Layouts
- ⚡ Intelligente Video-Metadaten-Extraktion via Regex

### Changed
- Sensor `entity_picture` nutzt jetzt Video-Thumbnails als Fallback wenn kein Bild vorhanden
- Erweiterte API-Feldnamen-Unterstützung: 
  - Videos: `video`, `videoUrl`, `video_url`, `youtubeUrl`, `youtube_url`
  - Thumbnails: `videoThumbnail`, `video_thumbnail`
- Verbesserte Rezept-Daten-Extraktion mit mehr optionalen Feldern

### Technical
- Neue Funktion `_extract_video_info()` für Video-Metadaten-Extraktion
- Regex-basierte URL-Erkennung für YouTube und Vimeo
- Erweiterte Attribute-Struktur für Multimedia-Inhalte
- YouTube Thumbnail-URL automatisch generiert wenn nicht vorhanden

## [1.0.1] - 2026-01-29

### Fixed
- Fixed `TypeError: ClientSession() got multiple values for keyword argument 'connector'`
  - Removed manual connector creation in `__init__.py`
  - Now using Home Assistant's built-in `async_get_clientsession()`
  - Headers are now passed explicitly in coordinator requests
- Improved session management and header handling

### Changed
- Session is now managed by Home Assistant's session pool
- Headers are stored in `api_data` dict and passed per request
- More efficient resource usage

## [1.0.0] - 2026-01-29

### Added
- Initial release of Norish Home Assistant integration
- Meal planning calendar integration
- Multiple meal sensors (breakfast, lunch, dinner, snack)
- Recipe image display support via `entity_picture`
- Camera entities for alternative image display
- Shopping list integration with per-store organization
- Multilingual support (German, English, French, Spanish, Italian)
- Comprehensive error handling and retry logic
- API credential validation in config flow
- Configurable update intervals
- Options flow for customizing displayed meal types

### Features
- **Calendar**: View weekly meal plans in Home Assistant calendar
- **Sensors**: 
  - All meals sensor showing daily overview
  - Individual sensors for each meal type
  - State attributes with cooking time, servings, descriptions
  - Automatic image display from recipe data
- **Todo Lists**: 
  - Manage grocery items
  - Organize by store
  - Create, update, and delete items
- **Cameras**: 
  - Alternative method for displaying recipe images
  - Cached image loading for better performance
  - Per-meal-type camera entities
- **Configuration**:
  - Easy setup through UI
  - API key validation
  - Connection testing
  - Customizable options

### Technical Improvements
- Exponential backoff retry logic for API calls
- 10-second timeout on all HTTP requests
- Defensive data validation
- Proper error messages and logging
- Type hints throughout codebase
- Centralized constants
- Connection pooling for HTTP sessions
- Memory-efficient caching

### Documentation
- Comprehensive README in multiple languages
- Dashboard examples and templates
- API requirements documentation
- Troubleshooting guide
- Installation instructions for HACS and manual installation

### Translations
- 🇩🇪 German (Deutsch)
- 🇬🇧 English
- 🇫🇷 French (Français)
- 🇪🇸 Spanish (Español)
- 🇮🇹 Italian (Italiano)

## [Unreleased]

### Planned Features
- Recipe nutrition information display
- Meal preparation notifications
- Recipe scaling based on servings
- Ingredient substitution suggestions
- Weekly meal plan automation
- Recipe favorites and ratings
- Custom meal categories
- Export meal plans to PDF
- Integration with other recipe platforms

---

For detailed upgrade instructions and migration guides, see [UPGRADE.md](UPGRADE.md).

For reporting bugs or requesting features, visit our [issue tracker](https://github.com/Caps3n/hass-norish/issues).
