"""Start window (from / until)."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import PvSurplusEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities([WindowTime(c, "window_start"), WindowTime(c, "window_end")])


class WindowTime(PvSurplusEntity, TimeEntity):
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def native_value(self) -> time:
        return getattr(self.controller.settings, self.key)

    async def async_set_value(self, value: time) -> None:
        self.controller.update_setting(self.key, value.replace(microsecond=0))
        self.async_write_ha_state()
