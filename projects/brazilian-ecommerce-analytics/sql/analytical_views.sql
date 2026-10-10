-- Analytical Views for Brazilian E-Commerce (Olist)
-- Star-schema style denormalized views for instant business intelligence

DROP VIEW IF EXISTS vw_orders_summary;
DROP VIEW IF EXISTS vw_customer_rfm_raw;
DROP VIEW IF EXISTS vw_category_sales;
DROP VIEW IF EXISTS vw_seller_performance;
DROP VIEW IF EXISTS vw_state_logistics;

-- 1. Enriched Orders Summary View (Order Granularity)
CREATE VIEW vw_orders_summary AS
WITH items_agg AS (
    SELECT 
        order_id,
        COUNT(order_item_id) AS total_items,
        SUM(price) AS items_value,
        SUM(freight_value) AS total_freight,
        SUM(price + freight_value) AS total_order_value
    FROM order_items
    GROUP BY order_id
),
pay_agg AS (
    SELECT 
        order_id,
        GROUP_CONCAT(DISTINCT payment_type) AS payment_types,
        MAX(payment_installments) AS max_installments,
        SUM(payment_value) AS total_payment_value
    FROM order_payments
    GROUP BY order_id
),
rev_agg AS (
    SELECT 
        order_id,
        AVG(review_score) AS avg_review_score,
        COUNT(review_id) AS review_count
    FROM order_reviews
    GROUP BY order_id
)
SELECT 
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    SUBSTR(o.order_purchase_timestamp, 1, 7) AS purchase_year_month,
    SUBSTR(o.order_purchase_timestamp, 1, 4) AS purchase_year,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    ROUND((JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp)), 1) AS delivery_days,
    ROUND((JULIANDAY(o.order_estimated_delivery_date) - JULIANDAY(o.order_purchase_timestamp)), 1) AS estimated_days,
    ROUND((JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date)), 1) AS delay_days,
    CASE 
        WHEN o.order_delivered_customer_date IS NOT NULL 
             AND o.order_estimated_delivery_date IS NOT NULL 
             AND JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date) 
        THEN 1 
        ELSE 0 
    END AS is_delayed,
    COALESCE(i.total_items, 0) AS total_items,
    COALESCE(i.items_value, 0) AS items_value,
    COALESCE(i.total_freight, 0) AS total_freight,
    COALESCE(i.total_order_value, 0) AS total_order_value,
    COALESCE(p.payment_types, 'unknown') AS payment_types,
    COALESCE(p.max_installments, 1) AS max_installments,
    COALESCE(p.total_payment_value, 0) AS total_payment_value,
    COALESCE(r.avg_review_score, NULL) AS review_score
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN items_agg i ON o.order_id = i.order_id
LEFT JOIN pay_agg p ON o.order_id = p.order_id
LEFT JOIN rev_agg r ON o.order_id = r.order_id;

-- 2. Customer RFM Raw Aggregates (Unique Customer Granularity)
CREATE VIEW vw_customer_rfm_raw AS
SELECT 
    c.customer_unique_id,
    c.customer_state,
    c.customer_city,
    COUNT(DISTINCT o.order_id) AS frequency,
    MAX(o.order_purchase_timestamp) AS last_purchase_timestamp,
    MIN(o.order_purchase_timestamp) AS first_purchase_timestamp,
    ROUND(SUM(COALESCE(i.price, 0)), 2) AS monetary_value,
    ROUND(AVG(COALESCE(i.price, 0)), 2) AS avg_item_price,
    ROUND(AVG(r.review_score), 2) AS avg_customer_review_score
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items i ON o.order_id = i.order_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_unique_id, c.customer_state, c.customer_city;

-- 3. Product Category Sales & Performance
CREATE VIEW vw_category_sales AS
SELECT 
    COALESCE(p.product_category_name_english, p.product_category_name, 'Other') AS category_name,
    COUNT(i.order_item_id) AS items_sold,
    COUNT(DISTINCT i.order_id) AS distinct_orders,
    ROUND(SUM(i.price), 2) AS total_revenue,
    ROUND(AVG(i.price), 2) AS avg_item_price,
    ROUND(AVG(i.freight_value), 2) AS avg_freight,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM order_items i
JOIN products p ON i.product_id = p.product_id
JOIN orders o ON i.order_id = o.order_id
LEFT JOIN order_reviews r ON i.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY COALESCE(p.product_category_name_english, p.product_category_name, 'Other');

-- 4. State Logistics & Delivery SLAs
CREATE VIEW vw_state_logistics AS
SELECT 
    customer_state,
    COUNT(order_id) AS total_orders,
    ROUND(AVG(delivery_days), 2) AS avg_delivery_days,
    ROUND(AVG(estimated_days), 2) AS avg_estimated_days,
    ROUND(AVG(delay_days), 2) AS avg_delay_days,
    ROUND(SUM(is_delayed) * 100.0 / COUNT(order_id), 2) AS late_delivery_rate_pct,
    ROUND(AVG(total_freight), 2) AS avg_freight_value,
    ROUND(AVG(review_score), 2) AS avg_review_score
FROM vw_orders_summary
WHERE order_status = 'delivered' AND delivery_days IS NOT NULL
GROUP BY customer_state;

-- 5. Seller Performance Metrics
CREATE VIEW vw_seller_performance AS
SELECT 
    s.seller_id,
    s.seller_state,
    s.seller_city,
    COUNT(DISTINCT i.order_id) AS total_orders,
    COUNT(i.order_item_id) AS total_items_sold,
    ROUND(SUM(i.price), 2) AS total_sales,
    ROUND(AVG(i.price), 2) AS avg_item_price,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM sellers s
JOIN order_items i ON s.seller_id = i.seller_id
JOIN orders o ON i.order_id = o.order_id
LEFT JOIN order_reviews r ON i.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY s.seller_id, s.seller_state, s.seller_city;
