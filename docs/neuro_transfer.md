# Neuro -> Second Brain Transfer

This package implements the following transfer rules:

1. Reconsolidation instead of overwrite
   - Notes are never silently deleted.
   - Contradictions move notes toward `labile` or `stale`.
   - Retrieval can trigger review, not blind mutation.

2. Precision weighting
   - Each note carries `source_precision`.
   - Ranking boosts reliable sources and penalizes stale, missing-source notes.

3. Synaptic tagging and capture
   - Inbox notes are transient.
   - Time-window matching to changed code can promote or stabilize them.

4. Molecular timers
   - `decay_class` gates note freshness.
   - `last_verified` is mandatory for freshness-aware ranking.

5. CA3 / CA1 split
   - Stable notes: ADR, architecture, system design.
   - Flexible notes: inbox, bugs, sprint context.

6. Interference management
   - Similar notes are candidates for merge, supersede, or cross-link.
   - Code contradictions outrank brain notes.

7. LC phasic / tonic modes
   - Small change-set: phasic incremental audit.
   - Large change-set: tonic full reconcile pass.
