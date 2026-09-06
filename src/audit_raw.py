"""Read-only pre-import audit; no cohort selected here. Original bytes preserved."""
from pathlib import Path
import argparse, hashlib, json
import import_olist as imp
from provenance import verify_inputs
import pandas as pd
HERE=Path(__file__).resolve().parent
def audit(data,out):
 out.mkdir(parents=True,exist_ok=False);frames={};manifest={};issues=[];schema=[]
 missing=[f for f in imp.FILES.values() if not (data/f).is_file()]
 if missing:raise FileNotFoundError(json.dumps(missing))
 for table,name in imp.FILES.items():
  p=data/name;d=pd.read_csv(p,dtype=str);frames[table]=d
  manifest[table]={'file':name,'rows':len(d),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  for col in d:
   schema.append({'table':table,'column':col,'rows':len(d),'null_or_blank':int((d[col].isna()|d[col].fillna('').str.strip().eq('')).sum())})
  keys=imp.UNIQUE.get(table)
  if keys:
   issues.append({'check':table+'_null_key_rows','n':int((d[keys].isna()|d[keys].fillna('').apply(lambda x:x.str.strip().eq(''))).any(axis=1).sum())})
   issues.append({'check':table+'_duplicate_key_excess','n':int(d.duplicated(keys).sum())})
  issues.append({'check':table+'_exact_duplicate_excess','n':int(d.duplicated().sum())})
 for child,key,parent,pkey in [('orders','customer_id','customers','customer_id'),('order_items','order_id','orders','order_id'),('order_items','product_id','products','product_id'),('order_items','seller_id','sellers','seller_id'),('reviews','order_id','orders','order_id'),('payments','order_id','orders','order_id')]:
  issues.append({'check':child+'_'+key+'_orphan_rows','n':int((~frames[child][key].isin(frames[parent][pkey])).sum())})
 for t in ['reviews','payments']:
  d=frames[t];cnt=d.groupby('order_id').size()
  cnt.value_counts().sort_index().rename_axis('rows_per_order').reset_index(name='n_orders').to_csv(out/(t+'_multiplicity.csv'),index=False)
  issues.append({'check':t+'_orders_with_multiple_rows','n':int(cnt.gt(1).sum())})
 for t,keys in [('payments',['order_id','payment_sequential']),('reviews',['review_id']),('reviews',['order_id','review_id'])]:
  issues.append({'check':t+'_'+'_'.join(keys)+'_duplicate_excess','n':int(frames[t].duplicated(keys).sum())})
 o=frames['orders'];dt=pd.to_datetime(o.order_purchase_timestamp,errors='coerce')
 pd.crosstab(dt.dt.strftime('%Y-%m'),o.order_status).reindex(pd.period_range(dt.min(),dt.max(),freq='M').astype(str),fill_value=0).rename_axis('purchase_month').reset_index().to_csv(out/'monthly_status.csv',index=False)
 pd.crosstab(dt.dt.strftime('%Y-%m-%d'),o.order_status).rename_axis('purchase_date').reset_index().to_csv(out/'daily_status.csv',index=False)
 dates=[]
 for col in [c for c in o if 'date' in c or 'timestamp' in c or c.endswith('_at')]:
  x=pd.to_datetime(o[col],errors='coerce');dates.append({'column':col,'missing':int(o[col].isna().sum()),'invalid_nonmissing':int((o[col].notna()&x.isna()).sum()),'min':str(x.min()),'max':str(x.max())})
 for col in ['review_creation_date','review_answer_timestamp']:
  x=pd.to_datetime(frames['reviews'][col],errors='coerce');issues.append({'check':col+'_invalid_nonmissing','n':int((frames['reviews'][col].notna()&x.isna()).sum())})
 score=pd.to_numeric(frames['reviews'].review_score,errors='coerce');issues.append({'check':'invalid_review_score_rows','n':int((~score.isin([1,2,3,4,5])).sum())})
 for c in ['price','freight_value']:
  x=pd.to_numeric(frames['order_items'][c],errors='coerce');issues.append({'check':c+'_zero_rows','n':int(x.eq(0).sum())});issues.append({'check':c+'_invalid_rows','n':int((x.isna()|x.lt(0)|x.isin([float('inf'),float('-inf')])).sum())})
 p=frames['products'];tr=frames['category_translation'];cat=p.product_category_name.fillna('').str.strip()
 issues.append({'check':'products_unknown_category','n':int(cat.eq('').sum())})
 un=p.loc[cat.ne('')&~cat.isin(tr.product_category_name),'product_category_name'].value_counts().rename_axis('category').reset_index(name='n_products');un.to_csv(out/'untranslated_products.csv',index=False)
 for name,rows in [('schema',schema),('raw_checks',issues),('dates',dates)]:pd.DataFrame(rows).to_csv(out/(name+'.csv'),index=False)
 (out/'input_manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps({'rows':{k:v['rows'] for k,v in manifest.items()},'audit_directory':str(out)},indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--data',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--manifest',type=Path,default=HERE.parent/'evidence/input_manifest.json');n=a.parse_args();verify_inputs(n.data,n.manifest);audit(n.data,n.out)
