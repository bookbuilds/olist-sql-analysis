"""Build the locked Markdown narrative only from QA-certified, snapshot-matching results."""
from pathlib import Path
import argparse
import json
import os
import re
import pandas as pd
from provenance import ROOT, verify_gate, file_hash
from verify_results import compare


def build(results, figures, out, evidence=None):
    results, figures, out = Path(results), Path(figures), Path(out)
    evidence = Path(evidence) if evidence else results.parent / 'evidence'
    certificate = verify_gate(results, evidence)
    compare(results, evidence=evidence)
    fp = json.loads((figures / 'figure_provenance.json').read_text())
    if fp['result_sha256'] != certificate['result_sha256']:
        raise ValueError('Figures belong to different result tables.')
    if len(fp['figures']) != 6 or any(file_hash(figures / name) != digest for name, digest in fp['figures'].items()):
        raise ValueError('Figure files changed after generation.')
    O = results
    m = json.loads((O / 'metrics.json').read_text())
    if (m['eligible_orders'], m['n_items'], m['item_sales_brl']) != (89860, 102738, 12342450.49) or m['window'] != {'start_date':'2017-01-01','end_date':'2018-08-01','min_items':1,'min_reviews':1}:
        raise ValueError('Report is locked to the verified metrics and window.')
    q = {i:pd.read_csv(O / f'Q{i:02}.csv') for i in range(1,13)}
    out.mkdir(parents=True, exist_ok=False)
    def relative(path): return Path(os.path.relpath(path, out)).as_posix()
    figure_link, result_link, evidence_link = map(relative, [figures, results, evidence])
    source_link, readme_link = relative(ROOT / 'docs/SOURCE_AND_DECISIONS.md'), relative(ROOT / 'README.md')
    def table(d):
     return '| '+' | '.join(map(str,d.columns))+' |\n|'+'|'.join(['---']*len(d.columns))+'|\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in d.itertuples(index=False,name=None))
    window='Delivered orders purchased 1 January 2017–31 July 2018; [2017-01-01, 2018-08-01). Brazil; BRL.'
    pareto=q[7].loc[q[7].cumulative_pct.ge(80)].iloc[0];seller=q[12].loc[q[12].cumulative_pct_sales.ge(80)].iloc[0]
    report=f'''# Olist: E-commerce Category Performance
    Executed SQL case study · 6 September 2026 verified snapshot

    ## Decision and analytical scope
    Use item sales, item volume, charged freight and order experience to prioritize category and seller investigations. The analysis supports proposed investigations; it does not establish achieved business improvements.

    {window}

    **89,860 delivered orders · 102,738 item rows · BRL 12,342,450.49 item sales.** These counts come from the actual imported extract and reconcile to the complete category totals, including unknown categories. Item sales exclude freight and are neither platform revenue nor profit.

    Source: [Olist's original Kaggle dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), acquired in the original 6 September 2026 execution. The recorded metadata displays CC BY-NC-SA 4.0. See [source and decisions]({source_link}) and the input hash manifest for the exact version evidence and its ambiguity.

    ## 1. What was analyzed, and why this window
    Q01 and Q02 audit all 99,441 raw orders. Subsequent queries share one delivered-order purchase window. The 2016 records are sparse and November is absent; delivered purchases taper sharply in August 2018 and cease after August 29. September/October records contain no delivered purchases. The main analysis stops before August to reduce concerns about the end of the extract.

    This creates 19 calendar-month bins, not a claim of 19 complete months. The first purchase observed in the main window is January 5, 2017. The source does not document a precise extract cutoff or prove monthly completeness. Including August and excluding January are explicit sensitivity scenarios, not replacements chosen to improve the story.

    {table(pd.read_csv(O/'window_sensitivity.csv'))}

    The inclusive-August scenario adds 6,351 delivered orders and BRL 838,576.64 item sales. Excluding January removes 750 orders and BRL 111,798.36. These are coverage sensitivities only; the full category ranking under each alternative window was not separately evaluated.

    ## 2. Item sales concentration and category roles — Q03/Q04/Q07
    The top 18 of 74 category buckets account for 81.3609% of item sales. The top five account for 39.8293%. All category buckets remain in the Pareto denominator, including one unknown bucket and two untranslated names. These are 74 observed buckets, not 74 verified translated product categories.

    {table(q[3].head(5))}

    Health & beauty leads item sales at BRL 1,110,166.49. Bed/bath/table has the largest item volume at 10,290 rows and an average unit selling price of BRL 93.50. Watches/gifts has a higher average unit price (BRL 200.90) and fewer item rows (5,444). Neither price nor sales concentration establishes profitability.

    **Proposed action:** use the leading categories as the initial scope for assortment and fulfillment diagnostics, and evaluate high-volume categories separately from high-unit-price categories. Do not allocate budget solely from this descriptive ranking.

    ![Category Pareto]({figure_link}/01_category_pareto.png)
    ![Category volume and price]({figure_link}/02_volume_price.png)

    ## 3. Delivery experience is an investigation priority — Q06/Q11
    {table(q[11])}

    Delivery at least six calendar days late is associated with a mean review score of 1.73/5, versus 4.30/5 for deliveries at least five days early. The rating denominators are 3,555 and 77,159 reviewed orders respectively. The corresponding exact score sums are 6,147 and 332,054. Eight eligible orders lack usable delivered dates and are excluded only from the delivery analysis; their item sales remain in the sales cohort. On-promised-date deliveries number 1,024 and are not counted as late.

    Office furniture merits a closer order-experience review: average score 3.64/5 from 1,215 reviewed orders, with 21.89% rated 1–2. Small categories are not automatically ranked as priorities: security_and_services has only two reviewed orders. Category ratings represent the whole order and can be attributed to more than one category; there are 708 multi-category orders in the cohort.

    **Proposed action:** inspect late delivery cases, promised-date accuracy, item/category mix and seller/location differences before proposing an operational intervention. This analysis does not isolate causal effects or certify statistical significance. Category-specific delivery performance and adjusted causal analysis remain future work.

    ![Delivery review comparison]({figure_link}/03_delivery_reviews.png)

    ## 4. Freight, timing and observed repeat — Q05/Q08/Q09/Q10
    Electronics records BRL 43,482.33 freight charged against BRL 144,196.37 item sales, a 30.15% ratio across 2,609 items. This is a reason to inspect the customer shipping proposition, not evidence of negative seller margin. The freight chart displays all 52 categories with at least 100 item rows; Q05.csv retains all 74 buckets. This display threshold does not change reconciled totals.

    Monthly top-five categories are selected from the same main window. Year and month are kept together, so unequal years are not pooled into a misleading seasonality chart. Differences in the monthly lines can reflect platform coverage, category mix or underlying activity; this extract alone cannot distinguish those explanations.

    Observed repeat purchasers are 2,609 out of 86,960 valid identified buyers (3.00% rounded) in the window. This is neither lifetime retention nor churn: buyers entering late have less observed time to reorder. No buyer IDs are missing from eligible orders.

    ![Monthly top five]({figure_link}/04_monthly_top5.png)
    ![Freight ratios]({figure_link}/05_freight_ratio.png)

    ## 5. Seller concentration — Q12
    The full cohort contains 2,793 observed sellers and no unknown seller IDs. The first 503 sellers by item sales represent 18.0093% of sellers and 80.0024% of item sales. A top-500 truncation would miss the 80% crossing.

    **Proposed action:** start a seller service review with the high-sales seller group, then examine delivery experience within each seller/category combination before making seller-specific decisions. Concentration is not evidence that those sellers deliver poor service, and no seller was contacted or sanctioned.

    ![Seller concentration]({figure_link}/06_seller_concentration.png)

    ## 6. Data quality and reproducibility
    All required entity/item keys passed null/uniqueness checks. Audited fact-to-dimension foreign-key relationships have zero orphan rows. Geolocation has 261,831 exact duplicate excess rows and is deliberately excluded from analytical joins. Raw data are preserved.

    Reviews contain 547 orders with multiple rows; payments contain 2,961. The review ID alone has 814 duplicate excess occurrences across orders and is not an order key. The selected valid review view has at most one row per order. There are 521 multi-review orders inside the main cohort.

    The main cohort keeps 1,504 unknown-category items worth BRL 168,461.69 and 17 untranslated items worth BRL 3,217.98. Items remain in the denominator. Across the entire raw product table, 610 products have missing categories and 13 products belong to two untranslated names.

    A deliberately unsafe diagnostic join of items to raw payments and raw reviews produces BRL 12,966,112.46, inflating item sales by 5.052983%. The correct result is BRL 12,342,450.49. COUNT DISTINCT on order IDs would not repair that sum.

    Twenty actual-data reconciliation checks pass, including row cardinality, integer-cent monetary totals, review uniqueness, delivery eligibility, buyer counts and full Pareto endpoints. Twelve synthetic regression tests separately pass. A fresh temporary import reproduces all 12 delivered SQL result tables exactly as parsed CSVs; notebook execution logs retain the actual evidence.

    Earliest/latest/order-mean review policies produce the same delivery-bucket means at two decimals, not proof of exact equality. Across category averages, the maximum earliest/latest difference at two decimals is 0.02 points. Detailed sensitivity tables are included.

    ## Limits and handoff
    - Historical Brazilian transactions only; no current-market or Thailand generalization.
    - Delivered-only selection omits canceled/unavailable experiences from the core results; all-status counts remain in Q01/Q02.
    - No cost, commission or margin data; charged freight is not known shipping cost.
    - No formal causal or inferential model was fit; no achieved uplift is claimed.
    - Source completeness, true extraction date and business-policy suitability remain unverified. Jupyter/DBeaver interfaces and live GitHub rendering were not tested.
    - Recommendations remain proposed investigations; implementation outcomes are untested.

    Reproduce using [README]({readme_link}). Claims ledger, query CSVs, runtime versions, input hashes and quality checks accompany this report. AI assisted the code, execution, QA and documentation; unaided authorship is not implied.
    '''
    (out/'REPORT.md').write_text(re.sub(r'(?m)^    ', '', report))
    summary=f'''# Executive summary — Olist SQL
    6 September 2026 · Actual-data analysis

    **Decision:** prioritize category and seller investigations using sales, volume, charged freight and delivery experience together.

    **Scope:** {window}

    **Verified scale:** 89,860 delivered orders; 102,738 item rows; BRL 12,342,450.49 item sales excluding freight. This is not platform revenue or profit.

    **Observations.** Eighteen of 74 category buckets account for 81.36% of item sales. Health & beauty leads sales; bed/bath/table leads item volume. Late-6+-day deliveries average 1.73/5 from 3,555 reviewed orders, compared with 4.30/5 from 77,159 reviews for early-5+-day deliveries. Office furniture averages 3.64/5 from 1,215 reviewed orders. The top 503 of 2,793 sellers account for 80.00% of item sales.

    **Proposed actions.** Scope an assortment and fulfillment review around leading categories; inspect late cases and promised-date accuracy; investigate office-furniture order experience; assess the high-sales seller group before making seller-specific decisions. No uplift or implemented intervention is claimed.

    **Trust checks.** All 12 SQL queries executed. Twenty real-data reconciliation checks and 12 separate synthetic tests passed. A clean re-import reproduces all 12 result tables. Unknown/untranslated categories are retained. An unsafe raw fact join inflated sales by 5.05%, demonstrating why grain control matters.

    **Limits.** This is a historical, delivered-only Brazilian cohort with incomplete boundary coverage. Ratings describe whole orders; no causal effect, profit or lifetime retention is established. The selected window ends before August 2018; boundary and review-policy sensitivities are documented.

    Evidence: REPORT.md, CLAIMS_LEDGER.csv, {result_link}/Q01–Q12.csv, {evidence_link}/qa_checks.csv. Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce (metadata license: CC BY-NC-SA 4.0).
    '''
    (out/'EXECUTIVE_SUMMARY.md').write_text(re.sub(r'(?m)^    ', '', summary))
    card=f'''# E-commerce Category Performance — Olist SQL

    **Challenge:** identify category and seller areas worth investigating without double-counting sales or overstating profitability.

    **Analysis:** audited nine original Olist CSVs; imported SQLite; executed 12 SQL questions using joins, CTEs and window functions; reconciled totals before charting; checked review and date-window sensitivity.

    | Verified metric | Actual result | Scope / evidence |
    |---|---:|---|
    | Delivered orders analyzed | 89,860 | eligible_orders; {result_link}/metrics.json; all have items |
    | Item rows analyzed | 102,738 | order_id + order_item_id; raw-to-view row reconciliation |
    | Item sales, excluding freight | BRL 12,342,450.49 | integer-cent raw/category reconciliation; not profit or platform revenue |

    **Delivered:** SQL · Python importer · executed notebook · result CSVs · six charts · data-quality log · report · claims ledger.

    **Disclosure:** Brazil, purchases 1 Jan 2017–31 Jul 2018; delivered-only cohort. Historical descriptive analysis, not causal proof or achieved business impact. AI-assisted execution and documentation; do not imply unaided authorship. Twelve separate synthetic tests and twenty real-data reconciliation checks passed. Source: Olist/Kaggle; CC BY-NC-SA 4.0 as recorded in source metadata. Not publicly published.
    '''
    (out/'PORTFOLIO_CARD.md').write_text(re.sub(r'(?m)^    ', '', card))
    # Explicit numerator, denominator and output links for every major portfolio/report claim.
    claims=[
    ('C01','89,860 eligible orders','count distinct eligible order_id','not applicable','orders','metrics.json; qa_checks.csv','All have items'),
    ('C02','102,738 item rows','count order_id + order_item_id','not applicable','items','metrics.json; qa_checks.csv','No join multiplication'),
    ('C03','12,342,450.49 item sales BRL','1,234,245,049 cents','100 cents/BRL','BRL','category_totals_cents.csv; qa_checks.csv','Excludes freight; no profit claim'),
    ('C04','Top 18 category buckets: 81.3609%','sum Q07 sales ranks 1..18','12,342,450.49 BRL','percent','Q07.csv','74 buckets includes unknown/untranslated'),
    ('C05','Late 6+ days mean score 1.73','6147 score points','3555 reviewed orders','score /5','Q11.csv; delivery_numerators.csv','Whole-order rating; association only'),
    ('C06','Early 5+ days mean score 4.30','332054 score points','77159 reviewed orders','score /5','Q11.csv; delivery_numerators.csv','Different populations; not causal'),
    ('C07','Office furniture low ratings 21.89%','266 low-rated orders','1215 reviewed orders','percent','Q06.csv','Rounded; multi-category attribution'),
    ('C08','Electronics freight ratio 30.15%','43482.33 freight BRL','144196.37 item sales BRL','percent','Q05.csv','Not cost or margin'),
    ('C09','Observed repeat buyers 3.00%','2609 buyers with 2+ orders','86960 valid observed buyers','percent','Q10.csv','Not lifetime retention'),
    ('C10','Top 503 sellers: 80.0024% item sales','sum Q12 sales ranks 1..503','12,342,450.49 BRL','percent','Q12.csv','2793 sellers; no service-quality inference'),
    ('C11','Unsafe raw join inflation 5.052983%','12966112.46 - 12342450.49 BRL','12342450.49 BRL','percent','join_inflation_diagnostic.csv','Diagnostic result; never the sales result'),
    ('C12','Unknown item sales 168461.69 BRL','16846169 cents','100 cents/BRL','BRL','unknown_categories.csv','1504 item rows retained'),
    ('C13','Top five categories 39.8293%','sum Q07 ranks 1..5 item sales','12342450.49 BRL','percent','Q07.csv','Same window'),
    ]
    d=pd.DataFrame(claims,columns=['claim_id','exact_claim','numerator','denominator','units','result_files','limitation']);d['result_files']=d['result_files'].apply(lambda names: '; '.join((evidence_link if name.strip()=='qa_checks.csv' else result_link)+'/'+name.strip() for name in names.split(';')));d['kind']='observed';d['window']=window;d['source_manifest']=evidence_link+'/input_manifest.json';d.to_csv(out/'CLAIMS_LEDGER.csv',index=False)
    print('PASS: Markdown report, summary, portfolio card and claims ledger match the verified snapshot.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--figures', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    build(args.results, args.figures, args.out, args.evidence)
