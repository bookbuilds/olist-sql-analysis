"""Adversarial QA/portability checks against copied aggregate evidence; no raw data needed."""
from pathlib import Path
import argparse
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from provenance import certify_results, verify_inputs
from make_charts import charts
from build_report import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=ROOT / 'results')
    parser.add_argument('--evidence', type=Path, default=ROOT / 'evidence')
    parser.add_argument('--figures', type=Path, default=ROOT / 'figures')
    args = parser.parse_args()
    checks = []
    with tempfile.TemporaryDirectory(prefix='olist_guard_') as temp:
        temp = Path(temp)
        def copy_case(name):
            case = temp / name
            for source, dest in [(args.results, 'results'), (args.evidence, 'evidence'), (args.figures, 'figures')]:
                shutil.copytree(source, case / dest)
            return case
        def rejected(name, action, output):
            try:
                action()
            except (ValueError, RuntimeError, KeyError):
                if output.exists():
                    raise AssertionError(f'{name}: created output before rejecting invalid evidence')
                checks.append({'check': name, 'passed': True})
            else:
                raise AssertionError(f'{name}: unsafe input was accepted')
        def certify(case):
            certify_results(case / 'results', case / 'evidence', ROOT / 'sql/analysis.sql', ROOT / 'sql/supplemental_checks.sql')
        case = copy_case('stale_result')
        target = case / 'results/Q07.csv'
        target.write_text(target.read_text().replace('1110166.49', '1110167.49', 1))
        rejected('chart_rejects_result_changed_after_QA', lambda: charts(case / 'results', case / 'output'), case / 'output')
        case = copy_case('marker_only')
        (case / 'evidence/QA_PASSED.json').write_text('{"checks_passed":20}')
        rejected('chart_rejects_marker_without_hashes', lambda: charts(case / 'results', case / 'output'), case / 'output')
        case = copy_case('failed_check')
        target = case / 'evidence/qa_checks.csv'
        target.write_text(target.read_text().replace('True', 'False', 1))
        rejected('chart_rejects_failed_QA', lambda: charts(case / 'results', case / 'output'), case / 'output')
        case = copy_case('wrong_window')
        target = case / 'results/metrics.json'
        metrics = json.loads(target.read_text()); metrics['window']['start_date'] = '2017-02-01'
        target.write_text(json.dumps(metrics)); certify(case)
        rejected('report_rejects_changed_window_even_with_new_certificate', lambda: build(case / 'results', case / 'figures', case / 'output'), case / 'output')
        case = copy_case('wrong_claim')
        target = case / 'results/Q11.csv'
        target.write_text(target.read_text().replace('1.73', '1.93', 1)); certify(case)
        rejected('report_checks_findings_beyond_three_headline_metrics', lambda: build(case / 'results', case / 'figures', case / 'output'), case / 'output')
        case = copy_case('wrong_figure')
        with (case / 'figures/01_category_pareto.png').open('ab') as stream: stream.write(b'changed')
        rejected('report_rejects_changed_figure', lambda: build(case / 'results', case / 'figures', case / 'output'), case / 'output')
        case = temp / 'bad_input'; case.mkdir()
        (case / 'example.csv').write_bytes(b'changed')
        (case / 'manifest.json').write_text(json.dumps({'example': {'file':'example.csv','bytes':7,'sha256':'0'*64}}))
        rejected('input_rejects_same_size_wrong_hash', lambda: verify_inputs(case, case / 'manifest.json'), case / 'output')
        result = subprocess.run([sys.executable, str(ROOT / 'tests/test_olist.py')], cwd=temp, capture_output=True, text=True)
        if result.returncode or 'Ran 12 tests' not in result.stderr:
            raise AssertionError('Synthetic suite failed from a foreign working directory')
        checks.append({'check':'synthetic_suite_works_from_foreign_working_directory', 'passed':True})
    print(json.dumps({'checks_passed':len(checks),'checks':checks},indent=2))


if __name__ == '__main__':
    main()
