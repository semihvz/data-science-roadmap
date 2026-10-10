# Production-Grade Binance Futures Trade Simulation Engine — Master Implementation Prompt

# ROLE

Sen kıdemli bir:

- C++ Systems Engineer
- Quantitative Backtesting Engineer
- High-Performance Computing / Data Processing Engineer
- Database Performance Engineer
- Reliability Engineer

olarak hareket edeceksin.

Görevin Binance USDⓈ-M Futures piyasasına ait çok büyük **1 dakikalık OHLCV veri setleri** üzerinde çalışan, production-grade, deterministic, auditable, reproducible, crash-safe ve yüksek performanslı bir **trade simulation engine** tasarlamak ve eksiksiz şekilde implement etmektir.

Sistem:

- C++20 veya daha yeni standartla yazılacak,
- her sembol için ayrı SQLite database oluşturacak,
- milyonlarca bağımsız trade simüle edecek,
- peak RSS RAM kullanımını varsayılan olarak **3072 MB altında tutacak**,
- look-ahead bias üretmeyecek,
- sonuçları brute-force reference engine ile doğrulayabilecek,
- yarım kalan simulation run'larını güvenli biçimde resume edebilecek,
- üretilen her trade'in neden o sonucu aldığını daha sonra audit etmeye imkân verecektir.

Örnek database çıktıları:

```text
BTCUSDT.sqlite
ETHUSDT.sqlite
SOLUSDT.sqlite
```

---

# 1. PROJENİN TEMEL AMACI

Bu sistem bir trading strategy veya trading signal engine değildir.

Her geçerli 1 dakikalık candle kapanışında birbirinden tamamen bağımsız şekilde:

- 1 LONG
- 1 SHORT

pozisyon açılacaktır.

Eğer bir contiguous data segment içerisinde `N` adet entry için kullanılabilir candle varsa yaklaşık `2N` bağımsız trade üretilir.

Önemli:

- Bir trade'in kapanmasını bekleyip yeni trade açılmayacaktır.
- Her candle close yeni bağımsız LONG ve SHORT entry üretir.
- Aynı anda açık olan pozisyon sayısında limit yoktur.
- Pozisyonlar birbirini etkilemez.
- Portfolio accounting yapılmaz.
- Position sizing yapılmaz.
- Capital constraint yoktur.
- Trade concurrency limiti yoktur.

Amaç milyonlarca bağımsız trade sonucunu sonradan veri bilimi ve istatistik yöntemleriyle inceleyerek:

- kaliteli trade dağılımları,
- piyasa koşulları,
- MAE/MFE davranışları,
- holding-period dağılımları,
- asymmetric market behavior,
- regime özellikleri,
- potansiyel predictive feature'lar,
- gelecekte test edilebilecek hipotezler

bulmaktır.

Bu nedenle **simulation correctness veri işleme hızından daha önemlidir.**

---

# 2. ÖNCELİK SIRASI

Engineering kararlarında aşağıdaki sıralamaya kesinlikle uy:

1. Simulation correctness
2. No look-ahead bias
3. Deterministic results
4. Data integrity
5. Auditability
6. Reproducibility
7. Crash safety
8. RAM <= configured hard limit
9. Performance
10. Maintainability

Daha yüksek hız uğruna yanlış, yaklaşık veya belirsiz simulation sonucu üretme.

---

# 3. CLI PARAMETRELERİ

Program en az aşağıdaki parametreleri desteklemelidir:

```text
--input
--output
--symbol
--timeframe
--sl
--rr
--threads
--batch-size
--memory-limit-mb
--intrabar-policy
--gap-execution-model
--calculate-excursions
--strict-validation
--repair-order
--unsafe-fast-mode
--resume
```

Varsayılanlar:

```text
timeframe                  = 1m
memory_limit_mb            = 3072
intrabar_policy            = sl-first
calculate_excursions       = true
strict_validation          = true
repair_order               = false
unsafe_fast_mode           = false
resume                     = true
maker_fee                  = 0
taker_fee                  = 0
entry_slippage_bps         = 0
exit_slippage_bps          = 0
```

Örnek:

```bash
simulator \
  --input ./data/BTCUSDT.csv \
  --output ./db \
  --symbol BTCUSDT \
  --sl 0.005 \
  --rr 3.0 \
  --threads 8 \
  --batch-size 10000 \
  --memory-limit-mb 3072 \
  --intrabar-policy sl-first \
  --gap-execution-model barrier \
  --calculate-excursions true \
  --strict-validation true
```

İstenirse TOML/JSON/YAML config file desteği eklenebilir; ancak CLI her durumda çalışmalıdır.

CLI parameter validation yap.

Örneğin:

```text
0 < SL < 1
RR > 0
threads >= 1
batch_size >= 1
memory_limit_mb > 0
```

Geçersiz parametrelerde fail-fast yap.

---

# 4. SL / TP HESABI

Girdi:

```text
stop_loss_percent = sl_pct
risk_reward_ratio = RR
```

TP otomatik:

```text
tp_pct = sl_pct * RR
```

Örnek:

```text
SL = 0.005
RR = 3

TP = 0.015
```

LONG:

```text
SL = entry_price * (1 - sl_pct)
TP = entry_price * (1 + tp_pct)
```

SHORT:

```text
SL = entry_price * (1 + sl_pct)
TP = entry_price * (1 - tp_pct)
```

---

# 5. PRICE REPRESENTATION

Floating-point boundary hatalarına karşı fiyat modelini bilinçli seç.

Tercih sırası:

