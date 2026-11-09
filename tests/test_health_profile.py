"""Checks against real official exports; mutations test rejection/missingness only."""

import json
from pathlib import Path
import tempfile
import unittest
import warnings

from openpyxl import load_workbook
import pandas as pd

from src import health_profile_import as health
from src.health_profile_collection import INDICATORS, ROOT


class HealthProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        complete = [p.parent for p in sorted((ROOT / "data/raw").glob("health_profile_2025_*/manifest.json"))
                    if json.loads(p.read_text())["status"] == "complete"]
        if not complete:
            raise unittest.SkipTest("Acquire a real 2025 health-profile snapshot first")
        cls.raw = complete[-1]
        base = pd.read_csv(ROOT / "data/processed/municipality_master_2024.csv", dtype={"municipality_code": str})
        cls.registry = dict(zip(base["municipality_code"], base["municipality"], strict=True))

    def workbook(self):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Workbook contains no default style")
            return load_workbook(self.raw / "daily_smoking_2025.xlsx")

    def test_all_official_exports_match_98(self):
        for key in INDICATORS:
            with self.subTest(key=key):
                frame, quality = health.import_workbook(self.raw / f"{key}_2025.xlsx", key, self.registry)
                self.assertEqual(quality["matched_municipalities"], 98)
                self.assertFalse(quality["missing_municipalities"])
                self.assertFalse(quality["duplicate_codes"])
                self.assertFalse(quality["unexpected_municipality_names"])
                self.assertTrue(frame["value_pct"].between(0, 100).all())

    def test_excel_percentage_format_controls_scaling(self):
        workbook = self.workbook()
        cell = workbook.active["B2"]
        percentage, status = health.parse_percentage(cell)
        self.assertAlmostEqual(percentage, cell.value * 100)
        self.assertEqual(status, "observed")
        cell.number_format = "General"
        with self.assertRaisesRegex(ValueError, "percentage formatting"):
            health.parse_percentage(cell)
        workbook.close()

    def test_missing_and_suppressed_cells_remain_null(self):
        workbook = self.workbook()
        cell = workbook.active["B2"]
        cell.value = None
        self.assertEqual(health.parse_percentage(cell), (None, "missing_source_value"))
        cell.value = ".."
        self.assertEqual(health.parse_percentage(cell), (None, "suppressed_or_unavailable"))
        workbook.close()

    def test_duplicate_rows_are_reported_without_aggregation(self):
        workbook = self.workbook()
        sheet = workbook.active
        sheet.append([c.value for c in sheet[2]])
        for source, duplicate in zip(sheet[2], sheet[sheet.max_row], strict=True):
            duplicate.number_format = source.number_format
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.xlsx"
            workbook.save(path)
            _, report = health.import_workbook(path, "daily_smoking", self.registry)
        workbook.close()
        self.assertTrue(report["duplicate_codes"])

    def test_self_rated_health_definition_is_verified(self):
        definition = (self.raw / "good_self_rated_health_definition.html").read_text()
        health.verify_self_rated_definition(definition)
        with self.assertRaisesRegex(ValueError, "partition unverified"):
            health.verify_self_rated_definition(definition.replace("font-weight:bold", "font-weight:normal"))

    def test_health_checksum_rejects_altered_export(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            for file in self.raw.iterdir():
                (raw / file.name).write_bytes(file.read_bytes())
            target = raw / "daily_smoking_2025.xlsx"
            target.write_bytes(target.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                health.import_snapshot(raw, output_root=raw / "derived")

    def test_replay_preserves_raw_and_socioeconomic_master(self):
        before = {p.name: health.digest(p) for p in self.raw.iterdir()}
        base_path = ROOT / "data/processed/municipality_master_2024.csv"
        base_hash = health.digest(base_path)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = health.import_snapshot(self.raw, output_root=root)
            self.assertEqual(report["status"], "passed")
            result = root / "data/processed/municipality_master_2024_health_2025.csv"
            initial = result.read_bytes()
            frame = pd.read_csv(result)
            self.assertTrue(((frame["less_good_or_poor_self_rated_health_pct"] + frame["good_self_rated_health_pct"] - 100).abs() < 1e-8).all())
            health.import_snapshot(self.raw, output_root=root)
            self.assertEqual(initial, result.read_bytes())
        self.assertEqual(before, {p.name: health.digest(p) for p in self.raw.iterdir()})
        self.assertEqual(base_hash, health.digest(base_path))


if __name__ == "__main__":
    unittest.main()
