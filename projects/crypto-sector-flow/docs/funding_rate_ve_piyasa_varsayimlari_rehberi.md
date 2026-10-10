# 📜 Fonlama Oranı (Funding Rate), Piyasa Mikroyapısı ve Temel Varsayımlar Rehberi

Bu belge, kripto para vadeli işlemlerinde (Perpetual Futures) **Fonlama Oranının (Funding Rate)** varoluş nedenini, bu veriye dayalı kantitatif stratejilerin arkasında yatan **temel finansal ve davranışsal varsayımları** ve piyasada işlem açarken dikkat edilmesi gereken altın kuralları belgeler.

---

## 🎯 1. Fonlama Oranı (Funding Rate) Nedir ve Neden Vardır?

Geleneksel vadeli işlemlerde bir vade sonu (Expiration Date) bulunur ve vade bittiğinde kontrat spot fiyattan nakit veya fiziki uzlaşmayla kapanır. 

Ancak kriptodaki **Sürekli Vadeli İşlemlerin (Perpetual Futures)** bir bitiş tarihi **yoktur**. 
Peki vadeli kontrat fiyatının, spot fiyattan sonsuza kadar kopup gitmesini engelleyen nedir?

👉 **Fonlama Oranı (Funding Rate) Mekanizması:**
- **Vadeli Fiyat > Spot Fiyat İse:** Fonlama **POZİTİF** olur. Long pozisyon taşıyanlar, Short pozisyon taşıyanlara faiz öder. Bu durum Long açmayı pahalılaştırarak fiyatı spot fiyata doğru geri çeker.
- **Vadeli Fiyat < Spot Fiyat İse:** Fonlama **NEGATİF** olur. Short pozisyon taşıyanlar, Long pozisyon taşıyanlara faiz öder. Bu durum Short açmayı pahalılaştırarak fiyatı yukarı, spot seviyesine doğru iter.

---

## 🧠 2. Fonlama Oranı Durumlarındaki 3 Temel Varsayım

Kantitatif modellerde fonlama oranı kullanılırken şu 3 aksiyom üzerine hipotez kurulur:

### 1. Varsayım: "Sürü Psikolojisi ve Ters Gösterge (Contrarian) Varsayımı"
> *"Piyasada perakende kitle (çoğunluk) aşırı derecede tek bir yöne yığılmışsa, o çoğunluk kurban edilmek üzeredir."*

- **Piyasa Sıfır Toplamlıdır (Zero-Sum Game):** Herkesin aynı anda kaldıraçlı short açıp zengin olduğu bir borsa dünyası matematiksel olarak imkânsızdır.
- Fonlama oranı aşırı negatife düştüğünde (örn: $< -\%0.05$), piyasadaki neredeyse tüm küçük yatırımcılar düşüşe oynamıştır.
- Aşağıda satacak başka kimse kalmadığı için satış baskısı tükenir. Piyasa yapıcılar (Market Makers) ve balinalar, tam tersi yöne (yukarı) sürerek likiditeyi avlar.

---

### 2. Varsayım: "Taşıma Maliyetinin Sürdürülemezliği (Cost of Carry) Varsayımı"
> *"Hiçbir spekülatör veya fon, her 8 saatte bir ağır ceza faizi ödemeye uzun süre dayanamaz; pozisyonu kapatmak zorunda kalırlar."*

- Vadeli işlemlerde fonlama negatif olduğunda Short'lar her 8 saatte bir faiz öder.
- Örneğin fonlama oranı **-%0.10** olduğunda:
  - 10x kaldıraç kullanan bir trader, **günde kasanın %3'ünü**, 10 günde ise **kasanın %30'unu sadece faiz olarak** kaybeder! Fiyat hiç kıpırdamasa bile cüzdanı erir.
- Bu faiz baskısı altındaki yatırımcılar en ufak bir yükselişte panikler ve pozisyonlarını kapatır.
- Short pozisyonu kapatmak demek **PİYASA ALIM EMRİ (BUY)** vermek demektir; bu da fiyatı dikey fırlatır.

---

### 3. Varsayım: "Likidasyon Havuzu Mıknatısı (Liquidation Magnet) Varsayımı"
> *"Fiyat rastgele hareket etmez; tahtadaki en büyük likidasyon ve stop-loss kümesinin olduğu yöne doğru çekilir."*

- Çok fazla short pozisyon biriktiğinde, bu insanların Stop-Loss emirleri giriş fiyatlarının %2 - %4 yukarısında devasa bir küme oluşturur.
- Piyasa yapıcı algoritmalar bu seviyeleri şeffaf olarak görür. Fiyatı küçük bir hacimle o seviyeye ittirdikleri anda, yüzlerce stop emri **otomatik piyasa alım emrine** dönüşür (Domino / Cascade Etkisi).

---

