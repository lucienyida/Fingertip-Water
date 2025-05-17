# sensor.py
from __future__ import annotations
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_KEYS_ORDER

SENSORS = {
    "owner_no": ("编号户名", "mdi:account-card", None),
    "balance": ("当前余额", "mdi:cash", "元", SensorDeviceClass.MONETARY),
    "current_usage": ("本期用量", "mdi:water", "m³"),
    "current_bill": ("本期金额", "mdi:cash-100", "元", SensorDeviceClass.MONETARY),
    "current_year_total_usage": ("本年用水总量", "mdi:chart-waterfall", "m³"),
    "annual_bill": ("年累计金额", "mdi:currency-cny", "元", SensorDeviceClass.MONETARY),
    "last_year_total_usage": ("去年用水总量", "mdi:chart-bar", "m³"),
    "monthly_usage": ("月度用水趋势", "mdi:chart-areaspline", None),
    "latest_reading_time": ("最近一次抄表时间", "mdi:calendar-clock", None),
    "latest_reading_value": ("最近一次抄表值", "mdi:gauge", "m³")
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for key in SENSOR_KEYS_ORDER:
        if sensor_def := SENSORS.get(key):
            name, icon, unit, *rest = sensor_def
            device_class = rest[0] if rest else None
            entities.append(
                WaterMeterSensor(coordinator, key, name, icon, unit, device_class)
            )
    
    async_add_entities(entities)

class WaterMeterSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator,
        key: str,
        name: str,
        icon: str,
        unit: str,
        device_class: SensorDeviceClass = None
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self):
        if self._key == "monthly_usage":
            return "图表"
        
        value = self.coordinator.data.get(self._key)
        
        if value is None:
            return "无数据" if self._key in ["latest_reading_time", "latest_reading_value"] else 0.0
        
        if isinstance(value, (int, float)):
            return round(value, 2) if self._key.endswith(("bill", "balance")) else value
            
        return value

    @property
    def extra_state_attributes(self):
        if self._key == "monthly_usage":
            monthly_data = self.coordinator.data.get("monthly_usage", [])
            return {
                "graph": [
                    {
                        "month": item["month"],
                        "usage": item["usage"]
                    } for item in monthly_data
                ],
                "friendly_name": self.name
            }
        return None