"""Resolve historical metadata paths without depending on the acquisition computer."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def artifact_path(recorded):
    """Resolve relative paths or a known project suffix from legacy absolute paths.

    Never fall back to reading an absolute path on the original workstation.
    """
    path=Path(recorded)
    if not path.is_absolute():
        candidate=(ROOT/path).resolve()
        if not candidate.is_relative_to(ROOT):
            raise ValueError('Artifact path escapes the project')
        return candidate
    for folder in ('data','outputs','report'):
        indices=[i for i,part in enumerate(path.parts) if part==folder]
        for i in indices:
            candidate=ROOT.joinpath(*path.parts[i:])
            if candidate.is_file():return candidate
    raise ValueError('Historical path has no corresponding project artifact')


def snapshot_source(file, expected, digest):
    """The analytical README is archived; the public project README can evolve."""
    live=ROOT/file
    if live.is_file() and digest(live)==expected:return live
    if file=='README.md':
        archived=ROOT/'report/analysis_snapshot/README.md'
        if archived.is_file() and digest(archived)==expected:return archived
    raise ValueError(f'Analysis source changed: {file}')
