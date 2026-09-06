"""Standalone figure exports from reconciled SQL result tables, never raw joins."""
from pathlib import Path
import argparse,json
from provenance import verify_gate, file_hash
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

def charts(results,out,evidence=None):
 evidence=evidence or results.parent/'evidence'
 certificate=verify_gate(results,evidence)
 out.mkdir(parents=True,exist_ok=False);m=json.loads((results/'metrics.json').read_text())
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':'#334155','text.color':'#142b43','figure.facecolor':'white','axes.facecolor':'white'})
 scope=f"Brazil | Delivered purchases: {m['window']['start_date']} to {m['window']['end_date']} (end exclusive)"
 def read(n):return pd.read_csv(results/f'Q{n:02}.csv')
 def save(fig,name,title,foot):
  fig.suptitle(title,x=.09,ha='left',fontsize=18,fontweight='bold',y=.97)
  fig.text(.09,.91,scope,fontsize=10,color='#52677e')
  fig.text(.09,.025,foot,fontsize=9,color='#52677e')
  fig.subplots_adjust(top=.83,bottom=.18,left=.10,right=.95)
  fig.savefig(out/(name+'.png'),dpi=160);plt.close(fig)
 d=read(7);cross=d.loc[d.cumulative_pct.ge(80)].iloc[0]
 fig,ax=plt.subplots(figsize=(12,6.6));ax.plot(d.category_rank,d.cumulative_pct,color='#0b817b',lw=2.8);ax.axhline(80,ls='--',color='#b9c8d5');ax.scatter([cross.category_rank],[cross.cumulative_pct],color='#df7a39',s=70,zorder=4)
 ax.annotate(f"{int(cross.category_rank)} of {len(d)} category buckets\n{cross.cumulative_pct:.2f}% of item sales",(cross.category_rank,cross.cumulative_pct),xytext=(cross.category_rank+8,55),arrowprops={'arrowstyle':'->','color':'#52677e'})
 ax.set(xlabel='Category rank by item sales (all buckets)',ylabel='Cumulative item sales (%)',ylim=(0,105),xlim=(1,len(d)));ax.grid(axis='y',alpha=.17)
 save(fig,'01_category_pareto','Item sales are concentrated across a subset of categories',f"Q07 | Denominator: BRL {m['item_sales_brl']:,.2f} item sales; all {len(d)} category buckets, including unknown/untranslated.")
 d=read(4);fig,ax=plt.subplots(figsize=(12,7));ax.scatter(d.units_sold,d.sales_per_item_brl,s=35,color='#0b817b',alpha=.75,edgecolors='white')
 labels=d.nlargest(3,'units_sold');
 for j,(_,r) in enumerate(labels.iterrows()):ax.annotate(r.category,(r.units_sold,r.sales_per_item_brl),xytext=(-160,35+j*20),textcoords='offset points',fontsize=9,arrowprops={'arrowstyle':'-','color':'#94a3b8'})
 ax.set(xlabel='Units sold (item rows; log scale)',ylabel='Average selling price per item (BRL; log scale)',xscale='log',yscale='log');ax.grid(alpha=.16)
 save(fig,'02_volume_price','Category volume and unit selling price measure different things',f"Q04 | {m['n_items']:,} item rows across {len(d)} buckets; unit price = item sales / item rows. All buckets retained; not profit.")
 d=read(11);fig,ax=plt.subplots(figsize=(12,7));x=range(len(d));ax.bar(x,d.avg_order_review,color=['#0b817b']*3+['#d18340','#ad4f42'],width=.62)
 ax.set_xticks(list(x),[v.replace(' days','\ndays').replace('On promised date','On promised\ndate') for v in d.delivery_bucket]);ax.set(ylabel='Mean order-experience review (1–5)',ylim=(0,5.3));ax.grid(axis='y',alpha=.16)
 for i,r in d.iterrows():ax.text(i,r.avg_order_review+.10,f"{r.avg_order_review:.2f}\nreviewed n={r.n_reviewed_orders:,}\norders n={r.n_orders:,}",ha='center',fontsize=10)
 save(fig,'03_delivery_reviews','Later delivery is associated with lower order-review scores',f"Q11 | {int(d.n_orders.sum()):,} orders with valid delivery dates; {int(d.n_reviewed_orders.sum()):,} reviewed. {int(m['delivery']['missing_invalid_dates'])} missing-date orders excluded. Association, not causation.")
 d=read(8);fig,ax=plt.subplots(figsize=(12,7));palette=['#0b817b','#da843d','#334e8c','#995d90','#84943f']
 for color,(cat,g) in zip(palette,d.groupby('category',sort=True)):ax.plot(pd.to_datetime(g.month),g.item_sales_brl,label=cat,color=color,lw=2)
 ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v/1000:,.0f}k'));ax.set(xlabel='Purchase month',ylabel='Item sales (BRL)');ax.legend(loc='upper left',fontsize=9,frameon=False);ax.grid(axis='y',alpha=.16)
 fig.autofmt_xdate(rotation=30)
 save(fig,'04_monthly_top5','Monthly item sales for the five leading categories',"Q08 | Top five chosen by item sales in the same window; each point sums that category/month's eligible items. No pooled seasonality claim.")
 d=read(5);d=d[d.n_items.ge(100)].sort_values('freight_pct_of_item_sales',ascending=True)
 fig,ax=plt.subplots(figsize=(12,18));ax.barh(d.category,d.freight_pct_of_item_sales,color='#0b817b');ax.tick_params(axis='y',labelsize=9);ax.set(xlabel='Freight charged / item sales (%)');ax.grid(axis='x',alpha=.16)
 save(fig,'05_freight_ratio','Freight charged relative to category item sales',f"Q05 | {len(d)} categories with >=100 item rows shown; denominator = each category's item sales. All categories in Q05.csv. Not shipping cost or margin.")
 # Long labels require a dedicated margin; save again with explicit positioning.
 # Figure is already closed after save, but remains available for deterministic re-export.
 fig.subplots_adjust(left=.36,top=.89,bottom=.075);fig.savefig(out/'05_freight_ratio.png',dpi=160)
 d=read(12);fig,ax=plt.subplots(figsize=(12,6.6));ax.plot(d.cumulative_pct_sellers,d.cumulative_pct_sales,lw=2.5,color='#0b817b');ax.plot([0,100],[0,100],ls=':',color='#94a3b8');ax.set(xlabel='Cumulative sellers ranked by item sales (%)',ylabel='Cumulative item sales (%)',xlim=(0,100),ylim=(0,100));ax.grid(alpha=.16)
 save(fig,'06_seller_concentration','Seller concentration uses the full observed seller set',f"Q12 | {len(d):,} sellers; denominator BRL {m['item_sales_brl']:,.2f}; unknown seller items: {m['unknown_seller_items']}. Full curve, no top-500 cap.")
 (out/'figure_provenance.json').write_text(json.dumps({'result_sha256':certificate['result_sha256'],'figures':{p.name:file_hash(p) for p in sorted(out.glob('*.png'))}},indent=2))
 print(json.dumps({'charts':sorted(x.name for x in out.glob('*.png')),'matplotlib':matplotlib.__version__},indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--results',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--evidence',type=Path);n=a.parse_args();charts(n.results,n.out,n.evidence)
