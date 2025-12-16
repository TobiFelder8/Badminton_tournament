### README — Matchmaking mit Live‑Punkten (Flask)

Kurz: Dieses Projekt stellt eine kleine Web‑App bereit, mit der du beliebig viele Spieler eintragen, Doppel‑Round‑Robin‑Spielpläne erzeugen, für jede Partie Ergebnisse eintragen und eine Live‑Rangliste (Punkte: Sieg 3 / Unentschieden 2 / Niederlage 1) anzeigen lassen kannst.

#### Inhalt
- `matchmaking_live.py` — Hauptapplikation (Flask)
- (optional) `matchmaking.py` — einfache Version ohne Live‑Punkte (falls vorhanden)
- `README.md` — diese Datei

#### Voraussetzungen
- Python 3.7+
- Empfohlene Libraries:
  - Flask
  - Flask-Session

Installation (empfohlen in virtuellem Environment):
1. python -m venv venv  
2. source venv/bin/activate  (Linux/macOS) oder `venv\Scripts\activate` (Windows)  
3. pip install flask flask-session

#### Starten
1. Datei `matchmaking_live.py` speichern.  
2. In der Konsole: `python matchmaking_live.py`  
3. Öffne den Browser: http://127.0.0.1:5000

#### Nutzung
1. Auf der Startseite die Spielernamen eingeben — *ein Name pro Zeile* oder durch Komma getrennt.  
2. Auf **Weiter** klicken → Spielplan wird als Double Round‑Robin erzeugt (bei ungerader Spielerzahl gibt es ein Freilos).  
3. In der Spielplanansicht kannst du für jede Partie die erzielten Tore/Punkte eingeben und auf **Punkte speichern** klicken.  
4. Die Rangliste oben aktualisiert sich live auf Basis der eingegebenen Ergebnisse:
   - Sieg = **3 Punkte**
   - Unentschieden = **2 Punkte**
   - Niederlage = **1 Punkt**
   - Freilos = **3 Punkte** (Standard, änderbar im Code)

#### Technische Details / Verhalten
- Pairing: Round‑Robin (Circle‑Method) → dann gespiegelte Runden für Double Round‑Robin. Runden werden leicht gemischt, um aufeinanderfolgende identische Paarungen zu reduzieren.  
- Speicherung: Session‑basierte Speicherung (Dateisystem via Flask-Session). Bei Neustart der App gehen die Daten verloren.  
- Statistiken: Für jede Person werden *Punkte*, *Spiele*, *Tore für (gf)* und *Tore gegen (ga)* berechnet; Sortierung nach Punkte, Tor‑Differenz, geschossene Tore, Name.  
- Formateingabe: Score‑Felder akzeptieren ganze Zahlen >= 0.

#### Anpassungen / Erweiterungen (Ideen)
- Persistente Speicherung: SQLite oder eine andere DB statt Session.  
- Export: CSV/PDF der Rangliste oder des Spielplans.  
- Live‑Updates: Websocket (Flask‑SocketIO) oder AJAX für sofortige Aktualisierung in mehreren Browsern.  
- UI: Bootstrap, bessere Druckansicht, Filter/Paginierung bei vielen Spielern.  
- Regeln: Anderes Punktesystem oder Freilosverhalten sind leicht änderbar im Code.

#### Bekannte Einschränkungen
- Kein User‑Management — jede Sitzung hat denselben Serverzustand.  
- Bei sehr vielen Spielern wird die Seite unübersichtlich.  
- Das Vermeiden von gleichen Gegnern in aufeinanderfolgenden Runden ist heuristisch und nicht optimal für alle Fälle.