1. symbol tick size biliniyorsa fixed-point `int64_t`
2. decimal scale biliniyorsa fixed-point `int64_t`
3. bunlar bilinmiyorsa dikkatli `double`
4. yalnız gerektiği yerde `long double`

Tick-size tabanlı representation mümkünse:

```text
price_ticks = round(price / tick_size)
```

SL/TP hesaplarında kullanılan rounding policy açık şekilde tanımlanmalı.

Örneğin:

```text
price_model = FIXED_POINT_TICKS
price_scale
tick_size
rounding_policy
```

metadata/runs içerisinde saklanmalıdır.

Threshold equality **hit kabul edilmelidir.**

Örnek:

```text
high == TP → TP hit
low == SL  → SL hit
```

Decimal input parse edilirken mümkünse binary floating-point üzerinden gereksiz çift dönüşüm yapma.

---

# 6. KRİTİK ENTRY KURALI

Trade candle close üzerinde açılır.

Candle index `i` için:

```text
entry_price = close[i]
```

Ancak:

**candle[i].high ve candle[i].low kesinlikle bu trade'in SL/TP detection işleminde kullanılamaz.**

İlk kontrol edilen candle:

```text
i + 1
```

olmalıdır.

Yani:

```text
search_range = [i + 1, segment_end]
```

Bu sistemin en kritik no-look-ahead kuralıdır.

Bu invariant:

- production engine,
- brute-force reference engine,
- unit tests,
- randomized tests

tarafından açık şekilde korunmalıdır.

---

# 7. TIMESTAMP SEMANTICS

Input timestamp semantics açıkça tanımlanmalıdır.

Binance open-time formatında:

```text
candle_open_time = timestamp[i]
candle_close_time = timestamp[i] + timeframe
```

1m için:

```text
entry_bar_open_time = timestamp[i]
entry_time = timestamp[i] + 60 seconds
```

Database içerisinde hem input timestamp semantics hem entry timestamp semantics saklanmalıdır.

Örneğin:

```text
input_timestamp_semantics = CANDLE_OPEN_TIME
entry_time_semantics = CANDLE_CLOSE_BOUNDARY
timeframe_seconds = 60
```

Timestamp unit de metadata içerisinde saklanmalıdır:

```text
milliseconds
microseconds
seconds
```

Internal representation için mümkünse UTC epoch `int64_t` kullan.

Timezone-dependent logic kullanma.

---

# 8. BARS_HELD TANIMI

`bars_held` kesin olarak tanımlansın.

Trade `i` candle kapanışında açılmış ve `j` candle içerisinde kapanmışsa:

```text
bars_held = j - i
```

Dolayısıyla ilk sonraki candle içerisinde kapanan trade:

```text
bars_held = 1
```

olur.

Bu semantic README ve metadata içerisinde açıkça belgelenmelidir.

---

# 9. EXIT ALGORİTMASI

Trade açıldıktan sonra yalnız gelecekteki candle'lar değerlendirilir.

LONG:

```text
TP hit ⇔ high >= TP
SL hit ⇔ low  <= SL
```

SHORT:

```text
TP hit ⇔ low  <= TP
SL hit ⇔ high >= SL
```

İlk threshold crossing exit kabul edilir.

---

# 10. AYNI CANDLE İÇİNDE SL + TP

1 dakikalık OHLC datasından intrabar fiyat sırası bilinemez.

Dolayısıyla aynı candle içerisinde hem SL hem TP seviyesine ulaşılması durumunda default politika:

```text
SL FIRST
```

olmalıdır.

LONG:

```text
low <= SL && high >= TP
```

SHORT:

```text
high >= SL && low <= TP
```

durumlarında:

```text
exit_reason = SL_AND_TP_SAME_BAR_SL_PRIORITY
status      = CLOSED
same_bar_sl_tp = 1
intrabar_ambiguous = 1
```

olarak kaydet.

Bu politika config hash'in parçası olmalıdır.

İleride farklı policy eklenebilecek şekilde architecture tasarlanabilir:

```text
SL_FIRST
TP_FIRST
AMBIGUOUS_ONLY
```

Ancak default kesinlikle:

```text
SL_FIRST
```

olacaktır.

---

# 11. EXIT TIME BELİRSİZLİĞİ

OHLCV 1m data kullanıldığından barrier'ın candle içerisinde hangi saniyede gerçekleştiği bilinemez.

Sistem uydurma exact exit timestamp üretmemelidir.

Sakla:

```text
exit_bar_open_time
exit_bar_index
bars_held
duration_lower_bound_seconds
duration_upper_bound_seconds
duration_minutes_approx
```

Trade `i` candle close'da açılıp `j` candle içinde kapanmışsa ve timeframe 60 saniyeyse:

```text
entry_time = close_time(i)

exit event interval:
[open_time(j), close_time(j)]
```

Buna göre duration:

```text
duration_lower_bound_seconds =
    open_time(j) - entry_time

duration_upper_bound_seconds =
    close_time(j) - entry_time
```

Gerekirse:

```text
duration_minutes_approx = bars_held
```

kullanılabilir.

Ancak bunun approximate OHLC-based duration olduğu metadata içerisinde belirtilmelidir.

---

# 12. DATA GAP POLICY

1m timeframe için normalde:

```text
timestamp[i+1] - timestamp[i] == 60 seconds
```

beklenir.

Timestamp gap bulunursa dataset **contiguous segmentlere** ayrılmalıdır.

Bir trade hiçbir koşulda data gap üzerinden devam ettirilmemelidir.

Örneğin trade segment sonuna kadar TP/SL olmadan geldiyse:

```text
status = UNRESOLVED_DUE_TO_GAP
exit_reason = DATA_GAP
```

olarak kaydet.

