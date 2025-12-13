Lastenheft: AMS2 Telemetrie & Virtual Race Engineer (v2.0)
1. Einleitung
Dieses Dokument beschreibt die Anforderungen an ein erweitertes Telemetrie-Analyse-System für Automobilista 2. Das System liest Fahrdaten in Echtzeit aus, visualisiert diese und fungiert als "Virtueller Race Engineer". Es analysiert das Fahrverhalten anhand definierter Regelwerke (basierend auf der Chris Haye Setup-Methodik), um konkrete Vorschläge zur Verbesserung des Fahrzeug-Setups zu generieren.

2. Projektziele
Echtzeit-Datenerfassung: Latenzarmes Auslesen der Shared Memory API.

Kontext-Erkennung: Das System versteht, wo sich das Fahrzeug befindet (Gerade, Bremszone, Kurveneingang, Scheitelpunkt, Ausgang).

Setup-Beratung: Automatische Ableitung von Setup-Änderungen bei Problemen (z. B. Übersteuern, Reifentemperatur, Blockieren).

Daten-Persistenz: Speicherung von Runden, Sektoren und dazugehörigen Setup-Empfehlungen.

3. Funktionale Anforderungen
3.1 Datenerfassung (Inputs)
Das System muss folgende Metriken über die Shared Memory API erfassen:

Basis: Fahrzeug-ID, Strecken-ID, Session-Status, Rundenzeit.

Fahrphysik:

Geschwindigkeit (Car Speed) vs. Radgeschwindigkeiten (Wheel Speeds FL/FR/RL/RR) -> Erkennung von Blockieren/Durchdrehen.

Lenkwinkel (Steering Angle).

Pedalstellungen (Throttle, Brake, Clutch).

G-Kräfte (Lateral, Longitudinal, Vertical).

Gierrate (Yaw Rate) -> Erkennung von Rutschwinkeln.

Fahrwerk & Reifen:

Reifentemperaturen (Innen, Mitte, Außen) -> Erkennung Sturz/Druck.

Reifendrücke.

Federweg (Suspension Travel) -> Erkennung von Aufsetzen (Bottoming) oder Ausfedern.

Reifenabnutzung.

3.2 Datenverarbeitung & Logik (Core Engine)
3.2.1 Phasen-Erkennung (Corner Phase Detection)
Das System muss die Kurvenfahrt in fünf Phasen unterteilen, um Setup-Tipps korrekt zuzuordnen:

Braking Zone: Hohe negative Longitudinal-G-Kräfte + Bremsdruck > 0.

Turn-In (Einlenken): Bremsdruck fällt, Lenkwinkel steigt, Laterale G-Kräfte steigen.

Mid-Corner (Scheitel): Maximale Laterale G-Kräfte, minimale Pedal-Eingabe.

Corner Exit (Ausgang): Lenkwinkel nimmt ab, Gaspedal steigt.

Straight (Gerade): Lenkung ~0, Vollgas.

3.2.2 Analyse-Module ("Chris Haye Logic")
Das System prüft in jeder Phase auf Anomalien und speichert folgende Events:

A. Brems-Analyse

Regel 1 (Front Lockup): WheelSpeed_Front < CarSpeed (signifikant).

-> Vorschlag: "Bremsbalance nach hinten."

Regel 2 (Rear Lockup/Instability): WheelSpeed_Rear < CarSpeed ODER Gierrate instabil beim Bremsen.

-> Vorschlag: "Bremsbalance nach vorne", "Dämpfer (Bump) weicher", "Motorbremse reduzieren."

Regel 3 (Bottoming): SuspensionTravel == 0 (Anschlag) beim Bremsen.

-> Vorschlag: "Bodenfreiheit erhöhen", "Federn vorne härter", "Bump Stop Range prüfen."

B. Einlenkverhalten (Turn-In)

Regel 1 (Untersteuern): Hoher Lenkwinkel aber geringe Gierrate/Rotation.

-> Vorschlag: "Reifendruck Vorderachse prüfen", "Stabi (ARB) vorne weicher", "Vorspur (Toe-out) vergrößern", "Diff-Coast verringern."

Regel 2 (Übersteuern/Lift-off): Heck bricht aus beim Lösen der Bremse/Gas.

-> Vorschlag: "Diff-Coast erhöhen (Sperre)", "Diff-Preload erhöhen", "Stabi vorne härter."

