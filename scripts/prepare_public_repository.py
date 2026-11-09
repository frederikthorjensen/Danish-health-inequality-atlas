"""Prepare a portable, path-redacted PUBLIC repository without editing originals.

Run `python -m scripts.prepare_public_repository --output public_release`.
Only documented project folders are copied. Raw acquisitions and local tooling
are excluded. Numeric observations, statistical CSVs, figures and PDFs are copied
byte-for-byte; ONLY local-path strings and related metadata hashes are updated.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def redact_paths(value):
    if isinstance(value,dict):return {k:redact_paths(v) for k,v in value.items()}
    if isinstance(value,list):return [redact_paths(v) for v in value]
    if isinstance(value,str) and (value.startswith('/Users/') or value.startswith('/private/') or value.startswith('/tmp/') or value.startswith('/home/')):
        parts=Path(value).parts
        for folder in ('data','outputs','report'):
            if folder in parts:return '/'.join(parts[parts.index(folder):])
        return '[local path omitted]'
    return value


def prepare(output):
    output=Path(output).resolve()
    if output==ROOT or ROOT.is_relative_to(output):raise ValueError('Choose a separate release directory')
    if output.exists() and any(output.iterdir()):raise ValueError('Output must be empty; existing files will not be overwritten')
    output.mkdir(parents=True,exist_ok=True)
    files=[]
    for folder in ('src','app_pages','assets','scripts','tests','report','data/processed','outputs','.streamlit','.github'):
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
    files.extend(p for pattern in ('*.txt','*.pdf','.python-version','app.py','README.md') for p in ROOT.glob(pattern) if p.is_file())
    originals={}
    for file in sorted(set(files)):
        relative=file.relative_to(ROOT)
        if '__pycache__' in relative.parts or file.suffix in ('.pyc','.log') or file.name=='secrets.toml':continue
        if relative.parts[0]=='report' and file.name.startswith('final_report_') and file.suffix=='.html':continue
        dest=output/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,dest)
        originals[str(relative)]=digest(file)
    changed=[]
    for folder in ('data/processed','outputs/tables'):
        for file in (output/folder).glob('*.json'):
            before=json.loads(file.read_text());after=redact_paths(before)
            if before!=after:
                file.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');changed.append(str(file.relative_to(output)))
    # Reconnect integrity metadata to the public copies. Never modify result values.
    path=output/'outputs/tables/analysis_manifest.json';manifest=json.loads(path.read_text())
    manifest['input_provenance_sha256']=digest(output/'data/processed/municipality_master_provenance.json')
    for item in manifest['artifacts']:item['sha256']=digest(output/item['file'])
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    pub=output/'report/publication_manifest.json';publication=json.loads(pub.read_text());publication['analysis_manifest_sha256']=digest(path)
    pub.write_text(json.dumps(publication,ensure_ascii=False,indent=2)+'\n')
    for relative in ['outputs/tables/analysis_manifest.json','report/publication_manifest.json']:
        if relative not in changed:changed.append(relative)
    # Exact-value assurance across every observation table, statistical table and figure.
    for relative,expected in originals.items():
        if Path(relative).suffix in ('.csv','.png','.pdf'):
            if digest(output/relative)!=expected:raise ValueError(f'Unexpected result change: {relative}')
    base=(ROOT/'.gitignore').read_text().split('# Downloaded data and generated outputs')[0]
    (output/'.gitignore').write_text(base+'\n# Private local material and rebuildable previews\ndata/raw/\n.agents/\n.codex/\n.aws/\n.venv*/\npublic_release/\nreport/final_report_*.html\n')
    record={'purpose':'Public repository export; original acquisition and analysis files were not modified.',
      'excluded':['data/raw/','.venv/','.agents/','.codex/','.aws/','secrets.toml','environment files','HTML previews'],
      'metadata_changes':'Only workstation paths and dependent integrity hashes; no statistical values changed.',
      'metadata_files_updated':sorted(set(changed)),
      'original_analysis_manifest_sha256':originals['outputs/tables/analysis_manifest.json'],
      'files':{str(p.relative_to(output)):digest(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output/'public_export_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='public_release')
    args=parser.parse_args();record=prepare(args.output)
    print(f"Prepared {len(record['files'])} public files; observation/statistical tables, images and PDFs unchanged.")
    print('No license was selected. Review the release directory before publishing.')


if __name__=='__main__':main()
