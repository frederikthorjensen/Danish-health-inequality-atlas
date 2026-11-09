"""Acquire HISBK and append life expectancy to the validated combined master.

Run: python -m src.life_expectancy_collection
Replay: python -m src.life_expectancy_collection --raw-dir data/raw/hisbk_<snapshot>
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any
import re
import sys
import uuid

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.data_collection import API, ROOT, decode_jsonstat, values, write_json

BASE = ROOT / "data/processed/municipality_master_2024_health_2025.csv"
SEX_COLUMNS = {"TOT": "life_expectancy_total", "M": "life_expectancy_male", "K": "life_expectancy_female"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def latest_period(metadata: dict) -> str:
    periods = list(values(metadata, "Tid"))
    if not periods or any(not re.fullmatch(r"\d{4}:\d{4}", p) for p in periods):
        raise ValueError("Unexpected HISBK period format")
    return max(periods, key=lambda p: tuple(map(int, p.split(":")))[::-1])


def read_base(base_path: Path) -> tuple[pd.DataFrame, dict]:
    provenance_path = base_path.with_name(base_path.stem + "_provenance.json")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if digest(base_path) != provenance["master_sha256"]:
        raise ValueError("Combined input master checksum mismatch")
    base = pd.read_csv(base_path, dtype={"municipality_code": str})
    if (len(base) != 98 or base[["municipality_code", "municipality"]].isna().any().any()
            or base["municipality_code"].duplicated().any() or base["municipality"].duplicated().any()):
        raise ValueError("Combined input must contain 98 unique municipality codes and names")
    if any(c.startswith("life_expectancy_") for c in base.columns):
        raise ValueError("Use the pre-life-expectancy combined master as input")
    return base, provenance


def acquire(codes: list[str]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = ROOT / "data/raw" / f"hisbk_{stamp}_{uuid.uuid4().hex[:8]}"
    raw.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {"table": "HISBK", "status": "in_progress", "files": [],
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "licence": "Statistics Denmark; CC BY 4.0 with attribution"}
    session = requests.Session()
    session.headers["User-Agent"] = "DanishHealthInequalityAtlas/0.1 (public-data research)"
    session.mount("https://", HTTPAdapter(max_retries=Retry(
        total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"], respect_retry_after_header=True)))

    def retrieve(filename: str, endpoint: str, payload: dict) -> dict:
        response = session.post(f"{API}/{endpoint}", json=payload, timeout=(15, 120))
        response.raise_for_status()
        with (raw / filename).open("xb") as handle:
            handle.write(response.content)
        manifest["files"].append({"file": filename, "url": response.url,
            "method": "POST", "request": payload, "http_status": response.status_code,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "sha256": digest(raw / filename)})
        data = response.json()
        if "error" in data:
            raise ValueError(f"StatBank error: {data}")
        return data

    try:
        metadata = retrieve("HISBK_metadata.json", "tableinfo", {"table": "HISBK", "format": "JSON", "lang": "da"})
        if {v["id"] for v in metadata["variables"]} != {"OMRÅDE", "KØN", "Tid"}:
            raise ValueError("Unexpected HISBK dimensions")
        period = latest_period(metadata)
        selection = {"OMRÅDE": ["000", *sorted(codes)], "KØN": list(SEX_COLUMNS), "Tid": [period]}
        for dimension, selected in selection.items():
            if not set(selected) <= values(metadata, dimension).keys():
                raise ValueError(f"Unavailable HISBK codes in {dimension}")
        manifest.update(period=period, selection=selection)
        retrieve("HISBK_data.json", "data", {"table": "HISBK", "format": "JSONSTAT", "lang": "da",
            "variables": [{"code": c, "values": v} for c, v in selection.items()]})
        manifest["status"] = "complete"
    except Exception as exc:
        manifest.update(status="failed", error=str(exc))
        raise
    finally:
        write_json(raw / "manifest.json", manifest, exclusive=True)
        session.close()
    return raw


def read_snapshot(raw: Path) -> tuple[dict, dict, dict]:
    manifest = json.loads((raw / "manifest.json").read_text(encoding="utf-8"))
    if manifest["table"] != "HISBK" or manifest["status"] != "complete":
        raise ValueError("Require a complete HISBK snapshot")
    if len(manifest["files"]) != 2 or {e["file"] for e in manifest["files"]} != {"HISBK_metadata.json", "HISBK_data.json"}:
        raise ValueError("Unexpected raw response files")
    for entry in manifest["files"]:
        if digest(raw / entry["file"]) != entry["sha256"]:
            raise ValueError(f"HISBK checksum mismatch: {entry['file']}")
    metadata = json.loads((raw / "HISBK_metadata.json").read_text(encoding="utf-8"))
    data = json.loads((raw / "HISBK_data.json").read_text(encoding="utf-8"))
    if manifest["period"] != latest_period(metadata):
        raise ValueError("Snapshot does not use the latest period in its saved metadata")
    return metadata, data, manifest


def build_master(base: pd.DataFrame, metadata: dict, data: dict, period: str) -> tuple[pd.DataFrame, dict]:
    frame = decode_jsonstat(data)
    registry = dict(zip(base["municipality_code"], base["municipality"], strict=True))
    expected = pd.DataFrame(itertools.product(["000", *registry], SEX_COLUMNS, [period]), columns=["OMRÅDE", "KØN", "Tid"])
    keys = ["OMRÅDE", "KØN", "Tid"]
    duplicates = int(frame.duplicated(keys).sum())
    structural = expected.merge(frame[keys], on=keys, how="outer", indicator=True)
    unmatched = int(structural["_merge"].ne("both").sum())
    metadata_names = values(metadata, "OMRÅDE")
    data_names = data["dataset"]["dimension"]["OMRÅDE"]["category"]["label"]
    unexpected_names = {c: {"master": n, "metadata": metadata_names.get(c), "response": data_names.get(c)}
        for c, n in registry.items() if metadata_names.get(c) != n or data_names.get(c) != n}
    errors = []
    if duplicates or unmatched or unexpected_names:
        errors.append("Unexpected source cells, duplicate cells, or municipality names")
    if errors:
        return base.copy(), {"status": "failed", "errors": errors, "period": period,
            "duplicate_source_cells": duplicates, "unexpected_or_missing_source_cells": unmatched,
            "unexpected_municipality_names": unexpected_names}
    # Zero is not a possible life expectancy. StatBank metadata declares zero
    # as its suppression encoding; preserve the original bytes and expose null.
    encoded_zero = frame["value"].eq(0)
    frame["source_status"] = np.where(frame["value"].isna(), "missing_or_suppressed", "observed")
    frame.loc[encoded_zero, "source_status"] = "suppressed_zero_encoding"
    frame.loc[encoded_zero, "value"] = np.nan
    wide = frame.pivot(index="OMRÅDE", columns="KØN", values="value")
    status = frame.pivot(index="OMRÅDE", columns="KØN", values="source_status")
    combined = base.copy()
    for sex, column in SEX_COLUMNS.items():
        combined[column] = combined["municipality_code"].map(wide[sex])
    combined["life_expectancy_sex_gap"] = combined["life_expectancy_female"] - combined["life_expectancy_male"]
    combined["life_expectancy_period"] = period
    for sex, label in (("TOT", "total"), ("M", "male"), ("K", "female")):
        combined[f"life_expectancy_{label}_status"] = combined["municipality_code"].map(status[sex])
    ranges, national = {}, {}
    for sex, column in SEX_COLUMNS.items():
        series = combined[column]
        invalid = series.notna() & (~np.isfinite(series) | ~series.between(50, 110))
        if invalid.any():
            errors.append(f"Implausible numeric values: {column}")
        minimum, maximum = series.min(), series.max()
        ranges[column] = {"min": float(minimum) if pd.notna(minimum) else None,
            "max": float(maximum) if pd.notna(maximum) else None,
            "minimum_municipalities": combined.loc[series.eq(minimum), "municipality"].tolist(),
            "maximum_municipalities": combined.loc[series.eq(maximum), "municipality"].tolist(),
            "allowed_min": 50, "allowed_max": 110, "invalid_nonmissing": int(invalid.sum())}
        national_value = wide.at["000", sex]
        national[column] = float(national_value) if pd.notna(national_value) else None
        if pd.notna(national_value) and (not np.isfinite(national_value) or not 50 <= national_value <= 110):
            errors.append(f"Implausible national value: {column}")
    gap = combined["life_expectancy_sex_gap"]
    gap_bad = gap.notna() & (~np.isfinite(gap) | ~gap.between(-20, 20))
    if gap_bad.any():
        errors.append("Implausible sex gap")
    missing = {c: int(combined[c].isna().sum()) for c in [*SEX_COLUMNS.values(), "life_expectancy_sex_gap", "life_expectancy_period"]}
    unavailable = combined.loc[combined[list(SEX_COLUMNS.values())].isna().any(axis=1), ["municipality_code", "municipality"]].to_dict("records")
    report = {"status": "failed" if errors else "passed_with_source_missingness" if unavailable else "passed",
        "errors": errors, "table": "HISBK", "period": period, "master_rows": len(combined),
        "matched_municipalities": len(registry), "municipalities_with_all_three_values": int(combined[list(SEX_COLUMNS.values())].notna().all(axis=1).sum()),
        "missing_values": missing, "unavailable_municipalities": unavailable,
        "duplicate_municipality_codes": int(combined["municipality_code"].duplicated().sum()),
        "duplicate_source_cells": duplicates, "unexpected_or_missing_source_cells": unmatched,
        "unexpected_municipality_names": unexpected_names,
        "source_status_counts": {str(k): int(v) for k, v in frame["source_status"].value_counts().items()},
        "source_footnote": metadata.get("footnote"), "national_values_years": national,
        "municipality_ranges_years": ranges,
        "sex_gap_range_years": {"min": float(gap.min()) if gap.notna().any() else None,
            "max": float(gap.max()) if gap.notna().any() else None, "invalid_nonmissing": int(gap_bad.sum()), "allowed_min": -20, "allowed_max": 20},
        "quality_only": True,
        "limitations": ["Five-year period life expectancy at birth, not an annual value or a prediction for a birth cohort.",
            "Missing/suppressed estimates are not imputed; the sex gap remains null if either sex is unavailable.",
            "Both-sex life expectancy is retrieved directly, never averaged from male/female values.",
            "National values are retrieved directly for area 000, never averaged over municipalities.",
            "Ranges are broad validation screens, not statistical results; missingness is reported without dropping municipalities."]}
    return combined, report


def run(raw_dir: Path | None = None, base_path: Path = BASE, output_root: Path = ROOT) -> dict:
    base, base_provenance = read_base(base_path)
    raw = raw_dir.resolve() if raw_dir else acquire(base["municipality_code"].tolist())
    metadata, data, manifest = read_snapshot(raw)
    combined, report = build_master(base, metadata, data, manifest["period"])
    report.update(raw_directory=str(raw), raw_manifest_sha256=digest(raw / "manifest.json"),
                  source_retrieval_utc=manifest["created_at_utc"])
    output = output_root / "outputs/tables"
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "life_expectancy_quality.json", report)
    if report["status"] == "failed":
        raise ValueError(f"HISBK quality checks failed: {report['errors']}")
    processed = output_root / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    destination = processed / "municipality_master.csv"
    combined.to_csv(destination, index=False, float_format="%.10g")
    shared = {"table": "HISBK", "source_url": "https://www.statbank.dk/HISBK", "period": manifest["period"],
        "unit": "years", "raw_directory": str(raw), "selection": manifest["selection"],
        "updated": metadata["updated"], "documentation": metadata["documentation"], "footnote": metadata.get("footnote")}
    variables = {column: {**shared, "sex_code": sex, "transformation": "Direct official period life expectancy; null/suppression preserved"}
                 for sex, column in SEX_COLUMNS.items()}
    variables["life_expectancy_sex_gap"] = {**shared, "transformation": "life_expectancy_female - life_expectancy_male; null if either is missing"}
    variables["life_expectancy_period"] = {**shared, "transformation": "Exact selected HISBK period code"}
    write_json(processed / "municipality_master_provenance.json", {
        "master_sha256": digest(destination), "base_master": str(base_path), "base_sha256": digest(base_path),
        "base_provenance": base_provenance, "raw_manifest_sha256": digest(raw / "manifest.json"),
        "life_expectancy_variables": variables})
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Raw: {raw}\nMaster: {destination}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, help="Replay a complete raw snapshot without network access")
    args = parser.parse_args()
    try:
        run(args.raw_dir)
    except (requests.RequestException, ValueError, KeyError, OSError) as exc:
        print(f"Life-expectancy pipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
