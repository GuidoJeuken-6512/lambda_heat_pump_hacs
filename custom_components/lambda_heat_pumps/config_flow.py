"""Config flow for Lambda WP integration."""
from __future__ import annotations
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SLAVE_ID,
    DEFAULT_HOST,
    DEFAULT_FIRMWARE,
    DEFAULT_ROOM_THERMOSTAT_CONTROL,
    DEFAULT_NUM_HPS,
    DEFAULT_NUM_BOIL,
    DEFAULT_NUM_HC,
    DEFAULT_NUM_BUFFER,
    DEFAULT_NUM_SOLAR,
    DEFAULT_HOT_WATER_MIN_TEMP,
    DEFAULT_HOT_WATER_MAX_TEMP,
    DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
    DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
    DEFAULT_HEATING_CIRCUIT_TEMP_STEP,
    CONF_SLAVE_ID,
    FIRMWARE_VERSION,
    CONF_ROOM_TEMPERATURE_ENTITY,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect."""
    # hass and data arguments are unused, kept for interface compatibility
    pass


class LambdaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lambda WP."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is None:
            user_input = {}

        # Default-Werte aus bestehendem Eintrag holen, falls vorhanden
        current_entries = self._async_current_entries()
        existing_data = (
            current_entries[0].data if current_entries else {}
        )
        existing_options = (
            dict(current_entries[0].options) if current_entries else {}
        )

        # Pflichtfelder prüfen
        required_fields = [
            CONF_NAME,
            CONF_HOST,
            CONF_PORT,
            CONF_SLAVE_ID
        ]
        if not all(
            k in user_input and user_input[k] for k in required_fields
        ):
            # Formular anzeigen, wenn Eingaben fehlen
            firmware_options = list(FIRMWARE_VERSION.keys())
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_NAME,
                            default=user_input.get(
                                CONF_NAME,
                                existing_data.get(CONF_NAME, DEFAULT_NAME)
                            ),
                        ): selector.TextSelector(),
                        vol.Required(
                            CONF_HOST,
                            default=user_input.get(
                                CONF_HOST,
                                existing_data.get(CONF_HOST, DEFAULT_HOST)
                            ),
                        ): selector.TextSelector(),
                        vol.Required(
                            CONF_PORT,
                            default=int(
                                user_input.get(
                                    CONF_PORT,
                                    existing_data.get(CONF_PORT, DEFAULT_PORT),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1,
                                max=65535,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            CONF_SLAVE_ID,
                            default=int(
                                user_input.get(
                                    CONF_SLAVE_ID,
                                    existing_data.get(
                                        CONF_SLAVE_ID,
                                        DEFAULT_SLAVE_ID
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1,
                                max=255,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            "num_hps",
                            default=int(
                                user_input.get(
                                    "num_hps",
                                    existing_data.get(
                                        "num_hps",
                                        DEFAULT_NUM_HPS
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1,
                                max=5,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            "num_boil",
                            default=int(
                                user_input.get(
                                    "num_boil",
                                    existing_data.get(
                                        "num_boil",
                                        DEFAULT_NUM_BOIL
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0,
                                max=5,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            "num_hc",
                            default=int(
                                user_input.get(
                                    "num_hc",
                                    existing_data.get(
                                        "num_hc",
                                        DEFAULT_NUM_HC
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0,
                                max=5,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            "num_buffer",
                            default=int(
                                user_input.get(
                                    "num_buffer",
                                    existing_data.get(
                                        "num_buffer",
                                        DEFAULT_NUM_BUFFER
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0,
                                max=5,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            "num_solar",
                            default=int(
                                user_input.get(
                                    "num_solar",
                                    existing_data.get(
                                        "num_solar",
                                        DEFAULT_NUM_SOLAR
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0,
                                max=5,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Optional(
                            "firmware_version",
                            default=user_input.get(
                                "firmware_version",
                                existing_data.get(
                                    "firmware_version",
                                    DEFAULT_FIRMWARE
                                ),
                            ),
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=firmware_options,
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        ),
                    }
                ),
                errors=errors,
            )

        try:
            # Convert numeric values to integers
            for key in [
                "port",
                "slave_id",
                "num_hps",
                "num_boil",
                "num_hc",
                "num_buffer",
                "num_solar",
            ]:
                if key in user_input:
                    user_input[key] = int(user_input[key])

            # Ergänze fehlende Pflichtfelder aus existing_data oder Default
            if CONF_NAME not in user_input or not user_input[CONF_NAME]:
                user_input[CONF_NAME] = existing_data.get(
                    CONF_NAME, DEFAULT_NAME
                )
            await validate_input(self.hass, user_input)
            if CONF_NAME not in user_input or not user_input[CONF_NAME]:
                errors["base"] = "name_required"
            else:
                # Erstelle den Eintrag mit Standard-Optionen
                default_options = {
                    # Immer false beim initialen Setup
                    "room_thermostat_control": False,
                    "hot_water_min_temp": user_input.get(
                        "hot_water_min_temp",
                        existing_options.get(
                            "hot_water_min_temp",
                            DEFAULT_HOT_WATER_MIN_TEMP
                        ),
                    ),
                    "hot_water_max_temp": user_input.get(
                        "hot_water_max_temp",
                        existing_options.get(
                            "hot_water_max_temp",
                            DEFAULT_HOT_WATER_MAX_TEMP
                        ),
                    ),
                    "heating_circuit_min_temp": user_input.get(
                        "heating_circuit_min_temp",
                        existing_options.get(
                            "heating_circuit_min_temp",
                            DEFAULT_HEATING_CIRCUIT_MIN_TEMP
                        ),
                    ),
                    "heating_circuit_max_temp": user_input.get(
                        "heating_circuit_max_temp",
                        existing_options.get(
                            "heating_circuit_max_temp",
                            DEFAULT_HEATING_CIRCUIT_MAX_TEMP
                        ),
                    ),
                    "heating_circuit_temp_step": user_input.get(
                        "heating_circuit_temp_step",
                        existing_options.get(
                            "heating_circuit_temp_step",
                            DEFAULT_HEATING_CIRCUIT_TEMP_STEP
                        ),
                    ),
                    "firmware_version": user_input.get(
                        "firmware_version",
                        existing_options.get(
                            "firmware_version",
                            DEFAULT_FIRMWARE
                        ),
                    ),
                }
                _LOGGER.debug(
                    "ConfigFlow: Erstelle neuen Eintrag mit data=%s, options=%s",
                    user_input,
                    default_options,
                )
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                    options=default_options,
                )
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=user_input.get(
                            CONF_NAME,
                            existing_data.get(CONF_NAME, DEFAULT_NAME)
                        ),
                    ): str,
                    vol.Required(
                        CONF_HOST,
                        default=user_input.get(
                            CONF_HOST,
                            existing_data.get(CONF_HOST, DEFAULT_HOST)
                        ),
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        default=user_input.get(
                            CONF_PORT,
                            existing_data.get(CONF_PORT, DEFAULT_PORT)
                        ),
                    ): int,
                    vol.Required(
                        CONF_SLAVE_ID,
                        default=user_input.get(
                            CONF_SLAVE_ID,
                            existing_data.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)
                        ),
                    ): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        # config_entry argument is unused, kept for interface compatibility
        return LambdaOptionsFlow(config_entry)


class LambdaOptionsFlow(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        # Stelle sicher, dass options ein Dictionary ist
        # und alle erforderlichen Schlüssel enthält
        self._options = {
            "room_thermostat_control": DEFAULT_ROOM_THERMOSTAT_CONTROL,
            "hot_water_min_temp": DEFAULT_HOT_WATER_MIN_TEMP,
            "hot_water_max_temp": DEFAULT_HOT_WATER_MAX_TEMP,
            "heating_circuit_min_temp": DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
            "heating_circuit_max_temp": DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
            "heating_circuit_temp_step": DEFAULT_HEATING_CIRCUIT_TEMP_STEP,
            "firmware_version": DEFAULT_FIRMWARE,
        }
        if config_entry.options:
            self._options.update(dict(config_entry.options))

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        _LOGGER.debug(
            "Options-Flow aufgerufen. Aktuelle Optionen: %s",
            self._options
        )
        if user_input is not None:
            _LOGGER.debug("Options-Flow user_input: %s", user_input)
            try:
                # Konvertiere numerische Werte zu float
                for key in ["hot_water_min_temp", "hot_water_max_temp"]:
                    if key in user_input:
                        user_input[key] = float(user_input[key])

                # Validate the input
                min_temp = user_input.get(
                    "hot_water_min_temp",
                    DEFAULT_HOT_WATER_MIN_TEMP
                )
                max_temp = user_input.get(
                    "hot_water_max_temp",
                    DEFAULT_HOT_WATER_MAX_TEMP
                )
                if min_temp >= max_temp:
                    errors["hot_water_min_temp"] = "min_temp_higher"
                    errors["hot_water_max_temp"] = "max_temp_lower"
                else:
                    # Wenn room_thermostat_control aktiviert wurde,
                    # gehe zum Schritt für die Sensorauswahl
                    if user_input.get("room_thermostat_control", False):
                        self._options.update(user_input)
                        _LOGGER.debug(
                            "Options-Flow: Wechsel zu room_sensor mit Optionen: %s",
                            self._options
                        )
                        return await self.async_step_room_sensor()
                    else:
                        # Wenn room_thermostat_control deaktiviert wurde,
                        # entferne alle Temperatursensoren aus den Optionen
                        num_hc = self._config_entry.data.get("num_hc", 1)
                        for hc_idx in range(1, num_hc + 1):
                            entity_key = CONF_ROOM_TEMPERATURE_ENTITY.format(hc_idx)
                            if entity_key in self._options:
                                del self._options[entity_key]
                        _LOGGER.debug(
                            "Room thermostat control disabled, removed temperature sensors from options"
                        )

                    # Update options with new values
                    updated_options = dict(self._options)
                    updated_options.update(user_input)
                    _LOGGER.debug(
                        "Options-Flow: Speichere Optionen: %s",
                        updated_options
                    )
                    return self.async_create_entry(
                        title="",
                        data=updated_options
                    )
            except ValueError as ex:
                _LOGGER.error(
                    "Fehler bei der Konvertierung der Temperaturwerte: %s",
                    ex
                )
                errors["base"] = "invalid_temperature"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"

        # Stelle sicher, dass die Standardwerte korrekt formatiert sind
        options = {
            "hot_water_min_temp": float(
                self._options.get(
                    "hot_water_min_temp",
                    DEFAULT_HOT_WATER_MIN_TEMP
                )
            ),
            "hot_water_max_temp": float(
                self._options.get(
                    "hot_water_max_temp",
                    DEFAULT_HOT_WATER_MAX_TEMP
                )
            ),
            "room_thermostat_control": bool(
                self._options.get(
                    "room_thermostat_control",
                    DEFAULT_ROOM_THERMOSTAT_CONTROL
                )
            ),
            "heating_circuit_min_temp": float(
                self._options.get(
                    "heating_circuit_min_temp",
                    DEFAULT_HEATING_CIRCUIT_MIN_TEMP
                )
            ),
            "heating_circuit_max_temp": float(
                self._options.get(
                    "heating_circuit_max_temp",
                    DEFAULT_HEATING_CIRCUIT_MAX_TEMP
                )
            ),
            "heating_circuit_temp_step": float(
                self._options.get(
                    "heating_circuit_temp_step",
                    DEFAULT_HEATING_CIRCUIT_TEMP_STEP
                )
            ),
            "firmware_version": self._options.get(
                "firmware_version",
                DEFAULT_FIRMWARE
            ),
        }
        _LOGGER.debug(
            "Config flow initialized with options: %s",
            options
        )
        try:
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            "hot_water_min_temp",
                            default=options["hot_water_min_temp"],
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=20,
                                max=80,
                                step=1,
                                unit_of_measurement="°C",
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Optional(
                            "hot_water_max_temp",
                            default=options["hot_water_max_temp"],
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=20,
                                max=80,
                                step=1,
                                unit_of_measurement="°C",
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Optional(
                            "heating_circuit_min_temp",
                            default=options["heating_circuit_min_temp"],
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=5,
                                max=50,
                                step=0.5,
                                unit_of_measurement="°C",
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Optional(
                            "heating_circuit_max_temp",
                            default=options["heating_circuit_max_temp"],
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=10,
                                max=70,
                                step=0.5,
                                unit_of_measurement="°C",
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Optional(
                            "heating_circuit_temp_step",
                            default=options["heating_circuit_temp_step"],
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0.1,
                                max=5,
                                step=0.1,
                                unit_of_measurement="°C",
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Optional(
                            "firmware_version",
                            default=(
                                self._options.get("firmware_version")
                                or self._config_entry.data.get(
                                    "firmware_version"
                                )
                                or DEFAULT_FIRMWARE
                            ),
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=list(FIRMWARE_VERSION.keys()),
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        ),
                        vol.Optional(
                            "room_thermostat_control",
                            default=options["room_thermostat_control"],
                        ): selector.BooleanSelector(),
                    }
                ),
                errors=errors,
            )
        except Exception as ex:
            _LOGGER.exception(
                "Options-Flow: Fehler beim Bauen des Schemas oder "
                "Anzeigen des Formulars: %s",
                ex,
            )
            raise

    async def async_step_room_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the room sensor selection step."""
        from homeassistant.helpers.entity_registry import async_get

        errors: dict[str, str] = {}
        num_hc = self._config_entry.data.get("num_hc", 1)

        if user_input is not None:
            try:
                # Prüfe, ob mindestens ein Sensor ausgewählt wurde
                has_selected_sensor = False
                for hc_idx in range(1, num_hc + 1):
                    entity_key = CONF_ROOM_TEMPERATURE_ENTITY.format(hc_idx)
                    if entity_key in user_input and user_input[entity_key]:
                        self._options[entity_key] = user_input[entity_key]
                        has_selected_sensor = True
                    elif entity_key in self._options:
                        del self._options[entity_key]

                # Setze room_thermostat_control basierend auf der Sensorauswahl
                self._options["room_thermostat_control"] = has_selected_sensor
                _LOGGER.debug(
                    "Room sensor selection completed. Has selected sensor: %s, "
                    "room_thermostat_control set to: %s",
                    has_selected_sensor,
                    self._options["room_thermostat_control"]
                )

                return self.async_create_entry(title="", data=self._options)
            except Exception:
                _LOGGER.exception(
                    "Unexpected exception in room sensor selection"
                )
                errors["base"] = "unknown"

        # Hole alle Entities, die NICHT zur eigenen Integration gehören
        temp_entities = []
        registry = async_get(self.hass)
        eigene_entity_ids = {
            e.entity_id
            for e in registry.entities.values()
            if e.config_entry_id == self._config_entry.entry_id
        }
        for entity_id in self.hass.states.async_entity_ids():
            if entity_id in eigene_entity_ids:
                continue
            state = self.hass.states.get(entity_id)
            if state is None:
                continue
            if state.attributes.get("device_class") == "temperature":
                friendly = state.attributes.get("friendly_name", entity_id)
                temp_entities.append((entity_id, friendly))

        if not temp_entities:
            errors["base"] = "no_temp_sensors"
            # Setze room_thermostat_control auf false, da keine Sensoren verfügbar sind
            self._options["room_thermostat_control"] = False
            return self.async_show_form(step_id="room_sensor", errors=errors)

        # Sortiere nach Friendly Name
        temp_entities.sort(key=lambda x: x[1].lower())

        schema = {}
        for hc_idx in range(1, num_hc + 1):
            entity_key = CONF_ROOM_TEMPERATURE_ENTITY.format(hc_idx)
            schema[
                vol.Optional(entity_key, default=self._options.get(entity_key, ""))
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": eid, "label": fname} for eid, fname in temp_entities
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        return self.async_show_form(
            step_id="room_sensor", data_schema=vol.Schema(schema), errors=errors
        )

    async def _test_connection(self, user_input: dict[str, Any]) -> None:
        """Test the connection to the Lambda device."""
        # user_input argument is unused, kept for interface compatibility
        pass


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
