# Dynamic Sensor Workflow

## Initialization of Dynamic Sensors

1. **`async_setup_entry` in `__init__.py`**:
   - Called when the integration is set up in Home Assistant.
   - Initializes the `LambdaDataUpdateCoordinator`, responsible for cyclically fetching Modbus data.
   - Calls `async_refresh` to immediately update data.

2. **`LambdaDataUpdateCoordinator` in `coordinator.py`**:
   - Inherits from `DataUpdateCoordinator` and manages fetching data from Modbus registers.
   - The `_async_update_data` method reads Modbus registers for each configured instance (heat pump, boiler, heating circuit) and each template.
   - The number of instances is determined by the configuration (`num_hps`, `num_boil`, `num_hc`).
   - Firmware compatibility is checked; unsupported sensors are skipped.
   - Results are scaled and stored in a data dictionary used by the entities.

3. **`async_setup_entry` in `sensor.py`**:
   - Called to create sensor entities in Home Assistant.
   - For each configured instance (HP, Boiler, HC) and each template, dynamic sensor entities are created if compatible with the firmware.
   - No entities are created if num_boil or num_hc = 0.

4. **`LambdaSensor` in `sensor.py`**:
   - Represents a single sensor in Home Assistant.
   - Inherits from `CoordinatorEntity` and `SensorEntity` and displays sensor data in the UI.
   - Fetches values from the coordinator's data dictionary.

5. **`async_setup_entry` in `climate.py`**:
   - Creates a separate climate entity for each boiler and HC instance, referencing the appropriate dynamic sensors.
   - Climate entities are only created if num_boil or num_hc > 0 and the sensors are compatible with the firmware.

6. **`LambdaClimateEntity` in `climate.py`**:
   - Represents a climate entity (hot water, heating circuit) in Home Assistant.
   - Reads current and target values from the dynamic sensors.
   - Allows setting the target value via Modbus.
   - Each climate entity gets a unique unique_id with instance number (e.g. eu08l_hot_water_1_climate).
   - Device info is always generated via build_device_info, so all entities (sensors, climate) are grouped under the correct subdevice and duplicate devices are avoided.

## Update of Dynamic Sensors

1. **`_async_update_data` in `LambdaDataUpdateCoordinator`**:
   - Called regularly to fetch data from Modbus registers.
   - Reads Modbus registers for each configured instance (HP, Boiler, HC) and each template.
   - Checks firmware compatibility and scales values.
   - Stores results in the coordinator's data dictionary.

2. **Sensor and Climate Entities**:
   - Use the updated data from the coordinator to update their state in the Home Assistant UI.
   - Climate entities can set target values via Modbus if supported.
