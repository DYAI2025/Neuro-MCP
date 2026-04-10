# CON-offline-first

**Status:** Approved
**Category:** Technical
**Source Stakeholder:** [[1-spec/stakeholders|STK-developer]], [[1-spec/stakeholders|STK-knowledge-worker]]

## Description

The default embedder must remain TF-IDF (deterministic, offline-safe). Semantic embeddings via sentence-transformers are opt-in. No feature may require an internet connection or external API for core functionality.

## Rationale

Privacy, reliability, and deployment simplicity. The system must work on a plane, behind a VPN, or in an air-gapped environment.

## Impact

All new features (evidence graph, claim engine, interference resolution) must work with TF-IDF alone. Semantic features enhance but never gate functionality.
