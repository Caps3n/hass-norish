# hass-norish
# Norish Integration for Home Assistant

Bring your [Norish](https://github.com/norish-recipes/norish) recipe manager directly into your smart home! This integration connects your self-hosted Norish instance with Home Assistant to streamline meal planning and grocery shopping for families and friends.

## ✨ Key Features
* **📅 Meal Plan Calendar:** Syncs your Norish meal schedule directly to the Home Assistant calendar component.
* **🛒 Grocery List Sync:** Integrates Norish shopping lists as native Home Assistant `todo` entities.
* **🍽️ "What's for Dinner?":** Dedicated sensors to display today's meal, including titles and recipe details on your dashboard.
* **🚀 Automation Ready:** Use your meal plan to trigger notifications (e.g., "Don't forget to take the meat out of the freezer for tonight's recipe").

## 🛠 Installation

### Manual Installation
1. Download the `norish` folder from this repository.
2. Copy the folder into your Home Assistant `/config/custom_components/` directory.
3. Restart Home Assistant.
4. Go to **Settings > Devices & Services > Add Integration** and search for "Norish".

## ⚙️ Configuration
You will need:
* The **URL** of your Norish instance (e.g., `http://192.168.1.50:8080`)
* Your **API Token** (found in your Norish user settings)

## 🗺️ Roadmap
- [ ] HACS (Home Assistant Community Store) support

---
*This project is an independent integration and is not officially affiliated with the core Norish development team.*
