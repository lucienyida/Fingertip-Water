from __future__ import annotations
import logging
from datetime import datetime, timedelta
import async_timeout
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

class WaterMeterAPI:
    def __init__(self, meter_no: str, company_id: str, auth_token: str, user_id: str, auth_t: str):
        self.base_url = "https://wl.tap-water.cn/waterMeter/getWaterMeter"
        self.history_url = "https://wl.tap-water.cn/waterMeter/getHistoryBill"
        self.trends_url = "https://wl.tap-water.cn/waterMeter/getWaterTrends"
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
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=self.params, headers=self.headers) as response:
                response.raise_for_status()
                data = await response.json()
                if data.get("code") != "0":
                    raise Exception(f"API错误: {data.get('message')}")
                return data["content"]

    async def fetch_annual_data(self, year: int):
        params = {
            "businessType": "0",
            "companyId": self.params["waterCompanyId"],
            "no": self.params["waterMeterNo"],
            "systemType": "0",
            "year": year
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.history_url, params=params, headers=self.headers) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("content", []) if data.get("code") == "0" else []

    async def fetch_water_trends(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.trends_url, params=self.params, headers=self.headers) as response:
                response.raise_for_status()
                data = await response.json()
                if data.get("code") != "0":
                    raise Exception(f"趋势接口错误: {data.get('message')}")
                return data["content"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = WaterMeterCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class WaterMeterCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
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
            sw_version="3.2.1"
        )
        self.api = WaterMeterAPI(
            meter_no=entry.data["water_meter_no"],
            company_id=entry.data["water_company_id"],
            auth_token=entry.data["auth_token"],
            user_id=entry.data["user_id"],
            auth_t=entry.data["authorization_t"]
        )

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(20):
                realtime_content = await self.api.fetch_data()
                history_data = await self._get_history_summary()
                trends_data = await self._get_water_trends()
                
                merged_data = {
                    "owner_no": f"{realtime_content.get('owner','')} {self.entry.data['water_meter_no']}",
                    "balance": self._clean_balance(realtime_content.get("balance", "0元")),
                    "current_year_total_usage": history_data["annual_usage"],
                    "last_year_total_usage": trends_data["last_year_total"],
                    "monthly_usage": trends_data["monthly"],
                    **history_data
                }
                _LOGGER.debug("合并后的数据: %s", merged_data)
                return merged_data
        except Exception as err:
            _LOGGER.error("数据更新失败: %s", err)
            raise

    def _clean_balance(self, value: str) -> float:
        try:
            return float(value.replace("元", "").strip())
        except:
            return 0.0

    async def _get_history_summary(self):
        current_year = datetime.now().year
        for year in range(current_year, current_year-2, -1):
            try:
                data = await self.api.fetch_annual_data(year)
                if data:
                    latest = max(data, key=lambda x: x["lastreaddate"])
                    return {
                        "current_usage": float(latest.get("waterquantity", 0)),
                        "current_bill": float(latest.get("arrears", 0)),
                        "annual_usage": round(sum(float(item["waterquantity"]) for item in data), 2),
                        "annual_bill": round(sum(float(item["arrears"]) for item in data), 2),
                        "latest_reading_value": latest["currentperiod"],
                        "latest_reading_time": latest["lastreaddate"].replace("年", "-").replace("月", "-").replace("日", "")
                    }
            except Exception as e:
                _LOGGER.error("获取历史数据失败: %s", e)
        return {
            "current_usage": 0.0,
            "current_bill": 0.0,
            "annual_usage": 0.0,
            "annual_bill": 0.0,
            "latest_reading_value": "无数据",
            "latest_reading_time": "无数据"
        }

    async def _get_water_trends(self):
        try:
            trends = await self.api.fetch_water_trends()
            monthly = []
            current_year = datetime.now().year
            
            # 处理最近两年数据
            for year_data in trends:
                year_label = year_data.get("label", "")
                if str(current_year) in year_label or str(current_year - 1) in year_label:
                    for month in year_data.get("waterTrendsValueList", []):
                        date_str = (
                            month["cherkBillDate"]
                            .replace("年", "")
                            .replace("月", "")
                        ).zfill(6)  # 格式化为6位数字字符串
                        monthly.append({
                            "month": date_str,
                            "usage": round(float(month.get("waterQuantity", 0)), 2)
                        })
            
            # 按月份倒序排列并截取最近24条
            monthly.sort(key=lambda x: x["month"], reverse=True)
            filtered_monthly = monthly[:24]
            
            # 计算去年总用水量
            last_year_total = sum(
                item["usage"] for item in filtered_monthly
                if str(current_year - 1) in item["month"]
            )
            
            return {
                "monthly": filtered_monthly,
                "last_year_total": round(last_year_total, 2)
            }
        except Exception as e:
            _LOGGER.error("处理趋势数据失败: %s", e)
            return {"monthly": [], "last_year_total": 0}
