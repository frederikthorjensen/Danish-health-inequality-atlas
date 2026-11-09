"""Validate official health-profile exports and merge with the socioeconomic master.

Usage: python -m src.health_profile_import --raw-dir data/raw/health_profile_<snapshot>
XLSX imports use the actual Excel percentage cell format; no inferred rescaling.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import math
from numbers import Real
from pathlib import Path
import re
import sys
import unicodedata
import warnings

from openpyxl import load_workbook
import pandas as pd

from src.health_profile_collection import INDICATORS, ROOT, report_url
from src.data_collection import write_json

DEFINITIONS = {
    "daily_smoking": "Self-reported daily smoking; excludes occasional-only smoking.",
    "obesity": "Severe overweight: BMI >=30 from self-reported height and weight.",
    "physical_inactivity": "Does not meet the portal's WHO minimum weekly activity definition; retain its saved wording and indicator-specific eligibility. Not sedentary leisure activity; 2017 and 2021 are not directly comparable.",
    "risky_alcohol": "More than 10 Danish standard drinks over a typical week; not binge drinking or an alcohol-dependence measure.",
    "good_self_rated_health": "Fremragende, vældig godt, or godt self-rated health among valid responses.",
    "poor_mental_health": "Low SF-12 mental component score <=35.76 per the portal definition; not a complement of high mental well-being.",
}
AMBIGUOUS_MISSING = {".", "..", "...", "-", "–", "—", "*", "**", ":", "n/a", "na"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split()).casefold()


def parse_percentage(cell) -> tuple[float | None, str]:
    """Preserve explicit missing markers, rejecting ambiguous numeric units."""
    value = cell.value
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, "missing_source_value"
    if isinstance(value, str):
        text = value.strip()
        if text.casefold() in AMBIGUOUS_MISSING:
            return None, "suppressed_or_unavailable"
        if "diskretion" in text.casefold() or "suppres" in text.casefold():
            return None, "suppressed"
        if re.fullmatch(r"\d+(?:[.,]\d+)?\s*%", text):
            result = float(text.rstrip("% ").replace(",", "."))
        else:
            raise ValueError(f"Unrecognised prevalence cell {cell.coordinate}: {value!r}")
    elif isinstance(value, Real) and not isinstance(value, bool) and "%" in cell.number_format:
        result = float(value) * 100
    else:
        raise ValueError(f"Prevalence lacks explicit percentage formatting: {cell.coordinate}")
    if not math.isfinite(result) or not 0 <= result <= 100:
        raise ValueError(f"Out-of-range prevalence at {cell.coordinate}")
    return result, "observed"


def import_workbook(path: Path, key: str, registry: dict[str, str]) -> tuple[pd.DataFrame, dict]:
    """Read one unmodified official formatted XLSX export.

    Map exact normalized official names to existing codes; never fuzzy-match.
    Accompanying published OR columns remain in raw only and are not analysed.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Workbook contains no default style")
        workbook = load_workbook(path, data_only=True)
    if workbook.sheetnames != ["Results"]:
        raise ValueError(f"Unexpected export sheets: {workbook.sheetnames}")
    sheet = workbook["Results"]
    headers = [c.value for c in sheet[1]]
    if headers.count("Kommune") != 1 or headers.count(INDICATORS[key]["column"]) != 1:
        raise ValueError(f"Unexpected headers in {path.name}: {headers}")
    geo, value_column = headers.index("Kommune"), headers.index(INDICATORS[key]["column"])
    name_to_code = {normalized_name(name): code for code, name in registry.items()}
    if len(name_to_code) != len(registry):
        raise ValueError("Ambiguous normalized municipality registry")
    rows, unexpected = [], []
    raw_tokens = Counter()
    for cells in sheet.iter_rows(min_row=2):
        if all(c.value is None for c in cells):
            continue
        name = cells[geo].value
        if not isinstance(name, str) or normalized_name(name) not in name_to_code:
            unexpected.append(str(name))
            continue
        number, status = parse_percentage(cells[value_column])
        if status != "observed":
            raw_tokens[str(cells[value_column].value)] += 1
        rows.append({"municipality_code": name_to_code[normalized_name(name)],
                     "source_municipality": name, "value_pct": number, "status": status})
    workbook.close()
    frame = pd.DataFrame(rows, columns=["municipality_code", "source_municipality", "value_pct", "status"])
    duplicates = frame.loc[frame.duplicated("municipality_code", keep=False), "municipality_code"].tolist()
    present = set(frame["municipality_code"])
    quality = {"source_rows": sheet.max_row - 1, "matched_municipalities": len(present),
        "missing_municipalities": sorted(set(registry) - present),
        "unexpected_municipality_names": unexpected, "duplicate_codes": duplicates,
        "source_status_counts": dict(Counter(frame["status"])), "missing_value_tokens": dict(raw_tokens),
        "null_source_values": int(frame["value_pct"].isna().sum()),
        "min_pct": float(frame["value_pct"].min()) if frame["value_pct"].notna().any() else None,
        "max_pct": float(frame["value_pct"].max()) if frame["value_pct"].notna().any() else None}
    return frame, quality


