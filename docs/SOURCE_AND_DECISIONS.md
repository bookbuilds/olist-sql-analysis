# Olist SQL — source and analytical contract
Recorded 2026-09-06 UTC. Analytical definitions are preserved from the original v2 SQL. Original inputs preserved without edits.

## Source identity and access
- Owner dataset: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- Actual download: https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce
- Metadata: https://www.kaggle.com/api/v1/datasets/view/olistbr/brazilian-ecommerce ; public-safe field selection saved in [selected source metadata](../evidence/source_metadata.json) (original response hash retained).
- Anonymous HTTP 200, application/zip; 44,717,580 bytes. No account login or credentials used.
- Original ZIP SHA-256: `967e41e04fc306fe604e2a693f488995a8b41e5047418f8a5c8e4abd6deca784`.
- ZIP CRC passed; all nine expected CSVs present. Per-file SHA-256, byte sizes, row counts: [input manifest](../evidence/input_manifest.json).
- Metadata reports `currentVersionNumber=2`, `lastUpdated=2021-10-01T19:08:27.97Z`, notes `Data Update 2021/10/01`. Its historical versions also include 7 and another version 2. We preserve this ambiguity; the archive and individual file hashes identify the precise extract used. No invented clean version sequence.
- Metadata displays **CC BY-NC-SA 4.0**. Terms reference: https://creativecommons.org/licenses/by-nc-sa/4.0/ . Retain attribution, noncommercial/share-alike notice with the analytical deliverable; no public release made. This is a record of the source license label, not certification of any future use.
- Brazil, historical extract; amounts BRL. No claims about current Olist performance or Thailand.

## Locked metric contract
| Measure | Grain/population and denominator | Missing/exclusion policy |
|---|---|---|
| Q01/Q02 | All raw orders, all statuses/dates | Report unparsed dates; no delivered filter |
| Q03/Q04/Q05/Q07/Q08/Q09/Q12 | Delivered orders purchased >=2017-01-01 and <2018-08-01; item grain order_id + order_item_id | Keep unknown/untranslated categories. No item-volume threshold for totals |
| Item sales | Sum order_items.price; BRL; excludes freight | Never platform revenue, profit or margin |
| Freight ratio | Sum freight_value / sum price in category | Charged freight, not known seller shipping cost; NULL denominator if zero sales |
| Category unit price | Item sales / number of item rows | Not average order value or profitability |
| Q06 | Distinct order-category pairs; low-rating denominator = valid reviewed orders in category | Missing review remains missing; one selected valid score per order can be attributed to multiple categories |
| Q10 | Unique nonblank customer_unique_id in eligible orders | Observed repeat within window; missing buyer IDs separately reported; unequal follow-up |
| Q11 | Eligible orders with parseable promised/delivered dates and delivered calendar date >= purchase calendar date | Invalid/missing dates excluded from delivery denominator only; mean score denominator = valid reviewed orders in each bucket |
| Q12 | All seller IDs in item cohort | Unknown ID bucket separately disclosed; no top-500 cutoff |

## Decisions
- D01: Main purchase window `[2017-01-01,2018-08-01)`, 19 month bins. Monthly audit shows sparse 2016 and no November 2016 purchases. August 2018 delivered purchases taper sharply and end on August 29; September/October have no delivered purchases. July cutoff reduces terminal-window concerns. The source does not certify complete monthly coverage or a precise extraction/censoring date; January begins after month start. Do not claim 19 fully observed months. Sensitivities include August and exclude January (`../results/window_sensitivity.csv`). No dates chosen to optimize a finding.
- D02: Keep min_items/min_reviews=1 in SQL for full visibility. Freight chart uses >=100 items solely for readability and ratio stability; outputs keep all categories. Flag low review n, no significance claims.
- D03: Latest valid integer review (1–5), answer timestamp fallback creation date; review_id then raw SQLite rowid breaks ties. Deterministic for the same hashed input order. Earliest and order-mean sensitivity saved for both delivery and category views.
- D04: Same calendar date is on promised date even if delivery is in the afternoon. Preserve v2 SQL. Raw audit checks timestamp parsing before analysis.
- D05: Importer now rejects whitespace-only keys and post-numeric-conversion item-key duplicates, nonpositive/fractional item IDs. Reason: original string-key validation could miss `01` vs `1`. No observed real rows excluded; invalid keys fail the run.
- D06: Reconcile monetary totals in integer cents (round each price*100) and compare SQL result totals to one-cent tolerance. Raw tables untouched. QA must pass before charts.
- D07: Packaging changes affect file organization, input/output paths and QA provenance only. SQL and the observed snapshot remain unchanged.
- D08: Raw CSVs, archive and generated database are omitted as a packaging choice for size, duplication and license/maintenance overhead; this is not a claim that CC BY-NC-SA prohibits redistribution. See [third-party data](../THIRD_PARTY_DATA.md).
