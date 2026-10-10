-- Business Query 2: Customer RFM (Recency, Frequency, Monetary) Segmentation
-- Segments customers based on transaction history into strategic customer tiers.

WITH reference_date AS (
    -- Anchor date: maximum order date in dataset plus 1 day
    SELECT DATE(MAX(order_purchase_timestamp), '+1 day') AS ref_date
    FROM orders
),
customer_rfm AS (
    SELECT 
        c.customer_unique_id,
        c.customer_state,
        CAST((JULIANDAY((SELECT ref_date FROM reference_date)) - JULIANDAY(MAX(o.order_purchase_timestamp))) AS INT) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(i.price), 2) AS monetary_value
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id, c.customer_state
),
rfm_scores AS (
    SELECT 
        customer_unique_id,
        customer_state,
        recency_days,
        frequency,
        monetary_value,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score, -- Lower recency days = higher score
        CASE 
            WHEN frequency = 1 THEN 1
            WHEN frequency = 2 THEN 3
            WHEN frequency = 3 THEN 4
            ELSE 5 
        END AS f_score,
        NTILE(5) OVER (ORDER BY monetary_value ASC) AS m_score
    FROM customer_rfm
),
segmented AS (
    SELECT 
        customer_unique_id,
        customer_state,
        recency_days,
        frequency,
        monetary_value,
        r_score,
        f_score,
        m_score,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
            WHEN r_score >= 4 AND f_score < 3 THEN 'Recent Customers'
            WHEN r_score = 3 AND f_score = 1 THEN 'Promising'
            WHEN r_score = 2 AND f_score >= 2 THEN 'Customers Needing Attention'
            WHEN r_score = 2 AND f_score = 1 THEN 'About to Sleep'
            WHEN r_score = 1 AND f_score >= 3 THEN 'At Risk (High Value)'
            WHEN r_score = 1 AND f_score = 2 THEN 'Hibernating'
            ELSE 'Lost Customers'
        END AS customer_segment
    FROM rfm_scores
)
SELECT 
    customer_segment,
    COUNT(customer_unique_id) AS customer_count,
    ROUND(COUNT(customer_unique_id) * 100.0 / (SELECT COUNT(*) FROM segmented), 2) AS customer_pct,
    ROUND(AVG(recency_days), 1) AS avg_recency_days,
    ROUND(AVG(frequency), 2) AS avg_frequency,
    ROUND(AVG(monetary_value), 2) AS avg_monetary_spend,
    ROUND(SUM(monetary_value), 2) AS total_segment_revenue,
    ROUND(SUM(monetary_value) * 100.0 / (SELECT SUM(monetary_value) FROM segmented), 2) AS revenue_share_pct
FROM segmented
GROUP BY customer_segment
ORDER BY total_segment_revenue DESC;
