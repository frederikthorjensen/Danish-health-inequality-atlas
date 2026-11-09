"""Portability and release checks, with immutable analytical results."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from src.project_paths import ROOT,artifact_path,snapshot_source
from scripts.prepare_public_repository import redact_paths


class DeploymentTests(unittest.TestCase):
    def test_historical_absolute_path_is_resolved_inside_current_checkout(self):
        manifest=json.loads((ROOT/'outputs/tables/analysis_manifest.json').read_text())
        self.assertEqual(artifact_path(manifest['input_file']),ROOT/'data/processed/municipality_master.csv')
        self.assertEqual(artifact_path('data/processed/municipality_master.csv'),ROOT/'data/processed/municipality_master.csv')
        with self.assertRaises(ValueError):artifact_path('../outside.csv')
        with self.assertRaises(ValueError):artifact_path('/unknown/not-a-project-file.csv')

    def test_original_readme_hash_is_preserved_in_snapshot_archive(self):
        manifest=json.loads((ROOT/'outputs/tables/analysis_manifest.json').read_text())
        digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        source=snapshot_source('README.md',manifest['source_hashes']['README.md'],digest)
        self.assertEqual(digest(source),manifest['source_hashes']['README.md'])
        with self.assertRaises(ValueError):snapshot_source('README.md','not-the-recorded-hash',digest)

    def test_metadata_redaction_preserves_numeric_values_and_public_urls(self):
        sample={'path':'/Users/example/project/data/processed/file.csv','value':81.6,'missing':None,
                'nested':[98,94,.7506748302533205],'url':'https://www.statbank.dk/HISBK'}
        redacted=redact_paths(sample)
        self.assertEqual(redacted['path'],'data/processed/file.csv')
        for field in ['value','missing','nested','url']:self.assertEqual(redacted[field],sample[field])
        self.assertEqual(sample['path'],'/Users/example/project/data/processed/file.csv')
