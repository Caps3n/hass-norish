# Norish Home Assistant Integration

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/Caps3n/hass-norish/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.6%2B-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Validate](https://github.com/Caps3n/hass-norish/actions/workflows/validate.yaml/badge.svg)](https://github.com/Caps3n/hass-norish/actions/workflows/validate.yaml)

A full-featured Home Assistant integration for [Norish](https://github.com/norish-recipes/norish) — the open-source recipe and meal planning app.

> Connects your Norish instance to Home Assistant, giving you meal sensors, a shopping list, a calendar, recipe images, and video support — all in one integration.

---

## ✨ Features

### 🍳 Meal Sensors
- **6 sensors**: All meals today, Breakfast, Lunch, Dinner, Snack, Week Planner
- Automatic **recipe image** display via `entity_picture`
- **Video support** — autoplay, loop, muted (just like in the Norish app)
- Attributes include recipe name, type, image URL, and recipe ID

### 📅 Week Planner Sensor
- 7-day overview of all planned meals
- Per-day attributes: `mo`, `tu`, `we`, `th`, `fr`, `sa`, `su`
- Highlights today and weekends
- Sorted by meal type (Breakfast → Lunch → Dinner → Snack)

### 📆 Calendar
- Native Home Assistant calendar entity
- One event per meal with correct time slots
- Full date-range support

### 🛒 Shopping List
- Native Home Assistant Todo list entity
- Displays items with quantity and unit
- Create, update, and delete support

### 📷 Camera Entities
- One camera entity per meal type (Breakfast, Lunch, Dinner, Snack)
- Locally cached images for fast display
- Fallback to remote image if cache is empty

### 🎬 Media Player Entities
- One media player per meal type
- Shows recipe video when available
- Compatible with dashboard `media-player` cards

### 🌍 Multilingual
- 5 languages: 🇩🇪 German · 🇬🇧 English · 🇫🇷 French · 🇪🇸 Spanish · 🇮🇹 Italian

---

## 📸 Screenshots

### Week Planner
![Week Planner](https://github.com/Caps3n/hass-norish/blob/main/images/week_planner.png?raw=true)

### Calendar
![Calendar](https://github.com/Caps3n/hass-norish/blob/main/images/calendar.png?raw=true)

### Todo / Shopping List
![Shopping List](https://github.com/Caps3n/hass-norish/blob/main/images/todo.png?raw=true)

---

## 🚀 Installation

### Option 1: HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Go to **Integrations**
3. Click the **⋮ menu** (top right) → **Custom repositories**
4. Add: `https://github.com/Caps3n/hass-norish` → Category: `Integration`
5. Search for **"Norish"** and click **Install**
6. Restart Home Assistant

### Option 2: Manual

1. Download the [latest release](https://github.com/Caps3n/hass-norish/releases)
2. Copy the `norish` folder into your `config/custom_components/` directory
3. Restart Home Assistant

---

## ⚙️ Configuration

1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration**
3. Search for **"Norish"**
4. Enter:
   - **Server URL** — e.g. `https://norish.yourdomain.com`
   - **API Key** — your Norish API key
5. Click **Submit**

---

## 📊 Entities

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.norish_meals_today` | All meals for today |
| `sensor.norish_breakfast` | Today's breakfast |
| `sensor.norish_lunch` | Today's lunch |
| `sensor.norish_dinner` | Today's dinner |
| `sensor.norish_snack` | Today's snack |
| `sensor.norish_week_planner` | 7-day meal overview |

Each sensor includes: meal name (state), `image_url`, `recipe_id`, `meal_count`, `meals`, `raw_data`.

### Calendar

| Entity | Description |
|--------|-------------|
| `calendar.norish_meal_plan` | Weekly meal calendar |

### Todo

| Entity | Description |
|--------|-------------|
| `todo.norish_shopping_list` | Grocery / shopping list |

### Cameras

| Entity | Description |
|--------|-------------|
| `camera.norish_breakfast_image` | Breakfast recipe image |
| `camera.norish_lunch_image` | Lunch recipe image |
| `camera.norish_dinner_image` | Dinner recipe image |
| `camera.norish_snack_image` | Snack recipe image |

### Media Players

| Entity | Description |
|--------|-------------|
| `media_player.norish_breakfast_video` | Breakfast recipe video |
| `media_player.norish_lunch_video` | Lunch recipe video |
| `media_player.norish_dinner_video` | Dinner recipe video |
| `media_player.norish_snack_video` | Snack recipe video |

---

## 🎨 Dashboard Examples

### Simple image card

```yaml
type: picture-entity
entity: sensor.norish_lunch
show_name: true
show_state: true
```

### Looping video (Norish style)

```yaml
type: markdown
content: |
  <video autoplay loop muted playsinline
         style="width:100%;height:400px;object-fit:cover;border-radius:12px;">
    <source src="{{ state_attr('sensor.norish_lunch', 'raw_data')[0]['image'] }}" type="video/mp4">
  </video>
```

### 2×2 meal grid

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

### Week overview (with today highlight)

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

More examples in [DASHBOARD_BEISPIELE.yaml](DASHBOARD_BEISPIELE.yaml)

---

## 🗓️ Week Planner Attributes

```yaml
sensor.norish_week_planner:
  state: "5 days planned"
  attributes:
    days_planned: 5
    total_meals: 14

    mo:
      date: "2026-03-23"
      weekday: "Monday"
      is_today: true
      is_weekend: false
      meals:
        - name: "Oatmeal"
          type: "BREAKFAST"
          image: "/local/norish_images/..."
          recipe_id: "abc123"
      meal_count: 1
      has_meals: true

    tu: { ... }
    we: { ... }
    # ...
    week_data: [...]
```

---

## 🔧 Troubleshooting

**No images displayed**
- Check if your Norish instance returns image URLs
- Verify the images are accessible from your Home Assistant host
- Check logs: `grep -i norish /config/home-assistant.log`

**Connection error on setup**
- Confirm the Server URL is reachable from Home Assistant
- Verify your API key is correct
- Check firewall / reverse proxy settings

**Enable debug logging**

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.norish: debug
```

---

## 🆕 What's New in v1.4.0

- **GitHub Actions CI** — automatic HACS and hassfest validation on every push
- **HA 2024.6+ compatibility** — modern type annotations, proper `async_setup_entry` signatures
- **Non-blocking I/O** — image caching now runs in an executor (no more event loop blocking)
- **`codeowners`** set in `manifest.json` (required for HACS default repository)
- **`integration_type: service`** added to `manifest.json`
- Code quality improvements across all platform files

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

---

## 📚 Documentation

- [CHANGELOG.md](CHANGELOG.md) — Version history
- [INSTALLATION.md](INSTALLATION.md) — Detailed installation guide
- [DASHBOARD_BEISPIELE.yaml](DASHBOARD_BEISPIELE.yaml) — Dashboard templates
- [WOCHENPLAN_DASHBOARDS.md](WOCHENPLAN_DASHBOARDS.md) — Week planner dashboard examples
- [VIDEO_SUPPORT.md](VIDEO_SUPPORT.md) — Video integration guide

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Open a pull request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Credits

- Created by [@Caps3n](https://github.com/Caps3n)
- Built for [Norish](https://github.com/norish-recipes/norish)
- Made with ❤️ for the Home Assistant community

## 🔗 Links

- [Norish App](https://github.com/norish-recipes/norish)
- [Home Assistant](https://www.home-assistant.io/)
- [HACS](https://hacs.xyz/)
- [Report a Bug](https://github.com/Caps3n/hass-norish/issues)
- [Request a Feature](https://github.com/Caps3n/hass-norish/issues)
