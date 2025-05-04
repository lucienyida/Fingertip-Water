# custom_components/water_meter/__init__.py
from __future__ import annotations
import logging
import asyncio
from datetime import timedelta
import async_timeout
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    coordinator = WaterMeterCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class WaterMeterCoordinator(DataUpdateCoordinator):
    """Data update coordinator with device support."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator with device info."""
        super().__init__(
            hass,
            _LOGGER,
            name=entry.data["name"],
            update_interval=timedelta(hours=12),
        )
        self.entry = entry
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data["water_meter_no"])},
            manufacturer="指尖水务",
            name=entry.data["name"],
            model="智能水表",
            sw_version="2.1"
        )
        self.api = WaterMeterAPI(
            meter_no=entry.data["water_meter_no"],
            company_id=entry.data["water_company_id"],
            auth_token=entry.data["auth_token"],
            user_id=entry.data["user_id"],
            auth_t=entry.data["authorization_t"]
        )

    async def _async_update_data(self):
        """Fetch data from API with retry logic."""
        for attempt in range(3):
            try:
                async with async_timeout.timeout(10):
                    return await self.api.fetch_data()
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                if attempt == 2:
                    raise UpdateFailed(f"API请求失败: {err}") from err
                await asyncio.sleep(5)
        return None

class WaterMeterAPI:
    """API client with enhanced error handling."""
    
    def __init__(self, meter_no: str, company_id: str, auth_token: str, user_id: str, auth_t: str):
        self.base_url = "https://wl.tap-water.cn/waterMeter/getWaterMeter"
        self.params = {
            "businessType": "0",
            "systemType": "0",
            "waterCompanyId": company_id,
            "waterMeterNo": meter_no
        }
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "userId": user_id,
            "AuthorizationT": auth_t,
            "User-Agent": "WaterAffairs1/3.7.0 (iPhone; iOS 14.4.1; Scale/3.00)",
            "Accept": "*/*"
        }

    async def fetch_data(self):
        """Fetch and validate data from the API."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.base_url,
                params=self.params,
                headers=self.headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data.get("code") != "0":
                    raise Exception(f"API错误: {data.get('message', '未知错误')}")
                
                content = data.get("content", {})
                return {
                    "owner": content.get("owner", "未知用户"),
                    "address": content.get("address", "未知地址"),
                    "balance": float(content.get("balance", 0.0)),
                    "arrears": float(content.get("arrears", 0.0))
                }