Ayrıca:

```text
data_segment_id
```

sakla.

Simülasyon search yapıları segment boundary'lerini kesinlikle aşmamalıdır.

---

# 13. DATASET END POLICY

Trade segment içerisinde herhangi bir barrier'a ulaşmadan dataset sonuna geldiyse:

```text
status = OPEN_AT_END_OF_DATA
exit_reason = END_OF_DATA
```

kaydet.

Bu trade silinmemelidir.

Alanlar:

```text
exit_price = NULL
last_available_price
last_available_timestamp
unrealized_pnl_pct
```

saklanabilir.

---

# 14. GAP-THROUGH-BARRIER EXECUTION

Yeni candle open değeri barrier'ın ötesinde olabilir.

Örnek LONG stop:

```text
SL = 100
next open = 98
```

Sistem en az iki execution modelini desteklemeye uygun tasarlanmalıdır.

## BARRIER_PRICE_MODEL

Barrier hit olmuş kabul edilir ve:

```text
exit_price = configured barrier
```

## CONSERVATIVE_GAP_MODEL

Adverse gap durumunda gerçek candle open dikkate alınır.

Örneğin LONG stop:

```text
open < SL
exit_price = open
```

SHORT stop:

```text
open > SL
exit_price = open
```

Favorable TP gap handling de aynı şekilde açıkça belgelenmelidir.

Default:

```text
BARRIER_PRICE_MODEL
```

olsun.

Bunun sebebi OHLC barrier study'nin deterministic ve nominal R interpretation'ını korumaktır.

Her trade için:

```text
gap_through_barrier
```

sakla.

Kullanılan model runs tablosuna yazılsın.

---

# 15. MAE / MFE

Optional parameter:

```text
--calculate-excursions=true|false
```

Default:

```text
true
```

LONG için trade açıkken:

```text
max_high = maksimum HIGH
min_low  = minimum LOW

MFE = max_high - entry
MAE = entry - min_low
```

SHORT için:

```text
MFE = entry - min_low
MAE = max_high - entry
```

Üret:

```text
mfe_percent
mae_percent
mfe_r
mae_r
```

Excursion window semantic'i kesin olarak belgele.

Default olarak entry candle high/low dahil edilmemelidir.

Window:

```text
[i+1, exit_bar]
```

olmalıdır.

Exit candle dahil edilir.

Ancak exit sonrasında candle içerisinde gerçekleşmiş olabilecek hareket OHLC'den ayrıştırılamadığı için `MFE/MAE` değerlerinin exit candle için intrabar belirsizlik taşıdığı metadata içerisinde belirtilmelidir.

Bu analytics hiçbir durumda exit decision'ı değiştirmemelidir.

---

# 16. FEES VE SLIPPAGE

Default:

```text
maker_fee = 0
taker_fee = 0
entry_slippage_bps = 0
exit_slippage_bps = 0
```

Architecture ileride desteklemelidir:

```text
gross_pnl_pct
net_pnl_pct

gross_r
net_r

entry_fee
exit_fee
total_fee
```

Simulation barrier detection logic fee/slippage'dan bağımsız kalmalıdır.

---

# 17. R DEFINITION

```text
1R = nominal stop distance
```

Normal nominal sonuç:

```text
TP → +RR
SL → -1R
```

Ancak gap/slippage/fee modeli actual result'ı değiştirebilir.

Bu nedenle mümkünse ayrı sakla:

```text
nominal_r
gross_r
net_r
```

---

# 18. PERFORMANCE — O(N²) YASAK

Production engine içerisinde her entry için gelecekteki tüm candle'ları sırayla tarayan:

```text
O(N²)
```

yaklaşım yasaktır.

Brute force yalnız reference/testing engine içerisinde kullanılabilir.

Production engine mümkünse:

```text
O(N log N)
```

veya daha iyi olmalıdır.

---

# 19. OPTIMIZED SEARCH ALGORITHM

Her contiguous segment için immutable threshold-search structure oluştur.

Production implementation için memory/correctness dengesine göre uygun çözümü seç.

Örneğin segment tree tabanlı yapı kullanılabilir.

HIGH array için:

```text
first index >= L where HIGH >= threshold
```

LOW array için:

```text
first index >= L where LOW <= threshold
```

query'lerini destekle.

LONG:

```text
tp_idx = first HIGH >= TP
sl_idx = first LOW  <= SL
```

SHORT:

```text
tp_idx = first LOW  <= TP
sl_idx = first HIGH >= SL
```

Sonuç:

```text
min(tp_idx, sl_idx)
```

Indexler aynı ise:

```text
SL priority
```

uygula.

Daha hızlı ve daha memory-efficient offline algorithm bulursan onu tercih edebilirsin.

Ancak:

- correctness proof,
- complexity analysis,
- memory analysis,
- brute-force equivalence

sağlanmalıdır.

Algorithm seçimini `docs/algorithm.md` içerisinde gerekçelendir.

---

# 20. RANGE QUERY + EXCURSIONS

MAE/MFE aktifse exit index bulunduğunda range min/max sorguları mümkünse aynı immutable indexing structure üzerinden yapılmalıdır.

Örneğin:

```text
range_max(high, i+1, exit_idx)
range_min(low,  i+1, exit_idx)
```

Bu sayede ikinci kez linear scan yapma.

---

# 21. MEMORY HARD LIMIT

Default hard limit:

```text
3072 MB peak RSS
```

Trade sonuçlarının tamamını RAM'de biriktirme.

Örnek architecture:

```text
Reader
  ↓
Validation
  ↓
Compact Candle Arrays
  ↓
Immutable Search Index
  ↓
Simulation Workers
  ↓
Bounded Result Queue
  ↓
Dedicated SQLite Writer
```

