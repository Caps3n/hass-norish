# Release v1.3.0 - Week Planner & Video Support

## 🎉 Major Update: Complete Week Planner with Images & Videos!

This release transforms the Norish integration with comprehensive week planning, video support, and loop playback just like the Norish app!

---

## ✨ New Features

### 📅 Week Planner Sensor

New sensor `sensor.norish_wochenplan` provides a complete 7-day overview:

- **7-day meal planning** with all meals per day
- **Images and videos** for each meal
- **Today highlighted** with special styling
- **Weekend detection** for better planning
- **German weekday names**
- **Individual day access** via attributes (mo, di, mi, do, fr, sa, so)

**Attributes:**
```yaml
sensor.norish_wochenplan:
  state: "5 days planned"
  attributes:
    days_planned: 5
    total_meals: 15
    videos_count: 8
    images_count: 12
    
    mo:  # Monday data
    di:  # Tuesday data
    mi:  # Wednesday data
    # ... etc
    
    week_data: [complete array]
```

### 🎥 Video Support

Complete video integration:

- **YouTube** - Automatic ID extraction, embed URLs, thumbnails
- **Vimeo** - Automatic detection
- **Direct videos** - MP4, WebM, and more
- **Loop playback** - Autoplay, muted, continuous (exactly like Norish app)

**Video attributes in sensors:**
```yaml
sensor.norish_lunch:
  attributes:
    video_url: "https://youtube.com/watch?v=ABC123"
    video_type: "youtube"
    youtube_id: "ABC123"
    youtube_embed_url: "https://youtube.com/embed/ABC123"
    video_thumbnail: "https://..."
    has_video: true
    has_image: true
```

### 🔄 Automatic URL Conversion

Relative URLs are now automatically converted to absolute URLs:

```
API returns: /recipes/ff8d4877.../video.mp4
          ↓
Sensor has: https://norish.example.com/recipes/ff8d4877.../video.mp4
```

Works for:
- ✅ Video URLs
- ✅ Image URLs
- ✅ Video thumbnails

### 🎨 Dashboard Templates

New comprehensive dashboard documentation:

- **WOCHENPLAN_DASHBOARDS.md** - Week planner layouts
  - Grid layout for desktop
  - Horizontal scroll for mobile
  - Compact list view
  - Premium version with all features

- **LOOP_VIDEOS.md** - Loop video integration
  - 5 implementation methods
  - Markdown card solutions
  - Webpage card examples
  - Mobile-optimized layouts

- **VIDEO_SUPPORT.md** - Complete video guide
  - YouTube embed examples
  - Vimeo integration
  - Direct video playback
  - Troubleshooting

---

## 🔧 Changes from Original Version

### Before (Original)
```python
# Basic sensors only
- sensor.norish_meals_today
- Basic image support
- No video support
- No week planning
```

### After (v1.3.0)
```python
# Complete feature set
- sensor.norish_meals_today
- sensor.norish_breakfast
- sensor.norish_lunch
- sensor.norish_dinner
- sensor.norish_snack
- sensor.norish_wochenplan  # NEW!

# Enhanced features
- Full image support
- Complete video support
- Loop video playback
- Week planner (7 days)
- Automatic URL conversion
- YouTube/Vimeo detection
```

---

## 📥 Installation

### New Installation

**Via HACS:**
1. Add custom repository: `https://github.com/Caps3n/hass-norish`
2. Install "Norish"
3. Restart Home Assistant
4. Add integration via UI

**Manual:**
1. Download `norish_v1.3.0.zip`
2. Extract to `/config/custom_components/`
3. Restart Home Assistant
4. Add integration via UI

### Upgrade from Original Version

**Important:** This is a complete rewrite with many improvements!

1. **Backup** your current configuration
2. **Remove** old integration (if installed)
3. **Install** v1.3.0 via HACS or manually
4. **Restart** Home Assistant
5. **Reconfigure** integration (Settings → Devices & Services → Add Norish)

**What carries over:**
- ✅ Same API endpoints
- ✅ Same API key
- ✅ Same server URL
- ✅ Backward compatible with your Norish instance

**What's new:**
- ✅ More sensors (breakfast, lunch, dinner, snack separated)
- ✅ Week planner sensor
- ✅ Video support
- ✅ Better error handling
- ✅ Automatic URL conversion

---

## 🎨 Quick Dashboard Examples

### Simple Loop Video

```yaml
type: markdown
content: |
  <video autoplay loop muted playsinline 
         style="width: 100%; height: 400px; object-fit: cover; border-radius: 12px;">
    <source src="{{ state_attr('sensor.norish_lunch', 'video_url') }}" type="video/mp4">
  </video>
```

### Week Overview

