"""Input identity and QA certificates. Paths are explicit; no network access."""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_inputs(data, manifest_path):
    expected = json.loads(Path(manifest_path).read_text())
    for item in expected.values():
        path = Path(data) / item['file']
        if not path.is_file() or path.stat().st_size != item['bytes'] or file_hash(path) != item['sha256']:
            raise ValueError(f"Input mismatch: {item['file']}. Stop and audit the source version; do not reuse snapshot claims.")
    return expected


def _passed_checks(evidence):
    with (evidence / 'qa_checks.csv').open(newline='') as stream:
        checks = list(csv.DictReader(stream))
    if len(checks) != 20 or len({c['check'] for c in checks}) != 20 or any(c['passed'] != 'True' for c in checks):
        raise ValueError('Expected 20 distinct passing actual-data checks.')
    return checks


def certify_results(results, evidence, sql_path, supplemental):
    _passed_checks(evidence)
    certificate = {
        'checks_passed': 20,
        'window': json.loads((results / 'metrics.json').read_text())['window'],
        'result_sha256': {p.name: file_hash(p) for p in sorted(results.iterdir()) if p.is_file()},
        'evidence_sha256': {name: file_hash(evidence / name) for name in ['qa_checks.csv', 'query_execution.csv', 'runtime.json', 'input_manifest.json']},
        'analysis_sql_sha256': file_hash(sql_path),
        'supplemental_sql_sha256': file_hash(supplemental),
    }
    (evidence / 'QA_PASSED.json').write_text(json.dumps(certificate, indent=2))
    return certificate


def verify_gate(results, evidence=None):
    results = Path(results)
    evidence = Path(evidence) if evidence else results.parent / 'evidence'
    path = evidence / 'QA_PASSED.json'
    if not path.is_file():
        raise ValueError('QA certificate absent; run analysis successfully first.')
    certificate = json.loads(path.read_text())
    _passed_checks(evidence)
    if certificate.get('checks_passed') != 20:
        raise ValueError('QA count mismatch.')
    actual = {p.name: file_hash(p) for p in sorted(results.iterdir()) if p.is_file()}
    if actual != certificate.get('result_sha256'):
        raise ValueError('Result files changed after QA. Re-run analysis before charting or reporting.')
    for name in ['qa_checks.csv', 'query_execution.csv', 'runtime.json', 'input_manifest.json']:
        if file_hash(evidence / name) != certificate.get('evidence_sha256', {}).get(name):
            raise ValueError(f'Evidence changed after QA: {name}')
    if json.loads((results / 'metrics.json').read_text())['window'] != certificate['window']:
        raise ValueError('Window differs from QA certificate.')
    return certificate
