-- Business Query 3: Logistics SLAs, Regional Delivery Times & Delay Impact
-- Analyzes delivery duration vs estimated delivery date, on-time delivery rates, and review score drops.

-- Part A: Regional State Delivery Performance and Late Rates
SELECT 
    customer_state,
    COUNT(order_id) AS total_delivered_orders,
    ROUND(AVG(delivery_days), 1) AS avg_actual_delivery_days,
    ROUND(AVG(estimated_days), 1) AS avg_promised_delivery_days,
    ROUND(AVG(estimated_days - delivery_days), 1) AS avg_early_buffer_days,
    ROUND(SUM(is_delayed) * 100.0 / COUNT(order_id), 2) AS late_delivery_rate_pct,
    ROUND(AVG(total_freight), 2) AS avg_freight_cost,
    ROUND(AVG(total_freight * 100.0 / NULLIF(total_order_value, 0)), 2) AS freight_to_order_ratio_pct,
    ROUND(AVG(review_score), 2) AS avg_customer_satisfaction_score
FROM vw_orders_summary
WHERE order_status = 'delivered'
  AND delivery_days IS NOT NULL
GROUP BY customer_state
ORDER BY avg_actual_delivery_days DESC;

-- Part B: Direct Impact of Delivery Delay on Customer Reviews (CSAT / NPS)
SELECT 
    CASE 
        WHEN is_delayed = 1 THEN 'Delayed (Missed SLA)'
        ELSE 'On-Time / Early'
    END AS delivery_performance,
    COUNT(order_id) AS total_orders,
    ROUND(AVG(review_score), 2) AS avg_review_score,
    ROUND(SUM(CASE WHEN review_score = 5 THEN 1 ELSE 0 END) * 100.0 / COUNT(order_id), 2) AS five_star_pct,
    ROUND(SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(order_id), 2) AS negative_review_pct
FROM vw_orders_summary
WHERE order_status = 'delivered' 
  AND review_score IS NOT NULL
GROUP BY is_delayed;
