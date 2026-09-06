-- Setup: run once after import_olist.py. Raw tables remain unchanged.
-- analysis_config must contain one row; dates are explicit analytical choices.
DROP VIEW IF EXISTS item_base;
DROP VIEW IF EXISTS review_one;
DROP VIEW IF EXISTS eligible_orders;
CREATE VIEW eligible_orders AS
SELECT o.* FROM orders o CROSS JOIN analysis_config c
WHERE o.order_status='delivered'
  AND o.order_purchase_timestamp >= c.start_date
  AND o.order_purchase_timestamp < c.end_date;
CREATE VIEW item_base AS
SELECT o.order_id, o.customer_id, o.order_purchase_timestamp,
       oi.order_item_id, oi.product_id, oi.seller_id, oi.price, oi.freight_value,
       COALESCE(NULLIF(TRIM(ct.product_category_name_english),''),
                CASE WHEN NULLIF(TRIM(p.product_category_name),'') IS NOT NULL
                     THEN 'UNTRANSLATED:' || p.product_category_name
                     ELSE '__UNKNOWN__' END) AS category
FROM eligible_orders o
JOIN order_items oi ON oi.order_id=o.order_id
LEFT JOIN products p ON p.product_id=oi.product_id
LEFT JOIN category_translation ct ON ct.product_category_name=p.product_category_name;
CREATE VIEW review_one AS
WITH ranked AS (
 SELECT r.*,
        ROW_NUMBER() OVER (
          PARTITION BY order_id
          ORDER BY COALESCE(NULLIF(review_answer_timestamp,''),
                            NULLIF(review_creation_date,''),'') DESC,
                   COALESCE(review_id,'') DESC, rowid DESC
        ) AS choice_rank
 FROM reviews r WHERE review_score IN (1,2,3,4,5)
)
SELECT * FROM ranked WHERE choice_rank=1;


-- Q01: Order status — all raw orders
SELECT order_status, COUNT(*) AS n_orders
FROM orders GROUP BY order_status ORDER BY n_orders DESC, order_status;

-- Q02: Coverage by status — before choosing a window
SELECT order_status, MIN(order_purchase_timestamp) AS first_purchase,
MAX(order_purchase_timestamp) AS last_purchase, COUNT(*) AS n_orders
FROM orders GROUP BY order_status;

-- Q03: Top categories — item sales, not platform revenue/profit
SELECT category, COUNT(DISTINCT order_id) AS n_orders,
COUNT(*) AS n_items, ROUND(SUM(price),2) AS item_sales_brl,
ROUND(AVG(price),2) AS avg_item_price_brl
FROM item_base GROUP BY category
ORDER BY item_sales_brl DESC, category LIMIT 15;

-- Q04: Volume and unit selling price
SELECT category, COUNT(*) AS units_sold,
ROUND(SUM(price),2) AS item_sales_brl,
ROUND(1.0*SUM(price)/NULLIF(COUNT(*),0),2) AS sales_per_item_brl
FROM item_base GROUP BY category
HAVING COUNT(*) >= (SELECT min_items FROM analysis_config)
ORDER BY units_sold DESC, category;

-- Q05: Freight charged relative to item sales
WITH category_stats AS (
 SELECT category, COUNT(*) AS n_items, SUM(price) AS item_sales,
        SUM(freight_value) AS freight_charged
 FROM item_base GROUP BY category
)
SELECT category, n_items, ROUND(item_sales,2) AS item_sales_brl,
ROUND(freight_charged,2) AS freight_charged_brl,
ROUND(100.0*freight_charged/NULLIF(item_sales,0),2) AS freight_pct_of_item_sales
FROM category_stats
WHERE n_items >= (SELECT min_items FROM analysis_config)
ORDER BY freight_pct_of_item_sales DESC, category;

-- Q06: Order-experience reviews attributed to categories
WITH order_category AS (
 SELECT DISTINCT order_id, category FROM item_base
)
SELECT oc.category, COUNT(*) AS n_order_category_pairs,
COUNT(r.review_score) AS n_reviewed_orders,
ROUND(AVG(r.review_score),2) AS avg_order_review,
ROUND(100.0*SUM(CASE WHEN r.review_score<=2 THEN 1 ELSE 0 END)
 /NULLIF(COUNT(r.review_score),0),2) AS pct_low_rating
FROM order_category oc LEFT JOIN review_one r ON oc.order_id=r.order_id
GROUP BY oc.category
HAVING COUNT(r.review_score) >= (SELECT min_reviews FROM analysis_config)
ORDER BY avg_order_review, oc.category;

