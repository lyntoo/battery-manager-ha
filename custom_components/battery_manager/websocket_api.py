"""WebSocket API for the Battery Manager integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import (
    AUTO_HIDE_CONFIG_DOMAINS,
    AUTO_HIDE_IF_HAS_ENTITY_DOMAIN,
    DEFAULT_BATTERY_TYPES,
    DOMAIN,
    RECHARGEABLE_PACK_TYPES,
    UNKNOWN_TYPE,
)
from .device_database import lookup_battery_type
from .storage import BatteryManagerStore


def _is_auto_hide_candidate(
    hass: HomeAssistant, ent_reg: er.EntityRegistry, dev_reg: dr.DeviceRegistry, device_id: str | None
) -> bool:
    """Detecte les appareils a pack rechargeable non remplacable (telephones, robots, tondeuses)."""
    if not device_id or not (device := dev_reg.async_get(device_id)):
        return False
    for entry_id in device.config_entries:
        if (entry := hass.config_entries.async_get_entry(entry_id)) and entry.domain in AUTO_HIDE_CONFIG_DOMAINS:
            return True
    entity_domains = {
        e.entity_id.split(".", 1)[0] for e in er.async_entries_for_device(ent_reg, device_id)
    }
    return bool(entity_domains & AUTO_HIDE_IF_HAS_ENTITY_DOMAIN)


async def _discover_battery_rows(
    hass: HomeAssistant, store: BatteryManagerStore
) -> list[dict[str, Any]]:
    """Interroge en direct les registres HA pour tous les capteurs de pile.

    Aucune liste statique : tout appareil avec un capteur device_class
    'battery' (sensor) ou 'battery'/'battery_charging' (binary_sensor)
    apparait automatiquement, y compris les appareils ajoutes apres coup.
    """
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    area_reg = ar.async_get(hass)

    rows: dict[str, dict[str, Any]] = {}

    for state in hass.states.async_all():
        device_class = state.attributes.get("device_class")
        if state.domain == "sensor" and device_class == "battery":
            kind = "level"
        elif state.domain == "binary_sensor" and device_class in ("battery", "battery_charging"):
            kind = "low" if device_class == "battery" else "charging"
        else:
            continue

        entry = ent_reg.async_get(state.entity_id)
        device_id = entry.device_id if entry else None
        key = device_id or state.entity_id

        if key not in rows:
            name = None
            area_name = None
            manufacturer = None
            model = None
            model_id = None
            if device_id and (device := dev_reg.async_get(device_id)):
                name = device.name_by_user or device.name
                manufacturer = device.manufacturer
                model = device.model
                # model_id existe sur certaines versions/integrations (ex: ZHA
                # separe parfois un identifiant brut du nom lisible) — champ
                # supplementaire pour le matching, absent = None sans erreur.
                model_id = getattr(device, "model_id", None)
                if device.area_id and (area := area_reg.async_get_area(device.area_id)):
                    area_name = area.name
            if not name:
                name = (entry.name if entry and entry.name else None) or state.attributes.get(
                    "friendly_name", state.entity_id
                )
            rows[key] = {
                "key": key,
                "device_id": device_id,
                "name": name,
                "area": area_name,
                "manufacturer": manufacturer,
                "model": model,
                "model_id": model_id,
                "battery_level": None,
                "battery_low": None,
                "entities": [],
                "battery_type": store.get_type(key),
                "auto_filled": store.is_auto_filled(key),
                "auto_hide_candidate": _is_auto_hide_candidate(hass, ent_reg, dev_reg, device_id),
            }

        rows[key]["entities"].append(state.entity_id)
        if kind == "level":
            try:
                rows[key]["battery_level"] = float(state.state)
            except (ValueError, TypeError):
                pass
        elif kind == "low":
            rows[key]["battery_low"] = state.state == "on"

    # Auto-remplissage : pour tout appareil encore Unknown, on cherche une
    # correspondance dans la base "apprise" (priorite) puis la base seed.
    # Toujours ecrit via async_set_type(auto=True) donc reste 100% modifiable
    # depuis le panneau ensuite.
    for row in rows.values():
        if row["battery_type"] != UNKNOWN_TYPE:
            continue
        # model_id (quand fourni par l'integration, ex: certains flux ZHA) est
        # inclus dans la recherche seed en plus de model, sans polluer la
        # base "apprise" (dont la cle reste manufacturer+model uniquement).
        search_model = " ".join(filter(None, [row["model"], row["model_id"]]))
        suggested = store.get_learned_type(row["manufacturer"], row["model"]) or lookup_battery_type(
            row["manufacturer"], search_model
        )
        if suggested:
            await store.async_set_type(row["key"], suggested, auto=True)
            row["battery_type"] = suggested
            row["auto_filled"] = True

    for row in rows.values():
        row["manually_hidden"] = store.is_manually_hidden(row["key"])
        hide_reason = row["auto_hide_candidate"] or row["battery_type"] in RECHARGEABLE_PACK_TYPES
        row["hidden"] = row["manually_hidden"] or (
            hide_reason and not store.is_unhide_override(row["key"])
        )

    return sorted(rows.values(), key=lambda r: (r["area"] or "￿", r["name"] or ""))


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register Battery Manager WebSocket commands."""
    websocket_api.async_register_command(hass, handle_list)
    websocket_api.async_register_command(hass, handle_set_type)
    websocket_api.async_register_command(hass, handle_add_custom_type)
    websocket_api.async_register_command(hass, handle_delete_custom_type)
    websocket_api.async_register_command(hass, handle_learn_device)
    websocket_api.async_register_command(hass, handle_hide_device)
    websocket_api.async_register_command(hass, handle_unhide_device)


