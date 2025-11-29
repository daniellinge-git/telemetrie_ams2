# Lastenheft: AMS2 Telemetrie Analyse System

## 1. Einleitung
Dieses Dokument beschreibt die Anforderungen an ein Telemetrie-Analyse-System für die Rennsimulation Automobilista 2 (AMS2). Ziel ist es, fahrzeug- und fahrerspezifische Daten auszulesen, zu speichern und zu analysieren, um die Fahrperformance zu optimieren.

## 2. Projektziele
- **Echtzeit-Datenerfassung**: Auslesen der Telemetriedaten über die Shared Memory API von AMS2.
- **Datenanalyse**: Aufbereitung der Daten zur Identifikation von Fahrfehlern und Setup-Problemen.
- **Visualisierung**: Grafische Darstellung von Rundenzeiten, Geschwindigkeiten, Reifen-Temperaturen, etc.

## 3. Funktionale Anforderungen

### 3.1 Datenerfassung
- Anbindung an AMS2 Shared Memory.
- Speichern der Kombination von Fahrzeug und Strecke:
    - Fahrzeug
    - Strecke
    - Datum
    - Uhrzeit
    - Session
    - Beste Rundenzeit
- Aufzeichnung folgender Metriken:
    - Wetterbedingungen
    - Geschwindigkeit, Drehzahl, Gang
    - Gas-, Brems-, Kupplungspedalstellung
    - Lenkwinkel
    - Reifentemperaturen, -drücke, -abnutzung
    - Positionsdaten (X, Y, Z) für Streckenkarten

### 3.2 Datenverarbeitung & Speicherung
- Speicherung der Sessions (CSV).
    - Automatische Erstellung von `best_laps.csv`.
    - Speicherung der besten Rundenzeit pro Auto/Strecke/Session-Typ.
- Erkennung von Runden (Start/Ziel).
- Segmentierung der Strecke (Sektoren).

### 3.3 Analyse & Feedback
- **Race Engineer (Ingenieur)**:
    - Analyse der Reifentemperaturen und -drücke.
    - Analyse des Lenkverhaltens (Untersteuern/Übersteuern).
    - **NEU:** Analyse-Trigger basierend auf **Daten-Stabilität**, nicht auf fixer Rundenanzahl.
    - **NEU:** Fortschrittsanzeige der Analyse in Prozent (0-100%).
    - **NEU:** Meldung "BOX, Änderung Notwendig!" sobald stabile Daten vorliegen und Handlungsbedarf besteht.
    - **NEU:** Persistenz der Analyse-Ergebnisse auch bei Boxenstopps oder Pausen.

## 4. Benutzeroberfläche (UI)
- **Technologie**: PyQt6 (Desktop-Overlay).
- **Layout**: 3 Reiter (Tabs).
    1. **Session & Setup**:
        - Live-Timing (Aktuelle Runde, Beste Runde, Sektoren).
        - **NEU:** Sektorzeiten farbig markiert (Grün = Schneller/Gleich, Rot = Langsamer als Session-Best).
        - Race Engineer Feedback (Text & Warnungen).
    2. **Track Map**:
        - Dynamische Streckenkarte.
        - Farbcodierung nach Geschwindigkeit.
        - Markierung der engsten Kurve (Ausnahme: Boxengasse/Ungültige Runden).
    3. **Lap Times**:
        - Tabelle aller gefahrenen Runden.
        - Spalten: Runde, Zeit, Sektor 1, **Setup / Notes**.
        - **NEU:** Automatische Speicherung der Setup-Empfehlung zu jeder Runde.

## 5. Nicht-Funktionale Anforderungen
- **Performance**: Geringe CPU-Last, da Overlay parallel zum Spiel läuft.
- **Stabilität**: Robustheit gegen Spiel-Pausen, Neustarts und Zeit-Resets (Time Trial).
- **Usability**: "Always on Top" Fenster, gut lesbar (Dark Mode).
