# 📘 Bölüm 6: Veri Hikayeciliği, Yönetici İletişimi & Mülakat Rehberi
**İlgili Müfredat:** Modül 14 (İş İletişimi & Data Storytelling) & Modül 15 (Portföy & Mülakat Hazırlığı)

---

## 1. Veri Hikayeciliği (Data Storytelling): Rakamlardan Stratejiye

Kıdemli bir veri analistini junior analistten ayıran temel fark, **"Ne oldu?"** sorusunun ötesine geçip **"Neden oldu ve şimdi ne yapmalıyız?"** sorularına yanıt vermesidir.

### C-Level 3 Dakikalık Yönetici Konuşması (Executive Elevator Pitch)

> *"Sayın Yönetim Kurulu,*  
> *Olist 2017-2018 döneminde cirosunu 4 katına çıkararak R$ 13.6M GMV hacmine ulaştı. Ancak veri derinlemesine incelendiğinde bu büyümenin sürdürülemez bir 'kova deliği' (leaky bucket) modeline dayandığı görülmektedir.*  
> 
> *Müşterilerimizin **%96.9'u platformdan yalnızca 1 kez alışveriş yapmakta**, ilk aydan sonra tekrar satın alma oranı **%0.5'e** düşmektedir. Bunun en büyük operasyonel kök nedeni ise lojistiktir: Zamanında teslim edilen siparişlerde memnuniyet **4.27 ★** iken, teslimatı geciken siparişlerde puan dramatik şekilde **1.62 ★** seviyesine çökmektedir.*  
> 
> *Önerimiz iki adımdan oluşmaktadır:*  
> *1. Teslimattan sonraki 7 gün içinde tetiklenen R$ 20'lik 'İkinci Sipariş Kuponu' ile müşteri tutundurma oranını %3.1'den %8'e çıkarmak.*  
> *2. En çok satan 16 Class A kategorisi için Kuzeydoğu bölgesinde mikro-dağıtım merkezi kurarak 28 günlük teslimat sürelerini 7 güne indirmektir."*

---

## 2. STAR Metodolojisi ile Bu Projeyi Mülakatta Anlatma

İş görüşmelerinde *"Bize en gurur duyduğun veri analizi projenizi anlatır mısınız?"* sorusu geldiğinde STAR tekniğini kullanın:

- **S (Situation - Durum):**  
  *Brezilya pazar yerinde 100k sipariş ve 93k tekil müşteriyi kapsayan çok tablolu ilişkisel bir e-ticaret veri kümesi üzerinde çalıştım.*
- **T (Task - Görev):**  
  *Amacım, platformun büyüme motorlarını analiz etmek, müşterileri yaşam boyu değerlerine göre segmente etmek, lojistik gecikmelerin müşteri memnuniyetine etkisini ölçmek ve C-Level için aksiyona dönüştürülebilir bir büyüme stratejisi üretmekti.*
- **A (Action - Eylem):**  
  *9 ham CSV dosyasını temizleyip 3. Normal Formda SQLite ilişkisel veritabanı olarak modelledim. Posta kodu koordinatlarını centroid algoritmasıyla 1 milyondan 19k satıra indirgedim. SQL'de `LAG()`, `NTILE(5)` ve koşan toplam pencere fonksiyonlarını kullanarak aylık MoM büyüme, RFM segmentasyonu ve Pareto 80/20 analizi yaptım. Hipotez testi ile teslimat gecikmesinin memnuniyeti düşürdüğünü $p < 0.001$ düzeyinde kanıtladım. Tüm içgörüleri canlı SQL konsolu içeren interaktif bir Streamlit BI paneline dönüştürdüm.*
- **R (Result - Sonuç):**  
  *Müşterilerin %96.9'unun tek siparişte kaldığını ortaya çıkararak yıllık R$ 1M+ ilave potansiyel ciro yaratabilecek 'İkinci Sipariş Tutundurma Playbook'u' geliştirdim. Ayrıca teslimat gecikmesinin 1 yıldızlı yorumları %71'e çıkardığını kanıtlayarak bölgesel fulfilment depo optimizasyon planını yönetime sundum.*

---

## 3. Mülakat Soru-Cevap Bankası (10 Teknik + 5 İş Sorusu)

### 💻 Teknik Mülakat Soruları

#### S1: Neden Olist'te `customer_id` yerine `customer_unique_id` kullandın?
**Cevap:** Olist mimarisinde `customer_id` her sipariş için üretilen geçici bir oturum token'ıdır. Aynı kişi 3 farklı sipariş verdiğinde 3 farklı `customer_id` oluşur. Ancak gerçek kişiyi temsil eden anahtar `customer_unique_id`'dir. Eğer analist `customer_id` kullanırsa tüm müşterileri tek sipariş vermiş sanır ve RFM/kohort analizleri çöker.

#### S2: Frekansın %96.9'unun 1 olduğu bir veri kümesinde RFM'i nasıl skorladın?
**Cevap:** Klasik `pd.qcut` quantile bölme yöntemi verideki değerler tekrarladığında çöker. Bu yüzden Recency ve Monetary için çeyreklik bölme (1-5) yaparken, Frequency için ayrık kural tabanlı bir mantık kurdum: 1 sipariş = 1 puan, 2 sipariş = 3 puan, 3 sipariş = 4 puan, 4+ sipariş = 5 puan.

