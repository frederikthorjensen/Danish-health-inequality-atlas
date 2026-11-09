"""Integration checks using real HISBK extracts; no substitute observations."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from src import life_expectancy_collection as life


class LifeExpectancyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        complete = [p.parent for p in sorted((life.ROOT / "data/raw").glob("hisbk_*/manifest.json"))
                    if json.loads(p.read_text())["status"] == "complete"]
        if not complete:
            raise unittest.SkipTest("Acquire a real HISBK snapshot first")
        cls.raw = complete[-1]
        cls.metadata, cls.data, cls.manifest = life.read_snapshot(cls.raw)
        cls.base, _ = life.read_base(life.BASE)

    def test_latest_period_selected_from_metadata(self):
        periods = life.values(self.metadata, "Tid")
        self.assertEqual(self.manifest["period"], life.latest_period(self.metadata))
        self.assertEqual(self.manifest["period"], max(periods, key=lambda p: int(p.split(":")[1])))

    def test_98_rows_with_source_missingness_preserved(self):
        combined, report = life.build_master(self.base, self.metadata, self.data, self.manifest["period"])
        self.assertEqual(len(combined), 98)
        self.assertEqual(report["matched_municipalities"], 98)
        self.assertFalse(report["errors"])
        source = life.decode_jsonstat(self.data)
        for sex, column in life.SEX_COLUMNS.items():
            direct = source.loc[source["KØN"].eq(sex)].set_index("OMRÅDE")["value"].replace(0, float("nan"))
            expected = combined["municipality_code"].map(direct)
            pd.testing.assert_series_equal(combined[column], expected, check_names=False)
        pd.testing.assert_series_equal(combined["life_expectancy_sex_gap"],
            combined["life_expectancy_female"] - combined["life_expectancy_male"], check_names=False)
        if self.manifest["period"] == "2021:2025":
            unavailable = set(combined.loc[combined["life_expectancy_total"].isna(), "municipality"])
            self.assertEqual(unavailable, {"Ærø", "Samsø", "Fanø", "Læsø"})
            self.assertEqual(report["municipalities_with_all_three_values"], 94)
            self.assertEqual(report["missing_values"]["life_expectancy_sex_gap"], 4)

    def test_duplicate_cells_rejected(self):
        damaged = copy.deepcopy(self.data)
        dimension = damaged["dataset"]["dimension"]["KØN"]["category"]["index"]
        # Repeated category labels make source-key duplicates without new values.
        damaged["dataset"]["dimension"]["KØN"]["category"]["index"] = ["TOT"] * len(dimension)
        _, report = life.build_master(self.base, self.metadata, damaged, self.manifest["period"])
        self.assertEqual(report["status"], "failed")
        self.assertGreater(report["duplicate_source_cells"], 0)

    def test_unexpected_municipality_name_rejected(self):
        damaged = copy.deepcopy(self.data)
        labels = damaged["dataset"]["dimension"]["OMRÅDE"]["category"]["label"]
        labels["101"] = labels["147"]
        _, report = life.build_master(self.base, self.metadata, damaged, self.manifest["period"])
        self.assertEqual(report["status"], "failed")
        self.assertIn("101", report["unexpected_municipality_names"])

    def test_checksum_rejects_altered_response(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            for path in self.raw.iterdir():
                (raw / path.name).write_bytes(path.read_bytes())
            target = raw / "HISBK_data.json"
            target.write_bytes(target.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                life.read_snapshot(raw)

    def test_offline_replay_preserves_raw_base_and_existing_columns(self):
        before = {p.name: life.digest(p) for p in self.raw.iterdir()}
        base_hash = life.digest(life.BASE)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(life.requests, "Session", side_effect=AssertionError("Replay must not use network")), patch("builtins.print"):
                life.run(self.raw, output_root=output)
                target = output / "data/processed/municipality_master.csv"
                first = target.read_bytes()
                result = pd.read_csv(target, dtype={"municipality_code": str})
                pd.testing.assert_frame_equal(result[self.base.columns], self.base)
                life.run(self.raw, output_root=output)
                self.assertEqual(first, target.read_bytes())
        self.assertEqual(base_hash, life.digest(life.BASE))
        self.assertEqual(before, {p.name: life.digest(p) for p in self.raw.iterdir()})


if __name__ == "__main__":
    unittest.main()