class ResponseCategories(HTMLParser):
    """Verify the five response categories and emphasis in the official definition."""
    def __init__(self):
        super().__init__()
        self.categories, self.selected, self.bold = set(), set(), False

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            self.bold = "font-weight:bold" in dict(attrs).get("style", "").replace(" ", "")

    def handle_data(self, data):
        text = data.strip()
        if text.startswith("•"):
            category = normalized_name(text[1:].strip())
            self.categories.add(category)
            if self.bold:
                self.selected.add(category)

    def handle_endtag(self, tag):
        if tag == "span":
            self.bold = False


def verify_self_rated_definition(html: str) -> None:
    parser = ResponseCategories()
    parser.feed(html)
    expected = {normalized_name(v) for v in ("Fremragende", "Vældig godt", "Godt", "Mindre godt", "Dårligt")}
    selected = {normalized_name(v) for v in ("Fremragende", "Vældig godt", "Godt")}
    if parser.categories != expected or parser.selected != selected:
        raise ValueError("Self-rated health response partition unverified; refusing complement")


def import_snapshot(raw: Path, base_path: Path | None = None, output_root: Path = ROOT) -> dict:
    """Validate all six exports; publish a separate combined master with provenance."""
    raw = raw.resolve()
    base_path = base_path or ROOT / "data/processed/municipality_master_2024.csv"
    manifest = json.loads((raw / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "complete" or manifest["wave"] not in (2025, 2021):
        raise ValueError("Require a complete 2025 or 2021 snapshot; never mix waves silently")
    wave = manifest["wave"]
    exports = {e["indicator"]: e for e in manifest["exports"]}
    if set(exports) != set(INDICATORS) or len(manifest["exports"]) != len(INDICATORS):
        raise ValueError("Snapshot must contain each required indicator exactly once")
    base = pd.read_csv(base_path, dtype={"municipality_code": str})
    if len(base) != 98 or base["municipality_code"].duplicated().any() or base["municipality"].duplicated().any() or base[["municipality_code", "municipality"]].isna().any().any():
        raise ValueError("Socioeconomic master must have 98 unique municipality codes/names")
    base_provenance = base_path.with_name(base_path.stem + "_provenance.json")
    socioeconomic_provenance = json.loads(base_provenance.read_text(encoding="utf-8"))
    if socioeconomic_provenance["master_sha256"] != digest(base_path):
        raise ValueError("Socioeconomic master checksum does not match its provenance")
    registry = dict(zip(base["municipality_code"], base["municipality"], strict=True))
    combined, checks, provenance, errors = base.copy(), {}, {}, []
    health_long = []
    for key, entry in exports.items():
        if entry["wave"] != wave or entry["source_url"] != report_url(key) or entry["geography"] != "Kommune; all 98 municipalities":
            raise ValueError(f"Incompatible source selection: {key}")
        for field in ("file", "definition_file"):
            if Path(entry[field]).name != entry[field]:
                raise ValueError("Snapshot filenames must be local basenames")
        path, definition = raw / entry["file"], raw / entry["definition_file"]
        if digest(path) != entry["sha256"] or digest(definition) != entry["definition_sha256"]:
            raise ValueError(f"Health snapshot checksum mismatch: {key}")
        frame, quality = import_workbook(path, key, registry)
        checks[key] = quality
        if quality["duplicate_codes"] or quality["unexpected_municipality_names"]:
            errors.append(f"Unmatched names or duplicate source municipalities: {key}")
            continue
        if key == "good_self_rated_health":
            verify_self_rated_definition(definition.read_text(encoding="utf-8"))
        frame = frame.set_index("municipality_code").reindex(base["municipality_code"])
        frame["status"] = frame["status"].fillna("missing_municipality")
        column = f"{key}_pct"
        combined[column] = frame["value_pct"].to_numpy()
        combined[f"{key}_year"] = wave
        combined[f"{key}_status"] = frame["status"].to_numpy()
        checks[key]["missing_or_suppressed_in_master"] = int(frame["value_pct"].isna().sum())
        provenance[column] = {**entry, "definition": DEFINITIONS[key],
            "transformation": "Excel percentage-format numeric fraction multiplied by 100; string percentages parsed explicitly",
            "source_column": INDICATORS[key]["column"], "unit": "percent", "raw_directory": str(raw),
            "source_status_counts": quality["source_status_counts"]}
        normalized = frame.reset_index()
        normalized["indicator"], normalized["wave"] = key, wave
        health_long.append(normalized)
    if not errors:
        key = "less_good_or_poor_self_rated_health"
        combined[f"{key}_pct"] = 100 - combined["good_self_rated_health_pct"]
        combined[f"{key}_year"] = wave
        combined[f"{key}_status"] = combined["good_self_rated_health_status"]
        provenance[f"{key}_pct"] = {**provenance["good_self_rated_health_pct"],
            "definition": "Mindre godt OR Dårligt self-rated health; combined category, not Dårligt alone.",
            "transformation": "100 minus published good self-rated health percentage; five-category exhaustive partition and three selected good categories verified against the saved official definition HTML. Missing stays missing; source rounding retained."}
    report = {"status": "failed" if errors else "passed", "errors": errors, "wave": wave,
        "automated_acquisition_succeeded": True, "base_municipalities": len(base),
        "raw_directory": str(raw), "indicators": checks,
        "health_missingness_assessed": True,
        "suppression_note": "Explicit suppression and ambiguous missing tokens are retained separately. No absent or suppressed value is imputed; no marker occurs in this acquired snapshot unless listed above.",
        "temporal_alignment": "2025 health with 2024 socioeconomic indicators; each variable retains its own year.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat()}
    output = output_root / "outputs/tables"
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / f"health_profile_quality_{wave}.json", report)
    if errors:
        raise ValueError(f"Health quality checks failed: {errors}")
    processed = output_root / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    destination = processed / f"municipality_master_2024_health_{wave}.csv"
    combined.to_csv(destination, index=False, float_format="%.10g")
    pd.concat(health_long, ignore_index=True).to_csv(processed / f"health_profile_{wave}_long.csv", index=False, float_format="%.10g")
    write_json(destination.with_name(destination.stem + "_provenance.json"), {
        "master_sha256": digest(destination), "health_wave": wave,
        "raw_manifest_sha256": digest(raw / "manifest.json"),
        "base_master": str(base_path), "base_sha256": digest(base_path),
        "base_provenance": socioeconomic_provenance, "health_variables": provenance})
    print(f"Health import passed: wave {wave}; {len(base)} master municipalities.")
    for key, check in checks.items():
        print(f"{key}: {check['matched_municipalities']} matched; {check['missing_or_suppressed_in_master']} missing/suppressed")
    print(f"Combined master: {destination}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        import_snapshot(args.raw_dir)
    except (ValueError, KeyError, OSError) as exc:
        print(f"Health import failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
