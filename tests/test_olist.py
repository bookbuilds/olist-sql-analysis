"""Synthetic regression tests, not actual Olist outputs. Run: python -m unittest discover -s tests -p test_olist.py -v"""
import unittest,sqlite3,re,tempfile,sys
from pathlib import Path
from contextlib import closing
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import import_olist as imp

def fixture():
    orders=pd.DataFrame([
      ['o1','c1','delivered','2017-01-03 12:00:00','2017-01-10 19:00:00','2017-01-10 00:00:00'],
      ['o2','c2','delivered','2017-02-03 12:00:00','2017-02-15 12:00:00','2017-02-10 00:00:00'],
      ['o3','c3','delivered','2018-01-03 12:00:00','2018-01-06 12:00:00','2018-01-10 00:00:00'],
      ['o4','c4','canceled','2017-02-03 12:00:00',None,None],
      ['o5','c5','delivered','2017-03-03 12:00:00','2017-03-01 12:00:00','2017-03-10 00:00:00'],
      ['o6','c6','delivered','2017-04-03 12:00:00','2017-04-15 12:00:00','2017-04-10 00:00:00']],
      columns=['order_id','customer_id','order_status','order_purchase_timestamp','order_delivered_customer_date','order_estimated_delivery_date'])
    items=pd.DataFrame([
      ['o1',1,'p1','s1',10.,1.],['o1',2,'p1','s1',20.,2.],
      ['o1',3,'p2','s2',30.,3.],['o2',1,'p3','s3',40.,4.],
      ['o3',1,'missing','s4',50.,5.],['o4',1,'p1','s1',999.,9.],
      ['o5',1,'p1','s1',0.,0.],['o6',1,'pzero','s5',0.,2.]],
      columns=['order_id','order_item_id','product_id','seller_id','price','freight_value'])
    reviews=pd.DataFrame([
      ['r1','o1',1,'2017-01-11','2017-01-12'],['r2','o1',5,'2017-01-13','2017-01-14'],
      ['r3','o2',2,'2017-02-16','2017-02-17'],['r4','o2',3.5,'2017-02-18','2017-02-19'],
      ['r5','o3',4,'2018-01-11','2018-01-12']],
      columns=['review_id','order_id','review_score','review_creation_date','review_answer_timestamp'])
    return {'orders':orders,'order_items':items,'reviews':reviews,
      'products':pd.DataFrame([['p1','a'],['p2','b'],['p3','c'],['pzero','zero']],columns=['product_id','product_category_name']),
      'category_translation':pd.DataFrame([['a','A'],['b','B'],['zero','Zero']],columns=['product_category_name','product_category_name_english']),
      'customers':pd.DataFrame([[f'c{i}','u1' if i in [1,2] else f'u{i}'] for i in range(1,7)],columns=['customer_id','customer_unique_id']),
      'sellers':pd.DataFrame({'seller_id':['s1','s2','s3','s4','s5']}),
      'geolocation':pd.DataFrame({'geolocation_zip_code_prefix':['00100','00100']}),
      'payments':pd.DataFrame([['o1',1,1,10],['o1',2,1,56]],columns=['order_id','payment_sequential','payment_installments','payment_value'])}

