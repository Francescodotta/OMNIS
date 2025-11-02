import argparse
import csv
import re
from pathlib import Path
from typing import List, Tuple

def detect_dialect(path: Path):
    sample = path.read_text(encoding="utf-8", errors="ignore")[:8192]
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample)
    except Exception:
        # fallback to tab
        class TabDialect(csv.excel):
            delimiter = "\t"
        dialect = TabDialect()
    return dialect

def split_hmdb_ids(field: str) -> List[str]:
    if not field:
        return []
    # replace common separators with space then split
    parts = re.split(r"[,\|;/\t]+|\s+", field.strip())
    ids = []
    for p in parts:
        if not p:
            continue
        p = p.strip()
        # normalize common forms to "HMDB:HMDBxxxxx"
        # if it already looks like HMDB:HMDB..., keep it
        if re.match(r"^HMDB:HMDB\d+", p, re.IGNORECASE):
            ids.append(p if p.startswith("HMDB:") else "HMDB:" + p.split("HMDB",1)[-1])
            continue
        # if it starts with HMDB and digits, add prefix
        m = re.match(r"^(?:HMDB[:\s-]*)?(0*?)(\d+)$", p)
        if re.match(r"^HMDB\d+$", p, re.IGNORECASE):
            ids.append("HMDB:" + p if p.upper().startswith("HMDB") else "HMDB:" + p)
            continue
        # if it looks like HMDB... (no colon)
        if p.upper().startswith("HMDB"):
            # ensure format HMDB:HMDBxxxxx
            if ":" in p:
                ids.append(p)
            else:
                ids.append("HMDB:" + p)
            continue
        # otherwise, keep as-is (some inputs may already be full URIs or other ids)
        ids.append(p)
    # deduplicate while preserving order
    seen = set()
    out = []
    for i in ids:
        if i not in seen:
            out.append(i)
            seen.add(i)
    return out

def try_parse_mass(token: str) -> Tuple[bool, str]:
    token = token.strip()
    # allow scientific notation and comma decimal
    token_norm = token.replace(",", ".")
    try:
        float(token_norm)
        # return canonical string with full precision from float
        return True, token_norm
    except Exception:
        return False, token

def parse_row_tokens(tokens: List[str]) -> Tuple[str, str, List[str]]:
    """
    Heuristics:
    - pick the token that can be parsed as mass (float) among first 3 tokens
    - the formula is a short token with letters/numbers and no 'HMDB' substring
    - HMDB ids are tokens containing 'HMDB' or the remaining tokens
    Returns (mass_str, formula_str, [hmdb_ids...])
    """
    # sanitize tokens
    toks = [t.strip() for t in tokens if t and t.strip() != ""]
    # quick cases
    if not toks:
        return ("", "", [])
    # if only 2 tokens: assume mass, formula or formula, hmdb.
    if len(toks) == 1:
        # single column: try to split by whitespace
        split = re.split(r"\s+", toks[0])
        if len(split) > 1:
            return parse_row_tokens(split)
        return ("", toks[0], [])
    if len(toks) == 2:
        # try find mass among them
        ok0, m0 = try_parse_mass(toks[0])
        ok1, m1 = try_parse_mass(toks[1])
        if ok0 and not ok1:
            return (m0, toks[1], [])
        if ok1 and not ok0:
            return (m1, toks[0], [])
        # else assume mass, hmdb or formula, hmdb: put mass first if numeric-like first
        if ok0:
            return (m0, toks[1], [])
        if ok1:
            return (m1, toks[0], [])
        # otherwise treat as (mass missing, formula=toks[0], hmdb=toks[1])
        return ("", toks[0], split_hmdb_ids(toks[1]))
    # 3 or more tokens:
    # try find numeric token for mass among first 3
    mass_idx = None
    mass_val = ""
    for i in range(min(3, len(toks))):
        ok, val = try_parse_mass(toks[i])
        if ok:
            mass_idx = i
            mass_val = val
            break
    # formula: prefer token that looks like chemical formula (letters+numbers, short)
    formula_idx = None
    for i, t in enumerate(toks[:4]):  # check first 4 tokens
        if re.match(r"^[A-Za-z0-9\+\-\(\)]+$", t) and len(t) <= 20 and "HMDB" not in t.upper():
            # avoid picking pure numeric
            ok, _ = try_parse_mass(t)
            if not ok:
                formula_idx = i
                break
    # fallback formula index
    if formula_idx is None:
        # pick first non-mass token
        for i, t in enumerate(toks[:4]):
            ok, _ = try_parse_mass(t)
            if not ok:
                formula_idx = i
                break
    # gather hmdb tokens from the rest
    remaining = [t for i,t in enumerate(toks) if i not in (mass_idx, formula_idx) and t]
    hmdb_ids = []
    if remaining:
        # sometimes remaining is a single field containing comma-separated ids
        if len(remaining) == 1:
            hmdb_ids = split_hmdb_ids(remaining[0])
        else:
            # multiple tokens likely already individual IDs
            hmdb_ids = []
            for r in remaining:
                hmdb_ids.extend(split_hmdb_ids(r))
    return (mass_val, toks[formula_idx] if formula_idx is not None else "", hmdb_ids)

