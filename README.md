# Lambda Wärmepumpe Integration für Home Assistant / Lambda Heat Pump Integration for Home Assistant


---

## Deutsch

Diese benutzerdefinierte Integration ermöglicht die Einbindung von Lambda Wärmepumpen in Home Assistant über das Modbus/TCP Protokoll. Sie liest Sensordaten aus und ermöglicht die Steuerung von Klima-Entitäten (z.B. Warmwasser, Heizkreis).

**Features:**
- Auslesen diverser Sensoren der Wärmepumpe (Temperaturen, Zustände, Energieverbrauch etc.)
- Steuerung der Zieltemperatur für Warmwasser und Heizkreise über `climate`-Entitäten
- Dynamische Anpassung der Sensoren und Entitäten basierend auf der Firmware-Version und der konfigurierten Anzahl von Wärmepumpen, Boilern, Heizkreisen, Pufferspeichern und Solarmodulen
- Zentrale, konsistente Filterung aller Sensoren/Entitäten nach Firmware-Version (utils.py)
- Raumthermostatsteuerung: Verwendung externer Temperatursensoren für jeden Heizkreis
- Konfigurierbarer Update-Intervall
- **Firmware-Version, Temperaturbereiche und Schritte sind jederzeit im Options-Dialog änderbar**
- **Debug-Logging beim Speichern der Konfiguration/Optionen**
- Konfiguration vollständig über die Home Assistant UI (Integrations)

**Installation:**
1. Kopieren Sie den gesamten Ordner `custom_components/lambda_heat_pumps` in Ihren `custom_components` Ordner innerhalb Ihres Home Assistant Konfigurationsverzeichnisses.
Alle anderen Ordner müssen  nicht übernommen werden.
Der Ordner "docs" enthält die Dokumentation, er muss nicht auf das Home Assistant System übernommen werden. Er enthällt weietrführende Dokumentation.

2. Starten Sie Home Assistant neu.

Eine weitergehende Beschreibung der Installation und Konfiguration ist hier zu finden: https://homeassistant.com.de/homeassistant/lambda-waermepumpe-integration-fuer-home-assistant/


**Konfiguration:**
- Integration über die Home Assistant UI hinzufügen (`Einstellungen` → `Geräte & Dienste` → `Integration hinzufügen` → "Lambda WP")
- Geben Sie Name, Host, Port, Slave ID, Firmware-Version und die Anzahl der Wärmepumpen, Boiler, Heizkreise, Pufferspeicher und Solarmodule an
- **Für alle Gerätetypen (Wärmepumpe, Boiler, Heizkreis, Puffer, Solar) kann die Anzahl flexibel zwischen 0 und 5 gewählt werden.**
- Optional: Aktivieren Sie die Raumthermostatsteuerung, um externe Temperatursensoren für jeden Heizkreis zu verwenden
- Nach der Einrichtung können Temperaturbereiche, Firmware-Version und Update-Intervall **jederzeit** über die Optionen angepasst werden

**Raumthermostatsteuerung & Modbus-Schreibvorgang (Kurzfassung):**
- Externe Temperatursensoren können für jeden Heizkreis ausgewählt werden (Dropdown, nur Fremdsensoren mit device_class 'temperature').
- Die Integration schreibt die gemessenen Werte automatisch und regelmäßig in die Modbus-Register der Heizkreise.
- Das Schreiben erfolgt über die Service-Funktion in `services.py` und kann auch manuell per Service-Aufruf ausgelöst werden.

**Firmware- und Sensor-Handling:**
- Die Firmware-Version kann nachträglich im Options-Dialog geändert werden und triggert ein vollständiges Reload (inkl. Filterung der Sensoren)
- Sensoren und Entitäten werden **zentral** nach Firmware gefiltert (siehe `utils.py`)
- Initialwerte für Sensoren (z.B. Dummy) können in const.py gesetzt werden

**Hinweise für Home Assistant 2025.3:**
- Diese Integration ist vollständig kompatibel mit Home Assistant 2025.3 ff
- Verwendet den neuen DataUpdateCoordinator für optimale Leistung
- Typisierung und async/await nach den neuesten Standards
- Verbesserte Fehlerbehandlung und Logging
- Moderne Konfigurations- und Options-Flows

**Debugging:**
- Im Debug-Mode werden die geschriebenen Werte im Home Assistant Log (DEBUG) ausgegeben

**Bekannte Probleme:**
- Die Übersetzung in andere Sprachen (außer Deutsch und Englisch)
- Die Zuordnung von Sensoren zu Firmware-Ständen ist nicht korrekt

**Haftungsausschluss/Disclaimer:**

