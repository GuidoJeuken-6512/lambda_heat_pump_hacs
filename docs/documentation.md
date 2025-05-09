# Lambda Wärmepumpe Integration - Dokumentation

## Modbus-Kommunikation

Die Integration kommuniziert mit der Lambda WP über Modbus TCP/IP. Die Kommunikation verwendet folgende Modbus-Funktionscodes:

- **Lesen von Registern**: Funktionscode 0x03 (Read Multiple Holding Registers)
- **Schreiben von Registern**: Funktionscode 0x10 (Write Multiple Registers)

### Register-Adressierung

Die Register werden wie folgt adressiert:

- Wärmepumpe: Basisadresse 4000
- Boiler: Basisadressen 4100, 4200, 4300, 4400 (für bis zu 4 Boiler)
- Heizkreis: Basisadressen 5000, 5100, 5200, 5300 (für bis zu 4 Heizkreise)
- Puffer: Basisadressen 6000, 6100, 6200, 6300 (für bis zu 4 Puffer)
- Solar: Basisadressen 7000, 7100, 7200, 7300 (für bis zu 4 Solaranlagen)

Die relative Adresse wird zur Basisadresse addiert, um die absolute Modbus-Registeradresse zu erhalten.

### Register-Typen

Die Integration unterstützt folgende Register-Typen:

- **Nur Lesen**: Sensoren und Statusinformationen
- **Lesen und Schreiben**: Zieltemperaturen und Steuerungsparameter

### Datenformate

Die Register verwenden folgende Datenformate:

- **int16**: 16-Bit vorzeichenbehaftete Ganzzahl
- **uint16**: 16-Bit vorzeichenlose Ganzzahl
- **float**: 32-Bit Fließkommazahl (zwei aufeinanderfolgende Register)

### Skalierung

Die Werte werden mit einem Skalierungsfaktor multipliziert, um die tatsächlichen Werte zu erhalten. Beispiel:

- Temperaturen: Skalierungsfaktor 0.1 (Registerwert 250 = 25,0°C)
- Drücke: Skalierungsfaktor 0.1 (Registerwert 150 = 15,0 bar)
- Durchflussraten: Skalierungsfaktor 0.1 (Registerwert 100 = 10,0 l/min)

## Deaktivierte Register

Die Integration bietet die Möglichkeit, bestimmte Modbus-Register zu deaktivieren, die in Ihrer spezifischen Konfiguration nicht vorhanden sind oder Fehler verursachen. Dies ist besonders nützlich, wenn:

- Bestimmte Sensoren in Ihrer Wärmepumpen-Konfiguration nicht vorhanden sind
- Modbus-Fehler für bestimmte Register auftreten
- Sie die Anzahl der Modbus-Anfragen reduzieren möchten

### Konfiguration

1. Aktivieren Sie den Debug-Modus in den Integrationseinstellungen
2. Beobachten Sie die Logs für Modbus-Fehler
3. Notieren Sie die Register-Adressen aus den Fehlermeldungen (z.B. "Modbus error for sensor_name (address: 1234)")
4. Tragen Sie die Adressen in die `disabled_registers.yaml` ein:

```yaml
disabled_registers:
  - 1234  # sensor_name
  - 1235  # another_sensor_name
```

5. Starten Sie Home Assistant neu

Die deaktivierten Register werden dann nicht mehr abgefragt, was die Fehlermeldungen beseitigt und die Performance verbessert.

### Technische Details

- Die deaktivierten Register werden beim Start der Integration geladen
- Die Konfiguration wird in einer YAML-Datei im Verzeichnis der Integration gespeichert
- Die Register-Adressen werden als Set gespeichert für effiziente Prüfung
- Debug-Logs zeigen die geladenen deaktivierten Register an
- Die Prüfung erfolgt vor jedem Modbus-Lesevorgang

## Struktur der Integration

Die Integration besteht aus folgenden Hauptdateien:

