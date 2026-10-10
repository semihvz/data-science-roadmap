# ⚡ Kripto Sektörel Para Akımı & Sermaye Rotasyonu Radarı

Binance USDⓈ-M Futures piyasasında işlem gören kripto para birimlerini sektörlerine göre (Yapay Zeka, ZK/Gizlilik, Katman-2, RWA, DeFi, Memes, L1 vb.) gruplayarak, **anlık Taker Alıcı/Satıcı Hacim Deltası (Net CVD / Net Inflow USD)** üzerinden **toplu para akışını an be an izleyen ve raporlayan profesyonel kantitatif analiz motoru**.

---

## 📌 Neden Bu Yöntem? (Matematiksel Mantık)

Basit fiyat artışları yanıltıcı olabilir (düşük hacimli sığ tahtalarda manipülasyonla fiyat yükselebilir). 

Bu motor, doğrudan **gerçekleşen piyasa alımları ve piyasa satışları arasındaki likidite farkına (Net Inflow)** bakar:

$$\text{Taker Satıcı Hacmi} = \text{Toplam Hacim (USDT)} - \text{Taker Alıcı Hacmi (USDT)}$$

$$\text{Net Para Girişi (USD)} = \text{Taker Alıcı Hacmi} - \text{Taker Satıcı Hacmi}$$

- **$\text{Net Inflow} > 0$**: Kurumsal / agresif alıcılar piyasaya doğrudan para sokuyor (Alım Baskısı).
- **$\text{Net Inflow} < 0$**: Piyasadan nakde kaçış var veya pasif alıcılara mal boşaltılıyor (Satış / Dağıtım).

---

## 📁 Proje Dizin Yapısı

```text
projects/crypto-sector-flow/
├── README.md                      # Proje Dokümantasyonu
├── requirements.txt               # Gerekli Kütüphaneler
├── config/
│   └── sectors.json               # Sektörler ve Taranacak Likit Binance Vadeli Çiftleri
└── src/
    ├── flow_calculator.py         # Binance Klines Taker Alıcı/Satıcı Delta Hesaplayıcı
    ├── sector_engine.py           # Çok İş Parçacıklı Sektörel Toplama ve Sıralama Motoru
    ├── anomalies.py               # Ani Sermaye Akışı ve Anomali Dedektörü
    ├── cli_monitor.py             # Canlı Otomatik Yenilenen Terminal Ekranı (Rich CLI)
    └── dashboard.py               # Streamlit İnteraktif Web Paneli & Grafikler
```

---

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları Yükleyin
```bash
pip install -r projects/crypto-sector-flow/requirements.txt
```

### 2. Canlı Terminal Ekranını (CLI Radar) Başlatın

Her 20 saniyede bir terminalde otomatik güncellenen canlı borsa ekranı:

```bash
# 1 Saatlik standart akış taraması
python3 projects/crypto-sector-flow/src/cli_monitor.py

# Son 15 dakikalık ani para girişlerini yakalamak için
python3 projects/crypto-sector-flow/src/cli_monitor.py --timeframe 15m

# Tek seferlik tarama yapıp çıkmak için
python3 projects/crypto-sector-flow/src/cli_monitor.py --once
```

### 3. İnteraktif Web Dashboard'unu Başlatın

Grafiksel çubuk haritaları ve sektör içi token dağılımını tarayıcıda izlemek için:

```bash
streamlit run projects/crypto-sector-flow/src/dashboard.py
```

---

## ⚙️ Sektörleri Özelleştirme

Yeni bir sektör eklemek veya yeni bir koin dahil etmek için [`config/sectors.json`](./config/sectors.json) dosyasını düzenlemeniz yeterlidir:

```json
"AI & Big Data": {
  "description": "Yapay zeka modelleri ve GPU hesaplama ağları",
  "symbols": ["NEARUSDT", "WLDUSDT", "ARPAUSDT", "RENDERUSDT", "FETUSDT"]
}
```
Motor, konfigürasyonu otomatik okuyarak dinamik olarak hesaplamaya dahil eder.
