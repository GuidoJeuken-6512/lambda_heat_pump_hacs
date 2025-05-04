"""The Lambda integration."""
from __future__ import annotations
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, DEBUG_PREFIX
from .coordinator import LambdaDataUpdateCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)

# Diese Konstante teilt Home Assistant mit, dass die Integration Übersetzungen hat
TRANSLATION_SOURCES = {DOMAIN: "translations"}


def setup_debug_logging(hass: HomeAssistant, config: ConfigType) -> None:
    """Set up debug logging for the integration."""
    if config.get("debug", False):
        logging.getLogger(DEBUG_PREFIX).setLevel(logging.DEBUG)
        _LOGGER.info("Debug logging enabled for %s", DEBUG_PREFIX)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Lambda integration."""
    setup_debug_logging(hass, config)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lambda from a config entry."""
    _LOGGER.debug("Setting up Lambda integration with config: %s", entry.data)

    try:
        coordinator = LambdaDataUpdateCoordinator(hass, entry)
        _LOGGER.debug("LambdaDataUpdateCoordinator initialized")
        await coordinator.async_refresh()
        _LOGGER.debug("LambdaDataUpdateCoordinator async_refresh called")
    except Exception as ex:
        _LOGGER.error("Failed to initialize Lambda integration: %s", ex)
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "climate"])

    # Beim ersten Setup die Services registrieren
    if len(hass.data[DOMAIN]) == 1:
        await async_setup_services(hass)

    # Registriere Update-Listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Lambda integration")
    try:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, ["sensor", "climate"]
        )
    except ValueError as ex:
        _LOGGER.debug("Platform was not loaded or already unloaded: %s", ex)
        unload_ok = True
    # Nur entfernen, wenn der Key existiert
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
        if coordinator and getattr(coordinator, "client", None):
            await hass.async_add_executor_job(coordinator.client.close)
        hass.data[DOMAIN].pop(entry.entry_id)

        # Wenn dies der letzte Entry war, entferne auch die Services
        if not hass.data[DOMAIN]:
            await async_unload_services(hass)
    else:
        _LOGGER.debug(
            "Entry %s not in hass.data[%s], nothing to remove.", entry.entry_id, DOMAIN
        )
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Reloading Lambda integration after config change")
    unload_ok = await async_unload_entry(hass, entry)
    if not unload_ok:
        _LOGGER.error("Could not unload entry for reload, aborting reload!")
        return
    await async_setup_entry(hass, entry)  # Completed the function call
