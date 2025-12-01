import pandas as pd
from pathlib import Path

# ---------- CONFIG ----------
BASE_DIR = Path(r"C:\Users\fulmi\Downloads\Set Lists")
ESSENTIAL_PATH = BASE_DIR / "essential_mix_final_fixed_encoding.csv"
MAPPING_PATH = BASE_DIR / "setlists_crates_mapping.xlsx"
OUTPUT_PATH = BASE_DIR / "essential_mix_with_setlists.csv"
LOG_PATH = BASE_DIR / "setlists_merge_log.txt"
# ----------------------------


def normalize_isrc(val):
    """Normalize ISRC to uppercase, stripped string, or None."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s:
        return None
    return s.upper()


def parse_setlist_row(header_str, selection_str):
    """
    Parse a setlist mapping row.
    
    Returns a dict mapping column_name -> value_or_list_of_values
    
    Examples:
        header: "Vibe", selection: "Air" -> {"Vibe": "Air"}
        header: "Sound", selection: "Dark; Hypnotic" -> {"Sound": ["Dark", "Hypnotic"]}
        header: "Culture, Language", selection: "France, French" -> {"Culture": "France", "Language": "French"}
        header: "Sound | Vibe", selection: "Dark; Rave | Madness" -> {"Sound": ["Dark", "Rave"], "Vibe": "Madness"}
    """
    result = {}
    
    # Split by | for multiple category pairs
    header_parts = [h.strip() for h in str(header_str).split('|')]
    selection_parts = [s.strip() for s in str(selection_str).split('|')]
    
    if len(header_parts) != len(selection_parts):
        raise ValueError(f"Mismatch: {len(header_parts)} headers vs {len(selection_parts)} selections")
    
    for header, selection in zip(header_parts, selection_parts):
        # Handle multiple headers in one (e.g., "Culture, Language")
        headers = [h.strip() for h in header.split(',')]
        
        if len(headers) > 1:
            # Multiple headers: split selection by comma
            selections = [s.strip() for s in selection.split(',')]
            if len(headers) != len(selections):
                raise ValueError(f"Mismatch in comma-split: {headers} vs {selections}")
            for h, s in zip(headers, selections):
                result[h] = s
        else:
            # Single header: check for semicolon (multi-select)
            if ';' in selection:
                # Multiple selections for this header
                selections = [s.strip() for s in selection.split(';')]
                result[header] = selections
            else:
                # Single selection
                result[header] = selection
    
    return result


def main():
    # ----- Load Essential Mix -----
    essential = pd.read_csv(ESSENTIAL_PATH, encoding='utf-8')
    essential["__ISRC"] = essential["ISRC"].apply(normalize_isrc)
    
    print(f"Essential Mix loaded: {len(essential)} tracks")
    
    # ----- Load Setlists mapping -----
    setlists_mapping = pd.read_excel(MAPPING_PATH, sheet_name="Setlists")
    
    print(f"Setlists mapping loaded: {len(setlists_mapping)} entries")
    
    # ----- Load each setlist CSV and build ISRC -> mapping lookup -----
    isrc_to_mappings = {}
    
    for idx, row in setlists_mapping.iterrows():
        setlist_filename = row.get("setlist_filename")
        mapped_header = row.get("mapped_header")
        mapped_selection = row.get("mapped_selection")
        notes = row.get("notes")
        
        if pd.isna(setlist_filename) or pd.isna(mapped_header) or pd.isna(mapped_selection):
            continue
        
        setlist_path = BASE_DIR / str(setlist_filename)
        
        if not setlist_path.exists():
            print(f"WARNING: {setlist_filename} not found at {setlist_path}")
            continue
        
        # Load setlist CSV
        try:
            setlist = pd.read_csv(setlist_path, encoding='utf-8')
        except Exception as e:
            print(f"ERROR loading {setlist_filename}: {e}")
            continue
        
        # Check for ISRC column
        if "ISRC" not in setlist.columns:
            print(f"WARNING: {setlist_filename} has no ISRC column, skipping")
            continue
        
        # Parse the mapping rule
        try:
            mapping = parse_setlist_row(mapped_header, mapped_selection)
        except Exception as e:
            print(f"ERROR parsing mapping for {setlist_filename}: {e}")
            continue
        
        # Add note if present
        if pd.notna(notes):
            mapping["__note_to_append"] = str(notes)
        
        # For each ISRC in the setlist, record this mapping
        for _, setlist_row in setlist.iterrows():
            isrc = setlist_row.get("ISRC")
            if pd.isna(isrc):
                continue
            
            norm_isrc = normalize_isrc(isrc)
            if not norm_isrc:
                continue
            
            if norm_isrc not in isrc_to_mappings:
                isrc_to_mappings[norm_isrc] = []
            
            isrc_to_mappings[norm_isrc].append(mapping)
    
    print(f"Unique ISRCs in setlists: {len(isrc_to_mappings)}")
    
    # ----- Convert relevant columns to object dtype -----
    target_columns = [
        "Culture", "Language", "Emotionality", "Motif", "Notes",
        "Placement", "Prominent Instruments", "Set", "Sound", "Vibe", "Want"
    ]
    
    for col in target_columns:
        if col in essential.columns:
            essential[col] = essential[col].astype("object")
    
    # ----- Apply mappings to Essential Mix -----
    updated_rows = 0
    
    for idx, row in essential.iterrows():
        isrc = row["__ISRC"]
        if not isrc or isrc not in isrc_to_mappings:
            continue
        
        mappings = isrc_to_mappings[isrc]
        updated_rows += 1
        
        # Apply all mappings for this ISRC (there can be multiple setlists)
        for mapping in mappings:
            for col, val in mapping.items():
                if col == "__note_to_append":
                    continue
                
                if col not in essential.columns:
                    continue
                
                # Handle list values (from semicolon-separated selections)
                if isinstance(val, list):
                    # Join with semicolon
                    val_str = "; ".join(val)
                else:
                    val_str = str(val)
                
                # Check if column already has a value
                existing = essential.at[idx, col]
                if pd.isna(existing) or existing == "":
                    essential.at[idx, col] = val_str
                else:
                    # Append if not already present
                    existing_str = str(existing)
                    if val_str not in existing_str:
                        essential.at[idx, col] = f"{existing_str}; {val_str}"
            
            # Handle notes separately
            if "__note_to_append" in mapping:
                note_val = mapping["__note_to_append"]
                existing_note = essential.at[idx, "Notes"]
                
                if pd.isna(existing_note) or existing_note == "":
                    essential.at[idx, "Notes"] = note_val
                else:
                    existing_note_str = str(existing_note)
                    if note_val not in existing_note_str:
                        essential.at[idx, "Notes"] = f"{existing_note_str}; {note_val}"
    
    # ----- Save -----
    essential = essential.drop(columns=["__ISRC"])
    essential.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    
    # ----- Log -----
    with open(LOG_PATH, "w", encoding='utf-8') as log:
        log.write(f"=== SETLISTS MERGE SUMMARY ===\n")
        log.write(f"Essential Mix original: {len(essential)} tracks\n")
        log.write(f"Setlists mapping entries: {len(setlists_mapping)}\n")
        log.write(f"Unique ISRCs found in setlists: {len(isrc_to_mappings)}\n")
        log.write(f"Tracks updated with setlist data: {updated_rows}\n")
        log.write(f"Output written to: {OUTPUT_PATH}\n")
    
    print(f"Tracks updated: {updated_rows}")
    print(f"Log written to: {LOG_PATH}")


if __name__ == "__main__":
    main()
