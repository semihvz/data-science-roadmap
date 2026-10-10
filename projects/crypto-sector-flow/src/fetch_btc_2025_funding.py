import urllib.request
import json
import datetime
import time
import os

OUTPUT_DIR = "/home/smhvz/Desktop/DATA-SCIENCE/projects/crypto-sector-flow/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "btc_2025_funding_rates.json")

start_dt = datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
end_dt = datetime.datetime(2025, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)
start_ts = int(start_dt.timestamp() * 1000)
end_ts = int(end_dt.timestamp() * 1000)

print(f"📡 Binance Futures'tan BTCUSDT 2025 Yılı Fonlama Oranları Çekiliyor...")
print(f"   Aralık: {start_dt.strftime('%Y-%m-%d %H:%M:%S UTC')} -> {end_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")

all_records = []
curr_start = start_ts

while curr_start < end_ts:
    url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime={curr_start}&endTime={end_ts}&limit=1000"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        batch = json.loads(resp.read().decode())
    if not batch:
        break
    all_records.extend(batch)
    if len(batch) < 1000:
        break
    curr_start = batch[-1]["fundingTime"] + 1
    time.sleep(0.1)

# Deduplicate by fundingTime
seen = set()
unique_records = []
for r in all_records:
    ft = r["fundingTime"]
    if ft not in seen and start_ts <= ft <= end_ts:
        seen.add(ft)
        unique_records.append(r)

unique_records.sort(key=lambda x: x["fundingTime"])

# Save to disk
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(unique_records, f, indent=2)

print(f"✅ Başarıyla {len(unique_records)} adet kayıt çekildi ve kaydedildi: {OUTPUT_FILE}\n")

rates = [float(x["fundingRate"]) for x in unique_records]
pos = [r for r in rates if r > 0]
neg = [r for r in rates if r < 0]
zero = [r for r in rates if r == 0]

print("=" * 70)
print("📊 2025 YILI BTCUSDT FONLAMA ORANI (FUNDING RATE) GENEL İSTATİSTİKLERİ")
print("=" * 70)
print(f"Toplam Dönem Sayısı (8 Saatlik) : {len(rates)} adet (Yılın tam 365 günü)")
print(f"Pozitif Fonlama Dönemi (Boğa/Long) : {len(pos)} adet (%{len(pos)/len(rates)*100:.1f})")
print(f"Negatif Fonlama Dönemi (Ayı/Short) : {len(neg)} adet (%{len(neg)/len(rates)*100:.1f})")
print(f"Nötr Dönem (0.0000%)               : {len(zero)} adet")
print(f"Yıllık Ortalama Fonlama Oranı      : %{sum(rates)/len(rates)*100:.5f} (Dönem Başına)")
print(f"Yıllık Kümülatif Fonlama Maliyeti  : %{sum(rates)*100:.2f} (Long taşıma maliyeti)")

# Extremes
sorted_by_rate = sorted(unique_records, key=lambda x: float(x["fundingRate"]))

print("\n" + "=" * 70)
print("🔥 2025 YILININ EN EKSTREM 5 NEGATİF DÖNEMİ (Aşırı Korku / Short Squeeze)")
print("=" * 70)
for r in sorted_by_rate[:5]:
    dt = datetime.datetime.fromtimestamp(r["fundingTime"] / 1000, tz=datetime.timezone.utc)
    rate_val = float(r["fundingRate"]) * 100
    price_val = float(r["markPrice"])
    print(f"  • {dt.strftime('%Y-%m-%d %H:%M UTC')} | Rate: %{rate_val:.4f} | Mark Price: ${price_val:,.2f}")

print("\n" + "=" * 70)
print("🚀 2025 YILININ EN EKSTREM 5 POZİTİF DÖNEMİ (Aşırı Coşku / Boğa Zirvesi)")
print("=" * 70)
for r in sorted_by_rate[-5:]:
    dt = datetime.datetime.fromtimestamp(r["fundingTime"] / 1000, tz=datetime.timezone.utc)
    rate_val = float(r["fundingRate"]) * 100
    price_val = float(r["markPrice"])
    print(f"  • {dt.strftime('%Y-%m-%d %H:%M UTC')} | Rate: %{rate_val:.4f} | Mark Price: ${price_val:,.2f}")

# Monthly breakdown
print("\n" + "=" * 70)
print("📅 2025 AY AY ORTALAMA FONLAMA ORANLARI VE BTC FİYATLARI")
print("=" * 70)
monthly = {}
for r in unique_records:
    dt = datetime.datetime.fromtimestamp(r["fundingTime"] / 1000, tz=datetime.timezone.utc)
    m = dt.strftime('%Y-%m')
    if m not in monthly:
        monthly[m] = []
    monthly[m].append((float(r["fundingRate"]), float(r["markPrice"])))

for m, vals in sorted(monthly.items()):
    avg_r = sum(v[0] for v in vals) / len(vals) * 100
    avg_p = sum(v[1] for v in vals) / len(vals)
    pos_sub = sum(1 for v in vals if v[0] > 0)
    print(f"  {m} | Ort. Rate: %{avg_r:>+7.4f} | Ort. Fiyat: ${avg_p:>10,.2f} | Pozitif/Negatif: {pos_sub:>2}/{len(vals)-pos_sub:<2}")
