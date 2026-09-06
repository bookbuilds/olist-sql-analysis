# GitHub handoff — Olist SQL

Prepared 6 September 2026 as a packaging record. The authorized initial destination is the **private** GitHub repository `olist-sql-analysis`. This dated handoff does not claim live repository state; verify the remote and visibility after push. It does not authorize public visibility, Git LFS or GitHub Pages.

Proposed repository name: **`olist-sql-category-performance`**

One-line GitHub description: **SQL case study of Olist category performance and delivery experience, with verified aggregates and reproducible QA.**

Suggested topics: `sql`, `sqlite`, `python`, `olist`, `data-analysis`, `ecommerce`, `portfolio`, `reproducible-research`, `data-quality`.

## Package decisions

The original Project 1 tree was treated as read-only. The deliverable is a new `github_ready/` directory under this task's `outputs/`; it is not nested in or written over the Desktop source folder. All copied source files have original-to-new mappings below. Before-and-after hashes confirm that all 92 data/code/document/archive files remain unchanged. The excluded Finder `.DS_Store` changed during the task; its before/after hashes are recorded, and the cause is not established. No agent command wrote to the source tree. Reversing the packaging work means discarding this new copy; the original analytical content is intact.

Markdown is the maintained document format. Six final PNGs are sufficient for GitHub; duplicate HTML and SVG exports are omitted. All original result CSVs and SQL bytes remain unchanged. CLI paths, imports and file discovery were adapted, and additional shared provenance/verification utilities were introduced. The former notebook executor is superseded by `src/run_pipeline.py`; the historical notebook is preserved as explicitly labeled evidence, not presented as a newly executed copy.

The `results/` directory contains data tables and metrics. QA, timing, runtime and input identity live in sibling `evidence/`. Reproduced runs use the same separation, with `--evidence` available for explicit alternatives. The chart certificate binds every result file and core evidence hash. The report checks the full snapshot, window and figure provenance before emitting the locked narrative. Supplemental SQL now runs during analysis, so report generation does not require a DB or alter result tables.

Q12 retains all 2,793 pseudonymous seller group keys because they are necessary to verify the exact full seller aggregate and tie ordering. It contains no seller names, address/location details or raw transactions. The audit file `untranslated_products.csv` contains two category-count rows, not product records. No raw customer/review/transaction records or free-text reviews are included.

## Dataset and license decisions

Original Olist CSVs, original dataset ZIP and generated SQLite DB are excluded to keep downloads small, avoid redundant data copies and reduce license/maintenance overhead. **This is a packaging choice, not a claim that the dataset license prohibits redistribution.** The local test DB was about 160 MiB and is rebuildable; no LFS was introduced.

The source metadata identifies **CC BY-NC-SA 4.0**. Its attribution, noncommercial and share-alike requirements are recorded in [THIRD_PARTY_DATA](THIRD_PARTY_DATA.md), with exact source/input hashes in [data/README](data/README.md). Whether a job-seeking portfolio is commercial or noncommercial remains undetermined. No source-code license has been selected yet. The owner must choose one separately; this package does not add MIT, Apache or another code license.

## DONE — actual checks

