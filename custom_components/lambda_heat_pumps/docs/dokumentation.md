# Lambda Wärmepumpen Integration - Dokumentation

## Struktur der Integration

Die Integration besteht aus folgenden Hauptdateien:

- **manifest.json**: Enthält Metadaten wie Name, Version, Abhängigkeiten (`pymodbus`), minimale Home Assistant Version (`2025.3.0`) und Konfigurationsdetails (`config_flow: true`, `iot_class: local_polling`).
- **const.py**: Definiert Konstanten, die in der gesamten Integration verwendet werden, darunter der Domain-Name (`DOMAIN`), Standardwerte für Host/Port/Slave-ID, verfügbare Firmware-Versionen (`FIRMWARE_VERSION`) und insbesondere die Templates für dynamische Modbus-Sensoren (`HP_SENSOR_TEMPLATES`, `BOIL_SENSOR_TEMPLATES`, `HC_SENSOR_TEMPLATES`, `BUFFER_SENSOR_TEMPLATES`, `SOLAR_SENSOR_TEMPLATES`) und deren Basisadressen. Die Anzahl der Instanzen (Wärmepumpen, Boiler, Heizkreise, Pufferspeicher, Solarmodule) wird über `num_hps`, `num_boil`, `num_hc`, `num_buffer`, `num_solar` konfiguriert.
- **__init__.py**: Initialisiert die Integration, richtet den zentralen `LambdaDataUpdateCoordinator` ein, lädt die Sensor- und Klima-Plattformen und registriert einen Listener für Konfigurationsänderungen, um die Integration bei Bedarf neu zu laden.
- **config_flow.py**: Implementiert den Konfigurationsfluss für die Einrichtung der Integration über die Home Assistant UI (`LambdaConfigFlow`) und den Options-Fluss für die Anpassung der Einstellungen nach der Einrichtung (`LambdaOptionsFlow`). Die Anzahl der Instanzen für HP, Boiler, HC, Pufferspeicher und Solar kann während der Einrichtung ausgewählt werden.
- **sensor.py**: Definiert die Sensor-Plattform. Die Funktion `async_setup_entry` erstellt dynamisch Sensor-Entitäten für jede konfigurierte Instanz (HP, Boiler, HC, Pufferspeicher, Solar) und jedes Template. Die Firmware-Kompatibilität wird überprüft. Die Klasse `LambdaSensor` repräsentiert einen einzelnen Sensor und bezieht seine Daten vom Coordinator.
- **climate.py**: Definiert die Klima-Plattform. Für jede Boiler- und HC-Instanz wird eine separate Klima-Entität dynamisch erstellt, die auf die entsprechenden dynamischen Sensoren verweist. Die Zieltemperatur kann über die Klima-Entität eingestellt werden.
- **coordinator.py**: Enthält die Klasse `LambdaDataUpdateCoordinator`, die zyklisch alle konfigurierten und kompatiblen Sensoren (HP, Boiler, HC, Pufferspeicher, Solar) ausliest und die Werte für die Entitäten bereitstellt.

## Dynamische Sensor- und Klima-Generierung

- Die Anzahl der Wärmepumpen (`num_hps`), Boiler (`num_boil`), Heizkreise (`num_hc`), Pufferspeicher (`num_buffer`) und Solarmodule (`num_solar`) wird während der Einrichtung festgelegt.
- Für jede Instanz und jedes Template werden Sensoren dynamisch erstellt (z.B. `hp1_flow_line_temperature`, `boil2_actual_high_temperature`, `hc1_room_device_temperature`, `buffer1_actual_high_temp`, `solar1_collector_temp`).
- Klima-Entitäten für Warmwasser und Heizkreis werden ebenfalls pro Instanz dynamisch erstellt (z.B. `climate.hot_water_1`, `climate.heating_circuit_2`).
- Die Firmware-Version wird berücksichtigt: Sensoren/Entitäten werden nur erstellt, wenn sie mit der ausgewählten Firmware kompatibel sind.
- Wenn die Anzahl einer Komponente (Boiler, Heizkreise, Pufferspeicher, Solarmodule) auf 0 gesetzt wird, werden keine entsprechenden Entitäten erstellt.

## Raumthermostatsteuerung & Modbus-Schreibvorgang

