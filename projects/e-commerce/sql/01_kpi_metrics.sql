-- ============================================================
-- SQL Analysis Module 1: Executive KPI Metrics & Monthly Performance
-- ============================================================

-- 1. Executive Summary KPIs (Overall Portfolio Performance)
SELECT 
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT CASE WHEN o.order_status = 'Completed' THEN o.order_id END) AS completed_orders,
    COUNT(DISTINCT o.customer_id) AS total_unique_customers,
    ROUND(SUM(CASE WHEN o.order_status = 'Completed' THEN o.total_amount ELSE 0 END), 2) AS gross_revenue,
    ROUND(AVG(CASE WHEN o.order_status = 'Completed' THEN o.total_amount END), 2) AS average_order_value_aov,
    ROUND(SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(o.order_id), 2) AS cancellation_rate_pct,
    ROUND(SUM(CASE WHEN o.order_status = 'Returned' THEN 1 ELSE 0 END) * 100.0 / COUNT(o.order_id), 2) AS return_rate_pct
FROM orders o;

-- 2. Monthly Revenue Trend & Month-over-Month (MoM) Growth
WITH monthly_stats AS (
    SELECT 
        STRFTIME('%Y-%m', order_date) AS order_month,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT customer_id) AS active_customers,
        SUM(total_amount) AS monthly_revenue,
        AVG(total_amount) AS monthly_aov
    FROM orders
    WHERE order_status = 'Completed'
    GROUP BY STRFTIME('%Y-%m', order_date)
)
SELECT 
    order_month,
    total_orders,
    active_customers,
    ROUND(monthly_revenue, 2) AS monthly_revenue,
    ROUND(monthly_aov, 2) AS monthly_aov,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY order_month)) 
        * 100.0 / LAG(monthly_revenue, 1) OVER (ORDER BY order_month), 
        2
    ) AS mom_growth_pct
FROM monthly_stats
ORDER BY order_month;

-- 3. Product Category Revenue & Gross Profit Margin Analysis
SELECT 
    p.category,
    COUNT(DISTINCT oi.order_id) AS orders_count,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.total_price), 2) AS category_revenue,
    ROUND(SUM(oi.quantity * p.cost_price), 2) AS category_cogs,
    ROUND(SUM(oi.total_price) - SUM(oi.quantity * p.cost_price), 2) AS gross_profit,
    ROUND(
        (SUM(oi.total_price) - SUM(oi.quantity * p.cost_price)) * 100.0 / SUM(oi.total_price), 
        2
    ) AS profit_margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'Completed'
GROUP BY p.category
ORDER BY category_revenue DESC;

-- 4. Top 10 Customers by Total Lifetime Spend
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.city,
    c.acquisition_channel,
    COUNT(DISTINCT o.order_id) AS total_orders_placed,
    ROUND(SUM(o.total_amount), 2) AS total_lifetime_spend,
    ROUND(AVG(o.total_amount), 2) AS avg_spend_per_order,
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS latest_order_date
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_status = 'Completed'
GROUP BY c.customer_id
ORDER BY total_lifetime_spend DESC
LIMIT 10;
