"""Reproduce the locked Olist snapshot using external CSVs and a new output folder."""
from pathlib import Path
import argparse
import subprocess
import sys
from provenance import ROOT, verify_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True, help='Directory containing the nine original CSVs')
    parser.add_argument('--out', type=Path, required=True, help='New directory for the DB, audit, results, figures and report')
    args = parser.parse_args()
    data, out = args.data.resolve(), args.out.resolve()
    verify_inputs(data, ROOT / 'evidence/input_manifest.json')
    out.mkdir(parents=True, exist_ok=False)
    def run(script, *options):
        subprocess.run([sys.executable, str(ROOT / 'src' / script), *map(str, options)], check=True)
    run('audit_raw.py', '--data', data, '--out', out / 'audit')
    run('import_olist.py', '--data', data, '--db', out / 'olist.db', '--start', '2017-01-01', '--end', '2018-08-01')
    run('run_analysis.py', '--db', out / 'olist.db', '--out', out / 'results')
    run('verify_results.py', '--results', out / 'results', '--out', out / 'comparison.json')
    run('make_charts.py', '--results', out / 'results', '--out', out / 'figures')
    run('build_report.py', '--results', out / 'results', '--figures', out / 'figures', '--out', out / 'docs')
    print('PASS: input hashes, audit, import, Q01-Q12, 20 QA checks, snapshot comparison, figures and report.')


if __name__ == '__main__':
    main()