Queue kesinlikle bounded olmalıdır.

Writer yavaşlarsa producer thread'ler backpressure ile beklemelidir.

Unbounded:

```text
std::vector<TradeResult>
std::queue<TradeResult>
```

kullanma.

Memory budget hesaplamasını explicit yap.

Runtime başlangıcında tahmini:

```text
candle arrays memory
index memory
worker memory
queue memory
SQLite cache memory
safety margin
```

raporla.

Eğer tahmini memory configured limit'i aşacaksa blind execution yerine fail-fast veya daha memory-efficient fallback kullan.

---

# 22. SYMBOL PROCESSING

Default:

```text
1 symbol
→ validate
→ segment
→ build indexes
→ simulate
→ persist
→ validate DB
→ release memory
→ next symbol
```

Birden fazla symbol'ü blind parallel işleme.

Global RAM budget korunmadan symbol-level parallelism açılmamalıdır.

---

# 23. COMPACT DATA LAYOUT

Mümkünse Array-of-Struct yerine cache-friendly Struct-of-Arrays yaklaşımını değerlendir.

Örneğin:

```cpp
timestamps[]
open[]
high[]
low[]
close[]
volume[]
```

Fixed-point mode'da:

```cpp
std::vector<int64_t>
```

tercih edilebilir.

Hot loop içerisinde:

- std::string oluşturma
- std::stringstream
- dynamic polymorphism
- heap allocation
- virtual dispatch
- formatted logging

kullanma.

`TradeResult` mümkün olduğunca POD-like compact struct olsun.

---

# 24. MULTITHREADING

Index immutable ise entry ranges worker thread'ler arasında bölünebilir.

Örneğin:

```text
worker 0 → [0, 999999]
worker 1 → [1000000, 1999999]
...
```

Worker thread'ler SQLite'a doğrudan yazmamalıdır.

Dedicated single writer kullan.

Sonuçlar:

```text
1 thread
2 threads
8 threads
16 threads
```

arasında identical trade semantics üretmelidir.

Database row order determinism zorunlu değildir.

Ancak deterministic trade identity ve içerik zorunludur.

---

# 25. DETERMINISTIC TRADE IDENTITY

Trade identity database insert order'a bağlı olmamalıdır.

Unique logical key:

```text
(run_id, entry_bar_index, side)
```

olmalıdır.

İstersen deterministic `trade_id` üret:

```text
trade_id = function(entry_bar_index, side)
```

veya DB integer PK yanında logical unique constraint kullan.

Zorunlu:

```sql
UNIQUE(run_id, entry_bar_index, side)
```

Bu checkpoint/resume güvenliği için kullanılmalıdır.

---

# 26. DATA VALIDATION

Simulation öncesi minimum kontroller:

```text
timestamp valid
timestamp ordered
timestamp aligned
duplicate timestamp
missing candles
NaN
Infinity
finite OHLC
price > 0
volume >= 0
high >= low
high >= open
high >= close
low <= open
low <= close
close > 0
```

Invalid candle'ı sessizce değiştirme.

Data quality report oluştur.

Strict mode:

```text
critical validation error → abort symbol
```

Optional repair mode varsa yapılan tüm mutation'lar audit log'a yazılmalıdır.

---

# 27. INPUT ORDER

Input sorted kabul edilmemeli.

Validation ile doğrulanmalıdır.

Default:

```text
out-of-order → fail-fast
```

Optional:

```text
--repair-order
```

kullanılabilir.

Ancak milyonlarca row için gereksiz sort yapma.

---

# 28. INPUT FORMAT ARCHITECTURE

Minimum CSV desteği implement et.

Parser:

- streaming veya memory-aware olmalı,
- malformed row detection yapmalı,
- locale-independent decimal parsing kullanmalı,
- quoted CSV corner-case'lerini güvenli ele almalı veya desteklenen CSV formatını README'de açıkça belirtmeli.

Architecture ileride:

```text
CSV
Parquet
binary
```

reader'larının eklenebileceği şekilde interface tabanlı olabilir.

Ancak hot simulation loop runtime polymorphism'e bağımlı olmamalıdır.

---

# 29. DATA SECURITY

Her source dataset için mümkünse SHA-256 hesapla.

Kaydet:

```text
source_file
source_size
source_hash
row_count
first_timestamp
last_timestamp
```

Symbol filename'e doğrudan güvenme.

Sadece whitelist-safe characters kabul et:

```text
A-Z
a-z
0-9
_
-
```

veya daha katı Binance symbol policy kullan.

Reject:

```text
../
/
\
NUL
absolute path
```

Output path canonicalize edilerek database'in output directory dışına çıkması engellenmelidir.

Prepared statements kullan.

SQL string concatenation ile user-controlled değer ekleme.

---

# 30. CONFIG HASH

Canonical deterministic config serialization oluştur.

Hash en az:

```text
symbol
timeframe
SL
RR
TP
intrabar policy
gap policy
gap execution model
price model
price rounding policy
tick size / price scale
fee model
slippage model
calculate excursions
algorithm version
schema version
```

içermelidir.

Serialization locale-independent olmalıdır.

Floating-point config values canonical representation ile hash'lenmelidir.

---

# 31. VERSIONING

Aşağıdakileri ayrı tut:

```text
algorithm_version
database_schema_version
build_version
git_commit_hash
compiler_id
compiler_version
build_type
```

Varsa compile flags da metadata'da tutulabilir.

Bu bilgiler reproducibility için kullanılacaktır.

---

# 32. SQLITE DATABASE

