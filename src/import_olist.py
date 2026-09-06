"""Import a user-provided Olist download. No network/login; never overwrite a DB.
Usage: python src/import_olist.py --data data/raw --db olist.db \
       --start YYYY-MM-01 --end YYYY-MM-01
End is exclusive. Choose dates AFTER auditing monthly coverage in the raw orders file.
"""
from pathlib import Path
from contextlib import closing
import argparse, json, sqlite3, hashlib, re
from provenance import verify_inputs
import numpy as np
import pandas as pd

FILES = {
 'customers':'olist_customers_dataset.csv', 'geolocation':'olist_geolocation_dataset.csv',
 'order_items':'olist_order_items_dataset.csv','payments':'olist_order_payments_dataset.csv',
 'reviews':'olist_order_reviews_dataset.csv','orders':'olist_orders_dataset.csv',
 'products':'olist_products_dataset.csv','sellers':'olist_sellers_dataset.csv',
 'category_translation':'product_category_name_translation.csv'}
UNIQUE = {'orders':['order_id'],'customers':['customer_id'],'products':['product_id'],
 'sellers':['seller_id'],'category_translation':['product_category_name'],
 'order_items':['order_id','order_item_id']}

def load(data: Path, db: Path, start: str, end: str) -> None:
 if db.exists(): raise FileExistsError(f'Refusing overwrite: {db}')
 if not all(re.fullmatch(r'\d{4}-\d{2}-01', v) for v in [start,end]):
  raise ValueError('Use YYYY-MM-01 strings for start and exclusive end.')
 a,b=pd.Timestamp(start),pd.Timestamp(end)
 if a>=b or a.day!=1 or b.day!=1: raise ValueError('Use ascending month-start dates; end exclusive.')
 missing=[name for name in FILES.values() if not (data/name).is_file()]
 if missing: raise FileNotFoundError(f'Missing original files: {missing}')
 db.parent.mkdir(parents=True,exist_ok=True)
 manifest={}
 try:
  with closing(sqlite3.connect(db)) as con:
   for table,name in FILES.items():
    path=data/name
    frame=pd.read_csv(path,dtype=str)  # retain leading zeroes in IDs/ZIPs
    if table in UNIQUE:
     keys=UNIQUE[table]
     if (frame[keys].isna() | frame[keys].fillna('').apply(lambda s: s.str.strip().eq(''))).any().any() or frame.duplicated(keys).any():
      raise ValueError(f'Null/duplicate key in {table}; audit before importing.')
    numeric={'order_items':['order_item_id','price','freight_value'],
             'reviews':['review_score'],'payments':['payment_sequential','payment_installments','payment_value']}.get(table,[])
    for col in numeric: frame[col]=pd.to_numeric(frame[col],errors='raise')
    if table=='order_items':
     ids=frame['order_item_id']
     if ids.isna().any() or (ids<1).any() or (ids%1!=0).any() or frame.duplicated(['order_id','order_item_id']).any():
      raise ValueError('Invalid/nonunique normalized item key.')
     if not np.isfinite(frame[['price','freight_value']].to_numpy()).all() or (frame[['price','freight_value']]<0).any().any():
      raise ValueError('Nonfinite/negative item prices/freight; needs an explicit exclusion policy.')
    frame.to_sql(table,con,index=False,if_exists='fail')
    manifest[table]={'file':name,'rows':len(frame),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
   pd.DataFrame([{'start_date':a.strftime('%Y-%m-%d'),'end_date':b.strftime('%Y-%m-%d'),
                 'min_items':1,'min_reviews':1}]).to_sql('analysis_config',con,index=False)
   for table,col in [('order_items','order_id'),('reviews','order_id'),('orders','order_id'),('products','product_id'),('customers','customer_id')]:
    con.execute(f'CREATE INDEX idx_{table}_{col} ON {table}({col})')
   con.commit()
  db.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 except Exception:
  # A failed import is not a usable DB. Only this newly created file is removed.
  if db.exists(): db.unlink()
  raise

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--data',type=Path,required=True); ap.add_argument('--db',type=Path,required=True)
 ap.add_argument('--start',required=True); ap.add_argument('--end',required=True)
 ap.add_argument('--manifest',type=Path,default=Path(__file__).resolve().parents[1]/'evidence/input_manifest.json')
 ns=ap.parse_args(); verify_inputs(ns.data,ns.manifest); load(ns.data,ns.db,ns.start,ns.end)
