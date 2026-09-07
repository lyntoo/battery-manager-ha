"""Persistent storage for Battery Manager.

Ne cree AUCUNE entite HA — les types de piles sont stockes dans
.storage/battery_manager.battery_types via le helper Store natif de HA,
exactement comme les autres donnees de config interne (jamais une entite
qui pourrait devenir "primaire" sur une carte d'appareil).
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION, UNKNOWN_TYPE


class BatteryManagerStore:
    """Wrapper around Store for device_id -> battery_type + custom types."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {
            "device_types": {},
            "custom_types": [],
            "learned_devices": {},
            "auto_filled": {},
            "hidden_devices": [],
            "unhide_overrides": [],
        }

    async def async_load(self) -> None:
        """Load data from disk (no-op if nothing saved yet)."""
        loaded = await self._store.async_load()
        if loaded:
            self._data = {
                "device_types": loaded.get("device_types", {}),
                "custom_types": loaded.get("custom_types", []),
                "learned_devices": loaded.get("learned_devices", {}),
                "auto_filled": loaded.get("auto_filled", {}),
                "hidden_devices": loaded.get("hidden_devices", []),
                "unhide_overrides": loaded.get("unhide_overrides", []),
            }

    async def _async_save(self) -> None:
        await self._store.async_save(self._data)

    def get_type(self, device_id: str) -> str:
        """Return the stored battery type for a device, or Unknown."""
        return self._data["device_types"].get(device_id, UNKNOWN_TYPE)

    def get_custom_types(self) -> list[str]:
        """Return the list of user-added custom battery types."""
        return list(self._data["custom_types"])

    def is_auto_filled(self, device_id: str) -> bool:
        """Whether this device's type came from the database, not a manual choice."""
        return self._data["auto_filled"].get(device_id, False)

    async def async_set_type(self, device_id: str, battery_type: str, auto: bool = False) -> None:
        """Set (or reset to Unknown) the battery type for a device.

        auto=True marks the value as database-suggested (still fully
        overridable) rather than a deliberate manual/confirmed choice.
        """
        if battery_type == UNKNOWN_TYPE:
            self._data["device_types"].pop(device_id, None)
            self._data["auto_filled"].pop(device_id, None)
        else:
            self._data["device_types"][device_id] = battery_type
            if auto:
                self._data["auto_filled"][device_id] = True
            else:
                self._data["auto_filled"].pop(device_id, None)
        await self._async_save()

    @staticmethod
    def _learned_key(manufacturer: str | None, model: str | None) -> str:
        return f"{(manufacturer or '').strip().lower()}|{(model or '').strip().lower()}"

    def get_learned_type(self, manufacturer: str | None, model: str | None) -> str | None:
        """Return a battery type previously taught for this manufacturer+model."""
        return self._data["learned_devices"].get(self._learned_key(manufacturer, model))

    async def async_learn_device(
        self, manufacturer: str | None, model: str | None, battery_type: str
    ) -> None:
        """Remember a manufacturer+model -> battery type mapping for future devices."""
        key = self._learned_key(manufacturer, model)
        if not key.strip("|"):
            return
        self._data["learned_devices"][key] = battery_type
        await self._async_save()

    async def async_add_custom_type(self, name: str) -> None:
        """Add a new custom battery type if not already present."""
        name = name.strip()
        if name and name not in self._data["custom_types"]:
            self._data["custom_types"].append(name)
            await self._async_save()

    async def async_delete_custom_type(self, name: str) -> None:
        """Remove a custom battery type and reset any device using it to Unknown."""
        if name in self._data["custom_types"]:
            self._data["custom_types"].remove(name)
            for device_id, assigned in list(self._data["device_types"].items()):
                if assigned == name:
                    del self._data["device_types"][device_id]
            await self._async_save()

    def is_manually_hidden(self, key: str) -> bool:
        """Whether the user explicitly hid this device from the panel."""
        return key in self._data["hidden_devices"]

    def is_unhide_override(self, key: str) -> bool:
        """Whether the user asked to force-show a device despite the auto-hide heuristic."""
        return key in self._data["unhide_overrides"]

    async def async_hide(self, key: str) -> None:
        """Manually hide a device from the panel (e.g. non-replaceable battery)."""
        if key not in self._data["hidden_devices"]:
            self._data["hidden_devices"].append(key)
        if key in self._data["unhide_overrides"]:
            self._data["unhide_overrides"].remove(key)
        await self._async_save()

    async def async_unhide(self, key: str) -> None:
        """Show a device again, whether it was manually hidden or auto-hidden."""
        if key in self._data["hidden_devices"]:
            self._data["hidden_devices"].remove(key)
        if key not in self._data["unhide_overrides"]:
            self._data["unhide_overrides"].append(key)
        await self._async_save()