Her symbol ayrı DB:

```text
SYMBOL.sqlite.partial
```

Simulation tamamen başarılı olduğunda:

```text
SYMBOL.sqlite
```

olarak atomic rename yapılır.

Minimum tablolar:

```text
runs
positions
data_quality
metadata
simulation_statistics
checkpoints
```

İstersen ayrıca:

```text
segments
validation_events
```

tabloları ekle.

---

# 33. POSITIONS SCHEMA

En az aşağıdaki alanları destekle:

```text
trade_id
run_id
symbol
side

entry_bar_index
exit_bar_index

entry_bar_open_time
entry_time
exit_bar_open_time

entry_price
exit_price
tp_price
sl_price

sl_percent
tp_percent
risk_reward_ratio

status
exit_reason

bars_held
duration_lower_bound_seconds
duration_upper_bound_seconds
duration_minutes_approx

nominal_r
gross_pnl_percent
net_pnl_percent
gross_pnl_r
net_pnl_r

same_bar_sl_tp
intrabar_ambiguous
gap_through_barrier

data_segment_id

entry_candle_open
entry_candle_high
entry_candle_low
entry_candle_close
entry_candle_volume

exit_candle_open
exit_candle_high
exit_candle_low
exit_candle_close
exit_candle_volume

max_favorable_excursion_pct
max_adverse_excursion_pct
mfe_r
mae_r

last_available_price
last_available_timestamp
unrealized_pnl_pct

created_at

algorithm_version
config_hash
source_data_hash
```

Compact representation kullan:

```text
side:
  +1 LONG
  -1 SHORT
```

Status ve exit reason integer enum olabilir.

Human-readable enum mapping metadata veya documentation içerisinde bulunmalıdır.

Boolean alanlar SQLite INTEGER olabilir.

---

# 34. NULL SEMANTICS

Database'teki NULL davranışlarını açıkça belirle.

Örneğin OPEN_AT_END_OF_DATA:

```text
exit_bar_index           = NULL
exit_bar_open_time       = NULL
exit_price               = NULL
exit_candle_*            = NULL
gross_pnl_percent        = NULL veya unrealized'dan ayrı tutulmalı
```

Unrealized değer realized PnL alanına karıştırılmamalıdır.

DATA_GAP unresolved trade için de aynı şekilde explicit semantic tanımla.

---

# 35. SQLITE WRITE STRATEGY

Her trade için transaction açma.

Kullan:

```text
prepared statement
BEGIN
batch insert
COMMIT
```

Benchmark batch sizes:

```text
5,000
10,000
25,000
```

Default örneğin:

```text
10,000
```

olabilir.

Default durability mode güvenli olmalı.

Benchmark et:

```text
journal_mode = WAL
synchronous = NORMAL
temp_store
cache_size
mmap_size
```

`PRAGMA` değerleri körü körüne kullanma.

RAM budget ile birlikte ayarla.

Sadece açıkça:

```text
--unsafe-fast-mode
```

aktifse:

```text
synchronous=OFF
journal_mode=OFF
```

gibi daha riskli seçeneklere izin ver.

---

# 36. SQLITE INDEX STRATEGY

Bulk insert sırasında analytics indexlerini oluşturma.

Simulation bittikten sonra oluştur:

```text
(run_id, side)
(run_id, exit_reason)
(run_id, entry_time)
(run_id, bars_held)
(run_id, status)
(run_id, data_segment_id)
```

Gerekli unique constraint ise baştan mevcut olabilir:

```text
UNIQUE(run_id, entry_bar_index, side)
```

---

# 37. CRASH RECOVERY

Simulation crash olduğunda sıfırdan başlamak zorunda olmamalıdır.

Checkpoint information:

```text
run_id
segment_id
last_completed_entry_index
last_committed_entry_index
last_committed_trade_id
committed_trade_count
checkpoint_time
```

Ancak checkpoint sadece successful DB transaction commit sonrası ilerletilmelidir.

Checkpoint ve ilgili trade batch mümkünse aynı SQLite transaction içerisinde atomik güncellenmelidir.

Böylece:

```text
trade rows committed
+
checkpoint advanced
```

tek atomic operation olur.

Crash sonrası duplicate üretmemelidir.

Resume idempotent olmalıdır.

---

# 38. RUN STATES

Runs tablosunda explicit state machine kullan:

```text
CREATED
VALIDATING
INDEXING
SIMULATING
FINALIZING
VALIDATING_OUTPUT
COMPLETED
FAILED
INTERRUPTED
```

Ayrıca:

```text
simulation_complete = 0/1
```

sakla.

`.partial` dosyası `COMPLETED` olmadan final filename'e rename edilmemelidir.

---

# 39. ATOMIC FINALIZATION

Başarılı completion için sırasıyla:

1. Simulation tamamlanır.
2. Queue tamamen drain edilir.
3. Writer thread kapanır.
4. Tüm transaction'lar commit edilir.
5. Expected trade counts doğrulanır.
6. Post-run sanity checks yapılır.
7. `PRAGMA integrity_check` çalıştırılır.
8. simulation statistics doğrulanır.
9. run state `COMPLETED` yapılır.
10. `simulation_complete = 1` yapılır.
11. DB connection clean şekilde kapanır.
12. `.partial` dosyası final DB adına atomic rename edilir.

Bu zincirin herhangi bir aşaması başarısızsa `.partial` final output gibi sunulmamalıdır.

---

# 40. BRUTE FORCE REFERENCE ENGINE

Production engine'den tamamen ayrı basit bir implementation oluştur.

Complexity:

```text
O(N²)
```

olabilir.

Ama yalnızca:

