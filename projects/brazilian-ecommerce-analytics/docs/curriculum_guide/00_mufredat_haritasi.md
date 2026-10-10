# 🎓 Olist E-Ticaret Veri Analitiği Müfredat Eşleme Rehberi (Curriculum Roadmap)

Bu rehber, **Olist Brezilya E-Ticaret Analitiği** projesinin, **15 Modüllük Veri Analisti Uzmanlık Müfredatı (Data Analyst Track)** ile nasıl birebir örtüştüğünü gösteren ana yol haritasıdır.

Bir veri analisti adayı veya profesyonel, teorik olarak öğrendiği tüm ders konularını bu projede çalışan kodlar, SQL sorguları, istatistiksel modeller ve yönetici sunumlarıyla somutlaştırmış olur.

---

## 🗺️ Müfredat - Proje Eşleme Matrisi

| Müfredat Modülü | Modül Başlığı | Projedeki Somut Karşılığı | İlgili Rehber Dosyası |
| :--- | :--- | :--- | :--- |
| **Modül 1** | **İş Problemleri & KPI Tanımlama** | Pazar yeri iş modeli, GMV vs Net Gelir ayrımı, SLA gecikme oranı, AOV, North Star Metriği | [`01_is_problemi_ve_kpi_mimarisi.md`](01_is_problemi_ve_kpi_mimarisi.md) |
| **Modül 2** | **İleri Excel & Finansal Modelleme** | Gelir projeksiyonları, taksitli sepet çarpanları, lojistik maliyet optimizasyon marjları | [`01_is_problemi_ve_kpi_mimarisi.md`](01_is_problemi_ve_kpi_mimarisi.md) |
| **Modül 3** | **Veri Temelleri, Kalitesi & ETL** | 9 ham CSV'nin audit edilmesi, çoğullanan müşteri id'leri, null analizi, centroid tekilleştirme | [`02_veri_kalitesi_ve_iliskisel_veritabani.md`](02_veri_kalitesi_ve_iliskisel_veritabani.md) |
| **Modül 4** | **İlişkisel Veritabanları & ERD** | 3. Normal Form (3NF) SQLite şeması, PK/FK kısıtları, B-Tree indeksleme stratejisi | [`02_veri_kalitesi_ve_iliskisel_veritabani.md`](02_veri_kalitesi_ve_iliskisel_veritabani.md) |
| **Modül 5** | **SQL Temel** | `SELECT`, `WHERE`, `GROUP BY`, `HAVING`, agregasyon fonksiyonları (`SUM`, `AVG`, `COUNT`) | [`03_sql_uzmanligi_temelden_ileriye.md`](03_sql_uzmanligi_temelden_ileriye.md) |
| **Modül 6** | **SQL Orta** | `INNER JOIN`, `LEFT JOIN`, alt sorgular (Subqueries), sipariş-ödeme-yorum birleştirmeleri | [`03_sql_uzmanligi_temelden_ileriye.md`](03_sql_uzmanligi_temelden_ileriye.md) |
| **Modül 7** | **SQL İleri** | Window Functions (`LAG`, `NTILE`, `SUM() OVER`), CTE'ler (`WITH`), Analitik Görünümler (`VIEW`) | [`03_sql_uzmanligi_temelden_ileriye.md`](03_sql_uzmanligi_temelden_ileriye.md) |
| **Modül 8** | **İstatistik & Olasılık** | Sağa çarpık gelir dağılımı, aykırı değer analizi, gecikme ile CSAT arasındaki korelasyon (r = -0.58) | [`04_istatistik_ve_kesifsel_veri_analizi.md`](04_istatistik_ve_kesifsel_veri_analizi.md) |
| **Modül 9** | **Python ile Veri Analizi** | Pandas ile tarih-zaman manipülasyonu, `qcut` quantile gruplama, vektörize metrik hesaplama | [`04_istatistik_ve_kesifsel_veri_analizi.md`](04_istatistik_ve_kesifsel_veri_analizi.md) |
| **Modül 10** | **Veri Görselleştirme** | Seaborn & Matplotlib yayın grafikleri, Plotly interaktif Treemap ve ikili eksen çizimleri | [`05_ileri_analitik_rfm_cohort_pareto.md`](05_ileri_analitik_rfm_cohort_pareto.md) |
| **Modül 11** | **Business Intelligence (BI)** | Streamlit interaktif analitik web paneli (`app.py`), filtreler, KPI kartları, canlı SQL Studio | [`05_ileri_analitik_rfm_cohort_pareto.md`](05_ileri_analitik_rfm_cohort_pareto.md) |
| **Modül 12** | **İleri Analitik Teknikler** | RFM Müşteri Segmentasyonu, Aylık Kohort Tutundurma Matrisi, Pareto 80/20 & ABC Analizi | [`05_ileri_analitik_rfm_cohort_pareto.md`](05_ileri_analitik_rfm_cohort_pareto.md) |
| **Modül 13** | **AI Destekli Analiz & Otomasyon** | Otomatikleştirilmiş SQL ETL boru hattı, algoritmik kural tabanlı segment playbook'ları | [`03_sql_uzmanligi_temelden_ileriye.md`](03_sql_uzmanligi_temelden_ileriye.md) |
| **Modül 14** | **İş İletişimi & Data Storytelling** | C-Level Stratejik Yönetici Özeti, 5 Eylemsel Büyüme Ayağı, Sayılarla İkna Sanatı | [`06_veri_hikayeciligi_ve_mulakat_rehberi.md`](06_veri_hikayeciligi_ve_mulakat_rehberi.md) |
| **Modül 15** | **Portföy & Mülakat Hazırlığı** | STAR Metodolojisi ile proje anlatımı, mülakatta sorulabilecek 15 teknik ve iş sorusu | [`06_veri_hikayeciligi_ve_mulakat_rehberi.md`](06_veri_hikayeciligi_ve_mulakat_rehberi.md) |

---

## 🎯 Bu Rehber Serisini Nasıl Kullanmalısınız?

1. **Öğrenme Amacıyla:** Eğer bir veri analitiği eğitimi alıyorsanız, her dersi bitirdiğinizde ilgili dökümantasyonu açıp projedeki SQL veya Python kodlarını inceleyin.
2. **Portföyünüzü Güçlendirmek İçin:** GitHub reponuzda veya CV'nizde Olist projesinden bahsederken buradaki mimariyi, iş terimlerini ve metodolojileri referans gösterin.
3. **Teknik Mülakatlara Hazırlık İçin:** Mülakat öncesinde `06_veri_hikayeciligi_ve_mulakat_rehberi.md` dosyasındaki soru-cevapları ve STAR hikayesini çalışın.
