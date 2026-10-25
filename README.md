# Norish Home Assistant Integration

[![Version](https://img.shields.io/github/v/release/Caps3n/hass-norish?label=version&color=blue)](https://github.com/Caps3n/hass-norish/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.6%2B-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Validate](https://github.com/Caps3n/hass-norish/actions/workflows/validate.yaml/badge.svg)](https://github.com/Caps3n/hass-norish/actions/workflows/validate.yaml)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-caps3n-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/caps3n)

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
- **Past meals auto-hidden** — meals are removed from today's view 30 min after their default time slot

### 📆 Calendar
- Native Home Assistant calendar entity
- One event per meal with correct time slots
- **Calendar notes** (e.g. "Dinner at Marlies'") shown as events
- Calories and servings in the event description
- Full date-range support

### 🛒 Shopping List
- Native Home Assistant Todo list entity
- Displays items with quantity and unit
- **Add, rename, check off and delete** items — synced back to Norish (Norish parses amounts, e.g. `2 kg flour`)

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
   - **API Key** — find this in your Norish settings under **API Keys**
5. Click **Submit**

### Updating your API Key

If your API key expires, Home Assistant will show a **"Reconfigure"** notification automatically. Click it (or use the ⋮ menu on the integration card → **Reconfigure**) to enter a new key — no need to delete and re-add the integration.

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

**"Reconfigure" / "API key expired" although the key is valid**
- Norish rate-limits every API key (500 requests per hour) and only resets the counter after **more than one hour without any request**. Continuous polling used to exhaust the key after ~1 day, and Norish then answers `401` — indistinguishable from an expired key.
- Since v1.8.0 the integration handles this automatically: one batched request per poll, a nightly no-polling window (03:00–04:05 local time) that resets the counter, and a 65-minute pause if the key is rejected anyway. "Reconfigure" only appears if the key is **still** rejected after that pause.
- Recommended poll interval: 5 minutes or longer. At 1 minute the integration uses more than 500 requests per day.
- If the key really expired or was deleted: **Settings → Devices & Services → Norish → ⋮ → Reconfigure** and enter a new key from Norish settings under **API Keys**.

**No meals shown / "No meals planned"**
- Check the integration is active (not showing a setup error)
- Past meals are automatically hidden: Breakfast after 08:30, Lunch after 12:30, Snack after 15:30, Dinner after 18:30
- Future days always show all meals regardless of time

**No images displayed**
- Check if your Norish instance returns image URLs
- Verify the images are accessible from your Home Assistant host

**Connection error on setup**
- Confirm the Server URL is reachable from Home Assistant
- Verify your API key is correct (Settings → Norish → API Keys)
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

## 🆕 What's New in v1.8.0

- **Fixed: "API key expired" after ~24 hours** — the real cause is Norish's rate limit, which only resets after an hour without requests. The integration now batches calendar + groceries into one request, pauses polling nightly (03:00–04:05) so the counter resets, and waits 65 minutes before asking you to reconfigure.
- **Fixed: checking off / deleting shopping items** — Norish changed these API calls (they now require the item version); both work again.
- **New: add and rename shopping items from Home Assistant** — e.g. via voice assistant: "add 2 kg flour to Norish Unsorted".
- **New: calories and servings** — from Norish's nutrition calculation (Norish v0.25), as sensor attributes (`calories`, `servings`) and in calendar event descriptions.
- **Recipe images** now come straight from the calendar data (fewer API requests).
- Store list is cached properly even when you have no stores.

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

---

## 🆕 What's New in v1.7.0

- **Calendar notes** — Norish now supports free-text notes on any time slot (e.g. "Going out for dinner"). Notes are now displayed in the Home Assistant calendar:
  - If a recipe is planned, the note appears in the **event description** (visible when you tap the event).
  - If no recipe is planned, the note becomes the **event title** — so a slot with "Going out to eat" shows up with that text instead of the generic "Meal" label.
- Fully backwards-compatible: existing setups without notes are unaffected.

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

---

## 🆕 What's New in v1.6.10

- **Startup timeout fix** — if the Norish server isn't reachable when Home Assistant boots (e.g. HA starts before Norish is ready), the integration now triggers a graceful retry via `ConfigEntryNotReady` instead of crashing permanently with a `TimeoutError`.
- **Longer validation timeout** — increased from 10 s to 30 s to handle slow server starts and high-latency networks.

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

---

## 🆕 What's New in v1.6.9

- **Automatic API key renewal** — when the key is exhausted the integration silently creates a new one using your stored Norish credentials. No manual "Reconfigure" needed.
- **Optional credentials** — enter your Norish email + password in the setup or reconfigure form to enable auto-renewal. The password is stored as a masked field and never shown in plaintext.
- **Fallback** — if no credentials are stored, the existing behaviour is kept: after 3 consecutive 401 errors Home Assistant shows the "Reconfigure" notification.
- **Exponential reconnect backoff** (v1.6.8) — 1st failure → 60 s, 2nd → 5 min, 3rd+ → 10 min before next retry; auto-restores to normal interval on success.

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
