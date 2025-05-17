from __future__ import annotations
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Required("water_meter_no"): str,
    vol.Required("water_company_id"): str,
    vol.Required("auth_token"): str,
    vol.Required("user_id"): str,
    vol.Required("authorization_t"): str,
})

class WaterMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 3

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}
        
        if user_input is not None:
            if len(user_input["water_company_id"]) not in (2, 3):
                errors["water_company_id"] = "invalid_length"
            elif not user_input["water_company_id"].isdigit():
                errors["water_company_id"] = "invalid_format"
            
            if not errors:
                await self.async_set_unique_id(
                    f"{user_input['water_company_id']}_{user_input['water_meter_no']}"
                )
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=user_input["name"],
                    data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WaterMeterOptionsFlow(config_entry)

class WaterMeterOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__()
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        return self.async_abort(reason="no_options")