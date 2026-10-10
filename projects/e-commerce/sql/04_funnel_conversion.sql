-- ============================================================
-- SQL Analysis Module 4: Marketing Performance & Payment Conversion
-- ============================================================

-- 1. Acquisition Channel Performance (Revenue & Order Efficiency)
SELECT 
    c.acquisition_channel,
    COUNT(DISTINCT c.customer_id) AS acquired_customers,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(o.total_amount), 2) AS total_revenue,
    ROUND(SUM(o.total_amount) / COUNT(DISTINCT c.customer_id), 2) AS revenue_per_acquired_customer,
    ROUND(COUNT(DISTINCT o.order_id) * 1.0 / COUNT(DISTINCT c.customer_id), 2) AS orders_per_customer
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_status = 'Completed'
GROUP BY c.acquisition_channel
ORDER BY total_revenue DESC;

-- 2. Payment Method Popularity & Order Success Rate
SELECT 
    payment_method,
    COUNT(order_id) AS total_attempted_orders,
    SUM(CASE WHEN order_status = 'Completed' THEN 1 ELSE 0 END) AS completed_orders,
    SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
    SUM(CASE WHEN order_status = 'Returned' THEN 1 ELSE 0 END) AS returned_orders,
    ROUND(SUM(CASE WHEN order_status = 'Completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(order_id), 2) AS completion_success_rate_pct,
    ROUND(SUM(CASE WHEN order_status = 'Completed' THEN total_amount ELSE 0 END), 2) AS total_processed_revenue
FROM orders
GROUP BY payment_method
ORDER BY total_processed_revenue DESC;

-- 3. Review Ratings vs Product Sales & Return Correlation
SELECT 
    p.category,
    ROUND(AVG(cr.rating), 2) AS avg_customer_rating,
    COUNT(DISTINCT cr.review_id) AS total_reviews_count,
    ROUND(SUM(CASE WHEN o.order_status = 'Returned' THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT o.order_id), 2) AS category_return_rate_pct
FROM products p
LEFT JOIN customer_reviews cr ON p.product_id = cr.product_id
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.order_id
GROUP BY p.category
ORDER BY avg_customer_rating DESC;