def transform(input_path: Path, output_path: Path, db_name: str="HMDB", db_version: str="4.0", verbose: bool=False):
    dialect = detect_dialect(input_path)
    rows = []
    with input_path.open("r", encoding="utf-8", errors="ignore") as fh:
        reader = csv.reader(fh, dialect)
        for raw_row in reader:
            if not raw_row:
                continue
            # skip comments and header-like obvious lines
            first = "".join(raw_row).strip()
            if not first:
                continue
            if first.startswith("#"):
                continue
            # some files may have a header line like "database_name" - skip known headers
            low = first.lower()
            if low.startswith("database_name") or low.startswith("database_version"):
                continue
            # parse tokens
            # if row has 1 col but contains tabs/spaces separated content, split
            if len(raw_row) == 1:
                toks = re.split(r"[\t,;|]+|\s+", raw_row[0].strip())
            else:
                toks = raw_row
            mass, formula, hmdb_ids = parse_row_tokens(toks)
            # if no hmdb ids found but some tokens look like HMDB inside formula, extract
            if not hmdb_ids and formula and "HMDB" in formula.upper():
                # move formula->hmdb, and pick next token as formula if present
                maybe_ids = split_hmdb_ids(formula)
                if maybe_ids:
                    hmdb_ids = maybe_ids
                    formula = toks[1] if len(toks) > 1 else ""
            # if still no hmdb and last token contains "HMDB", try last token
            if not hmdb_ids and toks and "HMDB" in toks[-1].upper():
                hmdb_ids = split_hmdb_ids(toks[-1])
            # final cleanup
            hmdb_ids = [h for h in hmdb_ids if h]
            if not mass and not hmdb_ids:
                # skip noisy lines if nothing sensible parsed
                if verbose:
                    print("Skipping (no mass and no HMDB ids):", toks)
                continue
            rows.append((mass, formula, hmdb_ids))
    # sort by mass numeric if possible (empty masses go to end)
    def mass_key(r):
        try:
            return float(r[0])
        except Exception:
            return float("inf")
    rows.sort(key=mass_key)
    # write output
    with output_path.open("w", encoding="utf-8") as out:
        out.write(f"database_name\t{db_name}\n")
        out.write(f"database_version\t{db_version}\n")
        for mass, formula, hmdb_ids in rows:
            # ensure mass numeric string formatting: keep as-is
            fields = [mass if mass else "", formula if formula else ""]
            # append HMDB ids each as separate column
            if hmdb_ids:
                fields.extend(hmdb_ids)
            out.write("\t".join(fields) + "\n")
    if verbose:
        print(f"Wrote {len(rows)} mappings to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Transform hmdb_mapping.tsv into HMDBMappingFile.tsv format.")
    parser.add_argument("input", help="input hmdb_mapping.tsv path")
    parser.add_argument("output", nargs="?", help="output file path (default: ./HMDBMappingFile.tsv)", default="HMDBMappingFile.tsv")
    parser.add_argument("--db-name", default="HMDB", help="database_name header value")
    parser.add_argument("--db-version", default="4.0", help="database_version header value")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    inp = Path(args.input)
    out = Path(args.output)
    if not inp.exists():
        print("Input file does not exist:", inp)
        raise SystemExit(2)
    transform(inp, out, db_name=args.db_name, db_version=args.db_version, verbose=args.verbose)

if __name__ == "__main__":
    main()