- **manifest.json**: Enthält Metadaten wie Name, Version, Abhängigkeiten (`pymodbus`), minimale Home Assistant Version (`2025.3.0`) und Konfigurationsdetails (`config_flow: true`, `iot_class: local_polling`).
- **const.py**: Definiert Konstanten, die in der gesamten Integration verwendet werden, einschließlich Domain-Name (`DOMAIN`), Standardwerte für Host/Port/Slave ID, verfügbare Firmware-Versionen (`FIRMWARE_VERSION`) und insbesondere die Templates für dynamische Modbus-Sensoren (`HP_SENSOR_TEMPLATES`, `BOIL_SENSOR_TEMPLATES`, `HC_SENSOR_TEMPLATES`, `BUFFER_SENSOR_TEMPLATES`, `SOLAR_SENSOR_TEMPLATES`) und deren Basisadressen. Die Anzahl der Instanzen (Wärmepumpen, Boiler, Heizkreise, Puffer, Solarmodule) wird über `num_hps`, `num_boil`, `num_hc`, `num_buffer`, `num_solar` konfiguriert.
- **__init__.py**: Initialisiert die Integration, richtet den zentralen `LambdaDataUpdateCoordinator` ein, lädt die Sensor- und Climate-Plattformen und registriert einen Listener für Konfigurationsänderungen, um die Integration bei Bedarf neu zu laden.
- **config_flow.py**: Implementiert den Konfigurationsfluss für die Einrichtung der Integration über die Home Assistant UI (`LambdaConfigFlow`) und den Options-Flow für die Anpassung der Einstellungen nach der Einrichtung (`LambdaOptionsFlow`). Die Anzahl der Instanzen für HP, Boiler, HC, Puffer und Solar kann während der Einrichtung ausgewählt werden.
- **sensor.py**: Definiert die Sensor-Plattform. Die Funktion `async_setup_entry` erstellt dynamisch Sensor-Entitäten für jede konfigurierte Instanz (HP, Boiler, HC, Puffer, Solar) und jedes Template. Die Firmware-Kompatibilität wird geprüft. Die Klasse `LambdaSensor` repräsentiert einen einzelnen Sensor und holt seine Daten vom Coordinator.
- **climate.py**: Definiert die Climate-Plattform. Für jede Boiler- und HC-Instanz wird dynamisch eine separate Climate-Entität erstellt, die auf die entsprechenden dynamischen Sensoren verweist. Die Zieltemperatur kann über die Climate-Entität eingestellt werden.
- **coordinator.py**: Enthält die Klasse `LambdaDataUpdateCoordinator`, die zyklisch alle konfigurierten und kompatiblen Sensoren (HP, Boiler, HC, Puffer, Solar) ausliest und die Werte für die Entitäten bereitstellt.

## Dynamische Sensor- und Climate-Generierung

- Die Anzahl der Wärmepumpen (`num_hps`), Boiler (`num_boil`), Heizkreise (`num_hc`), Puffer (`num_buffer`) und Solarmodule (`num_solar`) wird während der Einrichtung festgelegt.
- Für jede Instanz und jedes Template werden Sensoren dynamisch erstellt (z.B. `hp1_flow_line_temperature`, `boil2_actual_high_temperature`, `hc1_room_device_temperature`, `buffer1_actual_high_temp`, `solar1_collector_temp`).
- Climate-Entitäten für Warmwasser und Heizkreis werden ebenfalls pro Instanz dynamisch erstellt (z.B. `climate.hot_water_1`, `climate.heating_circuit_2`).
- Die Firmware-Version wird berücksichtigt: Sensoren/Entitäten werden nur erstellt, wenn sie mit der ausgewählten Firmware kompatibel sind.
- Wenn die Anzahl einer Komponente (Boiler, Heizkreise, Puffer, Solarmodule) auf 0 gesetzt wird, werden keine entsprechenden Entitäten erstellt.

## Raumthermostatsteuerung

Die Integration bietet eine Raumthermostatsteuerung, die die Verwendung externer Temperatursensoren für jeden Heizkreis ermöglicht:

- Aktivierung über die Option `room_thermostat_control` während der Einrichtung oder in den Optionen
- Nach der Aktivierung wird ein zusätzlicher Konfigurationsschritt angezeigt, bei dem für jeden konfigurierten Heizkreis ein Temperatursensor ausgewählt werden kann
- Die ausgewählten Sensoren werden im `options`-Dict des Config-Entrys gespeichert
- Die gemessenen Temperaturen werden über Modbus an die entsprechenden Register der Wärmepumpe übertragen
- Die Wärmepumpe verwendet diese Werte anstelle ihrer internen Messungen für die Heizkreissteuerung
- Die Übertragung erfolgt automatisch in regelmäßigen Abständen (konfiguriert über `ROOM_TEMPERATURE_UPDATE_INTERVAL`)

## Zentrale Firmware- und Sensor-Filterung
- Die Firmware-Version kann später im Options-Dialog geändert werden und löst einen vollständigen Reload aus (einschließlich Filterung der Sensoren und Entitäten).
- Sensoren und Entitäten werden **zentral** nach Firmware gefiltert (siehe `utils.py`).
- Temperaturbereiche, Schritte und Firmware-Version sind jederzeit im Options-Dialog konfigurierbar.
- Initialwerte für Sensoren (z.B. Dummy) können in const.py gesetzt werden.
- Beim Speichern der Konfiguration und Optionen werden die geschriebenen Werte im Home Assistant Log (DEBUG) ausgegeben.