C. Kurvenausgang (Exit)

Regel 1 (Power Oversteer): Throttle > 50% UND YawRate > Threshold (Heck kommt).

-> Vorschlag: "Stabi hinten weicher", "Diff-Power reduzieren (weniger Sperre)", "Federn hinten weicher."

-> High Speed: "Heckflügel erhöhen."

Regel 2 (Untersteuern am Ausgang): Fahrzeug schiebt trotz Lenkung nach außen.

-> Vorschlag: "Stabi hinten härter", "Diff-Power erhöhen", "Federn hinten härter."

D. Reifen-Thermo-Analyse

Temp Innen >> Temp Außen: -> Vorschlag: "Negativen Sturz (Camber) verringern."

Temp Mitte > Temp (Innen/Außen): -> Vorschlag: "Reifendruck verringern."

Temp Ränder > Temp Mitte: -> Vorschlag: "Reifendruck erhöhen."

Allgemein zu heiß: -> Vorschlag: "Bremskühlung öffnen" (falls Felgenheizung) oder "Drücke erhöhen (weniger Walken)."

E. Konsistenz-Check ("PICNIC"-Filter)

Bevor ein Setup-Tipp gegeben wird, muss das Problem in mindestens 3 Runden an derselben Stelle auftreten.

Tritt das Problem zufällig auf -> Meldung: "Fahrstil inkonsistent. Kein Setup-Rat möglich."

3.3 Speicherung
Session-Log: CSV mit allen Telemetriedaten (optional, da groß).

Analysis-Log: JSON/CSV Datenbank mit:

Runde #

Sektor / Kurve #

Erkanntes Problem (z.B. "Lockup Front")

Generierter Vorschlag

Persistenz bei Boxenstopp: Analyse-Daten werden bei Boxenstopp nicht gelöscht, sondern als "Stint 1", "Stint 2" markiert, um Änderungen zu vergleichen.

4. Benutzeroberfläche (UI) - PyQt6
Das Layout wird in drei Haupt-Tabs unterteilt:

4.1 Tab 1: "Live Dashboard" (Während der Fahrt)
Fokus: Wichtige Infos auf einen Blick (große Schrift).

Elemente:

Delta zur Bestzeit.

Reifentemperaturen (Farblich codiert: Blau/Grün/Rot).

Engineer-Message: Nur kritische Kurznachrichten (z.B. "Reifen VL überhitzt!", "Bremsbalance optimieren").

Sektor-Zeiten (Grün/Lila/Rot).

4.2 Tab 2: "Setup Engineer" (In der Box/Pause)
Fokus: Detaillierte Analyse und Setup-Arbeit.

Layout:

Linke Spalte (Problem-Liste): Liste aller erkannten Probleme, sortiert nach Häufigkeit (z.B. "5x Untersteuern Kurve 3").

Rechte Spalte (Lösungs-Wizard): Detailansicht des gewählten Problems.

Anzeige des entsprechenden "Chris Haye"-Textbausteins.

Konkrete Handlungsanweisung (z.B. "Ändere Front ARB von 5 auf 4").

Effektivitäts-Anzeige: Vergleicht aktuelle Probleme mit denen des vorherigen Stints (Ist es besser geworden?).

4.3 Tab 3: "Track & Data"
Dynamische Streckenkarte:

Zeichnet die gefahrene Linie.

Event-Marker: Farbige Punkte auf der Karte an den Stellen, wo Probleme erkannt wurden (Rot = Übersteuern, Gelb = Blockieren).

Telemetrie-Graphen: Einfache Plots für Speed, Brake, Throttle der schnellsten Runde.

5. Nicht-Funktionale Anforderungen
Performance: Die Analyse-Logik (Regelprüfung) darf den Main-Render-Loop des Overlays nicht blockieren (Multithreading für Datenverarbeitung).

Robustheit:

Ignorieren von "Outlaps" (kalte Reifen verfälschen Analyse).

Mindestdistanz für Analyse: 10 km oder 3 Runden (konfigurierbar).

Usability: "Dark Mode" als Standard, um Blendung bei Nachtfahrten im Simulator zu vermeiden.

Erweiterbarkeit: Die Regel-Sets (Setup-Tipps) sollten in einer separaten Konfigurationsdatei (JSON/YAML) liegen, um sie leicht anpassen zu können, ohne den Code neu zu kompilieren.