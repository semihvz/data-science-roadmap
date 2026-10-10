-- ============================================================
-- SQL Analysis Module 2: RFM Customer Segmentation
-- ============================================================

-- Reference Date for Recency calculation (usually MAX(order_date) + 1 day)
WITH max_date_cte AS (
    SELECT MAX(order_date) AS max_date FROM orders WHERE order_status = 'Completed'
),
customer_rfm_raw AS (
    SELECT 
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.email,
        c.city,
        c.acquisition_channel,
        CAST((JULIANDAY((SELECT max_date FROM max_date_cte)) - JULIANDAY(MAX(o.order_date))) AS INTEGER) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(o.total_amount), 2) AS monetary
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'Completed'
    GROUP BY c.customer_id
),
rfm_scores AS (
    SELECT 
        customer_id,
        customer_name,
        email,
        city,
        acquisition_channel,
        recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score, -- Recent orders get higher R score
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,     -- Higher frequency gets higher F score
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score        -- Higher spend gets higher M score
    FROM customer_rfm_raw
),
rfm_segmented AS (
    SELECT 
        *,
        (r_score || f_score || m_score) AS rfm_cell,
        ROUND((r_score + f_score + m_score) / 3.0, 2) AS rfm_score_avg,
        CASE 
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'
            WHEN r_score >= 4 AND f_score <= 2 THEN 'Promising / New'
            WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'At Risk'
            WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN 'Lost Customers'
            WHEN r_score = 3 AND f_score <= 2 THEN 'About to Sleep'
            ELSE 'Need Attention'
        END AS rfm_segment
    FROM rfm_scores
)
-- RFM Summary Aggregation by Segment
SELECT 
    rfm_segment,
    COUNT(customer_id) AS total_customers,
    ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM rfm_segmented), 2) AS customer_share_pct,
    ROUND(AVG(recency_days), 1) AS avg_recency_days,
    ROUND(AVG(frequency), 2) AS avg_frequency,
    ROUND(AVG(monetary), 2) AS avg_monetary_spend,
    ROUND(SUM(monetary), 2) AS total_segment_revenue
FROM rfm_segmented
GROUP BY rfm_segment
ORDER BY total_segment_revenue DESC;
