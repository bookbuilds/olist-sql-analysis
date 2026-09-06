# Executive summary — Olist SQL
6 September 2026 · Actual-data analysis

**Decision:** prioritize category and seller investigations using sales, volume, charged freight and delivery experience together.

**Scope:** Delivered orders purchased 1 January 2017–31 July 2018; [2017-01-01, 2018-08-01). Brazil; BRL.

**Verified scale:** 89,860 delivered orders; 102,738 item rows; BRL 12,342,450.49 item sales excluding freight. This is not platform revenue or profit.

**Observations.** Eighteen of 74 category buckets account for 81.36% of item sales. Health & beauty leads sales; bed/bath/table leads item volume. Late-6+-day deliveries average 1.73/5 from 3,555 reviewed orders, compared with 4.30/5 from 77,159 reviews for early-5+-day deliveries. Office furniture averages 3.64/5 from 1,215 reviewed orders. The top 503 of 2,793 sellers account for 80.00% of item sales.

**Proposed actions.** Scope an assortment and fulfillment review around leading categories; inspect late cases and promised-date accuracy; investigate office-furniture order experience; assess the high-sales seller group before making seller-specific decisions. No uplift or implemented intervention is claimed.

**Trust checks.** All 12 SQL queries executed. Twenty real-data reconciliation checks and 12 separate synthetic tests passed. A clean re-import reproduces all 12 result tables. Unknown/untranslated categories are retained. An unsafe raw fact join inflated sales by 5.05%, demonstrating why grain control matters.

**Limits.** This is a historical, delivered-only Brazilian cohort with incomplete boundary coverage. Ratings describe whole orders; no causal effect, profit or lifetime retention is established. The selected window ends before August 2018; boundary and review-policy sensitivities are documented.

Evidence: REPORT.md, CLAIMS_LEDGER.csv, ../results/Q01–Q12.csv, ../evidence/qa_checks.csv. Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce (metadata license: CC BY-NC-SA 4.0).
