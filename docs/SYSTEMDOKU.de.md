# Neuro MCP – Systemdokumentation (Idee, Funktionsweise, aktueller Reifegrad)

> Stand: 11. April 2026

## 1) Die Idee hinter Neuro MCP

Neuro MCP ist als **lokale Wissens-Engine mit MCP-Schnittstelle** gebaut: ein „zweites Gehirn“, das nicht nur Notizen speichert, sondern aktiv prüft, ob diese Notizen noch zur realen Codebasis passen.

Der Kernansatz lautet:

- **Notizen sind Kontext und Begründung** (Warum wurde etwas entschieden?).
- **Code ist die operative Wahrheit** (Was läuft tatsächlich?).
- Wenn beides auseinanderläuft, zeigt Neuro MCP den Widerspruch explizit statt ihn zu verstecken.

Damit löst das System ein typisches Problem in Projekten: Wissensdokumente veralten schnell, wirken aber trotzdem „vertrauenswürdig“. Neuro MCP versucht, diese Drift kontinuierlich sichtbar zu machen.

---

## 2) Architektur in einfachen Worten

Das System besteht aus vier Ebenen:

1. **Ingestion & Indexing**
   - Liest Markdown-Notizen (inkl. YAML-Frontmatter).
   - Liest Code-Dateien und zerlegt sie in Such-Chunks.
   - Schreibt beides in einen lokalen Daten-/Index-Stand.

2. **Bewertung & Anreicherung**
   - Berechnet Frische/Verfall (`last_verified`, `decay_class`, verlinkte Dateien).
   - Nutzt Präzisionsgewichte (wie belastbar ist eine Quelle?).
   - Optional: Auto-Enrichment von Frontmatter (Typ, Metadaten etc.).

3. **Abfrage & Abgleich**
   - Sucht in Notizen (`search_brain`) und Code (`search_codebase`).
   - Führt Abgleich zwischen Behauptung und Implementierung durch (`reconcile_brain_with_code`).
   - Liefert Freshness-Digests und Interference-/Duplikat-Hinweise.

4. **Bereitstellung**
   - CLI für lokale Workflows.
   - MCP-Server über `stdio` oder Streamable HTTP für Agenten/Clients.

---

## 3) Neuro-inspirierte Modellidee

Das System orientiert sich konzeptionell an sieben neuro-inspirierten Regeln:

- Reconsolidation statt blindem Überschreiben
- Präzisionsgewichtung
- Synaptic Tagging and Capture (STC)
- Molekulare Timer / Decay-Klassen
- CA3/CA1-Trennung (Muster vs. Abgleich)
- Interference-Management
- Phasic/Tonic-Modi

Diese Regeln sind **keine Biologie-Simulation**, sondern Design-Metaphern für robustes Wissensmanagement in Softwareprojekten.

---

## 4) Wie ein typischer Ablauf aussieht

1. `index` baut/aktualisiert Indizes für Brain + Code.
2. `search-brain` gibt semantisch/lexikalisch gewichtete Notiztreffer.
3. `search-code` zeigt aktuelle Codebelege.
4. `reconcile` prüft Aussagen gegen Manifeste/Dateipfade.
5. `digest` zeigt Staleness, Risiken und Prioritäten.
6. `gc` erzeugt Aufräumvorschläge; `gc --apply` markiert Statusänderungen in Notizen (ohne harte Auto-Deletes).

Ergebnis: Der Nutzer bekommt nicht nur „Treffer“, sondern einen **Vertrauenskontext** zu den Treffern.

---

## 5) Wo das System heute bereits gut und funktional ist

### 5.1 Solider Produktivkern

Bereits stabil umgesetzt sind:

- Duale Suche in Brain + Code.
- Expliziter Brain-vs-Code-Abgleich mit „Code wins“-Prinzip.
- Freshness-Modell mit Decay-Klassen.
- MCP-Tools für Suche, Digest, Reconcile, Note-Zugriff und GC.
- Serverbetrieb über `stdio` und HTTP inkl. Health-/Readiness-Endpunkten.
- Sicherheitsbasis (Origin-Validierung, optional Bearer Token).

