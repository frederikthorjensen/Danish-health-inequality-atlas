"""Collect official StatBank data; replay raw snapshots without network access.

Usage: python -m src.data_collection [--raw-dir data/raw/<snapshot>]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any
import sys
import uuid

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.statbank.dk/v1"
YEAR = "2024"
TABLES = ("FOLK1A", "INDKP106", "HFUDD11")
EDUCATION_AGES = [f"{a}-{a + 4}" for a in range(25, 65, 5)]


def write_json(path: Path, value: object, exclusive: bool = False) -> None:
    with path.open("x" if exclusive else "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def values(metadata: dict, dimension: str) -> dict[str, str]:
    variable = next(v for v in metadata["variables"] if v["id"] == dimension)
    return {v["id"]: v["text"] for v in variable["values"]}


def municipality_registry(metadata: dict) -> dict[str, str]:
    """Official FOLK1A labels; exclude aggregates and Christiansø (411).

    Christiansø is an administrative area outside the 98 municipalities.
    Municipality codes in these tables are three digits, >=101.
    """
    return {c: n for c, n in values(metadata, "OMRÅDE").items()
            if c.isdigit() and len(c) == 3 and int(c) >= 101 and c != "411"}


def selections(codes: list[str]) -> dict:
    return {
        "FOLK1A": {"OMRÅDE": codes, "KØN": ["TOT"],
                   "ALDER": ["IALT", *map(str, range(126))],
                   "CIVILSTAND": ["TOT"], "Tid": [f"{YEAR}K1"]},
        "INDKP106": {"OMRÅDE": codes, "ENHED": ["118"], "KOEN": ["MOK"],
                     "ALDER1": ["00"], "INDKINTB": ["000"], "Tid": [YEAR]},
        "HFUDD11": {"BOPOMR": codes, "HERKOMST": ["TOT"],
                    "HFUDD": ["TOT", "H10", "H90"], "ALDER": EDUCATION_AGES,
                    "KØN": ["TOT"], "Tid": [YEAR]},
    }


def fetch_run() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = ROOT / "data" / "raw" / f"statbank_{stamp}_{uuid.uuid4().hex[:8]}"
    raw.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
                "reference_year": YEAR, "api": API, "files": [],
                "licence": "CC BY 4.0; source: Statistics Denmark", "status": "in_progress"}
    session = requests.Session()
    session.headers["User-Agent"] = "DanishHealthInequalityAtlas/0.1 (public-data research)"
    session.mount("https://", HTTPAdapter(max_retries=Retry(
        total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"], respect_retry_after_header=True)))

    def retrieve(name: str, endpoint: str, payload: dict) -> dict:
        response = session.post(f"{API}/{endpoint}", json=payload, timeout=(15, 120))
        response.raise_for_status()
        body = response.content
        with (raw / name).open("xb") as handle:
            handle.write(body)
        manifest["files"].append({
            "file": name, "url": response.url, "method": "POST", "request": payload,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "http_status": response.status_code, "sha256": hashlib.sha256(body).hexdigest()})
        data = response.json()
        if "error" in data:
            raise ValueError(f"StatBank error: {data}")
        return data

    try:
        metadata = {t: retrieve(f"{t}_metadata.json", "tableinfo", {
            "table": t, "format": "JSON", "lang": "da"}) for t in TABLES}
        registry = municipality_registry(metadata["FOLK1A"])
        if len(registry) != 98:
            raise ValueError(f"Expected 98 municipality codes; found {len(registry)}")
        for table, selection in selections(sorted(registry)).items():
            if set(selection) != {v["id"] for v in metadata[table]["variables"]}:
                raise ValueError(f"Unexpected dimensions in {table}")
            for dimension, selected in selection.items():
                if not set(selected) <= values(metadata[table], dimension).keys():
                    raise ValueError(f"Unavailable codes: {table}/{dimension}")
            retrieve(f"{table}_data.json", "data", {
                "table": table, "format": "JSONSTAT", "lang": "da",
                "variables": [{"code": c, "values": v} for c, v in selection.items()]})
        manifest["status"] = "complete"
    except Exception as exc:
        manifest.update(status="failed", error=str(exc))
        raise
    finally:
        write_json(raw / "manifest.json", manifest, exclusive=True)
        session.close()
    return raw


def read_run(raw: Path) -> tuple[dict, dict, dict]:
    manifest = json.loads((raw / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "complete" or manifest["reference_year"] != YEAR:
        raise ValueError("Incomplete raw snapshot or incompatible reference year")
    required = {f"{t}_{k}.json" for t in TABLES for k in ("metadata", "data")}
    if {item["file"] for item in manifest["files"]} != required:
        raise ValueError("Manifest must contain all six required responses")
    for item in manifest["files"]:
        if hashlib.sha256((raw / item["file"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Raw checksum mismatch: {item['file']}")
    metadata = {t: json.loads((raw / f"{t}_metadata.json").read_text(encoding="utf-8")) for t in TABLES}
    data = {t: json.loads((raw / f"{t}_data.json").read_text(encoding="utf-8")) for t in TABLES}
    return metadata, data, manifest


def decode_jsonstat(payload: dict) -> pd.DataFrame:
    """Decode JSON-stat 1.x by category position; never replace missing with zero."""
    dataset = payload["dataset"]
    dimensions = dataset["dimension"]
    ids, sizes = dimensions["id"], dimensions["size"]
    categories = []
    for code, size in zip(ids, sizes, strict=True):
        index = dimensions[code]["category"]["index"]
        ordered = sorted(index, key=index.get) if isinstance(index, dict) else index
        if len(ordered) != size:
            raise ValueError(f"Invalid dimension size: {code}")
        categories.append(ordered)
    frame = pd.DataFrame(itertools.product(*categories), columns=ids)
    raw_values = dataset["value"]
    if isinstance(raw_values, dict):
        raw_values = [raw_values.get(str(i)) for i in range(len(frame))]
    if len(raw_values) != len(frame):
        raise ValueError("JSON-stat values do not match dimensions")
    frame["value"] = pd.to_numeric(pd.Series(raw_values), errors="raise")
    status = dataset.get("status", {})
    if status:
        flags = [status.get(str(i)) for i in range(len(frame))] if isinstance(status, dict) else status
        if len(flags) != len(frame):
            raise ValueError("Invalid status length")
        flags = pd.Series(flags)
        frame.loc[flags.notna() & flags.ne(""), "value"] = np.nan
    return frame


def build_master(metadata: dict, data: dict) -> tuple[pd.DataFrame, dict]:
    registry = municipality_registry(metadata["FOLK1A"])
    errors, source_checks, decoded = [], {}, {}
    for table, selection in selections(sorted(registry)).items():
        frame = decode_jsonstat(data[table])
        geo = "BOPOMR" if table == "HFUDD11" else "OMRÅDE"
        keys = list(selection)
        expected = pd.DataFrame(itertools.product(*selection.values()), columns=keys)
        duplicates = int(frame.duplicated(keys).sum())
        comparison = expected.merge(frame[keys], on=keys, how="outer", indicator=True)
        unmatched = int(comparison["_merge"].ne("both").sum())
        labels = data[table]["dataset"]["dimension"][geo]["category"]["label"]
        names = {c: labels.get(c) for c, n in registry.items() if labels.get(c) != n}
        source_checks[table] = {
            "rows": len(frame), "expected_rows": len(expected),
            "municipalities": int(frame[geo].nunique()),
            "missing_cells": int(frame["value"].isna().sum()),
            "duplicate_cells": duplicates, "unexpected_or_missing_cells": unmatched,
            "unexpected_municipality_names": names,
            "negative_cells": int(frame["value"].lt(0).sum())}
        if duplicates or unmatched or names or frame["value"].lt(0).any():
            errors.append(f"Source structure/name/range check failed: {table}")
        if duplicates:
            raise ValueError(f"Duplicate source cells in {table}; cannot aggregate safely")
        decoded[table] = frame.rename(columns={geo: "municipality_code"})
    master = pd.DataFrame(sorted(registry.items()), columns=["municipality_code", "municipality"]).set_index("municipality_code")
    pop = decoded["FOLK1A"].pivot(index="municipality_code", columns="ALDER", values="value")
    master["population"] = pop["IALT"]
    master["population_year"] = int(YEAR)
    master["population_reference_date"] = f"{YEAR}-01-01"
    counts = {}
    for label, ages in {"0_17": range(18), "18_64": range(18, 65), "65_plus": range(65, 126)}.items():
        count = pop[[str(a) for a in ages]].sum(axis=1, min_count=len(ages))
        counts[label] = count
        master[f"population_{label}"] = count
        master[f"age_{label}_share_pct"] = 100 * count / master["population"].where(master["population"].gt(0))
        master[f"age_{label}_share_year"] = int(YEAR)
    master["age_structure_reference_date"] = f"{YEAR}-01-01"
    age_sum = pd.DataFrame(counts).sum(axis=1, min_count=3)
    age_bad = int((age_sum.isna() | age_sum.ne(pop["IALT"])).sum())
    if age_bad:
        errors.append("Single-year ages do not reconcile with total population")
    master["disposable_income_mean_dkk"] = decoded["INDKP106"].set_index("municipality_code")["value"]
    master["disposable_income_year"] = int(YEAR)
    edu = decoded["HFUDD11"].groupby(["municipality_code", "HFUDD"])["value"].sum(min_count=len(EDUCATION_AGES)).unstack()
    master["education_population_25_64"] = edu["TOT"]
    master["primary_education_count_25_64"] = edu["H10"]
    master["education_unknown_count_25_64"] = edu["H90"]
    denominator = edu["TOT"].where(edu["TOT"].gt(0))
    master["low_education_share_25_64_pct"] = 100 * edu["H10"] / denominator
    master["education_unknown_share_25_64_pct"] = 100 * edu["H90"] / denominator
    master["low_education_year"] = int(YEAR)
    master["education_unknown_year"] = int(YEAR)
    master["education_reference_date"] = f"{YEAR}-09-30"
    edu_bad = int((edu["H10"] + edu["H90"]).gt(edu["TOT"]).sum())
    if edu_bad:
        errors.append("Primary plus unknown education exceeds education population")
    master = master.reset_index()
    ranges = {}
    for column in master.select_dtypes(include="number").columns:
        series = master[column]
        if column.endswith("year"):
            lower, upper = int(YEAR), int(YEAR)
        elif column.endswith("_pct"):
            lower, upper = 0, 100
        else:
            positive = column in ("population", "education_population_25_64", "disposable_income_mean_dkk")
            lower, upper = (1 if positive else 0), 10_000_000
        invalid = ~np.isfinite(series) | ~series.between(lower, upper)
        is_count = (column.startswith("population") or "count" in column or column == "education_population_25_64") and not column.endswith("year")
        fractional = int(series.mod(1).ne(0).sum()) if is_count else 0
        ranges[column] = {"min": float(series.min()) if series.notna().any() else None,
                          "max": float(series.max()) if series.notna().any() else None,
                          "allowed_min": lower, "allowed_max": upper,
                          "invalid_or_missing": int(invalid.sum()), "fractional_counts": fractional}
        if invalid.any() or fractional:
            errors.append(f"Numeric range/missing/integer check failed: {column}")
    missing = {c: int(n) for c, n in master.isna().sum().items()}
    if len(master) != 98 or any(missing.values()):
        errors.append("Expected 98 complete municipality rows")
    if any(c["missing_cells"] for c in source_checks.values()):
        errors.append("Missing source cells")
    duplicate_codes = int(master.duplicated("municipality_code").sum())
    duplicate_names = int(master.duplicated("municipality").sum())
    if duplicate_codes or duplicate_names:
        errors.append("Duplicate municipality codes/names")
    report = {
        "status": "passed" if not errors else "failed", "errors": errors,
        "expected_municipalities": 98, "matched_municipalities": len(master),
        "missing_values": missing, "duplicate_codes": duplicate_codes,
        "duplicate_names": duplicate_names, "source_checks": source_checks,
        "age_total_mismatches": age_bad, "education_component_mismatches": edu_bad,
        "numeric_ranges": ranges,
        "range_policy": "Shares 0–100%; counts nonnegative integers, positive denominators; income positive. 10 million is a broad screening ceiling, not an estimated bound.",
        "limitations": [
            "Common 2024 label: income is annual; population 1 January; education 30 September.",
            "Education denominator includes unknown attainment; unknown share is retained separately.",
            "StatBank metadata declares suppressedDataValue=0: confidential small counts may be indistinguishable from genuine zero counts; no imputation performed.",
            "Municipality names checked against FOLK1A labels; no fuzzy matching."]}
    return master, report


def run(raw_dir: Path | None = None) -> dict:
    raw = raw_dir.resolve() if raw_dir else fetch_run()
    metadata, data, manifest = read_run(raw)
    master, report = build_master(metadata, data)
    report["raw_directory"] = str(raw.relative_to(ROOT)) if raw.is_relative_to(ROOT) else str(raw)
    report["raw_manifest_sha256"] = hashlib.sha256((raw / "manifest.json").read_bytes()).hexdigest()
    report["source_retrieval_utc"] = manifest["created_at_utc"]
    output = ROOT / "outputs" / "tables"
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / f"data_quality_report_{YEAR}.json", report)
    pd.DataFrame.from_dict(report["numeric_ranges"], orient="index").rename_axis("variable").to_csv(output / f"numeric_ranges_{YEAR}.csv", encoding="utf-8")
    if report["status"] != "passed":
        raise ValueError(f"Quality checks failed; master not published: {report['errors']}")
    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    destination = processed / f"municipality_master_{YEAR}.csv"
    master.to_csv(destination, index=False, encoding="utf-8", float_format="%.10g")
    selection = selections(sorted(municipality_registry(metadata["FOLK1A"])))
    write_json(processed / f"municipality_master_{YEAR}_provenance.json", {
        "reference_year": YEAR, "raw_directory": report["raw_directory"],
        "raw_manifest_sha256": report["raw_manifest_sha256"],
        "master_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "sources": {t: {"url": f"https://www.statbank.dk/{t}", "updated": metadata[t]["updated"],
                        "documentation": metadata[t]["documentation"], "selection": selection[t]} for t in TABLES}})
    print(f"Quality checks passed: {len(master)} municipalities; {sum(report['missing_values'].values())} missing values.")
    print(f"Raw: {raw}\nMaster: {destination}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, help="Replay a complete raw snapshot without network access")
    args = parser.parse_args()
    try:
        run(args.raw_dir)
    except (requests.RequestException, ValueError, KeyError, OSError) as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
