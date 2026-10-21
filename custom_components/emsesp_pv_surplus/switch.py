"""Switches: observe mode, compressor control, forecast use."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import PvSurplusEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    c = entry.runtime_data
    keys = ["observe"]
    if c.has_compressor_control:
        keys.append("dynamic_power")
    if c.has_forecast:
        keys.append("use_forecast")
    async_add_entities(SettingSwitch(c, key) for key in keys)


class SettingSwitch(PvSurplusEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        return bool(getattr(self.controller.settings, self.key))

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.controller.update_setting(self.key, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.controller.update_setting(self.key, False)
        self.async_write_ha_state()
