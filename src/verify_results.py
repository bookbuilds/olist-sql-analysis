"""Compare a QA-certified run with the original verified aggregate snapshot."""
from pathlib import Path
from decimal import Decimal, InvalidOperation
import argparse
import csv
import json
from provenance import ROOT, file_hash, verify_gate


def tolerance(column):
    # Counts, ranks and integer cents are exact. Monetary results allow one cent.
    if column.endswith('_brl'):
        return Decimal('0.01')
    if any(word in column for word in ['pct', 'avg', 'cumulative']):
        return Decimal('0.000000001')
    return Decimal('0')


def compare(results, reference=ROOT / 'results', evidence=None):
    results, reference = Path(results), Path(reference)
    certificate = verify_gate(results, evidence)
    snapshot = json.loads((ROOT / 'evidence/verified_snapshot.json').read_text())
    for name, expected in snapshot['result_sha256'].items():
        if file_hash(reference / name) != expected:
            raise ValueError(f'Verified reference was modified: {name}')
    if certificate['analysis_sql_sha256'] != snapshot['analysis_sql_sha256'] or certificate['supplemental_sql_sha256'] != snapshot['supplemental_sql_sha256']:
        raise ValueError('SQL differs from the verified snapshot.')
    inputs = json.loads(((Path(evidence) if evidence else results.parent / 'evidence') / 'input_manifest.json').read_text())
    expected_inputs = json.loads((ROOT / 'evidence/input_manifest.json').read_text())
    if inputs != expected_inputs:
        raise ValueError('Input manifest differs from the verified snapshot.')
    if json.loads((results / 'metrics.json').read_text()) != json.loads((reference / 'metrics.json').read_text()):
        raise ValueError('Metrics/window differ from the verified snapshot.')
    comparisons = []
    for name in snapshot['result_sha256']:
        if not name.endswith('.csv'):
            continue
        with (results / name).open(newline='') as a, (reference / name).open(newline='') as b:
            actual, expected = list(csv.reader(a)), list(csv.reader(b))
        if not actual or actual[0] != expected[0] or len(actual) != len(expected):
            raise ValueError(f'{name}: headers or row count differ.')
        differing_cells = 0
        for row_number, (left, right) in enumerate(zip(actual[1:], expected[1:]), 2):
            if len(left) != len(right):
                raise ValueError(f'{name}:{row_number}: column count differs.')
            for column, x, y in zip(actual[0], left, right):
                if x == y:
                    continue
                try:
                    dx, dy = Decimal(x), Decimal(y)
                    matches = dx.is_finite() and dy.is_finite() and abs(dx - dy) <= tolerance(column)
                except InvalidOperation:
                    matches = False
                if not matches:
                    raise ValueError(f'{name}:{row_number}:{column}: snapshot mismatch.')
                differing_cells += 1
        comparisons.append({'file': name, 'rows': len(actual) - 1, 'passed': True, 'numeric_cells_within_tolerance': differing_cells, 'byte_identical': file_hash(results / name) == file_hash(reference / name)})
    return {'status': 'PASS', 'comparisons': comparisons, 'tolerance': 'Counts/ranks/cents/text/order exact; *_brl <= 0.01 BRL; percentage/average columns <= 1e-9; metrics/window exact.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--reference', type=Path, default=ROOT / 'results')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report = compare(args.results, args.reference, args.evidence)
    if args.out:
        with args.out.open('x') as stream:
            json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))
