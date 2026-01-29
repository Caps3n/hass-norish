# 🚀 GitHub Upload Anleitung

## Schritt-für-Schritt Anleitung zum Upload auf GitHub

### 📋 Voraussetzungen

- GitHub Account
- Git installiert auf deinem Computer
- Repository erstellt: `hass-norish`

---

## 🎯 Methode 1: GitHub Web Interface (Einfach)

### Schritt 1: Repository erstellen

1. Gehe zu https://github.com
2. Klicke auf **"+"** → **"New repository"**
3. Repository Name: `hass-norish`
4. Description: `Home Assistant integration for Norish - meal planning and recipes`
5. ✅ Public
6. ✅ Add README (wird überschrieben)
7. License: MIT
8. Klicke **"Create repository"**

### Schritt 2: Dateien hochladen

1. Im Repository klicke **"Add file"** → **"Upload files"**
2. Ziehe alle Dateien aus `norish_v1.3.0_complete/` rein:
   ```
   - README.md
   - LICENSE
   - CHANGELOG.md
   - custom_components/
   - alle anderen Dateien
   ```
3. Commit message: `Initial release v1.3.0 - Complete integration with week planner and video support`
4. Klicke **"Commit changes"**

### Schritt 3: Release erstellen

1. Klicke auf **"Releases"** (rechte Sidebar)
2. Klicke **"Create a new release"**
3. **Tag version**: `v1.3.0`
4. **Release title**: `v1.3.0 - Week Planner & Video Support`
5. **Description**: Kopiere Inhalt von `RELEASE_NOTES.md`
6. **Attach binaries**:
   - `norish_v1.3.0.zip`
   - `norish_v1.3.0.tar.gz`
7. Klicke **"Publish release"**

✅ **Fertig!**

---

## 💻 Methode 2: Git Command Line (Fortgeschritten)

### Schritt 1: Repository lokal erstellen

```bash
# In deinem lokalen Ordner
cd /pfad/zu/norish_v1.3.0_complete

# Git initialisieren
git init

# Remote hinzufügen (ersetze USERNAME mit deinem GitHub Username)
git remote add origin https://github.com/USERNAME/hass-norish.git
```

### Schritt 2: Dateien hinzufügen und committen

```bash
# Alle Dateien hinzufügen
git add .

# Status prüfen
git status

# Commit erstellen
git commit -m "Initial release v1.3.0

- Complete Norish integration
- Week planner with 7-day overview
- Video support (YouTube, Vimeo, direct)
- Loop video playback
- 5 meal sensors
- Calendar integration
- Shopping lists
- Multilingual support (DE, EN, ES, FR, IT)
- Comprehensive documentation"

# Branch zu main ändern (falls nötig)
git branch -M main

# Push to GitHub
git push -u origin main
```

### Schritt 3: Release erstellen

```bash
# Tag erstellen
git tag -a v1.3.0 -m "Release v1.3.0 - Week Planner & Video Support"

# Tag pushen
git push origin v1.3.0
```

Dann auf GitHub:
1. Gehe zu Releases
2. Tag `v1.3.0` sollte erscheinen
3. Klicke **"Create release from tag"**
4. Füge ZIP/TAR.GZ Dateien hinzu
5. Publish!

---

## 📁 Datei-Struktur für Upload

Stelle sicher, dass dein Repository diese Struktur hat:

```
hass-norish/
├── README.md                          # Hauptdokumentation (EN)
├── README_DE.md                       # Deutsche Dokumentation
├── CHANGELOG.md                       # Versionshistorie
├── LICENSE                            # MIT Lizenz
├── INSTALLATION.md                    # Installationsanleitung
├── VIDEO_SUPPORT.md                   # Video-Dokumentation
├── LOOP_VIDEOS.md                     # Loop-Video Guide
├── WOCHENPLAN_DASHBOARDS.md          # Wochenplan Dashboards
├── DASHBOARD_EXAMPLES.yaml            # Dashboard-Vorlagen
├── hacs.json                          # HACS-Konfiguration
├── .gitignore                         # Git Ignore
│
└── custom_components/
    └── norish/
        ├── __init__.py
        ├── config_flow.py
        ├── const.py
        ├── coordinator.py
        ├── sensor.py
        ├── calendar.py
        ├── todo.py
        ├── camera.py
        ├── manifest.json
        ├── strings.json
        └── translations/
            ├── de.json
            ├── en.json
            ├── es.json
            ├── fr.json
            └── it.json
```

