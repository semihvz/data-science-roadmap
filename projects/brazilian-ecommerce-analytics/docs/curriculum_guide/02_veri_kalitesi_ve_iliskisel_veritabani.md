# 📘 Bölüm 2: Veri Kalitesi, Modelleme & İlişkisel Veritabanı (ERD)
**İlgili Müfredat:** Modül 3 (Veri Temelleri, Kalitesi & ETL) & Modül 4 (İlişkisel Veritabanları & ERD Tasarımı)

---

## 1. Ham Veri Dosyalarının Anatomisi (Data Audit)

Olist veri seti, pazar yeri ekosistemini yansıtan 9 ayrı CSV dosyasından oluşur:

| Tablo Adı | Ham Satır Sayısı | Açıklama |
| :--- | :--- | :--- |
| `olist_orders_dataset.csv` | 99,441 | Sipariş durumları, satın alma ve teslimat zaman damgaları |
| `olist_customers_dataset.csv` | 99,441 | Müşteri tanımlayıcıları, şehir, eyalet ve posta kodu |
| `olist_order_items_dataset.csv` | 112,650 | Sipariş içindeki kalemler, ürün ID, satıcı ID, fiyat ve kargo |
| `olist_order_payments_dataset.csv` | 103,886 | Ödeme yöntemi (kredi kartı, boleto vb.), taksit sayısı, tutar |
| `olist_order_reviews_dataset.csv` | 99,224 (tekil) | Müşteri puanı (1-5), yorum başlığı, yorum metni ve cevap tarihi |
| `olist_products_dataset.csv` | 32,951 | Ürün boyutları, ağırlığı, fotoğraf sayısı ve kategori adı |
| `olist_sellers_dataset.csv` | 3,095 | Satıcı ID, şehir, eyalet ve posta kodu |
| `olist_geolocation_dataset.csv` | 1,000,163 | Posta kodu ön eki bazında enlem ve boylam koordinatları |
| `product_category_name_translation.csv` | 71 | Portekizce ürün kategorilerinin İngilizce karşılıkları |

---

## 2. Kritik Veri Kalitesi Tuzakları ve Analist Çözümleri

Gerçek dünya verileri asla temiz değildir. Bir veri analisti şu üç büyük veri kalitesi sorununu çözmek zorundadır:

### Tuzak 1: `customer_id` ile `customer_unique_id` Ayrımı (Kritik Nuans!)
- `olist_customers_dataset` tablosunda iki farklı müşteri ID'si bulunur:
  1. `customer_id`: **Her siparişe özel üretilen geçici sipariş anahtarıdır** (99,441 adet).
  2. `customer_unique_id`: **Gerçek, tekil kişiyi temsil eden anahtardır** (93,471 adet).
- **Hata:** Eğer analist RFM segmentasyonunda veya kohort analizinde `customer_id` kullanırsa, her müşteriyi yalnızca 1 kez alışveriş yapmış sanır ve **tüm tekrar alım (retention) analizini çöpe atar!**
- **Çözüm:** Sipariş tablosuyla birleştirme yaparken `customer_id` kullanılır; ancak müşteri düzeyinde gruplama (`GROUP BY`) yapılırken mutlaka `customer_unique_id` kullanılmalıdır.

### Tuzak 2: 1 Milyon Satırlık Coğrafi Veri Şişkinliği
- `olist_geolocation_dataset` içinde 1,000,163 satır vardır. Brezilya'daki aynı posta kodu ön eki (`geolocation_zip_code_prefix`) için yüzlerce GPS ölçümü bulunmaktadır.
- **Hata:** Müşteri veya satıcı tablosunu bu ham coğrafi tabloyla `LEFT JOIN` yapmak satır sayısını 100 binden milyonlara patlatır (Cartesian product etkisi).
- **Analist Çözümü (Centroid Aggregation):** Posta kodu başına ortalama enlem ve boylam hesaplanarak 19,015 tekil satıra indirgenir:
```python
df_geo_agg = df_geo.groupby("geolocation_zip_code_prefix").agg({
    "geolocation_lat": "mean",
    "geolocation_lng": "mean",
    "geolocation_city": "first",
    "geolocation_state": "first"
}).reset_index()
```

### Tuzak 3: Kategorilerde Dil Uyumu ve Kayıp Değerler
- Ürünler Portekizce kategorilere sahiptir (`cama_mesa_banho`). 71 kategori İngilizce sözlükle eşlenir; ancak eşlenmeyen veya null olan kategoriler analitik sorgularda kaybolmamalıdır (`COALESCE(english, portuguese, 'unknown')`).

---

## 3. İlişkisel Veritabanı Şeması (3NF Tasarımı & ERD)

Ham CSV dosyaları diskte bağımsız text dosyaları olarak sorgulanamaz. İlişkisel SQLite veritabanında (`data/olist.db`) aşağıdaki kısıtlarla modellenmiştir:

```sql
-- Sipariş Kalemleri Tablosu: Kompozit Birincil Anahtar
CREATE TABLE order_items (
    order_id TEXT NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    shipping_limit_date TEXT,
    price REAL NOT NULL,
    freight_value REAL NOT NULL,
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders (order_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers (seller_id)
);
```

### Neden 3. Normal Form (3NF)?
1. **Veri Tekrarının Önlenmesi:** Müşteri şehri ve eyaleti sipariş tablosuna yazılmaz; `customers` tablosunda tutulur.
2. **Güncelleme Anomalilerinin Önlenmesi:** Bir satıcının adresi değiştiğinde yalnızca `sellers` tablosunda tek bir satır güncellenir.

---

## 4. İndeksleme Stratejisi (B-Tree Indexing)

İlişkisel veritabanlarında yüz binlerce satırı birbirine bağlarken (`JOIN`) indeks yoksa veritabanı motoru **Full Table Scan (Tam Tablo Taraması)** yapar ($O(N)$ karmaşıklık).

Bu projede sorgu süresini 10 kat hızlandırmak için şu B-Tree indeksleri oluşturulmuştur:
```sql
CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_purchase_date ON orders (order_purchase_timestamp);
CREATE INDEX idx_order_items_product ON order_items (product_id);
CREATE INDEX idx_order_items_seller ON order_items (seller_id);
CREATE INDEX idx_order_reviews_score ON order_reviews (review_score);
```
*Sonuç:* Müşteri sipariş birleştirmeleri tam tarama yerine ikili arama ağacı üzerinden logaritmik zamanda ($O(\log N)$) tamamlanır.