- tests
- validation
- real-data spot verification

için kullanılmalıdır.

Brute-force engine mümkün olduğunca basit ve okunabilir olsun.

Production optimization kodunu reuse ederek aynı bug'ı iki engine'e taşıma.

İki implementation mümkün olduğunca bağımsız olmalıdır.

---

# 41. RANDOMIZED PROPERTY TESTING

Valid random OHLCV sequence generator oluştur.

Random generator seed sakla.

Her generated dataset üzerinde:

```text
brute_force_engine
optimized_engine
```

çalıştır.

Her trade için karşılaştır:

```text
side
entry_bar_index
entry_price
SL
TP
exit_bar_index
status
exit_reason
exit_price
same_bar_sl_tp
intrabar_ambiguous
gap_through_barrier
bars_held
MFE/MAE
```

MFE/MAE enabled ise onlar da eşit olmalıdır.

Binlerce random seed çalıştırılabilsin.

Mismatch durumunda seed yazdırılmalı ki vaka birebir reproduce edilebilsin.

---

# 42. ZORUNLU UNIT TESTLER

En az:

1. Entry candle TP görülüyor ama sonraki candle'larda yok → TP sayılmamalı.
2. Entry candle SL görülüyor ama sonraki candle'larda yok → SL sayılmamalı.
3. Next candle yalnız TP → TP.
4. Next candle yalnız SL → SL.
5. Aynı candle SL + TP → SL.
6. LONG hesapları doğru.
7. SHORT hesapları doğru.
8. Exact TP equality → hit.
9. Exact SL equality → hit.
10. Dataset end → OPEN_AT_END_OF_DATA.
11. Timestamp gap → DATA_GAP.
12. Duplicate timestamp → validation failure.
13. Out-of-order timestamp → validation failure.
14. Invalid OHLC → validation failure.
15. NaN → validation failure.
16. Infinity → validation failure.
17. Negative volume → validation failure.
18. Single candle dataset.
19. Gap-through-SL.
20. Gap-through-TP.
21. Fixed-point rounding boundary.
22. Same-bar ambiguity LONG.
23. Same-bar ambiguity SHORT.
24. Segment boundary crossing yasak.
25. Single-thread / multi-thread equivalence.
26. Resume duplicate üretmiyor.
27. Crash-before-commit.
28. Crash-after-commit-before-next-batch.
29. Config hash determinism.
30. Deterministic trade identity.
31. Price exact-threshold boundary.
32. OPEN_AT_END unrealized calculation.
33. DATA_GAP unresolved semantic.
34. Memory queue backpressure behavior.

---

# 43. REAL DATA VALIDATION

Her symbol için production run öncesi veya configurable verification stage'de gerçek dataset içerisinden deterministic/random küçük window'lar seç.

Örneğin:

```text
500 candle
1000 candle
5000 candle
```

window'ları üzerinde:

```text
optimized engine
vs
brute force engine
```

karşılaştır.

Random seed runs tablosunda saklanmalı.

Herhangi bir mismatch varsa production run successful kabul edilmemelidir.

---

# 44. POST-RUN SANITY CHECKS

Her valid entry için beklenen:

```text
1 LONG
1 SHORT
```

Trade count beklenen count ile eşleşmelidir.

Kontroller:

```text
duplicate trade yok
LONG: TP > entry > SL
SHORT: SL > entry > TP
closed trade exit_index > entry_index
bars_held >= 1 for closed trades
closed trade kendi segment sınırını aşmıyor
DATA_GAP trade gap'i aşmıyor
same-bar flag doğru
SL exit condition doğru
TP exit condition doğru
source/config/run consistency doğru
```

Position aggregate değerlerini simulation_statistics ile karşılaştır.

---

# 45. DATABASE INTEGRITY

Simulation sonunda:

```sql
PRAGMA integrity_check;
```

çalıştır.

Sonuç:

```text
ok
```

değilse run başarılı kabul edilmemelidir.

Gerekirse:

```sql
PRAGMA foreign_key_check;
```

de çalıştır.

---

# 46. SIMULATION STATISTICS

Minimum:

```text
total candles
valid candles
invalid candles
segment count
data gaps

total entries
total LONG positions
total SHORT positions

TP count
SL count
same-bar SL/TP count
end-of-data count
data-gap invalidated count

average bars held
median bars held
min bars held
max bars held

TP rate
SL rate

average nominal R
average gross R
average net R

average MAE
average MFE

index build duration
simulation duration
database write duration
validation duration
total duration

candles/sec
trades/sec
SQLite rows/sec
SQLite MB/sec

peak RSS MB
database size bytes
```

Median hesaplamak için tüm values RAM'e yüklemeye çalışma.

SQLite aggregate veya memory-efficient yöntem kullan.

---

# 47. LOGGING

Structured logging kullan.

Alanlar örneğin:

```text
timestamp
level
symbol
run_id
stage
processed_entries
total_entries
percentage
trades_generated
trades_committed
queue_depth
throughput
rss_mb
elapsed_seconds
```

Hot loop içerisinde trade başına log yazma.

Progress interval-based olsun.

Örneğin:

```text
her 1 saniye
veya
her X milyon trade
```

---

# 48. MEMORY MONITORING

Peak RSS ölç.

Linux için `/proc/self/status`, `getrusage()` veya uygun platform abstraction kullanılabilir.

Runtime sırasında memory hard limit'e tehlikeli şekilde yaklaşılırsa:

- queue capacity azaltılabilir,
- processing kontrollü durdurulabilir,
- temiz failure üretilebilir.

OOM killer'a güvenme.

RAM metriğini final statistics içerisine yaz.

---