## Home Assistant 2025.3 Kompatibilität (aktualisiert)
- Moderne Konfigurations- und Options-Flows
- Zentrale Filterfunktion für Firmware-Kompatibilität (`get_compatible_sensors` in utils.py)
- Debug-Logging beim Speichern der Konfiguration/Optionen
- Alle Features und Optionen sind vollständig über die UI konfigurierbar

## Raumthermostatsteuerung & Modbus-Schreibvorgang

Die Integration ermöglicht die Auswahl eines beliebigen externen Temperatursensors aus Home Assistant für jeden Heizkreis (Dropdown, nur Fremdsensoren mit device_class 'temperature'). Die Auswahl erfolgt im Options-Flow. Die gemessenen Werte werden automatisch und regelmäßig (z.B. jede Minute) in die Modbus-Register der jeweiligen Heizkreise geschrieben. Dies wird von der Service-Funktion `async_update_room_temperature` in `services.py` behandelt, die den Wert für jeden Kreis liest, validiert und über den Modbus-Client in das richtige Register schreibt. Fehler werden protokolliert. Die Übertragung kann auch manuell über den Service `lambda.update_room_temperature` ausgelöst werden. Jeder Schreibvorgang wird auf Debug-Level protokolliert. Die technische Implementierung und der Prozess sind in `services.py` dokumentiert.

## Workflow

1. **Setup (`async_setup_entry` in `__init__.py`)**:
    * Wenn die Integration über die UI hinzugefügt wird, wird `async_setup_entry` aufgerufen.
    * Ein `LambdaDataUpdateCoordinator` wird erstellt.
    * Der Coordinator versucht das erste Datenupdate (`async_refresh()`).
    * Die Daten des Coordinators werden im `hass.data` Dictionary gespeichert.
    * Die Sensor- und Climate-Plattformen (`sensor.py`, `climate.py`) werden geladen (`async_forward_entry_setups`).
    * Ein Update-Listener (`async_reload_entry`) wird registriert, um auf Konfigurationsänderungen zu reagieren.

2. **Platform Setup (`async_setup_entry` in `sensor.py` & `climate.py`)**:
    * Jede Plattform erhält den Coordinator aus `hass.data`.
    * Die konfigurierte Firmware-Version und Instanzanzahlen werden aus `entry.data` gelesen.
    * Für jede Instanz und jedes Template werden Sensoren und Climate-Entitäten dynamisch erstellt, wenn sie mit der Firmware kompatibel sind.
    * Alle erstellten Entitäten werden über `async_add_entities` zu Home Assistant hinzugefügt.

3. **Daten Update (`_async_update_data` in `LambdaDataUpdateCoordinator`)**:
    * Diese Methode wird periodisch aufgerufen (gemäß `SCAN_INTERVAL`).
    * Stellt die Verbindung zum Modbus-Gerät her, falls noch nicht verbunden.
    * Liest Modbus-Register für jede konfigurierte Instanz (HP, Boiler, HC, Puffer, Solar) und jedes Template.
    * Verarbeitet Rohdaten basierend auf Datentyp (`int16`, `int32`) und Skalierung (`scale`).
    * Speichert die verarbeiteten Werte in einem Dictionary.
    * Gibt das Daten-Dictionary zurück. Home Assistant benachrichtigt dann alle abhängigen Entitäten über die neuen Daten.

4. **Konfigurations Flow (`config_flow.py`)**:
    * **`LambdaConfigFlow`**: Wird aufgerufen, wenn die Integration hinzugefügt wird.
        * `async_step_user`: Zeigt das initiale Formular (Name, Host, Port, Slave ID, Debug-Modus, Firmware-Version, Anzahl HP/Boiler/HC/Puffer/Solar). Firmware-Optionen werden aus `FIRMWARE_VERSION` generiert. Nach der Eingabe werden die Daten validiert und ein Config-Entry erstellt (`async_create_entry`).
        * `async_step_room_sensor`: Wird aufgerufen, wenn die Raumthermostatsteuerung aktiviert wird. Listet verfügbare Temperatursensoren auf und ermöglicht die Auswahl pro Heizkreis.
    * **`LambdaOptionsFlow`**: Wird aufgerufen, wenn der Benutzer die Integrationsoptionen bearbeitet.
        * `async_step_init`: Zeigt das Options-Formular (Temperaturbereiche, Update-Intervall, Firmware-Version, Raumthermostatsteuerung). Die Anzahl der Instanzen kann danach nicht mehr geändert werden.
        * `async_step_room_sensor`: Wird aufgerufen, wenn die Raumthermostatsteuerung aktiviert oder geändert wird.