- Inventory captured before edits: 93 original files, size/SHA-256, archive member names, duplicate groups, Python imports and path references. Two exact duplicate pairs were found: root REPORT.html vs the SQL-folder report, and root state vs executed project state. [Original inventory](evidence/original_inventory.json)
- Original source scan found one temporary-directory string in notebook stdout and no credential/signature/private-key matches. The public copy removes that string with a documented substitution. No source/package Git configuration exists. [Original scan](evidence/original_scan.json)
- Fresh Python 3.12.14 virtual environment: pandas 2.2.3, numpy 2.3.5, matplotlib 3.10.8; SQLite 3.53.1. Installation and actual execution passed. [Runtime](evidence/runtime.json)
- Python source and notebook source syntax compiled. Q01–Q12 markers parsed; SQL setup and all twelve queries executed on synthetic fixtures and actual data.
- **Synthetic tests: 12/12 passed without raw data.** [Log](evidence/synthetic_tests.log)
- **Actual-data QA: 20/20 passed.** Eligible orders **89,860**; item rows **102,738**; item sales **BRL 12,342,450.49**. [Checks](evidence/qa_checks.csv)
- All nine input hashes, sizes and row counts match. Pre-import audit and clean import ran using original CSVs outside the package. All regenerated audit tables match the original audit.
- **All 20 aggregate CSVs are byte-identical**, including Q01–Q12, reconciliation and sensitivity tables. No numeric tolerance was needed in this run. The comparison still documents a maximum one-cent monetary / 1e-9 percentage-average tolerance for portability; counts/ranks/cents/text and metrics/window are exact. [Comparison](evidence/reproduction_comparison.json)
- **Eight additional guard/portability checks passed**: stale results, marker without hashes, failed QA, changed window, changed finding with unchanged headline totals, changed figure, wrong input hash, and foreign working directory. [Evidence](evidence/guard_checks.json)
- Notebook passes nbformat validation and has zero error outputs. Seven execution counts and all historical output values match the original; only the temporary directory string was substituted. Source paths were adapted after historical execution. [Notebook validation](evidence/notebook_validation.json)
- Six PNGs regenerated in temporary output and visually inspected. README and report rendered locally in a browser; relative images, headings and tables inspected. No preview HTML is duplicated in the package. [Visual review](evidence/visual_review.json)
- Markdown/notebook links, claims ledger references, CLI flags, .gitignore requirements, source scan and size/forbidden-file inventory validated. [Package checks](evidence/package_checks.json)
- Temporary DB, audit, reproduced results, generated test reports/figures, scratch environment and caches were removed after retaining aggregate evidence. All 92 original content files rehashed unchanged; the sole `.DS_Store` metadata exception is documented without altering or restoring it. [Original integrity](evidence/original_integrity.json)
- Final ZIP CRC and member inventory/hash validation are recorded in `ZIP_VERIFICATION.json` beside the delivered ZIP. The ZIP contains repository files directly at archive root.

Initial dependency installation was blocked by sandbox networking; the approved isolated-environment install succeeded. A temporary localhost preview needed the sandbox network permission and was stopped after inspection. Report regeneration exposed an indentation issue during the function refactor; it was fixed and the corrected Markdown was rebuilt and rendered. An initial link check correctly found the handoff file while it was still being authored; the final package check includes the completed handoff. No numerical mismatch was encountered or papered over.

## Commands run

The following are actual commands with the interpreter and private/local paths normalized to public-safe labels. `RAW` represents the supplied external CSV directory and `RUN` a new temporary folder outside this package. The pipeline dispatches the individual stages listed here; they are not claims of extra duplicate runs.

```bash
python -m unittest discover -s tests -p test_olist.py -v
python src/run_pipeline.py --data RAW --out RUN
python src/audit_raw.py --data RAW --out RUN/audit
python src/import_olist.py --data RAW --db RUN/olist.db --start 2017-01-01 --end 2018-08-01
python src/run_analysis.py --db RUN/olist.db --out RUN/results
python src/verify_results.py --results RUN/results --out RUN/comparison.json
python src/make_charts.py --results RUN/results --out RUN/figures
python src/build_report.py --results RUN/results --figures RUN/figures --out RUN/docs
python src/build_report.py --results results --figures figures --out docs_reproduced
python tests/check_guards.py
python src/check_package.py
```

[Full command record](evidence/commands_executed.json) also describes environment creation, installation, notebook validation and ZIP validation. Historical execution timings and logs remain separately labeled under `evidence/original_execution/`; current query timings are not substituted into historical notebook outputs.

## UNTESTED

- Native GitHub rendering and publication, Windows/Linux installation, the owner's pre-existing Python/Jupyter/DBeaver environments, and the owner's independent explanation of the work.
- The edited notebook's execution as a notebook or Jupyter kernel. The relocated CLI pipeline was independently executed successfully.
- Source completeness, precise extraction cutoff, current-market applicability, causal effects, actual intervention outcomes and full category rankings under alternative windows.
- A definitive chronological interpretation of ambiguous Kaggle version numbers; exact hashes identify this extract.

## BLOCKED / pending owner decisions

There is no remaining technical blocker to the local package. A private repository creation and initial push were authorized separately after this package was prepared. Public visibility remains unauthorized. The owner still needs to choose the source-code license and review attribution and intended-use obligations before any public release. See [PUBLICATION_CHECKLIST](PUBLICATION_CHECKLIST.md).

## Final directory tree

