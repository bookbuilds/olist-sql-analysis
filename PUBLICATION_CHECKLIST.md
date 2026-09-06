# Publication checklist — owner review

Local package QA is complete. The package is intended for an explicitly authorized initial push to the **private** repository `olist-sql-analysis`. Private publication does not complete this public-release checklist, and it does not authorize a visibility change or GitHub Pages.

- [ ] Review the proposed repository name: `olist-sql-category-performance`.
- [ ] Review description: “SQL case study of Olist category performance and delivery experience, with verified aggregates and reproducible QA.”
- [ ] Choose the source-code license. **No source-code license has been selected yet.** No default license file is included.
- [ ] Review Olist attribution, the [CC BY-NC-SA notice](THIRD_PARTY_DATA.md), changes disclosure and intended portfolio use. Commercial/noncommercial classification remains unresolved.
- [ ] Inspect [.gitignore](.gitignore), including raw inputs, DBs, archives, caches, environments and credentials.
- [ ] Re-run `python src/check_package.py` and review [secret/path scan evidence](evidence/package_checks.json) after any edit.
- [ ] Review [README](README.md) and its relative images. Local Markdown rendering passed; verify native GitHub rendering after the owner authorizes publication.
- [ ] Review all six charts against their units, window and denominators.
- [ ] Review [file inventory](evidence/package_inventory.json) and file sizes.
- [ ] Confirm no original CSVs, dataset ZIP, SQLite database, private config or logs with secrets are included.
- [ ] Re-run `python -m unittest discover -s tests -p test_olist.py -v` and optionally `python tests/check_guards.py`.
- [ ] With the exact input CSVs, use the README pipeline and inspect its 20 QA checks and snapshot comparison.
- [ ] Review the AI-assistance disclosure and be ready to explain the SQL and limitations independently.

## Private repository creation and push

For an explicitly authorized private repository setup:

1. Create the chosen GitHub repository with the reviewed description/visibility.
2. Initialize Git in the reviewed package directory and configure the intended branch and remote.
3. Stage only the intended package files. Inspect the staged file list and diff; specifically confirm raw data and DBs were not staged accidentally.
4. Make the initial commit and push to the owner-selected remote.
5. Verify the README, images, links, attribution and notebook display on GitHub.

After the private push, verify the remote, `main` branch, commit hash and private visibility. Git LFS and GitHub Pages are not configured. A later public release still requires the unchecked owner-review items above.
