# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
