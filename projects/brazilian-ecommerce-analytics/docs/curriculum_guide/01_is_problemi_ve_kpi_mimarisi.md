# 📘 Bölüm 1: İş Problemleri, Metrikler & KPI Mimarisi
**İlgili Müfredat:** Modül 1 (İş Problemleri & KPI Tanımlama) & Modül 2 (Finansal Modelleme Mantığı)

---

## 1. Pazar Yeri İş Modeli ve Olist Ekosistemi

Bir veri analisti olarak koda veya SQL'e başlamadan önce sorulması gereken ilk soru şudur:  
👉 **"Bu şirket nasıl para kazanıyor ve değer zincirindeki rolü nedir?"**

### Olist Nedir?
Olist, geleneksel bir perakende e-ticaret şirketi değildir. **Brezilya'daki küçük ve orta ölçekli satıcıları (KOBİ'leri)** ülkenin dev e-ticaret platformlarına (Mercado Livre, Americanas, Casas Bahia, Submarino vb.) tek bir entegrasyonla bağlayan bir **Pazar Yeri Kolaylaştırıcısı (Marketplace Enabler)** ve lojistik orkestratörüdür.

```
[Küçük Satıcılar / KOBİ'ler]
           │
           ▼
     ┌───────────┐
     │   OLIST   │ ◄── [Merkezi Katalog, Fiyatlama, Ödeme & Lojistik Dağıtım]
     └───────────┘
           │
           ▼
[Tüketiciler (Nihai Alıcılar)]
```

### Olist'in Gelir Modeli (Take Rate)
- Olist, platform üzerinden gerçekleşen her başarılı satıştan bir **komisyon (Take Rate)** ve bazen lojistik aracılık hizmet bedeli alır.
- **Komisyon Oranı:** Sektör standardı %10 - %20 bandındadır.
- Dolayısıyla, Olist'in karlılığı yalnızca daha fazla ürün satılmasına değil, **iade ve iptallerin düşük olmasına**, **müşterilerin platformda tekrar alışveriş yapmasına (LTV)** ve **lojistik maliyetlerin optimize edilmesine** bağlıdır.

---

## 2. Metrik Hiyerarşisi & KPI Ağacı (Metric Tree)

Veri analistleri, dağınık sayılar yerine birbiriyle ilişkili bir **Metrik Hiyerarşisi** kurmalıdır:

```
                            [ KUZEY YILDIZI METRİĞİ (North Star) ]
                                    Net İşlem Hacmi (GMV)
                                             │
             ┌───────────────────────────────┴──────────────────────────────┐
             ▼                                                              ▼
    [ Büyüme & Hacim ]                                             [ Müşteri Değeri & Birim Ekonomi ]
     Toplam Sipariş Sayısı                                            Ortalama Sepet Tutarı (AOV)
     Aktif Alıcı Sayısı                                              Sipariş Başı Ürün Adedi
             │                                                              │
     ┌───────┴───────┐                                              ┌───────┴───────┐
     ▼               ▼                                              ▼               ▼
Yeni Müşteri    Tekrar Alım Oranı                              Birim Ürün Fiyatı   Kargo Payı Oranı
(Acquisition)    (Retention Rate)
```

---

## 3. Temel Metrik Formülleri ve İş Anlamları

### A. Brüt Mal Değeri (Gross Merchandise Value - GMV)
Platform üzerinden satılan ürünlerin toplam parasal değeridir (kargo hariç net ürün bedeli).
$$\text{GMV} = \sum (\text{item\_price})$$
*Projedeki Değeri:* **R$ 13,591,643.70**

### B. Brüt Platform Hacmi (Gross Platform Revenue)
Tüketicilerin kredi kartı veya boleto ile ödediği toplam nakit girişi (ürünler + kargo bedeli).
$$\text{Gross Revenue} = \sum (\text{item\_price} + \text{freight\_value})$$
*Projedeki Değeri:* **R$ 15,843,527.24** (Kargo tutarı: R$ 2.25 Milyon)

### C. Ortalama Sepet Değeri (Average Order Value - AOV)
Teslim edilen her sipariş başına düşen ortalama harcama tutarıdır.
$$\text{AOV} = \frac{\text{Toplam Brüt Ciro}}{\text{Teslim Edilen Sipariş Sayısı}} = \frac{15,843,527.24}{96,478} = \text{R\$\ } 164.22$$
*(Yalnızca ürün bazında net AOV: R$ 140.88)*

### D. İptal Oranı (Cancellation Rate)
Verilen siparişlerin operasyonel veya müşteri kaynaklı iptal edilme yüzdesidir.
$$\text{Cancellation Rate} = \frac{\text{İptal Edilen Siparişler}}{\text{Toplam Siparişler}} \times 100 = \frac{625}{99,441} \times 100 = \%0.63$$
*Analist Notu:* %0.63 oranı e-ticaret sektörü için son derece sağlıklıdır (%2-5 arası normal kabul edilir).

### E. Lojistik SLA Uyum Oranı ve Gecikme Oranı (Late Delivery Rate)
Siparişin tahmini teslim tarihinden (Estimated Delivery Date) sonra müşteriye ulaşma oranı.
$$\text{Late Rate} = \frac{\sum (\text{Teslim Tarihi} > \text{Tahmini Tarih})}{\text{Toplam Teslim Edilen Sipariş}} \times 100 = \frac{7,827}{96,478} \times 100 = \%8.11$$
$$\text{SLA Compliance Rate} = 100\% - 8.11\% = \%91.89$$

### F. Kargo Maliyet Yükü Oranı (Freight-to-Value Ratio)
Müşterinin ödediği kargo tutarının ürün fiyatına oranıdır. Bu oran arttıkça sepet terk etme (cart abandonment) riski yükselir.
$$\text{Freight Ratio} = \frac{\text{Toplam Kargo Ücreti}}{\text{Toplam Ürün Tutarı}} \times 100 = \frac{2,251,883.54}{13,591,643.70} \times 100 = \%16.57$$
*Analist Notu:* Brezilya'nın güneydoğusunda bu oran %12 iken, kuzey eyaletlerinde %30'un üzerine çıkmaktadır.

---

## 4. Bir Veri Analistinin Çıkarması Gereken İş Teşhisi

1. **Büyüme Teşhisi:** Olist, sipariş hacmi ve ciro olarak hızla büyümektedir; ancak bu büyüme **yeni müşteri edinmeye (%96.9 tekil alıcı)** dayanmaktadır.
2. **Kırılganlık Teşhisi:** Kargo maliyetinin sepetin %16.5'ini oluşturması ve lojistik gecikmelerinin %8.1 olması, Olist'in müşteri tutundurma başarısını baltalayan temel operasyonel darboğazdır.
3. **Finansal Teşhis:** Taksitli ödemeler olmasaydı yüksek tutarlı sepetler (elektronik, mobilya) satılamazdı; çünkü Brezilya tüketicisi R$ 400 üzeri alışverişlerin %80'ini 6-10 taksite bölmektedir.
