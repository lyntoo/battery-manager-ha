"""Battery Manager integration for Home Assistant.

Panneau qui liste dynamiquement tous les appareils a pile (detection live
via les registres HA, jamais une liste figee) et permet d'assigner un type
de pile exact (AA, CR2032, etc.) a chacun. Le type est stocke via le
helper Store natif de HA (.storage/) — aucune nouvelle entite creee, donc
aucun risque qu'une entite "note" devienne primaire sur une carte d'appareil.
"""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.panel_custom import async_register_panel
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_ICON, PANEL_TITLE, PANEL_URL_PATH, URL_BASE
from .storage import BatteryManagerStore
from .websocket_api import async_register_websocket_commands

FRONTEND_PATH = Path(__file__).parent / "frontend"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Battery Manager from a config entry."""
    store = BatteryManagerStore(hass)
    await store.async_load()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["store"] = store

    await hass.http.async_register_static_paths(
        [StaticPathConfig(URL_BASE, str(FRONTEND_PATH), cache_headers=False)]
    )

    async_register_websocket_commands(hass)

    await async_register_panel(
        hass,
        webcomponent_name="battery-manager-panel",
        frontend_url_path=PANEL_URL_PATH,
        module_url=f"{URL_BASE}/battery-manager-panel.js",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=True,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Battery Manager config entry."""
    from homeassistant.components.frontend import async_remove_panel

    async_remove_panel(hass, PANEL_URL_PATH)
    hass.data.pop(DOMAIN, None)
    return True
