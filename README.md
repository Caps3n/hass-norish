# Norish Home Assistant Integration

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/Caps3n/hass-norish/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Complete Home Assistant integration for [Norish](https://github.com/norish-recipes/norish) - the open-source recipe and meal planning system.

## ✨ Features

### 🍳 Meal Sensors
- **5 sensors** for different meal types (All, Breakfast, Lunch, Dinner, Snack)
- Automatic **image display** from recipes
- **Video support** with autoplay, loop, and muted playback
- Recipe metadata: cooking time, servings, description

### 📅 Week Planner
- **7-day overview** sensor with all meals
- Displays images and videos for each day
- Highlights today and weekends
- German weekday names
- Access individual days via attributes (mo, di, mi, do, fr, sa, so)

### 📆 Calendar Integration
- Weekly meal calendar
- Different meal types with custom times
- Full event details

### 🛒 Shopping Lists
- Todo lists organized by store
- Create, update, and delete items
- Quantities and units support

### 🎥 Video Support
- **YouTube** - automatic ID extraction + embed URLs
- **Vimeo** - automatic detection
- **Direct videos** - MP4, WebM, etc.
- **Loop videos** - autoplay, muted, continuous playback (like Norish app)
- Automatic thumbnail extraction

### 📷 Camera Entities (Optional)
- Alternative image display using camera platform
- Cached image loading

### 🌍 Multilingual
- **5 languages**: German, English, French, Spanish, Italian
- Automatic language detection
- Translations for UI, entities, error messages

## 📸 Screenshots

### Week Planner with Videos
![Week Planner](docs/screenshots/week_planner.png)

### Meal Sensors with Images
![Meal Sensors](docs/screenshots/meal_sensors.png)

### Loop Videos
![Loop Videos](docs/screenshots/loop_videos.png)

## 🚀 Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the **three dots** (⋮) in the top right
4. Select **Custom repositories**
5. Add repository: `https://github.com/Caps3n/hass-norish`
6. Category: `Integration`
7. Click **Add**
8. Search for "Norish" in HACS
9. Click **Install**
10. Restart Home Assistant

### Option 2: Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/Caps3n/hass-norish/releases)
2. Extract the `norish` folder to your `custom_components` directory
3. Restart Home Assistant

## ⚙️ Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Norish"
4. Enter your configuration:
   - **Server URL**: e.g., `https://norish.yourdomain.com`
   - **API Key**: Your Norish API key
5. Click **Submit**

### Options

After installation, configure which meal types to display:
- ☑ Show breakfast
- ☑ Show lunch
- ☑ Show dinner
- ☑ Show snacks

## 📊 Entities

### Sensors

- `sensor.norish_meals_today` - All meals for today
- `sensor.norish_breakfast` - Breakfast
- `sensor.norish_lunch` - Lunch
- `sensor.norish_dinner` - Dinner
- `sensor.norish_snack` - Snacks
- `sensor.norish_wochenplan` - 7-day week planner

Each sensor includes:
- Current meal name as state
- Recipe image (if available)
- Video URL (if available)
- Cooking time, servings, description

### Calendar

- `calendar.norish_meal_plan` - Weekly meal calendar

### Todo Lists

- `todo.norish_unsorted` - Unsorted grocery items
- `todo.norish_<store_name>` - Grocery list per store

### Cameras (Optional)

- `camera.norish_breakfast_image` - Breakfast recipe image
- `camera.norish_lunch_image` - Lunch recipe image
- `camera.norish_dinner_image` - Dinner recipe image
- `camera.norish_snack_image` - Snack recipe image

## 🎨 Dashboard Examples

### Simple Picture Entity Card

```yaml
type: picture-entity
entity: sensor.norish_lunch
show_name: true
show_state: true
```

### Loop Video (Norish Style)

```yaml
type: markdown
content: |
  <video autoplay loop muted playsinline 
         style="width: 100%; height: 400px; object-fit: cover; border-radius: 12px;">
    <source src="{{ state_attr('sensor.norish_lunch', 'video_url') }}" type="video/mp4">
  </video>
```

### Week Planner Grid

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

### Complete Week Overview

```yaml
type: markdown
content: |
  {% set week = state_attr('sensor.norish_wochenplan', 'week_data') %}
  {% for day in week %}
    <div style="background: {% if day.is_today %}#ff6b6b{% else %}#2a2a2a{% endif %}; 
                border-radius: 8px; padding: 15px; margin: 10px 0;">
      <strong style="color: white;">{{ day.weekday }} • {{ day.date_formatted }}</strong>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 5px; margin-top: 10px;">
      {% for meal in day.meals %}
        <div style="position: relative; height: 80px; border-radius: 6px; overflow: hidden;">
          {% if meal.video %}
            <video autoplay loop muted playsinline style="width: 100%; height: 100%; object-fit: cover;">
              <source src="{{ meal.video }}" type="video/mp4">
            </video>
          {% elif meal.image %}
            <img src="{{ meal.image }}" style="width: 100%; height: 100%; object-fit: cover;">
          {% endif %}
        </div>
      {% endfor %}
      </div>
    </div>
  {% endfor %}
```

More examples in [DASHBOARD_EXAMPLES.yaml](DASHBOARD_EXAMPLES.yaml)

## 📡 API Requirements

### Calendar Endpoint

Your Norish API must return data in this format:

```json
{
  "date": "2026-01-29T00:00:00.000Z",
  "type": "LUNCH",
  "recipe": {
    "id": "123",
    "name": "Spaghetti Carbonara",
    "image": "https://example.com/images/carbonara.jpg",
    "video": "/recipes/ff8d4877.../video.mp4",
    "description": "Classic Italian pasta dish",
    "cookingTime": 30,
    "servings": 4
  }
}
```

**Supported field names:**
- Images: `image`, `imageUrl`, `picture`, `photo`, `thumbnail`
- Videos: `video`, `videoUrl`, `video_url`, `youtubeUrl`, `youtube_url`
- Video thumbnails: `videoThumbnail`, `video_thumbnail`

**Relative URLs** (like `/recipes/...`) are automatically converted to absolute URLs.

### Groceries Endpoint

```json
{
  "id": "456",
  "name": "Tomatoes",
  "amount": 2,
  "unit": "kg",
  "isDone": false,
  "storeId": "1"
}
```

## 🎬 Video Features

### Supported Formats

- ✅ **YouTube** - Automatic ID extraction, embed URLs, thumbnails
- ✅ **Vimeo** - Automatic detection
- ✅ **Direct URLs** - MP4, WebM, etc.
- ✅ **Loop playback** - Autoplay, muted, continuous (like Norish app)

### Video Attributes

```yaml
sensor.norish_lunch:
  attributes:
    video_url: "https://youtube.com/watch?v=..."
    video_type: "youtube"
    youtube_id: "ABC123"
    youtube_embed_url: "https://youtube.com/embed/ABC123"
    video_thumbnail: "https://..."
    has_video: true
```

See [VIDEO_SUPPORT.md](VIDEO_SUPPORT.md) for detailed documentation.

## 🗓️ Week Planner

The week planner sensor provides a 7-day overview:

```yaml
sensor.norish_wochenplan:
  state: "5 days planned"
  attributes:
    days_planned: 5
    total_meals: 15
    
    # Individual day access
    mo:  # Monday
      date: "2026-01-29"
      weekday: "Montag"
      is_today: true
      meals:
        - name: "Oatmeal"
          type: "BREAKFAST"
          image: "https://..."
          video: "https://..."
    
    di:  # Tuesday
    mi:  # Wednesday
    do:  # Thursday
    fr:  # Friday
    sa:  # Saturday
    so:  # Sunday
    
    # Complete week data
    week_data: [...]
```

See [WOCHENPLAN_DASHBOARDS.md](WOCHENPLAN_DASHBOARDS.md) for dashboard examples.

## 🔧 Troubleshooting

### No images displayed

1. Check if your API returns image URLs
2. Verify image URLs are accessible
3. Check logs: `grep -i norish /config/home-assistant.log`

### Videos not playing

1. Ensure `muted` attribute is set (required for autoplay)
2. Check if video URL is accessible
3. For relative URLs: verify base URL is correct

### Connection errors

1. Verify server URL is correct
2. Check API key
3. Ensure Home Assistant can reach your Norish server
4. Check firewall rules

### Enable debug logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.norish: debug
```

## 🆕 What's New in v1.3.0

### Added
- 📅 **Week Planner Sensor** - 7-day overview with images/videos
- 🎥 **Loop Video Support** - Videos play like in Norish app
- 🔄 **Automatic URL Conversion** - Relative URLs converted to absolute
- 🎨 **Week Dashboard Templates** - Multiple layout options
- 📊 **Week Statistics** - Days planned, total meals, video/image counts

### Changed
- Sensor setup extended with week planner
- Calendar data evaluated for 7 days
- Improved date processing

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## 📚 Documentation

- [VIDEO_SUPPORT.md](VIDEO_SUPPORT.md) - Video integration guide
- [LOOP_VIDEOS.md](LOOP_VIDEOS.md) - Loop video implementation
- [WOCHENPLAN_DASHBOARDS.md](WOCHENPLAN_DASHBOARDS.md) - Week planner dashboards
- [DASHBOARD_EXAMPLES.yaml](DASHBOARD_EXAMPLES.yaml) - Dashboard templates
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [INSTALLATION.md](INSTALLATION.md) - Detailed installation guide

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

- Created by [@Caps3n](https://github.com/Caps3n)
- Built for [Norish](https://github.com/norish-recipes/norish)
- Made with ❤️ for the Home Assistant community

## 🔗 Links

- [Norish Repository](https://github.com/norish-recipes/norish)
- [Home Assistant](https://www.home-assistant.io/)
- [HACS](https://hacs.xyz/)
- [Report a Bug](https://github.com/Caps3n/hass-norish/issues)
- [Request a Feature](https://github.com/Caps3n/hass-norish/issues)
- [Discussions](https://github.com/Caps3n/hass-norish/discussions)

---

Made with ❤️ for the Home Assistant community
