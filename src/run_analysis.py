"""Execute v2 SQL and fail-closed QA before charting. No network or random sampling."""
from pathlib import Path
import argparse, json, re, sqlite3, sys, time, hashlib
import pandas as pd
import numpy as np
from provenance import certify_results
HERE=Path(__file__).resolve().parent

def execute(db,out,evidence=None,sql_path=None,supplemental=None):
 evidence=evidence or out.parent/'evidence'
 sql_path=sql_path or HERE.parent/'sql/analysis.sql'
 supplemental=supplemental or HERE.parent/'sql/supplemental_checks.sql'
 if not db.is_file():raise FileNotFoundError('Database does not exist; run importer first.')
 evidence.mkdir(parents=True,exist_ok=False)
 out.mkdir(parents=True,exist_ok=False)
 con=sqlite3.connect(db);con.row_factory=sqlite3.Row
 def q(sql):return pd.read_sql_query(sql,con)
 def scalar(sql):return con.execute(sql).fetchone()[0]
 parts=re.split(r'-- Q\d+:',sql_path.read_text())
 assert len(parts)==13
 assert scalar('SELECT COUNT(*) FROM analysis_config')==1
 con.executescript(parts[0]);config=dict(con.execute('SELECT * FROM analysis_config').fetchone())
 results={};timings=[];checks=[]
 def check(name,ok,actual,expected):checks.append(dict(check=name,passed=bool(ok),actual=actual,expected=expected))
 for i,p in enumerate(parts[1:],1):
  sql=p.split('\n',1)[1].strip();st=time.perf_counter();d=q(sql);results[i]=d
  d.to_csv(out/f'Q{i:02}.csv',index=False);timings.append({'query':f'Q{i:02}','rows':len(d),'seconds':time.perf_counter()-st,'sql_sha256':hashlib.sha256(sql.encode()).hexdigest()})
 # Independent raw-fact total, using integer cents for monetary reconciliation.
 base=q('SELECT COUNT(*) n_items, COUNT(DISTINCT i.order_id) n_orders, SUM(CAST(ROUND(price*100) AS INTEGER)) sales_cents FROM order_items i JOIN eligible_orders o ON o.order_id=i.order_id').iloc[0]
 joined=q('SELECT COUNT(*) n_items, COUNT(DISTINCT order_id) n_orders, SUM(CAST(ROUND(price*100) AS INTEGER)) sales_cents FROM item_base').iloc[0]
 for c in base.index:check('raw_to_item_base_'+c,int(base[c])==int(joined[c]),int(joined[c]),int(base[c]))
 cats=q('SELECT category,COUNT(*) n_items,COUNT(DISTINCT order_id) n_orders,SUM(CAST(ROUND(price*100) AS INTEGER)) sales_cents FROM item_base GROUP BY category ORDER BY sales_cents DESC,category')
 cats.to_csv(out/'category_totals_cents.csv',index=False)
 check('category_sales_cents',int(cats.sales_cents.sum())==int(base.sales_cents),int(cats.sales_cents.sum()),int(base.sales_cents))
 check('review_one_unique',scalar('SELECT COUNT(*)-COUNT(DISTINCT order_id) FROM review_one')==0,scalar('SELECT COUNT(*)-COUNT(DISTINCT order_id) FROM review_one'),0)
 n_orders=scalar('SELECT COUNT(*) FROM eligible_orders');n_item_orders=int(base.n_orders)
 delivery=q("""SELECT COUNT(*) eligible_orders,
 SUM(CASE WHEN date(order_delivered_customer_date) IS NULL OR date(order_estimated_delivery_date) IS NULL THEN 1 ELSE 0 END) missing_invalid_dates,
 SUM(CASE WHEN date(order_delivered_customer_date)<date(order_purchase_timestamp) THEN 1 ELSE 0 END) delivered_before_purchase,
 SUM(CASE WHEN date(order_delivered_customer_date)=date(order_estimated_delivery_date) AND date(order_delivered_customer_date)>=date(order_purchase_timestamp) THEN 1 ELSE 0 END) same_date_orders
 FROM eligible_orders""").iloc[0].to_dict()
 valid=n_orders-int(delivery['missing_invalid_dates'])-int(delivery['delivered_before_purchase'])
 check('Q11_valid_delivery_orders',int(results[11].n_orders.sum())==valid,int(results[11].n_orders.sum()),valid)
 same=results[11].loc[results[11].delivery_bucket.eq('On promised date'),'n_orders'].sum()
 check('same_calendar_date_not_late',int(same)==int(delivery['same_date_orders']),int(same),int(delivery['same_date_orders']))
 for num,col in [(7,'cumulative_pct'),(12,'cumulative_pct_sales')]:
  d=results[num];check(f'Q{num:02}_monotonic',d[col].diff().dropna().ge(0).all(),bool(d[col].diff().dropna().ge(0).all()),True)
  check(f'Q{num:02}_ends_100',abs(float(d[col].iloc[-1])-100)<1e-4,float(d[col].iloc[-1]),100)
 for num in [4,5,7,9,12]:
  cents=int(round(results[num].item_sales_brl.sum()*100));check(f'Q{num:02}_sales_reconcile',abs(cents-int(base.sales_cents))<=1,cents,int(base.sales_cents))
 buyer=q("SELECT COUNT(*) n_orders,COUNT(DISTINCT c.customer_unique_id) n_buyers FROM eligible_orders o JOIN customers c ON c.customer_id=o.customer_id WHERE NULLIF(TRIM(c.customer_unique_id),'') IS NOT NULL").iloc[0]
 check('Q10_buyer_denominator',int(results[10].n_customers.sum())==int(buyer.n_buyers),int(results[10].n_customers.sum()),int(buyer.n_buyers))
 check('Q01_all_raw_orders',int(results[1].n_orders.sum())==scalar('SELECT COUNT(*) FROM orders'),int(results[1].n_orders.sum()),scalar('SELECT COUNT(*) FROM orders'))
 check('Q09_item_orders',int(results[9].n_orders.sum())==n_item_orders,int(results[9].n_orders.sum()),n_item_orders)
 nmonths=len(pd.date_range(config['start_date'],config['end_date'],freq='MS',inclusive='left'))
 check('Q08_month_spine',len(results[8])==nmonths*min(5,len(cats)),len(results[8]),nmonths*min(5,len(cats)))
 review_coverage=scalar('SELECT COUNT(*) FROM eligible_orders o JOIN review_one r ON r.order_id=o.order_id')
 extra={
 'eligible_orders':n_orders,'orders_with_items':n_item_orders,'orders_without_items':n_orders-n_item_orders,
 'n_items':int(base.n_items),'item_sales_brl':int(base.sales_cents)/100,'n_category_buckets':len(cats),
 'n_reviewed_eligible_orders':review_coverage,'review_coverage_pct':100*review_coverage/n_orders,
 'n_buyers_with_valid_id':int(buyer.n_buyers),'eligible_orders_missing_buyer_id':n_orders-int(buyer.n_orders),
 'multi_category_orders':scalar('SELECT COUNT(*) FROM (SELECT order_id FROM item_base GROUP BY order_id HAVING COUNT(DISTINCT category)>1)'),
 'unknown_seller_items':scalar("SELECT COUNT(*) FROM item_base WHERE NULLIF(TRIM(seller_id),'') IS NULL"),
 'delivery':delivery,'window':config,'n_month_bins':nmonths}
 cats[cats.category.eq('__UNKNOWN__')|cats.category.str.startswith('UNTRANSLATED:')].to_csv(out/'unknown_categories.csv',index=False)
 # Deliberately unsafe diagnostic: quantify the inflation from a raw many-to-many join.
 inflation=q('''SELECT SUM(i.price) naive_join_sales_brl, COUNT(*) naive_rows FROM item_base i LEFT JOIN payments p ON p.order_id=i.order_id LEFT JOIN reviews r ON r.order_id=i.order_id''')
 inflation['correct_item_sales_brl']=extra['item_sales_brl'];inflation['inflation_pct']=100*(inflation.naive_join_sales_brl/extra['item_sales_brl']-1);inflation.to_csv(out/'join_inflation_diagnostic.csv',index=False)
 # Sensitivity: earliest/mean versus latest, one score per order in all policies.
 con.executescript('''CREATE TEMP VIEW review_earliest AS SELECT order_id,review_score FROM (SELECT *,ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY COALESCE(NULLIF(review_answer_timestamp,''),NULLIF(review_creation_date,''),'') ASC,COALESCE(review_id,'') ASC,rowid ASC) rnk FROM reviews WHERE review_score IN(1,2,3,4,5)) WHERE rnk=1;
 CREATE TEMP VIEW review_mean AS SELECT order_id,AVG(review_score) review_score FROM reviews WHERE review_score IN(1,2,3,4,5) GROUP BY order_id;''')
 sensitivities=[]
 q11=parts[11].split('\n',1)[1].strip()
 for policy,view in [('latest','review_one'),('earliest','review_earliest'),('order_mean','review_mean')]:
  d=q(q11.replace('review_one',view));d.insert(0,'review_policy',policy);sensitivities.append(d)
 pd.concat(sensitivities).to_csv(out/'review_policy_sensitivity.csv',index=False)
 # Category sensitivity uses one review per order-category pair; never per item.
 q6=parts[6].split('\n',1)[1].strip();cs=[]
 for policy,view in [('latest','review_one'),('earliest','review_earliest'),('order_mean','review_mean')]:
  d=q(q6.replace('review_one',view));d.insert(0,'review_policy',policy);cs.append(d)
 pd.concat(cs).to_csv(out/'category_review_sensitivity.csv',index=False)
 # Read-only window scenarios, main analysis_config never changed.
 ws=[]
 for label,start,end in [('main',config['start_date'],config['end_date']),('include_august','2017-01-01','2018-09-01'),('exclude_january','2017-02-01','2018-08-01')]:
  d=pd.read_sql_query("SELECT COUNT(DISTINCT o.order_id) n_orders,COUNT(*) n_items,SUM(CAST(ROUND(i.price*100) AS INTEGER))/100.0 item_sales_brl FROM orders o JOIN order_items i ON i.order_id=o.order_id WHERE o.order_status='delivered' AND o.order_purchase_timestamp>=? AND o.order_purchase_timestamp<?",con,params=(start,end));d.insert(0,'scenario',label);d['start_date']=start;d['end_date_exclusive']=end;ws.append(d)
 pd.concat(ws).to_csv(out/'window_sensitivity.csv',index=False)
 # Month coverage and maturity diagnostics, no inference that final timestamp is extraction date.
 q("""SELECT strftime('%Y-%m',order_purchase_timestamp) month,COUNT(*) n_orders,SUM(order_status='delivered') delivered_orders,MIN(order_purchase_timestamp) first_purchase,MAX(order_purchase_timestamp) last_purchase,MAX(order_estimated_delivery_date) last_estimated_delivery,MAX(order_delivered_customer_date) last_observed_delivery FROM orders GROUP BY month ORDER BY month""").to_csv(out/'monthly_maturity.csv',index=False)
 pd.DataFrame(checks).to_csv(evidence/'qa_checks.csv',index=False);pd.DataFrame(timings).to_csv(evidence/'query_execution.csv',index=False)
 q(supplemental.read_text()).to_csv(out/'delivery_numerators.csv',index=False)
 (out/'metrics.json').write_text(json.dumps(extra,indent=2,default=lambda x:int(x)))
 versions={'python':sys.version,'sqlite':sqlite3.sqlite_version,'pandas':pd.__version__,'numpy':np.__version__,'randomness':'none; all rows; no sampling'}
 (evidence/'runtime.json').write_text(json.dumps(versions,indent=2))
 con.close()
 if not all(c['passed'] for c in checks):raise AssertionError('Reconciliation failed: inspect qa_checks.csv. Do not chart.')
 manifest=db.with_suffix('.manifest.json')
 if not manifest.is_file():raise RuntimeError('Input provenance absent; re-import with the supplied importer.')
 (evidence/'input_manifest.json').write_bytes(manifest.read_bytes())
 certify_results(out,evidence,sql_path,supplemental)
 print(json.dumps({'QA':'PASS','n_checks':len(checks),'metrics':extra},indent=2,default=lambda x:int(x)))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--db',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--evidence',type=Path);a.add_argument('--sql',type=Path,default=HERE.parent/'sql/analysis.sql');a.add_argument('--supplemental',type=Path,default=HERE.parent/'sql/supplemental_checks.sql');n=a.parse_args();execute(n.db,n.out,n.evidence,n.sql,n.supplemental)
