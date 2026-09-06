-- S01: Full precision delivery-review numerators for claims ledger.
WITH d AS (
 SELECT o.order_id,r.review_score,
 CAST(julianday(date(order_delivered_customer_date))-julianday(date(order_estimated_delivery_date)) AS INT) days_late
 FROM eligible_orders o LEFT JOIN review_one r ON r.order_id=o.order_id
 WHERE date(order_delivered_customer_date) IS NOT NULL
 AND date(order_estimated_delivery_date) IS NOT NULL
 AND date(order_delivered_customer_date)>=date(order_purchase_timestamp)
), b AS (
 SELECT *,CASE WHEN days_late<=-5 THEN 'Early 5+ days' WHEN days_late<0 THEN 'Early 1-4 days'
 WHEN days_late=0 THEN 'On promised date' WHEN days_late<=5 THEN 'Late 1-5 days' ELSE 'Late 6+ days' END bucket
 FROM d
)
SELECT bucket,COUNT(*) n_orders,COUNT(review_score) n_reviewed_orders,SUM(review_score) review_score_sum,
 AVG(review_score) avg_review_unrounded,SUM(CASE WHEN review_score<=2 THEN 1 ELSE 0 END) low_rating_orders
FROM b GROUP BY bucket;
