"""Buttons: lift the lock time, reset today's counter."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import PvSurplusEntity


def keys(c) -> list[str]:
    return ["reset_lock", "reset_counter"]


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities([ResetLockButton(c), ResetCounterButton(c)])


class ResetLockButton(PvSurplusEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, controller) -> None:
        super().__init__(controller, "reset_lock")

    async def async_press(self) -> None:
        self.controller.reset_lock()


class ResetCounterButton(PvSurplusEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, controller) -> None:
        super().__init__(controller, "reset_counter")

    async def async_press(self) -> None:
        self.controller.reset_counter()
