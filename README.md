# Audio Metadata Extraction & ETL Pipeline

### Reverse-Engineering Serato Crates and Reconciling Creative Metadata

**Status:** Shipped (v1.0)  
**Dataset Integrity:** 93.8% programmatic → 100% with HITL resolution

---

## Problem

Large portions of my DJ library metadata were locked inside proprietary formats (Serato `.crate` binaries), with additional fragmentation across third-party tools (Mixed In Key) and inconsistent local file naming. This made five years of curated taxonomy—mood, energy, light/dark, sub-genre, and structural intent—effectively non-queryable.

The goal of this project was to **recover, normalize, and reconcile creative metadata** into a structured dataset without access to official schemas, while preserving creative intent and avoiding silent data loss.

---

## Approach

This project implements a hybrid ETL pipeline combining deterministic parsing, probabilistic reconciliation, and human-in-the-loop (HITL) semantic cleanup.

### 1. Extraction and Normalization (Deterministic)

- **Binary parsing:** Reverse-engineered Serato `.crate` file structures to extract file paths and nested hierarchy data.
- **Regex-based normalization:** Cleaned inconsistent and noisy filename conventions into standardized artist/title fields.
- **Structured transforms:** Converted raw extractions into normalized Pandas DataFrames for downstream reconciliation.

### 2. Reconciliation (Probabilistic)

- **Fuzzy matching:** Used string similarity and Unicode normalization to reconcile local filenames against Mixed In Key exports.
- **Primary key recovery:** Leveraged ISRC codes where available to anchor joins and reduce false positives.
- **Confidence-aware joins:** Preferred partial matches with traceability over strict joins that would drop valid assets.

### 3. Semantic Resolution (Human-in-the-Loop)

- **LLM-assisted cleanup:** Introduced a HITL step for the remaining edge cases (e.g., ambiguous remixes, featured-artist formatting).
- **Taxonomy injection:** Mapped abstract qualities (vibe, texture, elemental theme) encoded in folder structure into explicit dataset columns.
- **Explicit review:** Ambiguous cases were surfaced for manual resolution rather than silently auto-corrected.

---

## Why This Design

- **Regex before LLM:** Deterministic logic handles scale cheaply and predictably; model assistance is reserved for genuine semantic ambiguity.
- **Fuzzy reconciliation over strict joins:** Creative metadata rarely shares a clean primary key across tools; probabilistic matching reflects reality.
- **Interpretability over automation:** Every reconciliation decision remains inspectable and reversible.

---

## Results

- **Assets recovered:** 2,700+ tracks successfully extracted and structured
- **Programmatic integrity:** 93.8% resolved via deterministic + fuzzy logic
- **Final integrity:** 100% after HITL semantic resolution
- **Outcome:** A fully queryable dataset now powering semantic search and playlist construction workflows

---

## Repository Structure

extractors/        # Serato .crate parsing and raw data extraction
normalization/     # Filename cleanup, encoding fixes, text normalization
reconciliation/    # Probabilistic matching, diagnostics, ambiguity surfacing
merging/           # Dataset assembly and master record creation
enrichment/        # Spotify API integration and feature augmentation
utilities/         # One-off diagnostics and helper scripts

---

## Execution Notes

This repository represents a curated snapshot of a larger local pipeline.
Scripts were executed in a staged manner with intermediate CSV outputs
persisted between phases. Environment-specific paths and credentials have
been intentionally omitted.

The focus of this repository is pipeline structure, reconciliation logic,
and ambiguity handling — not turnkey deployment.