## 🚨 3. En Büyük Tehlike: "Barut ve Kıvılcım Prensibi"

Yeni başlayanların yaptığı en büyük hata:  
*"Fonlama çok negatif, hemen Long açayım!"* $\rightarrow$ **BU KESİNLİKLE HATALIDIR VE KASAYI BATIRIR.**

Çünkü sert bir piyasa çöküşünde koin aşırı negatif fonlamada kalarak %15 daha çakılabilir.

Bu yüzden modelimizdeki değişmez mantık şudur:

| Öğe | Piyasada Karşılığı | Rolü |
| :--- | :--- | :--- |
| **Aşırı Negatif Fonlama Oranı** | **BARUT FIÇISI** | Odada potansiyel patlama enerjisi birikmiştir. Tek başına patlamaz. |
| **Kümülatif Hacim ($10M+) & %3 Kırılım** | **KIVILCIM** | Odaya atılan ateştir. Patlamayı anında başlatır. |

> [!IMPORTANT]
> **Altın Kural**:  
> Asla sadece fonlama oranına bakarak işleme girilmez!  
> Fonlama oranı **"Hangi koin patlamaya hazır?"** sorusunun cevabıdır.  
> Hacimli %3 kırılım ise **"Hangi saniyede işleme gireyim?"** sorusunun cevabıdır.

---

## 📊 4. Eşik Değerleri ve Sınıflandırma Tablosu

Binance standart taban oranı **+%0.0100**'dür (Yıllık %10.95 faiz).

| Fonlama Oranı (8 Saatlik) | Sınıflandırma | Piyasa Durumu | Beklenen Fırsat |
| :---: | :--- | :--- | :--- |
| **$\le -\%0.1000$** | 🔥 **EKSTREM SQUEEZE** | Ağır panik, short'lar eriyor | Çok sert ve dikey %10-%20 ralli |
| **$-\%0.0500 \text{ ile } -\%0.1000$** | 🚨 **GÜÇLÜ SQUEEZE** | Belirgin short yığılması | 1:3 R:R için ideal alım bölgesi |
| `-%0.0200 ile -%0.0400` | ⚠️ **DİKKAT ÇEKİCİ** | Hafif satıcı baskısı | Hacim onayı beklenmeli |
| `-%0.0100 ile +%0.0200` | ⚪ **NÖTR / NORMAL** | Standart piyasa dengesi | Normal teknik analiz |
| `+%0.0300 ile +%0.0600` | 🟢 **COŞKULU BOĞA** | Yoğun long alımı | Yükseliş trendi |
| **$\ge +\%0.0800$** | ⚠️ **TEPE TEHLİKESİ** | Aşırı long yığılması | Ani düzeltme / Long tasfiyesi |
| **$\ge +\%0.1500$** | 💥 **ZİRVE ÇÖKÜŞÜ** | Çılgınlık, sürdürülemez faiz | Flash crash (Sert düşüş) riski |

---

## 🔬 5. Empirik Kanıtlar (Gerçek Veri Sonuçları)

1. **6 Aylık Backtest Kanıtı**:
   - 59 koin arasında test ettiğimiz sistemde **filtresiz model -202 R zarar** ederken;
   - **GTCUSDT (+12.01 R)**: Fonlama oranı **-%1.2932'ye** kadar çakılmıştı.
   - **WLDUSDT (+13.39 R)**: Fonlama oranı **-%0.1266'ya** inmişti.
   - **BOMEUSDT (+21.48 R)** ve **ENAUSDT (+16.67 R)**: Yılın yarısında negatif fonlamadaydı.
   - Kazançların tesadüf olmadığı, Short Squeeze yakıtıyla beslendiği ispatlandı.

2. **2025 BTC Verisi Kanıtı**:
   - Temmuz 2025'te Bitcoin 115,000 $ zirvesindeyken 93 periyodun 93'ü de pozitif fonlamadaydı (%100).
   - Mayıs 2025 dip seviyesinde (96K $) fonlama **-%0.0122'ye** düşerek dip dönüşünü müjdeledi.

---

## 🛠️ İlgili Dosyalar ve Kod Referansları
- Fonlama & Mum Çekici: [`projects/crypto-sector-flow/src/flow_calculator.py`](file:///home/smhvz/Desktop/DATA-SCIENCE/projects/crypto-sector-flow/src/flow_calculator.py)
- 2025 BTC Fonlama Verisi: [`projects/crypto-sector-flow/data/btc_2025_funding_rates.json`](file:///home/smhvz/Desktop/DATA-SCIENCE/projects/crypto-sector-flow/data/btc_2025_funding_rates.json)
- Çekme Betiği: [`projects/crypto-sector-flow/src/fetch_btc_2025_funding.py`](file:///home/smhvz/Desktop/DATA-SCIENCE/projects/crypto-sector-flow/src/fetch_btc_2025_funding.py)