### 5.2 Gute Offline-/Lokalfähigkeit

- Betrieb als lokales Werkzeug ohne Cloud-Zwang.
- Deterministische Standard-Suche via TF-IDF als robuster Fallback.
- Optionale semantische Erweiterung über Embeddings.

### 5.3 Vorsichtige, sichere Mutation statt destruktiver Automation

- Garbage Collection ist konservativ gedacht.
- Das System vermeidet automatische Dateilöschung.
- Dadurch sinkt das Risiko, wertvolle Wissensartefakte versehentlich zu verlieren.

---

## 6) Wo aktuell noch Funktion fehlt oder bewusst begrenzt ist

### 6.1 Fortgeschrittene Reconsolidation-Workflows

Der Grundgedanke ist vorhanden, aber die nächste Ausbaustufe benötigt noch:

- transaktionale Review-Workflows,
- auditierbare Zustandsübergänge,
- tiefere, persistente Konfliktauflösung über mehrere Artefakte.

### 6.2 Evidence-Graph / Multi-Hop-Wissenslogik

Heute dominiert ein starker dualer Index (Brain + Code). Was noch fehlt bzw. im Ausbau steckt:

- echter, gewichteter Evidence-Graph als Primärmodell,
- mehrstufige Schlussfolgerungen über Kanten/Beziehungen,
- automatische Widerspruchspropagation entlang Abhängigkeitsketten.

### 6.3 Konservative Widerspruchserkennung

Aktuell ist die Erkennung bewusst vorsichtig und explizit (z. B. fehlende Datei, fehlende Dependency). Noch ausbaufähig:

- stärkere Free-Text-Claim-Extraktion,
- feinere semantische Konfliktmuster,
- weniger manuelle Nacharbeit bei impliziten Widersprüchen.

### 6.4 Operative Skalierung & Observability-Feinschliff

Die Basis ist da, aber für große Teams/Instanzen sind typischerweise zusätzliche Schritte nötig:

- tiefere Laufzeitmetriken auf Stage-Ebene,
- Performance-/Lastprofile für sehr große Vaults,
- ausgebautes Betriebs- und Fehlerdiagnose-Playbook.

---

## 7) Reifegradeinschätzung (ehrlich, praxisnah)

- **Heute gut produktiv einsetzbar** für: Solo-Entwicklung, kleine bis mittlere Teams, lokale Wissensdisziplin, Agent-gestützte Projektarbeit.
- **Mit klaren Stärken** bei: Nachvollziehbarkeit, Sicherheitskonservatismus, Drift-Erkennung zwischen Dokumentation und Code.
- **Noch nicht vollständig ausgereizt** bei: graphbasierter Evidenzlogik, tiefer automatischer Reconsolidation und großskaliger Betriebsautomatisierung.

Kurz gesagt: Neuro MCP ist bereits ein sehr brauchbarer „Knowledge Integrity Layer“, aber die Roadmap geht bewusst Richtung **noch stärker automatisierter Wissenspflege**.

---

## 8) Empfehlungen für den nächsten Ausbau

1. **Reconsolidation-Transaktionen priorisieren**
   - saubere Statusmaschine mit Begründungen, Review-Historie, Rückverfolgbarkeit.

2. **Evidence-Graph inkrementell einführen**
   - zuerst Knoten-/Kantentypen und Gewichtung, danach Multi-Hop-Retrieval.

3. **Claim Engine vertiefen**
   - strukturierte Extraktion aus Notizen + semantische Konfliktprüfung gegen Codebelege.

4. **Observability erweitern**
   - standardisierte Pipeline-Metriken, Fehlerklassen, Operatorsicht im Dauerbetrieb.

Damit bleibt der aktuelle stabile Kern erhalten, während die intelligenten Funktionen schrittweise auf Produktionsniveau gehoben werden.