class TestOlist(unittest.TestCase):
 def setUp(self):
    self.c=sqlite3.connect(':memory:')
    for name,df in fixture().items():df.to_sql(name,self.c,index=False)
    self.c.execute('CREATE TABLE analysis_config(start_date TEXT,end_date TEXT,min_items INT,min_reviews INT)')
    self.c.execute("INSERT INTO analysis_config VALUES('2017-01-01','2018-02-01',1,1)")
    parts=re.split(r'-- Q\d+:', (ROOT/'sql/analysis.sql').read_text())
    self.c.executescript(parts[0]);self.queries=[p.split('\n',1)[1].strip() for p in parts[1:]]
 def tearDown(self):self.c.close()
 def result(self,n):return pd.read_sql_query(self.queries[n-1],self.c)
 def test_all_12_execute(self):
    self.assertEqual(len(self.queries),12)
    for n in range(1,13):self.assertIsInstance(self.result(n),pd.DataFrame)
 def test_sales_reconcile_and_unknown_preserved(self):
    x=self.result(3);self.assertAlmostEqual(x.item_sales_brl.sum(),150.)
    self.assertIn('__UNKNOWN__',x.category.tolist());self.assertIn('UNTRANSLATED:c',x.category.tolist())
 def test_review_dedup_and_valid_integer_rating(self):
    a=self.result(6).set_index('category').loc['A'];self.assertEqual(a.n_reviewed_orders,1);self.assertEqual(a.avg_order_review,5)
    c=self.c.execute("SELECT review_score FROM review_one WHERE order_id='o2'").fetchone()[0]
    self.assertEqual(c,2)
 def test_calendar_same_date_not_late(self):
    x=self.result(11).set_index('delivery_bucket');self.assertEqual(x.loc['On promised date','n_orders'],1)
    self.assertEqual(x.n_orders.sum(),4) # malformed chronology o5 excluded
    self.assertEqual(x.loc['Late 1-5 days','n_orders'],2)
 def test_zero_price_ratio_null(self):
    x=self.result(5).set_index('category');self.assertTrue(pd.isna(x.loc['Zero','freight_pct_of_item_sales']))
 def test_pareto_and_full_sellers(self):
    self.assertAlmostEqual(self.result(7).cumulative_pct.iloc[-1],100.)
    x=self.result(12);self.assertEqual(len(x),5);self.assertAlmostEqual(x.cumulative_pct_sales.iloc[-1],100.)
 def test_month_spine_and_year_separation(self):
    x=self.result(8);self.assertEqual(len(x),13*5);self.assertTrue((x.n_orders==0).any())
    jan=self.result(9).query("month_number=='01'");self.assertEqual(len(jan),2)
 def test_repeat_uses_unique_customer(self):
    x=self.result(10).set_index('customer_type');self.assertEqual(x.loc['2 orders','n_customers'],1)
 def test_import_roundtrip_and_overwrite_guard(self):
    with tempfile.TemporaryDirectory() as td:
      root=Path(td)
      for name,df in fixture().items():df.to_csv(root/imp.FILES[name],index=False)
      db=root/'o.db';imp.load(root,db,'2017-01-01','2018-02-01')
      with closing(sqlite3.connect(db)) as c:
       self.assertEqual(c.execute('select count(*) from orders').fetchone()[0],6)
       self.assertEqual(c.execute('select geolocation_zip_code_prefix from geolocation limit 1').fetchone()[0],'00100')
      self.assertTrue(db.with_suffix('.manifest.json').exists())
      with self.assertRaises(FileExistsError):imp.load(root,db,'2017-01-01','2018-02-01')
 def test_import_rejects_duplicate_keys_and_nonfinite_prices(self):
    with tempfile.TemporaryDirectory() as td:
      root=Path(td);data=fixture()
      data['order_items'].loc[0,'price']=float('inf')
      for name,df in data.items():df.to_csv(root/imp.FILES[name],index=False)
      with self.assertRaises(ValueError):imp.load(root,root/'bad.db','2017-01-01','2018-02-01')
      self.assertFalse((root/'bad.db').exists())
      data=fixture();data['orders']=pd.concat([data['orders'],data['orders'].iloc[[0]]])
      for name,df in data.items():df.to_csv(root/imp.FILES[name],index=False)
      with self.assertRaises(ValueError):imp.load(root,root/'bad2.db','2017-01-01','2018-02-01')

 def test_import_rejects_blank_and_normalized_item_keys(self):
    with tempfile.TemporaryDirectory() as td:
      root=Path(td)
      for case in ['blank','normalized','fractional']:
       data=fixture()
       if case=='blank': data['orders'].loc[0,'order_id']='  '
       if case=='normalized':
        data['order_items']['order_item_id']=data['order_items']['order_item_id'].astype(str)
        data['order_items'].loc[0,'order_item_id']='01'
        data['order_items'].loc[1,'order_item_id']='1'
       if case=='fractional':
        data['order_items']['order_item_id']=data['order_items']['order_item_id'].astype(float)
        data['order_items'].loc[0,'order_item_id']=1.5
       for name,df in data.items():df.to_csv(root/imp.FILES[name],index=False)
       with self.assertRaises(ValueError):imp.load(root,root/(case+'.db'),'2017-01-01','2018-02-01')
       self.assertFalse((root/(case+'.db')).exists())
 def test_window_boundaries_and_missing_review(self):
    self.c.execute("UPDATE analysis_config SET start_date='2017-02-01',end_date='2017-04-01'")
    self.assertEqual(self.c.execute('SELECT COUNT(*) FROM eligible_orders').fetchone()[0],2)
    self.assertEqual(self.c.execute("SELECT COUNT(*) FROM review_one WHERE order_id='o5'").fetchone()[0],0)

if __name__=='__main__':unittest.main(verbosity=2)
