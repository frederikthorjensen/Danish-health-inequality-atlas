"""Integration checks using acquired official data, with no invented observations."""

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src import data_collection as collection


class OfficialSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        snapshots = sorted((collection.ROOT / "data" / "raw").glob("statbank_*/manifest.json"))
        complete = [p.parent for p in snapshots if json.loads(p.read_text())["status"] == "complete"]
        if not complete:
            raise unittest.SkipTest("Acquire an official snapshot with python -m src.data_collection first")
        cls.raw = complete[-1]
        cls.metadata, cls.data, cls.manifest = collection.read_run(cls.raw)

    def test_complete_official_snapshot_passes(self):
        master, report = collection.build_master(self.metadata, self.data)
        self.assertEqual(report["status"], "passed", report["errors"])
        self.assertEqual(len(master), 98)
        self.assertEqual(set(master["municipality_code"]), set(collection.municipality_registry(self.metadata["FOLK1A"])))
        self.assertNotIn("411", set(master["municipality_code"]))
        self.assertFalse(master.isna().any().any())

    def test_missing_education_cell_is_not_silently_zero_filled(self):
        damaged = copy.deepcopy(self.data)
        dataset = damaged["HFUDD11"]["dataset"]
        if isinstance(dataset["value"], dict):
            dataset["value"]["0"] = None
        else:
            dataset["value"][0] = None
        _, report = collection.build_master(self.metadata, damaged)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["source_checks"]["HFUDD11"]["missing_cells"], 1)
        self.assertGreater(sum(report["missing_values"].values()), 0)

    def test_wrong_source_name_is_rejected(self):
        damaged = copy.deepcopy(self.data)
        labels = damaged["INDKP106"]["dataset"]["dimension"]["OMRÅDE"]["category"]["label"]
        codes = list(labels)
        labels[codes[0]] = labels[codes[1]]
        _, report = collection.build_master(self.metadata, damaged)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(report["source_checks"]["INDKP106"]["unexpected_municipality_names"])

    def test_checksum_rejects_altered_raw_file(self):
        with tempfile.TemporaryDirectory() as directory:
            raw_copy = Path(directory)
            for file in self.raw.iterdir():
                (raw_copy / file.name).write_bytes(file.read_bytes())
            target = raw_copy / "INDKP106_data.json"
            target.write_bytes(target.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                collection.read_run(raw_copy)

    def test_offline_replay_is_deterministic_and_preserves_raw(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.raw.iterdir()}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(collection, "ROOT", root), patch.object(
                collection.requests, "Session", side_effect=AssertionError("Replay must not use network")
            ):
                collection.run(self.raw)
                master_path = root / "data" / "processed" / "municipality_master_2024.csv"
                first = master_path.read_bytes()
                collection.run(self.raw)
                self.assertEqual(first, master_path.read_bytes())
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.raw.iterdir()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