Die Integration ermöglicht es, für jeden Heizkreis einen beliebigen externen Temperatursensor aus Home Assistant auszuwählen (Dropdown, nur Fremdsensoren mit device_class 'temperature'). Die Auswahl erfolgt im Options-Flow. Die gemessenen Werte werden automatisch und regelmäßig (z.B. jede Minute) in die Modbus-Register der jeweiligen Heizkreise geschrieben. Dies geschieht über die Service-Funktion `async_update_room_temperature` in `services.py`, die für jeden Heizkreis den Wert ausliest, prüft und über den Modbus-Client in das passende Register schreibt. Fehler werden geloggt. Die Übertragung kann auch manuell über den Service `lambda.update_room_temperature` ausgelöst werden. Jeder Schreibvorgang wird im Log dokumentiert (Debug-Level). Die technische Umsetzung und der Ablauf sind in `services.py` dokumentiert.

## Zentrale Firmware- und Sensor-Filterung
- Die Firmware-Version kann nachträglich im Options-Dialog geändert werden und triggert ein vollständiges Reload (inkl. Filterung der Sensoren und Entitäten).
- Sensoren und Entitäten werden **zentral** nach Firmware gefiltert (siehe `utils.py`).
- Temperaturbereiche, Schritte und Firmware-Version sind jederzeit im Options-Dialog konfigurierbar.
- Initialwerte für Sensoren (z.B. Dummy) können in const.py gesetzt werden.
- Beim Speichern der Konfiguration und Optionen werden die geschriebenen Werte im Home Assistant Log (DEBUG) ausgegeben.

## Home Assistant 2025.3 Kompatibilität (aktualisiert)
- Moderne Konfigurations- und Options-Flows
- Zentrale Filterfunktion für Firmware-Kompatibilität (`get_compatible_sensors` in utils.py)
- Debug-Logging beim Speichern der Konfiguration/Optionen
- Alle Features und Optionen sind vollständig UI-basiert konfigurierbar

## Workflow

1. **Setup (`async_setup_entry` in `__init__.py`)**:
    * Wenn die Integration über die UI hinzugefügt wird, wird `async_setup_entry` aufgerufen.
    * Ein `LambdaDataUpdateCoordinator` wird erstellt.
    * Der Coordinator versucht das erste Daten-Update (`async_refresh()`).
    * Die Daten des Coordinators werden im `hass.data`-Dictionary gespeichert.
    * Die Sensor- und Klima-Plattformen (`sensor.py`, `climate.py`) werden geladen (`async_forward_entry_setups`).
    * Ein Update-Listener (`async_reload_entry`) wird registriert, um auf Konfigurationsänderungen zu reagieren.

2. **Plattform-Setup (`async_setup_entry` in `sensor.py` & `climate.py`)**:
    * Jede Plattform bezieht den Coordinator aus `hass.data`.
    * Die konfigurierte Firmware-Version und Anzahl der Instanzen werden aus `entry.data` gelesen.
    * Für jede Instanz und jedes Template werden Sensoren und Klima-Entitäten dynamisch erstellt, wenn sie mit der Firmware kompatibel sind.
    * Alle erstellten Entitäten werden mittels `async_add_entities` zu Home Assistant hinzugefügt.

3. **Daten-Update (`_async_update_data` in `LambdaDataUpdateCoordinator`)**:
    * Diese Methode wird periodisch aufgerufen (entsprechend `SCAN_INTERVAL`).
    * Verbindung zum Modbus-Gerät, falls noch nicht verbunden.
    * Auslesen der Modbus-Register für jede konfigurierte Instanz (HP, Boiler, HC, Pufferspeicher, Solar) und jedes Template.
    * Verarbeitung der Rohdaten basierend auf Datentyp (`int16`, `int32`) und Skalierung (`scale`).
    * Speicherung der verarbeiteten Werte in einem Dictionary.
    * Rückgabe des Daten-Dictionaries. Home Assistant benachrichtigt dann alle abhängigen Entitäten über die neuen Daten.

