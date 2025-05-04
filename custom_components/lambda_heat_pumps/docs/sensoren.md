# Lambda Wärmepumpe Sensoren Dokumentation

## Übersicht
Dieses Dokument beschreibt alle verfügbaren Sensoren in der Lambda Wärmepumpen-Integration, mit Fokus auf die neu hinzugefügten Puffer- und Solarmodulsensoren.

## Puffermodul-Sensoren
Basis-Adressbereich: 3000-3400

### Zustandssensoren
- **Puffer Betriebszustand**: Aktueller Betriebszustand des Puffers
  - Adresse: 3000
  - Typ: Zustandssensor
  - Zustände: Gemäß BUFFER_OPERATING_STATE zugeordnet
  - Einheit: Keine

### Temperatursensoren
- **Puffer Temperatur Oben**: Temperatur im oberen Bereich des Puffers
  - Adresse: 3100
  - Typ: Temperatursensor
  - Einheit: °C
  - Skalierungsfaktor: 0,1

- **Puffer Temperatur Unten**: Temperatur im unteren Bereich des Puffers
  - Adresse: 3101
  - Typ: Temperatursensor
  - Einheit: °C
  - Skalierungsfaktor: 0,1

- **Puffer Solltemperatur**: Zieltemperatur für den Puffer
  - Adresse: 3102
  - Typ: Temperatursensor
  - Einheit: °C
  - Skalierungsfaktor: 0,1

## Solarmodul-Sensoren
Basis-Adressbereich: 4000-4100

### Zustandssensoren
- **Solar Betriebszustand**: Aktueller Betriebszustand der Solaranlage
  - Adresse: 4000
  - Typ: Zustandssensor
  - Zustände: Gemäß SOLAR_OPERATING_STATE zugeordnet
  - Einheit: Keine

### Temperatursensoren
- **Solar Kollektortemperatur**: Temperatur am Solarkollektor
  - Adresse: 4100
  - Typ: Temperatursensor
  - Einheit: °C
  - Skalierungsfaktor: 0,1

- **Solar Speichertemperatur**: Temperatur des Solarspeichers
  - Adresse: 4101
  - Typ: Temperatursensor
  - Einheit: °C
  - Skalierungsfaktor: 0,1

### Leistungssensoren
- **Solar Aktuelle Leistung**: Aktuelle Leistungsabgabe der Solaranlage
  - Adresse: 4200
  - Typ: Leistungssensor
  - Einheit: kW
  - Skalierungsfaktor: 0,1

- **Solar Gesamtenergie**: Gesamte erzeugte Energie der Solaranlage
  - Adresse: 4201
  - Typ: Energiesensor
  - Einheit: kWh
  - Skalierungsfaktor: 1

## Konfiguration
Sowohl Puffer- als auch Solarmodule können in der Integrationseinrichtung konfiguriert werden:
- Anzahl der Puffermodule: 1-10
- Anzahl der Solarmodule: 1-10

## Firmware-Kompatibilität
Alle neuen Sensoren sind ab Firmware-Version 1 verfügbar.

## Hinweise
- Alle Temperatursensoren verwenden einen Skalierungsfaktor von 0,1 für präzise Messungen
- Zustandssensoren verwenden spezifische Zustandszuordnungen, die in der Integration definiert sind
- Alle Sensoren werden gemäß dem konfigurierten Aktualisierungsintervall aktualisiert
- Sensoren werden basierend auf der Anzahl der konfigurierten Module automatisch erstellt

## Fehlerbehandlung
- Ungültige oder nicht verfügbare Sensorwerte werden als Fehler gemeldet
- Zustandssensoren mit unbekannten Zuständen melden "unbekannt"
- Temperatursensoren mit ungültigen Messwerten melden "nicht verfügbar"

## Zentrale Filterung und Optionen
- Sensoren werden nur angezeigt, wenn sie mit der gewählten Firmware-Version kompatibel sind (zentrale Filterung über `utils.py`).
- Die Firmware-Version und Temperaturbereiche sind jederzeit im Options-Dialog konfigurierbar.
- Initialwerte für Sensoren (z.B. Dummy) können in const.py gesetzt werden. 