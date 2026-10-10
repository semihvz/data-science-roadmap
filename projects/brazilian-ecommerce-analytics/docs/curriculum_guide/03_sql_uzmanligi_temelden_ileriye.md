# 📘 Bölüm 3: SQL ile Veri Analitiği (Temelden İleri Seviyeye)
**İlgili Müfredat:** Modül 5 (SQL Temel), Modül 6 (SQL Orta) & Modül 7 (SQL İleri Teknikler)

---

## 1. Temel SQL: Filtreleme, Gruplama ve Agregasyon (Modül 5)

Veri analistinin günlük işlerinin temelini oluşturan agregasyon fonksiyonları, Olist veritabanında teslimat durumlarına göre şu şekilde uygulanır:

```sql
-- Teslim edilen siparişlerin eyalet bazında sipariş sayısı ve toplam cirosu
SELECT 
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(i.price), 2) AS total_revenue,
    ROUND(AVG(i.price), 2) AS avg_item_price
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items i ON o.order_id = i.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
HAVING COUNT(DISTINCT o.order_id) > 500
ORDER BY total_revenue DESC;
```
### Temel Prensipler:
- `WHERE`: Verileri satır düzeyinde filtreler (yalnızca teslim edilen siparişler).
- `GROUP BY`: Eyalet bazında özetleme yapar.
- `HAVING`: Agregasyon sonucunu filtreler (yalnızca 500'den fazla siparişi olan eyaletler).

---

## 2. Orta SQL: Çoklu Tablo Birleştirmeleri (JOINs) & Görünümler (Modül 6)

Olist gibi ilişkisel bir pazar yerinde sipariş detaylarını tek bir satırda görmek için birden fazla tablonun birleştirilmesi gerekir.

### Neden `LEFT JOIN` Tercih Edilir?
Bazı siparişlerde müşteriler yorum yapmamış olabilir veya sipariş kalemleri henüz onaylanmamış olabilir. `INNER JOIN` kullanılırsa yorumu olmayan siparişler sonuç kümesinden tamamen silinir. Bu yüzden çekirdek sipariş tablosuna diğer detaylar `LEFT JOIN` ile bağlanır:

```sql
-- Analitik Sipariş Özeti Görünümü (vw_orders_summary)
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
)
SELECT 
    o.order_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    ROUND((JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp)), 1) AS delivery_days,
    ROUND((JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date)), 1) AS delay_days,
    COALESCE(i.items_value, 0) AS items_value,
    COALESCE(i.total_freight, 0) AS total_freight,
    COALESCE(p.max_installments, 1) AS max_installments
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN items_agg i ON o.order_id = i.order_id
LEFT JOIN pay_agg p ON o.order_id = p.order_id;
```

---

## 3. İleri SQL: Window Functions (Pencere Fonksiyonları) (Modül 7)

Kıdemli veri analistlerini ayırt eden en kritik yetkinlik **Pencere Fonksiyonları (Window Functions)** kullanımıdır.

### A. Aylık Büyüme Oranı Hesabı (`LAG()` Fonksiyonu)
Bir önceki ayın cirosuna erişmek için kendi kendine join (self-join) yapmak yerine `LAG()` pencere fonksiyonu kullanılır:

```sql
WITH monthly AS (
    SELECT 
        SUBSTR(order_purchase_timestamp, 1, 7) AS year_month,
        ROUND(SUM(items_value), 2) AS gmv
    FROM vw_orders_summary
    WHERE order_status = 'delivered'
    GROUP BY SUBSTR(order_purchase_timestamp, 1, 7)
)
SELECT 
    year_month,
    gmv,
    LAG(gmv, 1) OVER (ORDER BY year_month) AS prev_month_gmv,
    ROUND(
        (gmv - LAG(gmv, 1) OVER (ORDER BY year_month)) * 100.0 / LAG(gmv, 1) OVER (ORDER BY year_month), 
        2
    ) AS mom_growth_pct
FROM monthly;
```

### B. Pareto 80/20 Kümülatif Koşan Toplam (`SUM() OVER`)
Kategorilerin pazar yeri cirosundaki kümülatif payını hesaplamak için koşan toplam (running total) penceresi kullanılır:

```sql
SELECT 
    category_name,
    total_revenue,
    SUM(total_revenue) OVER (
        ORDER BY total_revenue DESC 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_revenue,
    ROUND(
        SUM(total_revenue) OVER (
            ORDER BY total_revenue DESC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) * 100.0 / SUM(total_revenue) OVER (), 
        2
    ) AS cumulative_revenue_pct
FROM vw_category_sales
ORDER BY total_revenue DESC;
```

### C. Müşteri Dilimleme (`NTILE(5)` Fonksiyonu)
Tüm müşterileri harcama tutarlarına göre 5 eşit parçaya (Quintiles) böler:
```sql
SELECT 
    customer_unique_id,
    monetary_value,
    NTILE(5) OVER (ORDER BY monetary_value ASC) AS m_score
FROM vw_customer_rfm_raw;
```
- `m_score = 1`: En az harcayan %20'lik müşteri grubu.
- `m_score = 5`: En çok harcayan en değerli %20'lik müşteri grubu.
