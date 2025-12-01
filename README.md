# Audio Metadata Extraction & ETL Pipeline 🎵 -> 📊

### Reverse-Engineering Serato Crates & Reconciling Metadata Debt

**Status:** Shipped (v1.0) | **Accuracy:** 93.8% (Code) -> 100% (AI-Assisted)

## ⚡ The Engineering Challenge
Spotify restricted API access for non-commercial developers, locking my library of **2,700+ tracks** and **200+ curated playlists** inside a "walled garden." I needed to migrate 5 years of granular taxonomy (Mood, Energy, "Dark vs. Light," Nested Sub-genres) out of proprietary formats and into a queryable dataset.

## 🛠 The Solution: A Hybrid ETL Pipeline
I architected a custom pipeline that bridges local binary files, third-party analysis tools, and LLM-based data cleaning.

### 1. The "Hard" Engineering (Python & Pandas)
* **Binary Parsing:** Reverse-engineered Serato's proprietary `.crate` file structure to extract raw file paths and nested hierarchy data (`crate_extractor_corrected.py`).
* **Data Normalization:** Wrote regex parsers to clean "garbage" file naming conventions (e.g., `01_Track_Name_(Original_Mix).mp3`) into standardized Artist/Title tuples (`parse_artist_title.py`).
* **Fuzzy Matching:** Implemented `thefuzz` and `unicodedata` to reconcile local file names against "Mixed In Key" (MIK) export data, using ISRC codes as the join key (`setlists_merge.py`).

### 2. The "Soft" Engineering (AI & Semantic Cleanup)
* **LLM Data Enrichment:** Utilized Notion AI (Lumen) as a "Human-in-the-Loop" cleaning agent to resolve the final 6.2% of edge cases (e.g., ambiguously titled remixes, "feat." artist formatting) that programmatic logic missed.
* **Taxonomy Injection:** Mapped abstract qualities (Vibe, Texture, Elemental Theme) from the folder structure into the dataset columns.

## 📂 Repository Structure
* `/src/extractors` - Scripts for parsing `.crate` files and raw binaries.
* `/src/normalization` - Regex and string cleaning logic for file names.
* `/src/merging` - Pandas logic for joining MIK data, local files, and taxonomy.

## 🚀 Impact
* **Recovered Data:** Successfully extracted and structured metadata for 2,700+ assets.
* **Accuracy:** Achieved 100% data integrity after the HITL (Human-in-the-Loop) pass.
* **Usage:** This dataset now powers a "Semantic Search" interface for my personal DJ library.
