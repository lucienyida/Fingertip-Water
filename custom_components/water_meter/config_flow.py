# custom_components/water_meter/config_flow.py
from __future__ import annotations
import logging
from typing import Any
import aiohttp

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
    """Config flow with authentication validation."""
    
    VERSION = 3

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step with API test."""
        errors = {}
        
        if user_input is not None:
            # 验证API连通性
            try:
                async with aiohttp.ClientSession() as session:
                    response = await session.get(
                        "https://wl.tap-water.cn/waterMeter/getWaterMeter",
                        params={
                            "waterCompanyId": user_input["water_company_id"],
                            "waterMeterNo": user_input["water_meter_no"]
                        },
                        headers={
                            "Authorization": f"Bearer {user_input['auth_token']}",
                            "AuthorizationT": user_input["authorization_t"],
                            "userId": user_input["user_id"]
                        }
                    )
                    if response.status == 401:
                        errors["base"] = "invalid_auth"
                    else:
                        data = await response.json()
                        if data.get("code") != "0":
                            errors["base"] = "api_error"
            except Exception as e:
                errors["base"] = "connection_failed"
            
            if not errors:
                await self.async_set_unique_id(user_input["water_meter_no"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input["name"],
                    data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors,
            description_placeholders={
                "note": "请确保使用最新抓包数据填写所有字段"
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WaterMeterOptionsFlow(config_entry)

class WaterMeterOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""
    
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return self.async_abort(reason="no_options")