# 📘 Bölüm 5: İleri Analitik Teknikler (RFM, Kohort & Pareto)
**İlgili Müfredat:** Modül 10 (Veri Görselleştirme), Modül 11 (İş Zekası - BI) & Modül 12 (İleri Analitik Teknikler)

---

## 1. RFM Müşteri Yaşam Boyu Değeri Segmentasyonu (Modül 12)

Müşteri tabanını tek bir homojen kitle olarak görmek e-ticaret şirketlerinin yaptığı en büyük hatadır. **RFM Modeli**, müşterileri geçmiş satın alma davranışlarına göre 3 eksende puanlar:

1. **Recency (R - Tazelik):** Müşteri en son ne zaman sipariş verdi? (Son alışverişten bugüne geçen gün). Yakın zamanda alanların tekrar alma olasılığı daha yüksektir.
2. **Frequency (F - Sıklık):** Müşteri ne sıklıkla sipariş veriyor? (Toplam tamamlanan sipariş sayısı).
3. **Monetary (M - Parasal Değer):** Müşteri platforma ne kadar para bıraktı? (Toplam harcama).

### Olist'teki Kritik Frekans Dağılımı ve Ayrık Puanlama
Klasik RFM'de Recency, Frequency ve Monetary için `pd.qcut(..., q=5)` yapılır. Ancak Olist'te **müşterilerin %96.9'unun frekansı 1'dir!**  
Dolayısıyla klasik çeyreklik bölme matematiksel olarak çöker. Bir veri analisti şu özel ayrık puanlama mantığını kurmalıdır:

```python
def assign_f_score(frequency):
    if frequency == 1:
        return 1  # Tek seferlik alıcılar (Ezici çoğunluk)
    elif frequency == 2:
        return 3  # İki kez alan sadakat adayı
    elif frequency == 3:
        return 4  # Üç kez alan sadık alıcı
    else:
        return 5  # Dört ve üzeri alan VIP / Kurumsal
```

### 9 Stratejik Müşteri Segmenti ve CRM Eylem Planı (Playbook)

| Segment Adı | R Skoru | F Skoru | Müşteri Sayısı | Ciro Payı | Eylemsel Pazarlama Stratejisi |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Champions (Şampiyonlar)** | 4 - 5 | 4 - 5 | 535 | %1.9 | Ağır indirim yapmayın. VIP erken erişim, özel müşteri temsilcisi ve marka elçisi programı sunun. |
| **Loyal Customers (Sadıklar)** | 3 - 5 | 3 | 712 | %2.1 | Çapraz kategorilere yönlendirin (Cross-sell), sadakat puanı biriktirme sistemi kurun. |
| **Recent Customers (Yeni Gelenler)**| 4 - 5 | 1 | 35,420 | %35.2 | **En Kritik Kitle:** İlk teslimattan sonraki 7 gün içinde geçerli ikinci sipariş kuponu gönderin. |
| **Promising (Gelecek Vadedenler)** | 3 | 1 - 2 | 18,210 | %17.2 | İlgilendikleri kategorideki çok satanları ve kullanıcı incelemelerini e-posta ile tanıtın. |
| **At Risk (Risk Altındaki VIP'ler)**| 1 | 3 - 5 | 1,410 | %3.8 | **Yüksek Öncelik:** Eskiden çok alan ama kaybolan müşteriler. %20 özel indirim veya telefonla anket. |
| **Hibernating / Lost (Kayıplar)** | 1 | 1 | 37,184 | %39.8 | Reklam bütçesi harcamayın. Yalnızca Black Friday gibi kitlesel yıllık kampanyalarda bülten gönderin. |

---

## 2. Kohort Analizi ve Müşteri Tutundurma Matrisi (Cohort Retention)

Bir e-ticaret platformunda müşterilerin edinildikleri aydan sonra platformda kalıp kalmadığını ölçmenin tek bilimsel yolu **Kohort Analizidir**.

```python
# 1. Her müşterinin ilk sipariş ayını (Cohort Month) bulma
df['cohort_month'] = df.groupby('customer_unique_id')['order_month'].transform('min')

# 2. Sipariş ayı ile kohort ayı arasındaki farkı (Period Offset) hesaplama
df['period_offset'] = (df['order_month'].dt.year - df['cohort_month'].dt.year) * 12 + \
                      (df['order_month'].dt.month - df['cohort_month'].dt.month)

# 3. Yüzdelik tutundurma matrisi (Retention Matrix)
cohort_pivot = df.pivot_table(index='cohort_month', columns='period_offset', values='customer_unique_id', aggfunc='nunique')
retention_matrix = cohort_pivot.divide(cohort_pivot.iloc[:, 0], axis=0) * 100
```

### Olist Kohort Matrisi Bulgusu:
- **Ay 0 (Edinme Ayı):** %100
- **Ay 1:** %0.45 - %0.60
- **Ay 2:** %0.35 - %0.45
- **Ay 3:** %0.30 - %0.40
- **Analist Yorumu:** Olist'te müşterilerin tekrar sipariş verme mekanizması neredeyse yoktur. Şirket bir "kova deliği" (leaky bucket) problemi yaşamaktadır; her ay ciroyu korumak için sıfırdan pazarlama harcaması (CAC) yapmak zorundadır.

---

## 3. Pareto 80/20 Analizi ve ABC Sınıflandırması

Vilfredo Pareto'nun 80/20 prensibine göre gelirlerin büyük kısmı az sayıda ürün veya kategoriden gelir:

$$\text{Class A (Çekirdek \%80 Gelir)} \rightarrow \text{İlk 16 Kategori (\%21.6)}$$
$$\text{Class B (İkincil \%15 Gelir)} \rightarrow \text{Sonraki 18 Kategori (\%24.3)}$$
$$\text{Class C (Uzun Kuyruk \%5 Gelir)} \rightarrow \text{Kalan 40 Kategori (\%54.1)}$$

```
Kümülatif Gelir %
 100% │                                ┌───────────────── Class C (Kalan %5)
      │                     ┌──────────┘ ◄── Class B (Sonraki %15)
  80% │          ┌──────────┘ ◄── Pareto Sınırı (%80)
      │   ┌──────┘ ◄── Class A (İlk 16 Kategori: Sağlık, Saat, Yatak-Banyo...)
      │  ╱
   0% └──────────────────────────────────────────────── Kategoriler
```

### Operasyonel Çıkarım:
- Kategori yöneticileri ve tedarik ekipleri zamanlarının %80'ini **Class A'daki 16 kategoriye** (stok bulunurluğu, satıcı rekabeti, kargo hızlandırması) ayırmalıdır.

---

## 4. Taksitli Ödeme Finansmanı Modeli

Brezilya ödeme ekosisteminde tüketiciler kredi kartı taksitini bir nakit akışı yönetim aracı olarak kullanır:

- **1 Taksit (Tek Çekim):** Ortalama Sepet: **R$ 95.80**
- **2-3 Taksit:** Ortalama Sepet: **R$ 138.20**
- **4-6 Taksit:** Ortalama Sepet: **R$ 214.50**
- **7-10 Taksit:** Ortalama Sepet: **R$ 442.10**

> **Finansal Kaldıraç:** Taksit sayısı ile sepet büyüklüğü arasında güçlü bir pozitif doğrusal ilişki vardır ($R^2 = 0.94$). Yüksek marjlı kategorilerde sıfır faizli 10 taksit seçeneği sunmak sepet büyüklüğünü doğrudan 4 katına çıkarmaktadır!