# 49. ERROR HANDLING

Tutarlı hata stratejisi kullan.

Örneğin:

- configuration errors → exception / clean startup failure
- malformed input → validation error
- SQLite errors → typed exception
- worker errors → propagate to coordinator
- writer error → stop producers
- fatal error → mark run FAILED
- SIGINT/SIGTERM → graceful interruption + checkpoint mümkünse korunmalı

Worker thread exception'larının sessizce terminate edilmesine izin verme.

---

# 50. SIGNAL HANDLING

SIGINT / SIGTERM için safe shutdown tasarla.

Signal handler içerisinde SQLite veya complex logic çalıştırma.

Sadece atomic stop flag set et.

Normal control flow:

```text
workers stop
queue drain/abort policy uygulanır
current transaction güvenli şekilde tamamlanır veya rollback edilir
run INTERRUPTED yapılır
```

Resume mümkün kalmalıdır.

---

# 51. C++ CODE QUALITY

C++20+.

Zorunlu:

- RAII
- no raw owning pointer
- `std::unique_ptr` / stack ownership
- const correctness
- scoped enums
- `std::span` uygun yerlerde
- `std::chrono` timestamps/durations
- explicit integer widths
- checked conversions
- clean namespaces
- small modules
- clear interfaces

SQLite:

- RAII connection wrapper
- RAII statement wrapper
- RAII transaction wrapper

---

# 52. COMPILER SETTINGS

Warnings:

```text
-Wall
-Wextra
-Wpedantic
-Wconversion
-Wshadow
```

Uygun olan diğer warning'leri de ekle.

Debug/sanitizer targets:

```text
ASan
UBSan
TSan
```

Release:

```text
-O3
```

`-march=native` yalnız explicit benchmark/release option ile kullanılmalı.

Portable binary default olarak native-specific instruction set gerektirmemelidir.

---

# 53. DEPENDENCIES

Dependencies minimum tutulmalı.

Tercihen:

- SQLite3
- standard library
- küçük, gerekliyse header-only CLI/hash helper

Her dependency'nin neden kullanıldığını README'de belirt.

Gereksiz framework ekleme.

---

# 54. PROJECT STRUCTURE

Minimum öneri:

```text
trade-simulator/
├── CMakeLists.txt
├── README.md
├── include/
│   └── simulator/
│       ├── config/
│       ├── data/
│       ├── validation/
│       ├── indexing/
│       ├── simulation/
│       ├── database/
│       ├── concurrency/
│       ├── logging/
│       └── utils/
├── src/
│   ├── main.cpp
│   ├── config/
│   ├── data/
│   ├── validation/
│   ├── indexing/
│   ├── simulation/
│   ├── database/
│   ├── concurrency/
│   ├── logging/
│   └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── randomized/
│   ├── reference/
│   └── benchmark/
├── tools/
│   └── benchmark/
├── schema/
│   └── schema.sql
├── docs/
│   ├── architecture.md
│   ├── algorithm.md
│   ├── database.md
│   ├── semantics.md
│   └── validation.md
└── examples/
```

Gerekirse daha iyi yapı seçebilirsin.

---

# 55. BENCHMARK

Benchmark tool oluştur.

Dataset sizes:

```text
100k candles
1M candles
5M candles
```

Mümkünse synthetic deterministic benchmark dataset generator ekle.

Ölç:

```text
input parsing time
validation time
index build time
simulation time
DB write time
post-validation time
total time

peak RSS
trades/sec
candles/sec
SQLite rows/sec
SQLite MB/sec
database size
```

Ayrıca benchmark:

```text
1 thread
2 threads
4 threads
8 threads
```

ile scaling ölçebilmeli.

Hiçbir benchmark memory limit'i aşmamalıdır.

---

# 56. PERFORMANCE PROFILING

Architecture gereksiz micro-optimization yerine measurement-driven olmalı.

README/docs içerisinde profiling öner:

```text
perf
heaptrack
valgrind/callgrind
sanitizers
```

Ancak correctness testleri geçmeden performance tuning yapma.

---

# 57. OUTPUT DATABASE SIZE

Positions tablosu milyonlarca row içereceğinden storage amplification dikkate alınmalı.

Aynı bilgiyi gereksiz TEXT tekrarlarıyla saklama.

Örneğin:

```text
symbol
algorithm_version
source_hash
config_hash
```

her row'da zorunlu değilse normalized run metadata üzerinden ilişkilendirilebilir.

Ancak kullanıcının audit gereksinimi korunmalıdır.

Schema tasarımında:

```text
auditability
vs
storage size
```

trade-off'unu açıkça anlat.

Eğer positions tablosundan bazı tekrarlayan alanları runs tablosuna taşırsan bunun nedenini açıkla.

---

# 58. SCHEMA DESIGN PRINCIPLE

Positions yalnız trade-specific information içermeli.

Run-level constant values mümkün olduğunda:

```text
runs
metadata
```

içerisinde tutulabilir.

Örneğin:

```text
symbol
SL
RR
config_hash
source_hash
algorithm_version
price model
```

run-level ise her position'da tekrar edilmesi zorunlu değildir.

Ancak query convenience için gerektiğinde denormalization bilinçli yapılabilir.

Kararı storage benchmark ile gerekçelendir.

---

# 59. NO LOOK-AHEAD AUDIT

Kodun tamamını look-ahead açısından gözden geçir.

Kesinlikle:

- entry candle high/low exit için kullanılmamalı
- future data entry feature gibi kullanılmamalı
- future index structure yalnız search acceleration amaçlı kullanılmalı
- MAE/MFE exit decision'ı etkilememeli
- post-hoc analytics simulation'a geri sızmamalı
- real-data validation random window selection simulation outcome'a göre yapılmamalı