-- Q07: Category Pareto — includes unknown category
WITH cat_sales AS (
 SELECT category, SUM(price) AS item_sales FROM item_base GROUP BY category
)
SELECT category, ROUND(item_sales,2) AS item_sales_brl,
ROW_NUMBER() OVER (ORDER BY item_sales DESC, category) AS category_rank,
ROUND(100.0*item_sales/NULLIF(SUM(item_sales) OVER (),0),4) AS pct_of_sales,
ROUND(100.0*SUM(item_sales) OVER (
 ORDER BY item_sales DESC, category ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
 /NULLIF(SUM(item_sales) OVER (),0),4) AS cumulative_pct
FROM cat_sales ORDER BY item_sales DESC, category;

-- Q08: Monthly top-five categories in the same chosen window
WITH RECURSIVE months(month) AS (
 SELECT date(start_date,'start of month') FROM analysis_config
 UNION ALL SELECT date(month,'+1 month') FROM months
 WHERE date(month,'+1 month') < (SELECT end_date FROM analysis_config)
), top5 AS (
 SELECT category FROM item_base GROUP BY category
 ORDER BY SUM(price) DESC, category LIMIT 5
), monthly AS (
 SELECT date(order_purchase_timestamp,'start of month') AS month,
 category,SUM(price) AS item_sales,COUNT(DISTINCT order_id) AS n_orders
 FROM item_base GROUP BY month,category
)
SELECT strftime('%Y-%m',m.month) AS month,t.category,
ROUND(COALESCE(x.item_sales,0),2) AS item_sales_brl,
COALESCE(x.n_orders,0) AS n_orders
FROM months m CROSS JOIN top5 t
LEFT JOIN monthly x ON x.month=m.month AND x.category=t.category
ORDER BY t.category,m.month;

-- Q09: Year-month comparison — not pooled seasonality
SELECT strftime('%Y',order_purchase_timestamp) AS year,
strftime('%m',order_purchase_timestamp) AS month_number,
COUNT(DISTINCT order_id) AS n_orders, ROUND(SUM(price),2) AS item_sales_brl
FROM item_base GROUP BY year,month_number ORDER BY year,month_number;

-- Q10: Observed repeat purchasing within the window
WITH customer_orders AS (
 SELECT c.customer_unique_id, COUNT(*) AS n_orders
 FROM eligible_orders o JOIN customers c ON c.customer_id=o.customer_id
 WHERE NULLIF(TRIM(c.customer_unique_id),'') IS NOT NULL
 GROUP BY c.customer_unique_id
), bands AS (
 SELECT CASE WHEN n_orders=1 THEN '1 order'
 WHEN n_orders=2 THEN '2 orders' ELSE '3+ orders' END AS customer_type
 FROM customer_orders
)
SELECT customer_type,COUNT(*) AS n_customers,
ROUND(100.0*COUNT(*)/NULLIF(SUM(COUNT(*)) OVER (),0),2) AS pct_customers
FROM bands GROUP BY customer_type ORDER BY customer_type;

-- Q11: Calendar-day delivery delay and order-experience rating
WITH delivery AS (
 SELECT order_id,
 CAST(julianday(date(order_delivered_customer_date))
      -julianday(date(order_estimated_delivery_date)) AS INTEGER) AS days_late
 FROM eligible_orders
 WHERE date(order_delivered_customer_date) IS NOT NULL
 AND date(order_estimated_delivery_date) IS NOT NULL
 AND date(order_delivered_customer_date)>=date(order_purchase_timestamp)
), bucketed AS (
 SELECT order_id,days_late,
 CASE WHEN days_late<=-5 THEN 1 WHEN days_late<0 THEN 2
 WHEN days_late=0 THEN 3 WHEN days_late<=5 THEN 4 ELSE 5 END AS bucket_order,
 CASE WHEN days_late<=-5 THEN 'Early 5+ days' WHEN days_late<0 THEN 'Early 1-4 days'
 WHEN days_late=0 THEN 'On promised date' WHEN days_late<=5 THEN 'Late 1-5 days'
 ELSE 'Late 6+ days' END AS delivery_bucket
 FROM delivery
)
SELECT b.delivery_bucket,COUNT(*) AS n_orders,
COUNT(r.review_score) AS n_reviewed_orders,ROUND(AVG(r.review_score),2) AS avg_order_review
FROM bucketed b LEFT JOIN review_one r ON b.order_id=r.order_id
GROUP BY b.bucket_order,b.delivery_bucket ORDER BY b.bucket_order;

-- Q12: Seller concentration — no arbitrary top-500 truncation
WITH seller_sales AS (
 SELECT COALESCE(NULLIF(seller_id,''),'__UNKNOWN_SELLER__') AS seller,
 SUM(price) AS item_sales FROM item_base GROUP BY seller
), ranked AS (
 SELECT seller,item_sales,ROW_NUMBER() OVER (ORDER BY item_sales DESC,seller) AS seller_rank,
 SUM(item_sales) OVER () AS total_sales,COUNT(*) OVER () AS n_sellers
 FROM seller_sales
)
SELECT seller,seller_rank,ROUND(item_sales,2) AS item_sales_brl,
ROUND(100.0*seller_rank/n_sellers,4) AS cumulative_pct_sellers,
ROUND(100.0*SUM(item_sales) OVER (
 ORDER BY seller_rank ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
 /NULLIF(total_sales,0),4) AS cumulative_pct_sales
FROM ranked ORDER BY seller_rank;