```yaml
type: markdown
content: |
  {% set week = state_attr('sensor.norish_wochenplan', 'week_data') %}
  {% for day in week %}
    <div style="background: {% if day.is_today %}#ff6b6b{% else %}#2a2a2a{% endif %}; 
                border-radius: 8px; padding: 15px; margin: 10px 0;">
      <strong style="color: white;">{{ day.weekday }}</strong>
      <!-- Loop through meals with videos/images -->
    </div>
  {% endfor %}
```

### Today's Meals Grid

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

---

## 🐛 Bug Fixes

### v1.0.1
- Fixed `TypeError: ClientSession() got multiple values for keyword argument 'connector'`
- Improved session management
- Headers now passed per request

### v1.1.0
- Added video URL support
- YouTube/Vimeo detection
- Video metadata extraction

### v1.2.0
- Loop video implementation
- Relative URL conversion
- Video thumbnail support

### v1.3.0
- Week planner sensor
- 7-day data extraction
- Improved date processing

---

## 📊 Technical Improvements

### Performance
- ✅ Update interval: 5 minutes (reduced from 30 seconds)
- ✅ Store cache: 24 hours
- ✅ Connection pooling
- ✅ Retry logic with exponential backoff
- ✅ 10-second timeout on all requests

### Code Quality
- ✅ Type hints throughout
- ✅ Defensive data validation
- ✅ Specific exception handling
- ✅ Comprehensive logging
- ✅ Constants extracted

### Reliability
- ✅ API validation during setup
- ✅ Automatic retry on failure
- ✅ Graceful degradation
- ✅ Better error messages

---

## 🌍 Multilingual Support

Fully translated in:
- 🇩🇪 German (Deutsch)
- 🇬🇧 English
- 🇫🇷 French (Français)
- 🇪🇸 Spanish (Español)
- 🇮🇹 Italian (Italiano)

All UI elements, entity names, and error messages are localized!

---

## 📚 Documentation

### New Files
- `WOCHENPLAN_DASHBOARDS.md` - Week planner dashboard examples
- `LOOP_VIDEOS.md` - Loop video implementation guide
- `VIDEO_SUPPORT.md` - Complete video integration docs
- `INSTALLATION.md` - Detailed installation guide
- `CHANGELOG.md` - Complete version history

### Updated Files
- `README.md` - Complete overview
- `sensor.py` - Week planner sensor added
- `manifest.json` - Version 1.3.0

---

## 🎯 Migration Guide

### From Original Version → v1.3.0

**Step 1: Install v1.3.0**
- Via HACS or manual installation
- Restart Home Assistant

**Step 2: Remove Old Integration (if exists)**
- Settings → Devices & Services
- Find old Norish integration
- Click Remove

**Step 3: Add New Integration**
- Settings → Devices & Services → Add Integration
- Search "Norish"
- Enter same server URL and API key
- Done!

**Step 4: Update Dashboards**
- New sensor names might differ
- Use new features (videos, week planner)
- See dashboard examples

**No Data Loss:**
- ✅ All data comes from Norish server
- ✅ Same API endpoints
- ✅ Just reconnect and it works!

---

## 📦 What's Included

### Integration Files
```
custom_components/norish/
├── __init__.py              # Main setup
├── config_flow.py           # UI configuration
├── const.py                 # Constants
├── coordinator.py           # Data coordinator
├── sensor.py                # Sensors (including week planner!)
├── calendar.py              # Calendar integration
├── todo.py                  # Shopping lists
├── camera.py                # Camera entities
├── manifest.json            # Metadata
├── strings.json             # English translations
└── translations/            # Multilingual support
    ├── de.json              # German
    ├── en.json              # English
    ├── es.json              # Spanish
    ├── fr.json              # French
    └── it.json              # Italian
```

### Documentation Files
- README.md
- CHANGELOG.md
- LICENSE
- INSTALLATION.md
- VIDEO_SUPPORT.md
- LOOP_VIDEOS.md
- WOCHENPLAN_DASHBOARDS.md
- DASHBOARD_EXAMPLES.yaml

---

## 🚀 Next Steps

After installation:

1. ✅ Configure integration
2. 📖 Read documentation
3. 🎨 Create dashboards
4. 🎬 Enjoy videos!
5. 📅 Plan your week!

---

## 🙏 Support

- 🐛 [Report a Bug](https://github.com/Caps3n/hass-norish/issues)
- 💡 [Request a Feature](https://github.com/Caps3n/hass-norish/issues)
- 💬 [Discussions](https://github.com/Caps3n/hass-norish/discussions)
- ⭐ [Star on GitHub](https://github.com/Caps3n/hass-norish)

---

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

---

**Thank you for using Norish Home Assistant Integration!** 🎉

Made with ❤️ by [@Caps3n](https://github.com/Caps3n)
