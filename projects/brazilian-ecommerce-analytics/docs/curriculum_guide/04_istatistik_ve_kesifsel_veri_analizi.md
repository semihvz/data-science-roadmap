# 📘 Bölüm 4: İstatistik & Keşifsel Veri Analizi (EDA)
**İlgili Müfredat:** Modül 8 (İstatistik & Olasılık) & Modül 9 (Python ile Veri Analizi - Pandas & NumPy)

---

## 1. Gelir Dağılımının Anatomisi: Sağa Çarpıklık (Right-Skewed Distribution)

Bir veri analisti adayı veriyi açtığında ilk yaptığı şey ortalama almaksa yanılır!  
Olist pazar yerindeki sipariş tutarları **Sağa Çarpık (Right-Skewed)** bir dağılım sergiler:

| İstatistiksel Metrik | Değer | İş Anlamı |
| :--- | :--- | :--- |
| **Ortalama (Mean)** | **R$ 160.54** | Aşırı yüksek harcamalardan yukarı çekilmiştir |
| **Medyan (50. Yüzdelik)** | **R$ 105.28** | Gerçek tipik Brezilyalı tüketicinin sepet tutarı |
| **Mod (En Sık Geçen)** | **R$ 59.90** | En popüler tekil ürün fiyat bandı |
| **Minimum** | **R$ 9.59** | En küçük alışveriş |
| **Maksimum** | **R$ 13,664.08** | Nadir toplu / kurumsal alımlar (Outlier) |
| **Çarpıklık (Skewness)** | **+3.42** | Güçlü pozitif sağa çarpıklık |

```
Frekans
  │   ▲ Mod (~60 R$)
  │  ╱ ╲
  │ ╱   ╲   Medyan (~105 R$)
  │╱     ╲      │
  │       ╲     ▼   Ortalama (~160 R$)
  │        ╲    │       │
  │         ╲───┴───────┴───────────────► Uzun Sağ Kuyruk (Outliers > 5000 R$)
  └─────────────────────────────────────── Harcama Tutarı (R$)
```

### Analist Çıkarımı:
> Yönetime sepet ortalaması sunulurken mutlaka **Medyan Sepet Değeri** de belirtilmelidir. Aksi takdirde pazarlama ekipleri müşterilerin R$ 160 harcamaya hazır olduğunu varsayarak yanlış fiyatlandırma stratejileri kurar.

---

## 2. Aykırı Değer (Outlier) Tespiti: IQR Yöntemi

Veri setindeki uç harcamaları tespit etmek için Çeyrekler Arası Açıklık (Interquartile Range - IQR) kullanılır:
$$\text{IQR} = Q_3 - Q_1 = 176.87 - 61.20 = \text{R\$\ } 115.67$$
$$\text{Üst Sınır (Upper Bound)} = Q_3 + 1.5 \times \text{IQR} = 176.87 + (1.5 \times 115.67) = \text{R\$\ } 350.38$$

- **Bulgu:** R$ 350.38 üzerindeki siparişler istatistiksel olarak "yüksek değerli aykırı değer" (High-Value Outliers) sınıfındadır.
- Bu siparişler toplam siparişlerin yalnızca **%7.8'ini** oluşturmasına rağmen, toplam cironun **%34.2'sini** getirmektedir!

---

## 3. İki Değişkenli Analiz: Lojistik Gecikmesi vs Müşteri Memnuniyeti

Veri analitiğinde en kritik iş korelasyonu, teslimat gecikmesi ($\Delta t_{\text{delay}}$) ile müşteri yorum puanı ($Score$) arasındaki ilişkidir:

### İstatistiksel Korelasyon Katsayısı (Pearson & Spearman)
$$r = -0.58 \quad (p < 0.001)$$
- **Anlamı:** Gecikme süresi arttıkça müşteri memnuniyet puanı güçlü ve ters yönlü bir düşüş yaşamaktadır.

### Hipotez Testi Bakış Açısı (A/B Testi Formülasyonu)
- **Sıfır Hipotezi ($H_0$):** Zamanında teslim edilen siparişlerin ortalama puanı ile geciken siparişlerin puanı arasında fark yoktur ($\mu_{\text{ontime}} = \mu_{\text{late}}$).
- **Alternatif Hipotez ($H_1$):** Zamanında teslim edilen siparişlerin puanı istatistiksel olarak anlamlı derecede daha yüksektir ($\mu_{\text{ontime}} > \mu_{\text{late}}$).

**Test Sonuçları:**
$$\mu_{\text{ontime}} = 4.27 \star \quad \text{vs} \quad \mu_{\text{late}} = 2.27 \star$$
$$t = 114.8, \quad p\text{-value} = 0.000000...$$
- **Karar:** $p < 0.05$ olduğu için $H_0$ sıfır hipotezi kesin olarak reddedilir. Gecikmenin memnuniyeti düşürdüğü %99.99 güven aralığında kanıtlanmıştır.

---

## 4. Python & Pandas ile Keşifsel Kodlama Pratikleri (Modül 9)

```python
import pandas as pd
import numpy as np

# 1. Tarih-zaman sütunundan saatlik ve günlük alım yoğunluğu matrisi çıkarma
df['purchase_dt'] = pd.to_datetime(df['order_purchase_timestamp'])
df['hour'] = df['purchase_dt'].dt.hour
df['day_name'] = df['purchase_dt'].dt.day_name()

# 2. Pivot tablo ile ısı haritası oluşturma
heatmap_data = df.pivot_table(
    index='day_name', 
    columns='hour', 
    values='order_id', 
    aggfunc='count',
    fill_value=0
)

# 3. pd.qcut ile eşit hacimli çeyreklik (Quantile) RFM puanı oluşturma
df['recency_score'] = pd.qcut(df['recency_days'], q=5, labels=[5, 4, 3, 2, 1])
```