---

## 🏷️ HACS Submission (Optional)

Nachdem das Repository öffentlich ist:

### Schritt 1: HACS.json prüfen

Stelle sicher, dass `hacs.json` existiert:

```json
{
  "name": "Norish Recipes & Meal Planning",
  "render_readme": true,
  "domains": ["sensor", "calendar", "todo", "camera"],
  "iot_class": "Cloud Polling",
  "homeassistant": "2024.1.0"
}
```

### Schritt 2: HACS Default Repository

1. Fork https://github.com/hacs/default
2. Bearbeite `integration` Datei
3. Füge hinzu:
   ```json
   {
     "name": "Norish Recipes & Meal Planning",
     "domain": "norish",
     "description": "Complete integration for Norish meal planning with week planner and video support"
   }
   ```
4. Pull Request erstellen
5. Warten auf Review

---

## ✅ Checkliste vor dem Upload

- [ ] Alle Dateien in `custom_components/norish/` vorhanden
- [ ] README.md ist auf Englisch
- [ ] LICENSE Datei vorhanden (MIT)
- [ ] CHANGELOG.md aktuell
- [ ] Version in `manifest.json` ist `1.3.0`
- [ ] Keine sensiblen Daten (API Keys, URLs) im Code
- [ ] `.gitignore` vorhanden
- [ ] ZIP und TAR.GZ Dateien erstellt für Release
- [ ] Release Notes vorbereitet

---

## 🔐 .gitignore Beispiel

Erstelle `.gitignore` im Root:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/

# Virtual Environment
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/

# Home Assistant
*.log
*.db
*.db-shm
*.db-wal

# Temporary
*.tmp
*.bak
```

---

## 📸 Repository Settings

Nach dem Upload, konfiguriere:

### About Section
1. Klicke auf ⚙️ neben "About"
2. **Description**: `Complete Home Assistant integration for Norish - meal planning, recipes, week planner, and video support`
3. **Website**: URL zu deiner Norish Instanz oder Docs
4. **Topics**:
   - `home-assistant`
   - `hacs`
   - `norish`
   - `meal-planning`
   - `recipes`
   - `integration`
   - `homeassistant-integration`

### Repository Topics
Füge Tags hinzu für bessere Auffindbarkeit!

---

## 📢 Nach dem Upload

### 1. Teste die Installation

```bash
# Via HACS
# Füge Custom Repository hinzu
# Installiere
# Prüfe ob alles funktioniert
```

### 2. Dokumentation verlinken

Stelle sicher, dass alle Links in der README funktionieren:
- Screenshots (erstelle `docs/screenshots/` Ordner)
- Wiki-Links
- Issue-Links

### 3. Community informieren

- Post im Home Assistant Community Forum
- Reddit r/homeassistant
- Discord

---

## 🎉 Geschafft!

Dein Repository ist jetzt live unter:
`https://github.com/USERNAME/hass-norish`

Release ist verfügbar unter:
`https://github.com/USERNAME/hass-norish/releases/tag/v1.3.0`

Installation via HACS:
`https://github.com/USERNAME/hass-norish`

---

## 💡 Tipps

1. **GitHub Actions** - Erstelle automatische Tests
2. **Issues Template** - Erstelle Templates für Bug Reports
3. **PR Template** - Template für Pull Requests
4. **Wiki** - Erweiterte Dokumentation
5. **GitHub Pages** - Schöne Dokumentations-Website

---

## 🆘 Probleme?

**"Permission denied"**
→ Prüfe Git Credentials und Repository-Rechte

**"Files too large"**
→ Keine großen Binärdateien committen
→ Nutze Git LFS falls nötig

**"Merge conflict"**
→ Pull erst, dann push
→ `git pull origin main`

---

**Viel Erfolg! 🚀**

Bei Fragen: GitHub Issue erstellen oder Community fragen!