```text
github_ready/
├── data/
│   └── README.md
├── docs/
│   ├── CLAIMS_LEDGER.csv
│   ├── EXECUTIVE_SUMMARY.md
│   ├── INTERVIEW_WALKTHROUGH_TH.md
│   ├── PORTFOLIO_CARD.md
│   ├── QUALITY_LOG.md
│   ├── REPORT.md
│   └── SOURCE_AND_DECISIONS.md
├── evidence/
│   ├── original_execution/
│   │   ├── notebook_execution.log
│   │   ├── qa_checks.csv
│   │   ├── query_execution.csv
│   │   ├── runtime.json
│   │   └── synthetic_tests.log
│   ├── raw_audit/
│   │   ├── daily_status.csv
│   │   ├── dates.csv
│   │   ├── monthly_status.csv
│   │   ├── payments_multiplicity.csv
│   │   ├── raw_checks.csv
│   │   ├── reviews_multiplicity.csv
│   │   ├── schema.csv
│   │   └── untranslated_products.csv
│   ├── QA_PASSED.json
│   ├── actual_pipeline.log
│   ├── audit_comparison.json
│   ├── commands_executed.json
│   ├── excluded_files.csv
│   ├── file_mapping.csv
│   ├── guard_checks.json
│   ├── input_manifest.json
│   ├── notebook_transformations.json
│   ├── notebook_validation.json
│   ├── original_integrity.json
│   ├── original_inventory.json
│   ├── original_scan.json
│   ├── package_checks.json
│   ├── package_inventory.json
│   ├── qa_checks.csv
│   ├── query_execution.csv
│   ├── reproduction_comparison.json
│   ├── runtime.json
│   ├── source_code_hashes.json
│   ├── source_metadata.json
│   ├── synthetic_tests.log
│   ├── verified_snapshot.json
│   └── visual_review.json
├── figures/
│   ├── 01_category_pareto.png
│   ├── 02_volume_price.png
│   ├── 03_delivery_reviews.png
│   ├── 04_monthly_top5.png
│   ├── 05_freight_ratio.png
│   ├── 06_seller_concentration.png
│   └── figure_provenance.json
├── notebooks/
│   └── executed_analysis.ipynb
├── results/
│   ├── Q01.csv
│   ├── Q02.csv
│   ├── Q03.csv
│   ├── Q04.csv
│   ├── Q05.csv
│   ├── Q06.csv
│   ├── Q07.csv
│   ├── Q08.csv
│   ├── Q09.csv
│   ├── Q10.csv
│   ├── Q11.csv
│   ├── Q12.csv
│   ├── category_review_sensitivity.csv
│   ├── category_totals_cents.csv
│   ├── delivery_numerators.csv
│   ├── join_inflation_diagnostic.csv
│   ├── metrics.json
│   ├── monthly_maturity.csv
│   ├── review_policy_sensitivity.csv
│   ├── unknown_categories.csv
│   └── window_sensitivity.csv
├── sql/
│   ├── analysis.sql
│   └── supplemental_checks.sql
├── src/
│   ├── audit_raw.py
│   ├── build_report.py
│   ├── check_package.py
│   ├── import_olist.py
│   ├── make_charts.py
│   ├── provenance.py
│   ├── run_analysis.py
│   ├── run_pipeline.py
│   └── verify_results.py
├── tests/
│   ├── check_guards.py
│   └── test_olist.py
├── .gitignore
├── GITHUB_HANDOFF.md
├── PUBLICATION_CHECKLIST.md
├── README.md
├── THIRD_PARTY_DATA.md
└── requirements.txt
```

## Included original-to-new mapping and reasons

All paths on the left are relative to the original Project 1 folder. New files without an original counterpart are listed after this table. The same mapping is available as [CSV](evidence/file_mapping.csv).

