# E-commerce Category Performance — Olist SQL

**Challenge:** identify category and seller areas worth investigating without double-counting sales or overstating profitability.

**Analysis:** audited nine original Olist CSVs; imported SQLite; executed 12 SQL questions using joins, CTEs and window functions; reconciled totals before charting; checked review and date-window sensitivity.

| Verified metric | Actual result | Scope / evidence |
|---|---:|---|
| Delivered orders analyzed | 89,860 | eligible_orders; ../results/metrics.json; all have items |
| Item rows analyzed | 102,738 | order_id + order_item_id; raw-to-view row reconciliation |
| Item sales, excluding freight | BRL 12,342,450.49 | integer-cent raw/category reconciliation; not profit or platform revenue |

**Delivered:** SQL · Python importer · executed notebook · result CSVs · six charts · data-quality log · report · claims ledger.

**Disclosure:** Brazil, purchases 1 Jan 2017–31 Jul 2018; delivered-only cohort. Historical descriptive analysis, not causal proof or achieved business impact. AI-assisted execution and documentation; do not imply unaided authorship. Twelve separate synthetic tests and twenty real-data reconciliation checks passed. Source: Olist/Kaggle; CC BY-NC-SA 4.0 as recorded in source metadata. Not publicly published.