#### S3: 1 milyondan fazla satırı olan `geolocation` tablosunu nasıl yönettin?
**Cevap:** Posta kodları için tekil olmayan yüz binlerce GPS koordinatı vardı. Doğrudan `JOIN` yapmak Cartesian çoğalmasına (fan-out) sebep olacağı için posta kodu ön eki (`zip_code_prefix`) bazında enlem ve boylamın ortalamasını (centroid) alarak tabloyu 19,015 tekil satıra indirgedim.

#### S4: SQL'de MoM (Aydan Aya) ciro büyümesini nasıl hesapladın?
**Cevap:** `LAG(gmv, 1) OVER (ORDER BY year_month)` pencere fonksiyonunu kullandım. Kendi kendine join (self-join) yapmaya kıyasla çok daha performanslı ve okunabilir oldu.

#### S5: Neden ortalama sipariş değeri (AOV) yerine medyanı da raporladın?
**Cevap:** Sipariş tutarları sağa çarpık (right-skewed) bir dağılıma sahipti ($Skewness = +3.42$). R$ 13,000'lık uç değerler aritmetik ortalamayı R$ 160'a yükseltirken, medyan R$ 105 idi. Tipik tüketicinin davranışını anlamak için medyan daha güvenilir bir merkezi eğilim ölçüsüdür.

#### S6: SQL Görünümü (`VIEW`) kullanmanın projeye katkısı ne oldu?
**Cevap:** Sipariş, müşteri, kalem, ödeme ve yorum tablolarını birbirine bağlayan 60 satırlık karmaşık sorguyu `vw_orders_summary` görünümünde kapsülledim (encapsulation). Böylece Python tarafında veya analitik sorgularda kod tekrarını önledim ve tek satırda denormalize analitik verilere erişebildim.

#### S7: İndekslemenin (B-Tree) sorgu hızına etkisi ne oldu?
**Cevap:** `orders` ve `order_items` tablolarında `order_id` ve `customer_id` üzerine B-Tree indeksi oluşturduk. Bu sayede join işlemlerinin zaman karmaşıklığı $O(N)$ tam taramadan $O(\log N)$ seviyesine inerek sorguları saniyeler seviyesine düşürdü.

#### S8: Parquet yerine neden %100 saf SQLite tercih ettiniz?
**Cevap:** İlişkisel veri bütünlüğü (ACID), yabancı anahtar kısıtları, dinamik görünüm (View) desteği ve doğrudan SQL konsolundan sorgulanabilirlik için tek ve tutarlı bir kaynak (Single Source of Truth) olarak SQLite kullandık.

#### S9: Pareto analizini SQL'de nasıl gerçekleştirdin?
**Cevap:** `SUM(total_revenue) OVER (ORDER BY total_revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` ifadesi ile koşan toplam (running total) aldım ve bunu genel toplam ciroya bölerek kümülatif yüzdelik eğrisini hesapladım.

#### S10: NPS proxy metriğini nasıl modelledin?
**Cevap:** 5 yıldız verenleri Destekleyenler (Promoters), 4 yıldız verenleri Pasifler (Passives), 1-3 yıldız verenleri Kötüleyenler (Detractors) olarak grupladım. Formül: `NPS = % Promoters - % Detractors`.

---

### 💼 İş Problemi ve Strateji Mülakat Soruları

#### S11: Olist için en kritik büyüme darboğazı sence nedir?
**Cevap:** Müşteri edinme maliyeti (CAC) yüksekken, tekrar alım oranının yalnızca %3.1 olmasıdır. Şirket müşteri tutunduramadığı için sürekli yeni müşteri bulmak zorundadır.

#### S12: Lojistik gecikmelerini çözmek için şirkete ne önerirsin?
**Cevap:** Siparişlerin %62'si São Paulo ve çevresinden gelmektedir; ancak Kuzey eyaletlerine teslimat 28 gün sürmektedir. Class A kategorilerindeki en popüler ürünler için bölgesel konsinye depoları (Regional Hubs) kurulmalıdır.

#### S13: Taksitli ödemeler neden pazar yeri için stratejiktir?
**Cevap:** Taksit sayısı arttıkça ortalama sepet büyüklüğü R$ 95'ten R$ 442'ye çıkmaktadır. Taksit imkanı sunulmayan pahalı ürünlerin sepet dönüşüm oranı düşmektedir.

#### S14: Pazarlama bütçesini RFM segmentlerine nasıl dağıtırsın?
**Cevap:** Bütçenin %60'ı "Recent Customers" segmentine 2. siparişi aldırmak için, %25'i "At Risk" VIP müşterileri geri kazanmak için ayrılmalıdır. "Lost" segmentine reklam bütçesi harcanmamalıdır.

#### S15: Black Friday döneminde operasyonel darboğazı nasıl önlersin?
**Cevap:** Kasım 2017'de ciro %53 artmış ancak kargolama süreleri uzamıştır. Satıcılara kargoya teslim için 48 saat kuralı konulmalı ve kargo firmalarıyla önceden dinamik hacim taahhütleri yapılmalıdır.