4. **Konfigurationsfluss (`config_flow.py`)**:
    * **`LambdaConfigFlow`**: Wird beim Hinzufügen der Integration aufgerufen.
        * `async_step_user`: Zeigt das initiale Formular (Name, Host, Port, Slave-ID, Debug-Modus, Firmware-Version, Anzahl HP/Boiler/HC). Firmware-Optionen werden aus `FIRMWARE_VERSION` generiert. Nach der Eingabe werden die Daten validiert und ein Config-Eintrag erstellt (`async_create_entry`).
        * `async_step_room_sensor`: Wird aufgerufen, wenn die Raumthermostatsteuerung aktiviert wird. Listet verfügbare Temperatursensoren auf und ermöglicht die Auswahl pro Heizkreis.
    * **`LambdaOptionsFlow`**: Wird aufgerufen, wenn der Benutzer die Integrationsoptionen bearbeitet.
        * `async_step_init`: Zeigt das Optionen-Formular (Temperaturbereiche, Update-Intervall, Firmware-Version, Raumthermostatsteuerung). Die Anzahl der Instanzen kann nachträglich nicht geändert werden.
        * `async_step_room_sensor`: Wird aufgerufen, wenn die Raumthermostatsteuerung aktiviert oder geändert wird.

5. **Neuladen bei Konfigurationsänderung (`async_reload_entry` in `__init__.py`)**:
    * Der in `async_setup_entry` registrierte Listener ruft diese Funktion auf, wenn sich die Config-Entry-Daten ändern (z.B. über den Options-Fluss).
    * Entladen der Plattformen (`async_unload_platforms`).
    * Schließen der Modbus-Verbindung.
    * Erneuter Aufruf von `async_setup_entry`, um die Integration mit den neuen Einstellungen zu initialisieren.

## Klassen und Methoden

* **LambdaDataUpdateCoordinator (`coordinator.py`)**
    * `__init__(hass, entry)`: Initialisiert den Coordinator, speichert den Config-Entry und setzt den Modbus-Client auf `None`. Gibt `config_entry` an die Superklasse weiter.
    * `_async_update_data()`: Hauptmethode zum Abrufen von Daten. Verbindet, liest alle relevanten Modbus-Register für alle konfigurierten Instanzen und Templates, verarbeitet die Daten und gibt sie zurück. Implementiert Fehlerbehandlung für Modbus-Kommunikation.

* **LambdaConfigFlow (`config_flow.py`)**
    * `async_step_user(user_input)`: Behandelt den initialen Einrichtungsschritt. Zeigt das Formular und erstellt den Config-Entry.
    * `async_step_room_sensor(user_input)`: Ermöglicht die Auswahl von Temperatursensoren für die Raumthermostatsteuerung.

* **LambdaOptionsFlow (`config_flow.py`)**
    * `async_step_init(user_input)`: Behandelt den Options-Fluss. Zeigt das Formular. Aktualisiert die Hauptdaten (`config_entry.data`), wenn sich die Firmware-Version ändert, und speichert die restlichen Optionen.
    * `async_step_room_sensor(user_input)`: Ermöglicht die Änderung der Temperatursensoren für die Raumthermostatsteuerung.

* **LambdaSensor (`sensor.py`)**
    * `__init__(coordinator, entry, sensor_id, sensor_config)`: Initialisiert die Sensor-Entität. Speichert Konfiguration, setzt Attribute wie Name, `unique_id`, Einheit, `device_class`, `state_class` und Präzision basierend auf dem Template.
    * `native_value`: Property, das den aktuellen Wert vom Coordinator abruft. Skalierung ist bereits im Coordinator angewendet.

* **LambdaClimateEntity (`climate.py`)**
    * `__init__(coordinator, entry, climate_type, translation_key, current_temp_sensor, target_temp_sensor, min_temp, max_temp, temp_step)`: Initialisiert die Klima-Entität. Speichert Typ, Namen der benötigten Temperatursensoren und Temperaturgrenzen. Setzt Attribute wie Name, `unique_id`, Temperatureinheit, unterstützte Funktionen und HVAC-Modi.
    * `current_temperature`: Property, das den Wert von `current_temp_sensor` vom Coordinator abruft.
    * `target_temperature`: Property, das den Wert von `target_temp_sensor` vom Coordinator abruft.
    * `async_set_temperature(**kwargs)`: Methode zum Einstellen der Zieltemperatur. Holt die Sensordefinition aus dem entsprechenden Template, berechnet den Rohwert für Modbus, schreibt den Wert über den Modbus-Client des Coordinators und aktualisiert den lokalen Coordinator-Cache und HA-State.

---

Diese Dokumentation beschreibt die aktuelle, dynamische Architektur der Integration (Stand: April 2025).