Die Nutzung dieser Software erfolgt auf eigene Gefahr. Es wird keine Haftung für Schäden, Datenverluste oder sonstige Folgen übernommen, die durch die Verwendung der Software entstehen. Jeglicher Regressanspruch ist ausgeschlossen.

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

---

## English

This custom integration allows you to connect Lambda heat pumps to Home Assistant via the Modbus/TCP protocol. It reads sensor data and enables control of climate entities (e.g., hot water, heating circuit).

**Features:**
- Reads various heat pump sensors (temperatures, states, energy consumption, etc.)
- Control of target temperature for hot water and heating circuits via `climate` entities
- Dynamic adaptation of sensors and entities based on firmware version and configured number of heat pumps, boilers, heating circuits, buffer tanks, and solar modules
- Central, consistent filtering of all sensors/entities by firmware version (utils.py)
- Room thermostat control: Use external temperature sensors for each heating circuit
- Configurable update interval
- **Firmware version, temperature ranges and steps can be changed at any time in the options dialog**
- **Debug logging when saving configuration/options**
- Configuration fully via the Home Assistant UI (Integrations)

**Installation:**
1. Copy the entire `lambda` folder into your `custom_components` directory inside your Home Assistant configuration folder.
However, all folders that are not required do not interfere with the integration.

2. Restart Home Assistant.
A more detailed description of the installation and configuration can be found here: https://homeassistant.com.de/homeassistant/lambda-waermepumpe-integration-fuer-home-assistant/

**Configuration:**
- Add the integration via the Home Assistant UI (`Settings` → `Devices & Services` → `Add Integration` → "Lambda WP")
- Enter name, host, port, slave ID, firmware version, and the number of heat pumps, boilers, heating circuits, buffer tanks, and solar modules
- **For all device types (heat pump, boiler, heating circuit, buffer, solar) the number can be flexibly set between 0 and 5 per type.**
- Optional: Enable room thermostat control to use external temperature sensors for each heating circuit
- After setup, temperature ranges, firmware version and update interval can be **changed at any time** via the options

**Room thermostat control & Modbus write process (short version):**
- External temperature sensors can be selected for each heating circuit (dropdown, only non-integration sensors with device_class 'temperature').
- The integration automatically and regularly writes the measured values to the Modbus registers of the heating circuits.
- Writing is handled by the service function in `services.py` and can also be triggered manually via a service call.

**Firmware and Sensor Handling:**
- The firmware version can be changed later in the options dialog and triggers a full reload (including filtering of sensors)
- Sensors and entities are **centrally** filtered by firmware (see `utils.py`)
- Initial values for sensors (e.g. dummy) can be set in const.py

**Notes for Home Assistant 2025.3:**
- This integration is fully compatible with Home Assistant 2025.3 ff
- Uses the new DataUpdateCoordinator for optimal performance
- Typing and async/await according to the latest standards
- Improved error handling and logging
- Modern configuration and options flows

**Debugging:**
- in debug mode the written values are output to the Home Assistant log (DEBUG)

**Known Issues:**
- Translation to other languages (besides German and English)
- the assignment of sensors to firmware stands is not correct

---

*Diese Integration wird nicht offiziell von Lambda unterstützt. / This integration is not officially supported by Lambda.*

---

## Modbus Test-Tools (Server & Client)

Für Entwicklung und Test der Integration steht ein separates Repository mit Modbus-Testtools zur Verfügung:

**GitHub:** [https://github.com/GuidoJeuken-6512/modbus_tools](https://github.com/GuidoJeuken-6512/modbus_tools)

**Enthalten:**
- Ein einfacher Modbus TCP Server (`server.py`), der Register aus einer YAML-Datei bereitstellt (ideal zum Mocken der Wärmepumpe)
- Ein grafischer Modbus TCP Client (`modbus_client.py`) zum Testen und Debuggen von Registerzugriffen

**Kurzanleitung:**
1. Repository klonen: `git clone https://github.com/GuidoJeuken-6512/modbus_tools`
2. In das Verzeichnis wechseln: `cd modbus_tools`
3. Server starten: `python server.py` (Register werden aus `config/registers.yaml` geladen)
4. Client starten: `python modbus_client.py` (GUI zum Lesen/Schreiben von Registern)

Weitere Details und Konfigurationsmöglichkeiten finden sich im README des Repositories und in den jeweiligen Python-Dateien.

---

**Haftungsausschluss/Disclaimer:**

Use of this software is at your own risk. No liability is accepted for any damages, data loss, or other consequences resulting from the use of this software. Any claims for compensation are excluded.

---