def _get_store(hass: HomeAssistant) -> BatteryManagerStore:
    return hass.data[DOMAIN]["store"]


@websocket_api.websocket_command({vol.Required("type"): "battery_manager/list"})
@websocket_api.async_response
async def handle_list(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return all battery-powered devices + their stored battery type."""
    store = _get_store(hass)
    all_rows = await _discover_battery_rows(hass, store)
    connection.send_result(
        msg["id"],
        {
            "devices": [r for r in all_rows if not r["hidden"]],
            "hidden_devices": [r for r in all_rows if r["hidden"]],
            "default_types": DEFAULT_BATTERY_TYPES,
            "custom_types": store.get_custom_types(),
            "unknown_type": UNKNOWN_TYPE,
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "battery_manager/set_type",
        vol.Required("key"): str,
        vol.Required("battery_type"): str,
    }
)
@websocket_api.async_response
async def handle_set_type(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Set (or reset) the battery type for a device (deliberate/manual choice)."""
    await _get_store(hass).async_set_type(msg["key"], msg["battery_type"], auto=False)
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "battery_manager/add_custom_type",
        vol.Required("name"): str,
    }
)
@websocket_api.async_response
async def handle_add_custom_type(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Add a user-defined custom battery type."""
    await _get_store(hass).async_add_custom_type(msg["name"])
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "battery_manager/delete_custom_type",
        vol.Required("name"): str,
    }
)
@websocket_api.async_response
async def handle_delete_custom_type(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Delete a user-defined custom battery type (resets affected devices to Unknown)."""
    await _get_store(hass).async_delete_custom_type(msg["name"])
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "battery_manager/learn_device",
        vol.Optional("manufacturer"): vol.Any(str, None),
        vol.Optional("model"): vol.Any(str, None),
        vol.Required("battery_type"): str,
    }
)
@websocket_api.async_response
async def handle_learn_device(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Remember manufacturer+model -> battery type for all matching devices, present and future."""
    await _get_store(hass).async_learn_device(
        msg.get("manufacturer"), msg.get("model"), msg["battery_type"]
    )
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "battery_manager/hide_device",
        vol.Required("key"): str,
    }
)
@websocket_api.async_response
async def handle_hide_device(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Hide a device from the main list (e.g. non-replaceable/charging-only battery)."""
    await _get_store(hass).async_hide(msg["key"])
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "battery_manager/unhide_device",
        vol.Required("key"): str,
    }
)
@websocket_api.async_response
async def handle_unhide_device(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Show a device again, whether it was manually or automatically hidden."""
    await _get_store(hass).async_unhide(msg["key"])
    connection.send_result(msg["id"])
