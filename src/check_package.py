"""Read-only local package QA: syntax, links, notebook, private files and CLI contracts."""
from pathlib import Path
import argparse
import csv
import json
import re
import shlex
import subprocess
import sys
from urllib.parse import unquote, urlsplit
from provenance import ROOT, file_hash
from verify_results import compare


def check(root):
    root = Path(root).resolve()
    checks = []
    def passed(name, detail):
        checks.append({'check': name, 'passed': True, 'detail': detail})
    files = sorted(
        p for p in root.rglob('*')
        if p.is_file() and '.git' not in p.relative_to(root).parts
    )
    for p in files:
        if p.suffix == '.py':
            compile(p.read_text(), p.relative_to(root).as_posix(), 'exec')
    passed('python_syntax_compilation', sum(p.suffix == '.py' for p in files))
    parts = re.split(r'-- Q\d+:', (root / 'sql/analysis.sql').read_text())
    if len(parts) != 13 or re.findall(r'-- (Q\d+):', (root / 'sql/analysis.sql').read_text()) != [f'Q{i:02}' for i in range(1, 13)]:
        raise ValueError('Expected Q01-Q12 exactly once and in order.')
    passed('sql_query_markers', 12)
    links = []
    for p in files:
        if p.suffix == '.md':
            source = p.read_text()
        elif p.suffix == '.ipynb':
            source = '\n'.join(''.join(c['source']) for c in json.loads(p.read_text())['cells'] if c['cell_type'] == 'markdown')
        else:
            continue
        for match in re.finditer(r'!?\[[^\]]*\]\(([^)]+)\)', source):
            target = match.group(1).strip().strip('<>')
            url = urlsplit(target)
            if url.scheme or not url.path:
                continue
            dest = (p.parent / unquote(url.path)).resolve()
            if not dest.is_relative_to(root) or not dest.exists():
                raise ValueError(f'Broken/outside link in {p.relative_to(root)}: {target}')
            links.append({'source': p.relative_to(root).as_posix(), 'target': target})
    passed('markdown_and_notebook_relative_links', len(links))
    nb = json.loads((root / 'notebooks/executed_analysis.ipynb').read_text())
    code = [c for c in nb['cells'] if c['cell_type'] == 'code']
    if nb['nbformat'] != 4 or [c['execution_count'] for c in code] != list(range(1, 8)):
        raise ValueError('Historical notebook format/counts changed.')
    if any(o.get('output_type') == 'error' for c in code for o in c['outputs']):
        raise ValueError('Notebook has error outputs.')
    if 'not Jupyter kernel' not in nb['metadata'].get('execution_method', ''):
        raise ValueError('Notebook execution method is not explicit.')
    for c in code:
        compile(''.join(c['source']), c['id'], 'exec')
    passed('notebook_JSON_source_compilation_and_error_outputs', '7 historical code cells; no errors; not re-executed')
    banned_suffixes = {'.db', '.sqlite', '.sqlite3', '.zip', '.pyc', '.pyo', '.pem', '.key', '.p12', '.pfx', '.har'}
    banned_parts = {'.git', '__pycache__', '.ipynb_checkpoints', '.pytest_cache', '.mypy_cache', '.venv', 'venv', '.aws', '.ssh'}
    input_names = {v['file'] for v in json.loads((root / 'evidence/input_manifest.json').read_text()).values()}
    for p in files:
        rel = p.relative_to(root)
        if p.suffix in banned_suffixes or banned_parts.intersection(rel.parts) or p.name in input_names or p.name in {'.env', '.DS_Store', 'kaggle.json', '.netrc', '.npmrc'} or p.name.startswith('.env.'):
            raise ValueError(f'Excluded artifact present: {rel}')
        if p.is_symlink() or p.stat().st_size >= 50 * 1024 * 1024:
            raise ValueError(f'Symlink or oversized artifact: {rel}')
    passed('raw_private_generated_files_and_size', 'No prohibited package files/symlinks; every packaged file below 50 MiB; .git metadata excluded from content checks')
    # Rules report locations only, never matched secret values. Hashes/group IDs are not tokens.
    rules = {
        'credential_assignment': r'(?i)(?:api[_-]?key|access[_-]?token|password|client[_-]?secret|authorization)\s*[=:]\s*[\"\x27]?[^\s\"\x27,]{8,}',
        'private_key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        'signed_url': r'(?i)[?&](?:X-Amz-Signature|Signature|X-Goog-Signature|token|access_token)=',
        'known_token': r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{24,})',
        'local_absolute_path': '(?:' + '|'.join(re.escape('/' + name + '/') for name in ['Users', 'home', 'mnt', 'tmp', 'private']) + r'|[A-Z]:\\)',
    }
    findings = []
    for p in files:
        if p.suffix == '.png':
            continue
        text = p.read_text(errors='replace')
        for rule, pattern in rules.items():
            for match in re.finditer(pattern, text):
                findings.append({'file': p.relative_to(root).as_posix(), 'line': text.count('\n', 0, match.start()) + 1, 'rule': rule})
    if findings:
        raise ValueError(json.dumps({'scan_findings': findings}))
    passed('secrets_signed_URLs_and_absolute_local_paths', 'No matches in all text, notebook outputs, JSON, Markdown or logs; allowed /path/to placeholder')
    required = ['.DS_Store','__pycache__/','*.py[cod]','.ipynb_checkpoints/','.pytest_cache/','.mypy_cache/','.venv/','venv/','.env','data/raw/','*.db','*.sqlite','*.sqlite3','*.zip','reproduced.db','audit_reproduced/','results_reproduced/','charts_reproduced/']
    ignore = (root / '.gitignore').read_text().splitlines()
    if any(rule not in ignore for rule in required):
        raise ValueError('Required gitignore pattern missing.')
    passed('gitignore_required_patterns', len(required))
    readme = (root / 'README.md').read_text()
    commands = []
    for line in readme.splitlines():
        if line.startswith('python src/'):
            args = shlex.split(line)
            script = root / args[1]
            help_result = subprocess.run([sys.executable, str(script), '--help'], cwd=root, capture_output=True, text=True)
            if help_result.returncode or any(flag not in help_result.stdout for flag in args if flag.startswith('--')):
                raise ValueError(f'README CLI contract mismatch: {args[1]}')
            commands.append(line)
    passed('readme_commands_match_actual_CLI', len(commands))
    for name in ['README.md','docs/REPORT.md','docs/EXECUTIVE_SUMMARY.md','docs/PORTFOLIO_CARD.md']:
        text = (root / name).read_text()
        if any(value not in text for value in ['89,860','102,738','12,342,450.49']):
            raise ValueError(f'Headline metrics missing: {name}')
    passed('headline_metrics_consistent', 'README, report, executive summary, portfolio card')
    with (root / 'docs/CLAIMS_LEDGER.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            for path in row['result_files'].split(';') + [row['source_manifest']]:
                if not (root / 'docs' / path.strip()).is_file():
                    raise ValueError(f'Claims ledger evidence link missing: {row["claim_id"]}')
    passed('claims_ledger_evidence_paths', 13)
    comparison = compare(root / 'results')
    passed('verified_snapshot_and_QA_certificate', comparison['status'])
    return {'status':'PASS','checks':checks,'files_checked':len(files),'largest_file_bytes':max(p.stat().st_size for p in files)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report = check(args.root)
    if args.out:
        with args.out.open('x') as stream:
            json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))
