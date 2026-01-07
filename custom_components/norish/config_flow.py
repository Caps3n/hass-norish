import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_URL, CONF_PASSWORD
from .const import DOMAIN, DEFAULT_URL

class NorishConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Norish", data=user_input)

        # Wir fragen nur noch nach URL und API-Key
        data_schema = vol.Schema({
            vol.Required(CONF_URL, default=DEFAULT_URL): str,
            vol.Required(CONF_PASSWORD): str, # Intern als Passwort gespeichert, Label ist API-Key
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NorishOptionsFlowHandler(config_entry)

class NorishOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.entry.options or {}
        schema = vol.Schema({
            vol.Optional("show_breakfast", default=opts.get("show_breakfast", True)): bool,
            vol.Optional("show_lunch", default=opts.get("show_lunch", True)): bool,
            vol.Optional("show_dinner", default=opts.get("show_dinner", True)): bool,
            vol.Optional("show_snack", default=opts.get("show_snack", True)): bool,
        })
        return self.async_show_form(step_id="init", data_schema=schema)