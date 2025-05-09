"""The Lambda integration."""
from __future__ import annotations
from datetime import timedelta
import logging
import asyncio
from typing import Dict, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, DEBUG_PREFIX
from .coordinator import LambdaDataUpdateCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)
VERSION = "1.0.0"

# Diese Konstante teilt Home Assistant mit, dass die Integration Übersetzungen hat
TRANSLATION_SOURCES = {DOMAIN: "translations"}

# Lock für das Reloading
_reload_lock = asyncio.Lock()

def setup_debug_logging(hass: HomeAssistant, config: ConfigType) -> None:
    """Set up debug logging for the integration."""
    # hass argument is unused, kept for interface compatibility
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
    await hass.config_entries.async_forward_entry_setups(
        entry, ["sensor", "climate"]
    )

    # Beim ersten Setup die Services registrieren
    if len(hass.data[DOMAIN]) == 1:
        await async_setup_services(hass)

    # Registriere Update-Listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Lambda integration for entry %s", entry.entry_id)
    
    # First try to unload the platforms
    try:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, ["sensor", "climate"]
        )
    except ValueError as ex:
        _LOGGER.debug("Platform was not loaded or already unloaded: %s", ex)
        unload_ok = True
    except Exception as ex:
        _LOGGER.error("Error unloading platforms: %s", ex)
        unload_ok = False

    # Then clean up the coordinator and data
    try:
        if DOMAIN in hass.data:
            entry_data = hass.data[DOMAIN].get(entry.entry_id)
            if entry_data:
                coordinator = entry_data.get("coordinator")
                if coordinator:
                    try:
                        if getattr(coordinator, "client", None):
                            await hass.async_add_executor_job(coordinator.client.close)
                    except Exception as ex:
                        _LOGGER.error("Error closing Modbus client: %s", ex)
                
                # Remove the entry data
                hass.data[DOMAIN].pop(entry.entry_id, None)
                
                # If this was the last entry, unload services
                if not hass.data[DOMAIN]:
                    try:
                        await async_unload_services(hass)
                    except Exception as ex:
                        _LOGGER.error("Error unloading services: %s", ex)
            else:
                _LOGGER.debug("No entry data found for %s", entry.entry_id)
        else:
            _LOGGER.debug("No domain data found for %s", DOMAIN)
    except Exception as ex:
        _LOGGER.error("Error during cleanup: %s", ex)
        unload_ok = False

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Reloading Lambda integration after config change for entry %s", entry.entry_id)
    
    # Use a lock to prevent multiple simultaneous reloads
    async with _reload_lock:
        try:
            # First, try to unload the entire integration
            try:
                await async_unload_entry(hass, entry)
            except Exception as ex:
                _LOGGER.error("Error during initial unload: %s", ex)
                # Continue anyway, as we want to force a reload

            # Wait a moment to ensure everything is unloaded
            await asyncio.sleep(1)

            # Now try to set up the entry again
            try:
                # Create a new coordinator
                coordinator = LambdaDataUpdateCoordinator(hass, entry)
                await coordinator.async_refresh()

                # Store the coordinator
                hass.data.setdefault(DOMAIN, {})
                hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

                # Set up platforms
                await hass.config_entries.async_forward_entry_setups(
                    entry, ["sensor", "climate"]
                )

                # Set up services if this is the first entry
                if len(hass.data[DOMAIN]) == 1:
                    await async_setup_services(hass)

                # Register update listener
                entry.async_on_unload(entry.add_update_listener(async_reload_entry))

                _LOGGER.debug("Successfully reloaded Lambda integration for entry %s", entry.entry_id)
            except Exception as ex:
                _LOGGER.error("Error setting up entry after reload: %s", ex)
                # Clean up if setup failed
                if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
                    hass.data[DOMAIN].pop(entry.entry_id, None)
        except Exception as ex:
            _LOGGER.error("Unexpected error during reload: %s", ex)
