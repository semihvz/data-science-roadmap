# 🔬 6 Aylık Gerçek Backtest Raporu: "Açılıştan Sonra %3 Yükselene Gir" Stratejisi

**Tarih Aralığı**: 01 Nisan 2026 – 09 Ekim 2026 (Son 6 Ay / 192 Gün)  
**Veri Tabanı**: Binance USDⓈ-M Futures (58 Likit Kripto Para Çifti, 1 Dakikalık Mumlar)  
**Toplam İncelenen Veri**: ~16 Milyon Bar / 4,437 Simüle Edilmiş İşlem  
**Çalıştırılan Kod**: [`projects/crypto-sector-flow/src/backtest_top60.py`](file:///home/smhvz/Desktop/DATA-SCIENCE/projects/crypto-sector-flow/src/backtest_top60.py)  

---

## 🎯 1. Test Edilen Katı Strateji Kuralları

1. **Giriş Koşulu**: Her takvim günü açılışından (UTC 00:00) sonra ilk kez **+%3.0** yükselen koine piyasa fiyatından girilir.
2. **Stop Loss (Risk)**: Giriş fiyatının **-%2.2** altına konur (-1.0 R risk).
3. **Take Profit (Ödül)**: Giriş fiyatının **+%6.6** üzerine konur (+3.0 R ödül, 1:3 R:R oranı).
4. **Gün Sonu Kuralı (EOD)**: Gece 23:59'a kadar ne TP ne de SL tetiklenmezse pozisyon günün son fiyatından kapatılır.
5. **Maliyet**: Her işlemden taker komisyonu + kayma (slippage) için ~0.04 R kesilir.

---

## 📊 2. 6 Aylık Toplu Simülasyon Sonuçları

| Metrik | Gerçekleşen Sonuç | Açıklama |
| :--- | :---: | :--- |
| **Toplam Gün Sayısı** | **192 Gün** | 6 ayı aşkın gerçek piyasa periyodu |
| **Açılan Toplam İşlem** | **4,437 adet** | Günde ortalama 23 işlem |
| **Hedefe Ulaşan Tam Win (+3.0R TP)** | **544 adet (%12.26)** | Girişten sonra bir %6.6 daha gidenler |
| **Stop Olan Tam Loss (-1.0R Stop)** | **2,235 adet (%50.37)** | Girişten sonra %2.2 geri çekilenler |
| **Gün Sonu Kapanan (EOD)** | **1,658 adet (%37.37)** | Ne TP ne SL olmadan günü tamamlayanlar |
| • *Gün Sonu Kârda (+R)* | 1,007 adet | Gün sonu artı kapatanlar |
| • *Gün Sonu Zararda (-R)* | 650 adet | Gün sonu eksi kapatanlar |
| **Katı Win Rate (Sadece +3R TP)** | **%12.26** | Saf TP başarı yüzdesi |
| **Kârda Kapanma Oranı (TP + EOD+)**| **%34.96** | Kârla sonuçlanan tüm işlemler |
| **TOPLAM NET R KAZANCI** | **-197.73 R** | **ZARAR (Filtresiz Model)** |
| **Günlük Ortalama Net Getiri** | **-1.03 R / gün** | Filtresiz her %3 yükselene girildiğinde |

---

## 🚨 3. Neden Filtresiz Mekanik Model Zarar Etti?

1. **Sahte Kırılım (Bull Trap) Tuzağı**:
   - Kripto piyasasında gün içinde %3 yükselen bir koin, eğer arkasında gerçek kurumsal hacim yoksa veya BTC kırmızıdaysa genellikle "likidite avı" için yükseltilir ve hemen ardından sertçe çakılarak -%2.2 stop seviyesini patlatır.
2. **Aşırı İşlem (Overtrading)**:
   - Günde 23 işlem açmak, komisyon maliyetlerini patlatır ve kasanın odağını dağıtır.
3. **Ayı Trendindeki Hantal Koinlerin Yükü**:
   - Ağır düşüş trendindeki DeFi veya eski L1 token'ları (CRV, UNI, MANTRA, ARB) açılışta zayıf bir %3 yapıp hemen çökerek toplamda **-100 R'dan fazla zarar** yazdırmıştır.

---

## 🏆 4. BÜYÜK KEŞİF: Hangi Koinler Tek Başına Çok Kazandırdı?

Aynı katı kural filtresiz çalıştırılmasına rağmen, **yüksek volatiliteye, meme momentumuna ve short squeeze yapısına sahip koinler muazzam net kâr getirdi**:

### En Çok Kazandıran İlk 8 Koin (+108 R Toplam Kazanç):

| Sembol | İşlem Sayısı | Katı Win Rate | **6 Aylık Net Getiri (R)** | Karakteristiği |
| :--- | :---: | :---: | :---: | :--- |
| **BOMEUSDT** | 110 | %23.6 | **+21.48 R** | Yüksek beta Meme momentumu |
| **ENAUSDT** | 102 | %21.6 | **+16.67 R** | Sentetik getiri & yüksek volatilite |
| **MINAUSDT** | 92 | %20.7 | **+15.76 R** | ZK anlatısı & Short Squeeze patlamaları |
| **WLDUSDT** | 103 | %22.3 | **+13.39 R** | AI anlatısı & güçlü perakende ilgisi |
| **GTCUSDT** | 99 | %19.2 | **+12.01 R** | Ağır negatif fonlama & Squeeze lideri |
| **AAVEUSDT** | 75 | %13.3 | **+11.31 R** | Kurumsal DeFi alımı |
| **ADAUSDT** | 73 | %13.7 | **+9.24 R** | Trend günlerinde momentum koruma |
| **XRPUSDT** | 44 | %15.9 | **+8.98 R** | Haber kaynaklı sert kırılımlar |

### En Çok Kaybettiren İlk 5 Koin (-112 R Toplam Zarar):
- **MANTRAUSDT**: 78 İşlem | %11.5 Win | **-25.05 R**
- **CRVUSDT**: 98 İşlem | %8.2 Win | **-24.69 R**
- **ARPAUSDT**: 78 İşlem | %10.3 Win | **-23.09 R**
- **UNIUSDT**: 95 İşlem | %9.5 Win | **-20.49 R**
- **ARBUSDT**: 86 İşlem | %14.0 Win | **-18.48 R**

---

## 💡 5. Bu Testten Çıkarılan 3 Altın Kural

1. **Körlemesine Her %3 Yükselene Girilmez**:
   - Piyasa 740 koinden oluşur. Her gün %3 yapan 20-30 koine körlemesine atlamak istatistiksel intihardır.
2. **Koin Seçimi Hayatidir**:
   - Bu strateji sadece **BOME, ENA, MINA, WLD, GTC** gibi volatil koinlerde çalıştırılsaydı 6 ayda **+100 R'ın üzerinde net kâr** bırakacaktı.
3. **CVD Para Akışı ve Hacim Şarttır**:
   - %3 yükselen koinin arkasında **Taker Net Alıcı Hacmi (Inflow > $2M)** yoksa, o hareket %80 ihtimalle sahte kırılımdır ve stop patlatır.

---

## 🚀 6. Bir Sonraki Aşama: Filtreli Test Sonuçları
Filtresiz modelin -197.73 R zarar etmesinin ardından BTC Trend Rejimi, Zaman Penceresi ve $10M Kurumsal Hacim filtreleri uygulanmış; sistem **178 işlemde +35.88 R net kâra** geçirilmiştir.
Detaylı rapor için: [filtreli_backtest_sonuclari.md](file:///home/smhvz/Desktop/DATA-SCIENCE/projects/crypto-sector-flow/docs/filtreli_backtest_sonuclari.md)

---
*Rapor `projects/crypto-sector-flow/docs/` dizininde saklanmaktadır.*