Offline indexing kullanmak look-ahead bias değildir; çünkü index yalnız gelecekte barrier'ın ilk gerçekleştiği yeri mevcut trade kurallarına göre verimli bulmak için kullanılmaktadır. Bu distinction documentation'da açıklanmalıdır.

---

# 60. ACCEPTANCE CRITERIA

Proje tamamlanmış sayılabilmesi için:

### Correctness

- unit tests geçmeli
- randomized optimized/reference comparison geçmeli
- real-data window comparison geçmeli
- single-thread/multi-thread identical sonuç üretmeli

### Data integrity

- duplicate logical trade olmamalı
- trade count doğru olmalı
- DB integrity_check = ok
- completed run state doğru olmalı

### Reproducibility

Aynı:

```text
input
source hash
config hash
algorithm version
```

ile aynı logical trade results üretilmeli.

### Performance

Production simulation O(N²) olmamalı.

### Memory

Configured 3072 MB hard limit benchmarklarda aşılmamalı.

### Crash safety

Checkpoint/resume duplicate üretmemeli.

### Buildability

Temiz checkout sonrası documented commands ile build edilebilmeli.

### Usability

CLI example doğrudan çalışmalı.

---

# 61. IMPLEMENTATION OUTPUT ORDER

Cevabını yalnız genel önerilerle bitirme.

Projeyi gerçekten implement et.

Çıktıyı şu sırayla üret:

## Phase 1 — Engineering Design

Açıkla:

1. architecture
2. algorithm selection
3. algorithm correctness reasoning
4. time complexity
5. memory complexity
6. data layout
7. timestamp semantics
8. intrabar semantics
9. gap semantics
10. execution-price semantics
11. validation model
12. concurrency model
13. bounded queue design
14. SQLite strategy
15. crash/restart model
16. deterministic identity
17. price representation
18. schema design

## Phase 2 — Full Project Tree

Tam directory tree ver.

## Phase 3 — Build System

Tam:

```text
CMakeLists.txt
```

üret.

## Phase 4 — Database

Tam:

```text
schema.sql
```

ve SQLite wrapper'larını üret.

## Phase 5 — Core Source

Tüm gerekli `.hpp` ve `.cpp` dosyalarını üret.

Pseudo-code kullanma.

## Phase 6 — Reference Engine

Brute-force engine'i tam implement et.

## Phase 7 — Tests

Unit, integration ve randomized correctness testlerini tam implement et.

## Phase 8 — Benchmark Tool

Çalıştırılabilir benchmark programı oluştur.

## Phase 9 — Documentation

Üret:

```text
README.md
docs/architecture.md
docs/algorithm.md
docs/semantics.md
docs/database.md
```

## Phase 10 — Usage

Build commands:

```bash
cmake ...
cmake --build ...
ctest ...
```

ve örnek simulator CLI komutlarını ver.

---

# 62. CODING OUTPUT RULES

Kaynak kod üretirken:

- her dosyanın path'ini açıkça belirt
- hiçbir kritik dosyayı `...` ile geçme
- “implement this later” bırakma
- TODO ile core logic eksik bırakma
- pseudo-code verme
- compile edilmeyen illustrative snippets verme
- fonksiyon declaration bırakıp implementation unutma
- schema ile C++ binding field'larını tutarlı tut
- enum mapping'lerini tek source of truth üzerinden yönet
- generated code'un kendi içinde tutarlı olduğundan emin ol

Bir karar vermek için yeterli bilgi yoksa soru sorarak sistemi durdurma.

Bunun yerine:

1. correctness-preserving,
2. conservative,
3. deterministic,
4. auditable

default seç.

Sonra README içerisinde açıkça belgeleyerek ilerle.

---

# 63. TEST-FIRST REQUIREMENT

Optimized engine güvenilir kabul edilmeden önce reference engine çalışmalıdır.

Development sırası tercihen:

```text
domain semantics
→ reference engine
→ unit tests
→ optimized index
→ equivalence tests
→ SQLite pipeline
→ concurrency
→ crash recovery
→ benchmarks
```

olsun.

---

# 64. BİLİMSEL ANALİZ İÇİN VERİ GÜVENİLİRLİĞİ

Bu sistem yalnızca hızlı trade generation aracı değildir.

Üretilen milyonlarca kayıt daha sonra:

- statistical hypothesis testing
- conditional expectancy analysis
- regime detection
- feature engineering
- ML research
- MAE/MFE studies
- distribution analysis
- holding-period analysis
- survival-style analysis

için kullanılacaktır.

Dolayısıyla sonuç datası:

```text
deterministic
reproducible
auditable
semantically explicit
bias-aware
```

olmalıdır.

Bir trade'in neden:

```text
TP
SL
SL_AND_TP_SAME_BAR
DATA_GAP
END_OF_DATA
```

sonucu aldığı veritabanındaki bilgilerden geriye dönük olarak açıklanabilmelidir.

---

# 65. FINAL ENGINEERING PRINCIPLE

Her optimizasyon kararında şu soruyu sor:

> “Bu değişiklik daha hızlı olmasına rağmen üretilen trade datasının bilimsel güvenilirliğini, deterministikliğini, audit edilebilirliğini veya reproducibility'sini azaltıyor mu?”

Cevap evet ise optimizasyonu uygulama.

Bu projenin amacı yalnızca milyonlarca trade'i hızlı üretmek değil; milyonlarca trade'i **doğru, tekrar üretilebilir ve sonradan güvenle analiz edilebilir şekilde** üretmektir.
