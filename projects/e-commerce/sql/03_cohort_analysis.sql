-- ============================================================
-- SQL Analysis Module 3: Customer Cohort Retention Analysis
-- ============================================================

WITH customer_first_order AS (
    SELECT 
        customer_id,
        MIN(STRFTIME('%Y-%m', order_date)) AS cohort_month,
        MIN(order_date) AS first_order_date
    FROM orders
    WHERE order_status = 'Completed'
    GROUP BY customer_id
),
customer_orders_period AS (
    SELECT 
        o.customer_id,
        cfo.cohort_month,
        STRFTIME('%Y-%m', o.order_date) AS order_month,
        (
            (STRFTIME('%Y', o.order_date) - STRFTIME('%Y', cfo.first_order_date)) * 12 +
            (STRFTIME('%m', o.order_date) - STRFTIME('%m', cfo.first_order_date))
        ) AS month_number
    FROM orders o
    JOIN customer_first_order cfo ON o.customer_id = cfo.customer_id
    WHERE o.order_status = 'Completed'
),
cohort_size AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_id) AS total_cohort_customers
    FROM customer_first_order
    GROUP BY cohort_month
),
retention_counts AS (
    SELECT 
        cop.cohort_month,
        cop.month_number,
        COUNT(DISTINCT cop.customer_id) AS active_retaining_customers
    FROM customer_orders_period cop
    GROUP BY cop.cohort_month, cop.month_number
)
SELECT 
    rc.cohort_month,
    cs.total_cohort_customers AS initial_cohort_size,
    rc.month_number,
    rc.active_retaining_customers,
    ROUND((rc.active_retaining_customers * 100.0 / cs.total_cohort_customers), 2) AS retention_rate_pct
FROM retention_counts rc
JOIN cohort_size cs ON rc.cohort_month = cs.cohort_month
ORDER BY rc.cohort_month ASC, rc.month_number ASC;