| Original | New | Reason |
|---|---|---|
| `olist_sql/06_analysis.sql` | `sql/analysis.sql` | Original SQL preserved byte-for-byte; Q01–Q12 retained. |
| `olist_sql/07_import_olist.py` | `src/import_olist.py` | Adapted CLI/import/file discovery; report is Markdown-only; hash-bound QA gates added. |
| `olist_sql/08_test_p1.py` | `tests/test_olist.py` | Adapted CLI/import/file discovery; report is Markdown-only; hash-bound QA gates added. |
| `olist_sql/09_audit_raw.py` | `src/audit_raw.py` | Adapted CLI/import/file discovery; report is Markdown-only; hash-bound QA gates added. |
| `olist_sql/10_run_analysis.py` | `src/run_analysis.py` | Adapted CLI/import/file discovery; report is Markdown-only; hash-bound QA gates added. |
| `olist_sql/11_make_charts.py` | `src/make_charts.py` | Adapted CLI/import/file discovery; report is Markdown-only; hash-bound QA gates added. |
| `olist_sql/13_supplemental.sql` | `sql/supplemental_checks.sql` | Original SQL preserved byte-for-byte; Q01–Q12 retained. |
| `olist_sql/14_build_report.py` | `src/build_report.py` | Adapted CLI/import/file discovery; report is Markdown-only; hash-bound QA gates added. |
| `olist_sql/CLAIMS_LEDGER.csv` | `docs/CLAIMS_LEDGER.csv` | Same 13 claims; evidence paths updated. |
| `olist_sql/EXECUTIVE_SUMMARY.md` | `docs/EXECUTIVE_SUMMARY.md` | Portfolio/analytical documentation, updated paths and explicit historical/current status. |
| `olist_sql/INTERVIEW_WALKTHROUGH_TH.md` | `docs/INTERVIEW_WALKTHROUGH_TH.md` | Portfolio/analytical documentation, updated paths and explicit historical/current status. |
| `olist_sql/PORTFOLIO_CARD.md` | `docs/PORTFOLIO_CARD.md` | Portfolio/analytical documentation, updated paths and explicit historical/current status. |
| `olist_sql/QUALITY_LOG.md` | `docs/QUALITY_LOG.md` | Portfolio/analytical documentation, updated paths and explicit historical/current status. |
| `olist_sql/README.md` | `README.md` | Portfolio/analytical documentation, updated paths and explicit historical/current status. |
| `olist_sql/REPORT.md` | `docs/REPORT.md` | Portfolio/analytical documentation, updated paths and explicit historical/current status. |
| `olist_sql/SOURCE_AND_DECISIONS.md` | `docs/SOURCE_AND_DECISIONS.md` | Portfolio/analytical documentation, updated paths and explicit historical/current status. |
| `olist_sql/charts/01_category_pareto.png` | `figures/01_category_pareto.png` | PNG regenerated from the matching QA-certified results; presentation inspected. |
| `olist_sql/charts/02_volume_price.png` | `figures/02_volume_price.png` | PNG regenerated from the matching QA-certified results; presentation inspected. |
| `olist_sql/charts/03_delivery_reviews.png` | `figures/03_delivery_reviews.png` | PNG regenerated from the matching QA-certified results; presentation inspected. |
| `olist_sql/charts/04_monthly_top5.png` | `figures/04_monthly_top5.png` | PNG regenerated from the matching QA-certified results; presentation inspected. |
| `olist_sql/charts/05_freight_ratio.png` | `figures/05_freight_ratio.png` | PNG regenerated from the matching QA-certified results; presentation inspected. |
| `olist_sql/charts/06_seller_concentration.png` | `figures/06_seller_concentration.png` | PNG regenerated from the matching QA-certified results; presentation inspected. |
| `olist_sql/evidence/metadata.json` | `evidence/source_metadata.json` | Selected identity/license/version fields; original response hash retained; unrelated profile/thumbnail fields omitted. |
| `olist_sql/evidence/notebook_execution.log` | `evidence/original_execution/notebook_execution.log` | Historical timings/runtime/test evidence, distinct from this run. |
| `olist_sql/evidence/raw_audit/daily_status.csv` | `evidence/raw_audit/daily_status.csv` | Reproducibility or pre-import aggregate audit evidence. |
| `olist_sql/evidence/raw_audit/dates.csv` | `evidence/raw_audit/dates.csv` | Reproducibility or pre-import aggregate audit evidence. |
| `olist_sql/evidence/raw_audit/input_manifest.json` | `evidence/input_manifest.json` | Reproducibility or pre-import aggregate audit evidence. |
| `olist_sql/evidence/raw_audit/monthly_status.csv` | `evidence/raw_audit/monthly_status.csv` | Reproducibility or pre-import aggregate audit evidence. |
| `olist_sql/evidence/raw_audit/payments_multiplicity.csv` | `evidence/raw_audit/payments_multiplicity.csv` | Reproducibility or pre-import aggregate audit evidence. |
| `olist_sql/evidence/raw_audit/raw_checks.csv` | `evidence/raw_audit/raw_checks.csv` | Reproducibility or pre-import aggregate audit evidence. |
| `olist_sql/evidence/raw_audit/reviews_multiplicity.csv` | `evidence/raw_audit/reviews_multiplicity.csv` | Reproducibility or pre-import aggregate audit evidence. |
| `olist_sql/evidence/raw_audit/schema.csv` | `evidence/raw_audit/schema.csv` | Reproducibility or pre-import aggregate audit evidence. |
| `olist_sql/evidence/raw_audit/untranslated_products.csv` | `evidence/raw_audit/untranslated_products.csv` | Reproducibility or pre-import aggregate audit evidence. |
| `olist_sql/evidence/synthetic_tests.log` | `evidence/original_execution/synthetic_tests.log` | Historical timings/runtime/test evidence, distinct from this run. |
| `olist_sql/executed_analysis.ipynb` | `notebooks/executed_analysis.ipynb` | Historical executed evidence; paths adapted and one temporary path redacted with provenance. |
| `olist_sql/requirements-tested.txt` | `requirements.txt` | Reproducibility or pre-import aggregate audit evidence. |
| `olist_sql/results/Q01.csv` | `results/Q01.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q02.csv` | `results/Q02.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q03.csv` | `results/Q03.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q04.csv` | `results/Q04.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q05.csv` | `results/Q05.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q06.csv` | `results/Q06.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q07.csv` | `results/Q07.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q08.csv` | `results/Q08.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q09.csv` | `results/Q09.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q10.csv` | `results/Q10.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q11.csv` | `results/Q11.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/Q12.csv` | `results/Q12.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/category_review_sensitivity.csv` | `results/category_review_sensitivity.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/category_totals_cents.csv` | `results/category_totals_cents.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/delivery_numerators.csv` | `results/delivery_numerators.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/join_inflation_diagnostic.csv` | `results/join_inflation_diagnostic.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/metrics.json` | `results/metrics.json` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/monthly_maturity.csv` | `results/monthly_maturity.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/qa_checks.csv` | `evidence/original_execution/qa_checks.csv` | Historical timings/runtime/test evidence, distinct from this run. |
| `olist_sql/results/query_execution.csv` | `evidence/original_execution/query_execution.csv` | Historical timings/runtime/test evidence, distinct from this run. |
| `olist_sql/results/review_policy_sensitivity.csv` | `results/review_policy_sensitivity.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/runtime.json` | `evidence/original_execution/runtime.json` | Historical timings/runtime/test evidence, distinct from this run. |
| `olist_sql/results/unknown_categories.csv` | `results/unknown_categories.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |
| `olist_sql/results/window_sensitivity.csv` | `results/window_sensitivity.csv` | Original verified aggregate bytes; full reconciliation/sensitivity evidence. |

