"""Mode select (automatic / off / manual)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import PvSurplusEntity
from .logic import MODES


def keys(c) -> list[str]:
    return ["mode"]


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities([ModeSelect(entry.runtime_data)])


class ModeSelect(PvSurplusEntity, SelectEntity):
    _attr_options = MODES

    def __init__(self, controller) -> None:
        super().__init__(controller, "mode")

    @property
    def current_option(self) -> str:
        return self.controller.settings.mode

    async def async_select_option(self, option: str) -> None:
        self.controller.update_setting("mode", option)
        self.async_write_ha_state()