5. **Reload bei Konfigurationsänderung (`async_reload_entry` in `__init__.py`)**:
    * Der in `async_setup_entry` registrierte Listener ruft diese Funktion auf, wenn sich die Config-Entry-Daten ändern (z.B. über den Options-Flow).
    * Entlädt die Plattformen (`async_unload_platforms`).
    * Schließt die Modbus-Verbindung.
    * Ruft `async_setup_entry` erneut auf, um die Integration mit den neuen Einstellungen neu zu initialisieren.

## Klassen und Methoden

* **LambdaDataUpdateCoordinator (`coordinator.py`)**
    * `__init__(hass, entry)`: Initialisiert den Coordinator, speichert den Config-Entry und setzt den Modbus-Client auf `None`. Übergibt `config_entry` an die Superklasse.
    * `_async_update_data()`: Hauptmethode zum Abrufen von Daten. Stellt die Verbindung her, liest alle relevanten Modbus-Register für alle konfigurierten Instanzen und Templates, verarbeitet die Daten und gibt sie zurück. Implementiert Fehlerbehandlung für die Modbus-Kommunikation.

* **LambdaConfigFlow (`config_flow.py`)**
    * `async_step_user(user_input)`: Behandelt den initialen Setup-Schritt. Zeigt das Formular und erstellt den Config-Entry.
    * `async_step_room_sensor(user_input)`: Ermöglicht die Auswahl von Temperatursensoren für die Raumthermostatsteuerung.

* **LambdaOptionsFlow (`config_flow.py`)**
    * `async_step_init(user_input)`: Behandelt den Options-Flow. Zeigt das Formular. Aktualisiert die Hauptdaten (`config_entry.data`), wenn sich die Firmware-Version ändert, und speichert die restlichen Optionen.
    * `async_step_room_sensor(user_input)`: Ermöglicht das Ändern der Temperatursensoren für die Raumthermostatsteuerung.

* **LambdaSensor (`sensor.py`)**
    * `__init__(coordinator, entry, sensor_id, sensor_config)`: Initialisiert die Sensor-Entität. Speichert die Konfiguration, setzt Attribute wie Name, `unique_id`, Einheit, `device_class`, `state_class` und Präzision basierend auf dem Template.
    * `native_value`: Property, die den aktuellen Wert vom Coordinator abruft. Die Skalierung wird bereits im Coordinator angewendet.

* **LambdaClimateEntity (`climate.py`)**
    * `__init__(coordinator, entry, climate_type, translation_key, current_temp_sensor, target_temp_sensor, min_temp, max_temp, temp_step)`: Initialisiert die Climate-Entität. Speichert Typ, Namen der erforderlichen Temperatursensoren und Temperaturgrenzen. Setzt Attribute wie Name, `unique_id`, Temperatureinheit, unterstützte Features und HVAC-Modi.
    * `current_temperature`: Property, die den Wert von `current_temp_sensor` vom Coordinator abruft.
    * `target_temperature`: Property, die den Wert von `target_temp_sensor` vom Coordinator abruft.
    * `async_set_temperature(**kwargs)`: Methode zum Setzen der Zieltemperatur. Holt die Sensor-Definition aus dem entsprechenden Template, berechnet den Rohwert für Modbus, schreibt den Wert über den Modbus-Client des Coordinators und aktualisiert den lokalen Coordinator-Cache und den HA-Status.

## Neue Features und Verbesserungen

- Jede Climate-Entität (z.B. für Boiler 1, Boiler 2, HC 1, HC 2) erhält nun ihre eigene eindeutige unique_id (z.B. eu08l_hot_water_1_climate).
- Device-Info wird immer über den zentralen build_device_info Helper in utils.py generiert. Dies vermeidet doppelte Geräte in Home Assistant und stellt sicher, dass alle Entitäten (Sensoren, Climate) unter dem richtigen Untergerät gruppiert sind (z.B. "Boiler 2").
- Namen von Climate-Entitäten werden dynamisch und übersetzbar generiert, einschließlich Nummerierung bei mehreren Instanzen.

---

Diese Dokumentation beschreibt die aktuelle, dynamische Architektur der Integration (Stand April 2025). 