## Excluded files and reasons

Every excluded original remains untouched in the source tree. No actual secret was found; exclusions are not characterized as illegal or inherently dangerous. [Machine-readable list](evidence/excluded_files.csv)

| Original file | Reason |
|---|---|
| `.DS_Store` | Finder metadata; no portfolio value, harmless noise. |
| `Olist Project 1 Sept 6/olist_customers_dataset.csv` | Original raw dataset; excluded by packaging decision, hashes/row counts retained. |
| `Olist Project 1 Sept 6/olist_geolocation_dataset.csv` | Original raw dataset; excluded by packaging decision, hashes/row counts retained. |
| `Olist Project 1 Sept 6/olist_order_items_dataset.csv` | Original raw dataset; excluded by packaging decision, hashes/row counts retained. |
| `Olist Project 1 Sept 6/olist_order_payments_dataset.csv` | Original raw dataset; excluded by packaging decision, hashes/row counts retained. |
| `Olist Project 1 Sept 6/olist_order_reviews_dataset.csv` | Original raw dataset; excluded by packaging decision, hashes/row counts retained. |
| `Olist Project 1 Sept 6/olist_orders_dataset.csv` | Original raw dataset; excluded by packaging decision, hashes/row counts retained. |
| `Olist Project 1 Sept 6/olist_products_dataset.csv` | Original raw dataset; excluded by packaging decision, hashes/row counts retained. |
| `Olist Project 1 Sept 6/olist_sellers_dataset.csv` | Original raw dataset; excluded by packaging decision, hashes/row counts retained. |
| `Olist Project 1 Sept 6/product_category_name_translation.csv` | Original raw dataset; excluded by packaging decision, hashes/row counts retained. |
| `Olist Project 1 Sept 6.zip` | Source archive or duplicate execution bundle; avoid large/redundant packaged inputs. |
| `Project 1 Olist SQL Executed Sept 6.zip` | Source archive or duplicate execution bundle; avoid large/redundant packaged inputs. |
| `Project 1 Olist SQL Report.html` | Duplicate narrative/embedded images; Markdown is the maintained public documentation. |
| `Project 1 State Sept 6 2026.md` | Internal execution handoff; superseded for publication preparation by GITHUB_HANDOFF. |
| `olist_sql/12_execute_notebook.py` | Historical flat-layout executor writes delivered notebook and assumes fixed paths; replaced by explicit CLI pipeline. Original retained untouched. |
| `olist_sql/EXECUTIVE_SUMMARY.html` | Duplicate narrative/embedded images; Markdown is the maintained public documentation. |
| `olist_sql/PACKAGE_MANIFEST.json` | Stale package inventory with old paths; replaced by current inventory plus original pre-edit inventory. |
| `olist_sql/PORTFOLIO_CARD.html` | Duplicate narrative/embedded images; Markdown is the maintained public documentation. |
| `olist_sql/PROJECT_STATE_2026-09-06_EXECUTED.md` | Internal execution handoff; superseded for publication preparation by GITHUB_HANDOFF. |
| `olist_sql/REPORT.html` | Duplicate narrative/embedded images; Markdown is the maintained public documentation. |
| `olist_sql/charts/01_category_pareto.svg` | Duplicate chart format; PNG renders directly on GitHub and is sufficient here. |
| `olist_sql/charts/02_volume_price.svg` | Duplicate chart format; PNG renders directly on GitHub and is sufficient here. |
| `olist_sql/charts/03_delivery_reviews.svg` | Duplicate chart format; PNG renders directly on GitHub and is sufficient here. |
| `olist_sql/charts/04_monthly_top5.svg` | Duplicate chart format; PNG renders directly on GitHub and is sufficient here. |
| `olist_sql/charts/05_freight_ratio.svg` | Duplicate chart format; PNG renders directly on GitHub and is sufficient here. |
| `olist_sql/charts/06_seller_concentration.svg` | Duplicate chart format; PNG renders directly on GitHub and is sufficient here. |
| `olist_sql/evidence/source_code_hashes.json` | Hashes refer to earlier attached reference files, not current packaged code; replaced by source-code/original inventories. |
| `olist_sql/olist.manifest.json` | Redundant input manifest lacks byte sizes; canonical evidence/input_manifest.json retained. |
| `olist_sql/reference_v2/02_PROJECT_REFERENCE.md` | Internal project reference/archived guide/previous handoff, not needed to inspect public results. |
| `olist_sql/reference_v2/03_GUIDE_v2.md` | Internal project reference/archived guide/previous handoff, not needed to inspect public results. |
| `olist_sql/reference_v2/04_QA_AND_HANDOFF.md` | Internal project reference/archived guide/previous handoff, not needed to inspect public results. |
| `olist_sql/reference_v2/PROJECT_STATE_2026-09-06_PREVIOUS.md` | Internal project reference/archived guide/previous handoff, not needed to inspect public results. |
| `olist_sql/results/QA_PASSED.json` | Old marker has no result hashes; replaced with a verified hash-bound certificate. |

## New supporting files

`THIRD_PARTY_DATA.md`, `data/README.md`, `.gitignore`, `GITHUB_HANDOFF.md` and `PUBLICATION_CHECKLIST.md` record acquisition, licensing and publication boundaries. `src/provenance.py`, `src/verify_results.py`, `src/run_pipeline.py`, `src/check_package.py` and `tests/check_guards.py` make the package reproducible and test its gates. Current execution, transformation, inventory, mapping, scan and visual-review evidence are generated from actual checks; they contain no raw records. `evidence/package_inventory.json` hashes all package files except itself to avoid a self-referential hash. The separate ZIP validation includes that inventory file too.
