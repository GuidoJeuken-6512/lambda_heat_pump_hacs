# Ablauf der Dynamischen Sensoren

## Initialisierung der Dynamischen Sensoren

1. **`async_setup_entry` in `__init__.py`**:
   - Wird beim Einrichten der Integration in Home Assistant aufgerufen.
   - Initialisiert den `LambdaDataUpdateCoordinator`, der für das zyklische Abrufen der Modbus-Daten verantwortlich ist.
   - Ruft `async_refresh` auf, um die Daten sofort zu aktualisieren.

2. **`LambdaDataUpdateCoordinator` in `coordinator.py`**:
   - Erbt von `DataUpdateCoordinator` und verwaltet das Abrufen der Daten von den Modbus-Registrierungen.
   - Die Methode `_async_update_data` liest für jede konfigurierte Instanz (Wärmepumpe, Boiler, Heizkreis) und jedes Template die Modbus-Register aus.
   - Die Anzahl der Instanzen wird über die Konfiguration (`num_hps`, `num_boil`, `num_hc`) bestimmt.
   - Die Firmware-Kompatibilität wird geprüft, nicht unterstützte Sensoren werden übersprungen.
   - Die Ergebnisse werden skaliert und in einem Datenwörterbuch gespeichert, das von den Entitäten verwendet wird.

3. **`async_setup_entry` in `sensor.py`**:
   - Wird aufgerufen, um die Sensor-Entitäten in Home Assistant zu erstellen.
   - Für jede konfigurierte Instanz (HP, Boiler, HC) und jedes Template werden dynamisch Sensor-Entitäten erzeugt, sofern sie mit der Firmware kompatibel sind.
   - Es werden keine Entitäten erzeugt, wenn num_boil oder num_hc = 0 ist.

4. **`LambdaSensor` in `sensor.py`**:
   - Repräsentiert einen einzelnen Sensor in Home Assistant.
   - Erbt von `CoordinatorEntity` und `SensorEntity` und zeigt die Sensordaten in der Oberfläche an.
   - Holt die Werte aus dem Koordinator-Datenwörterbuch.

5. **`async_setup_entry` in `climate.py`**:
   - Erzeugt für jede Boiler- und HC-Instanz eine eigene Climate-Entity, die auf die passenden dynamischen Sensoren verweist.
   - Climate-Entitäten werden nur erzeugt, wenn num_boil bzw. num_hc > 0 ist und die Sensoren mit der Firmware kompatibel sind.

6. **`LambdaClimateEntity` in `climate.py`**:
   - Repräsentiert eine Climate-Entität (Warmwasser, Heizkreis) in Home Assistant.
   - Liest Ist- und Sollwert aus den dynamischen Sensoren.
   - Ermöglicht das Setzen des Sollwerts über Modbus.
   - Jede Climate-Entity erhält eine eindeutige unique_id mit Instanznummer (z. B. eu08l_hot_water_1_climate).
   - Die Device-Info wird zentral über build_device_info erzeugt, sodass alle Entities (Sensoren, Climate) dem richtigen Subgerät zugeordnet werden. Doppelte Geräte werden so vermieden.

## Update der Dynamischen Sensoren

1. **`_async_update_data` in `LambdaDataUpdateCoordinator`**:
   - Wird regelmäßig aufgerufen, um die Daten von den Modbus-Registrierungen abzurufen.
   - Liest für jede konfigurierte Instanz (HP, Boiler, HC) und jedes Template die Modbus-Register aus.
   - Prüft die Firmware-Kompatibilität und skaliert die Werte.
   - Speichert die Ergebnisse im Koordinator-Datenwörterbuch.

2. **Sensor- und Climate-Entitäten**:
   - Verwenden die aktualisierten Daten aus dem Koordinator, um ihre Zustände in der Home Assistant-Benutzeroberfläche anzuzeigen.
   - Climate-Entitäten können Sollwerte über Modbus setzen, sofern unterstützt.