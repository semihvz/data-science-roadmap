import sys
import os
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure src path is in sys.path
sys.path.append(os.path.dirname(__file__))

from sector_engine import SectorFlowEngine
from anomalies import SectorAnomalyDetector

st.set_page_config(
    page_title="Kripto Sektörel Para Akımı Radarı",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .card {
        padding: 1.2rem;
        border-radius: 10px;
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚡ Kripto Sektörel Para Akımı & Sermaye Rotasyonu Radarı</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Binance Futures Taker Volume Delta (CVD) ile An Be An Net Sermaye Giriş ve Çıkışları</div>', unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.header("⚙️ Kontrol Paneli")
timeframe = st.sidebar.selectbox("Zaman Dilimi (Timeframe)", ["15m", "1h", "4h"], index=1)
auto_refresh = st.sidebar.checkbox("Otomatik Yenileme (30 sn)", value=False)

if auto_refresh:
    time.sleep(30)
    st.rerun()

if st.sidebar.button("🔄 Verileri Şimdi Güncelle"):
    st.rerun()

engine = SectorFlowEngine()
detector = SectorAnomalyDetector()

with st.spinner(f"Binance Futures üzerinden {timeframe} sektörel akışlar hesaplanıyor..."):
    sector_results = engine.scan_all_sectors(timeframe=timeframe)
    signals = detector.detect_signals(sector_results)

# Top Metrics Row
total_market_net = sum(s["net_inflow_usdt"] for s in sector_results)
top_gaining_sector = sector_results[0]
top_losing_sector = sector_results[-1]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(
        "Piyasa Net Taker Akımı",
        f"${total_market_net:,.0f}",
        delta=f"Toplam Hacim: ${sum(s['total_volume_usdt'] for s in sector_results):,.0f}"
    )
with c2:
    st.metric(
        "En Çok Para Çeken Sektör",
        top_gaining_sector["sector"],
        delta=f"+${top_gaining_sector['net_inflow_usdt']:,.0f}"
    )
with c3:
    st.metric(
        "En Çok Para Kaybeden Sektör",
        top_losing_sector["sector"],
        delta=f"-${abs(top_losing_sector['net_inflow_usdt']):,.0f}",
        delta_color="inverse"
    )
with c4:
    st.metric(
        "Lider Odak Noktası (MVP)",
        f"{top_gaining_sector['mvp_symbol']}",
        delta=f"+${top_gaining_sector['mvp_net_inflow']:,.0f}"
    )

st.markdown("<br>", unsafe_allow_html=True)

# Signals Display
if signals:
    st.subheader("🚨 Anlık Algoritmik Sinyaller & Para Girişi Uyarıları")
    for sig in signals:
        alert_type = "success" if "GİRİŞ" in sig["type"] else ("warning" if "ROTASYON" in sig["type"] else "error")
        if alert_type == "success":
            st.success(f"**{sig['type']}**: {sig['message']}")
        elif alert_type == "warning":
            st.warning(f"**{sig['type']}**: {sig['message']}")
        else:
            st.error(f"**{sig['type']}**: {sig['message']}")

st.markdown("<br>", unsafe_allow_html=True)

# Main Bar Chart: Net Inflow by Sector
st.subheader(f"📊 Sektörel Net Para Akışı ({timeframe})")
df_sec = pd.DataFrame(sector_results)
df_sec['color'] = df_sec['net_inflow_usdt'].apply(lambda x: '#10B981' if x >= 0 else '#EF4444')

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    x=df_sec['net_inflow_usdt'],
    y=df_sec['sector'],
    orientation='h',
    marker_color=df_sec['color'],
    text=df_sec['net_inflow_usdt'].apply(lambda x: f"${x:,.0f}"),
    textposition='auto'
))
fig_bar.update_layout(
    xaxis_title="Net Sermaye Girişi / Çıkışı (USD)",
    yaxis_title="Sektör",
    yaxis={'categoryorder': 'total ascending'},
    height=450,
    margin=dict(l=20, r=20, t=20, b=20)
)
st.plotly_chart(fig_bar, use_container_width=True)

# Detailed Sector Deep-Dive Tabs
st.subheader("🔍 Sektör İçindeki Coinlerin Detaylı Para Akımları")
selected_sec_name = st.selectbox("İncelemek İstediğiniz Sektörü Seçin:", [s["sector"] for s in sector_results])

selected_sec = next(s for s in sector_results if s["sector"] == selected_sec_name)
sym_df = pd.DataFrame(selected_sec["symbols_details"])

col_t1, col_t2 = st.columns([3, 2])
with col_t1:
    fig_sym = px.bar(
        sym_df.sort_values(by="net_inflow_usdt", ascending=True),
        x="net_inflow_usdt",
        y="symbol",
        orientation="h",
        color="net_inflow_usdt",
        color_continuous_scale="RdYlGn",
        title=f"{selected_sec_name} İçindeki Tokenlerin Net Para Akımı ($)",
        labels={"net_inflow_usdt": "Net Inflow ($)", "symbol": "Token"}
    )
    fig_sym.update_layout(height=350)
    st.plotly_chart(fig_sym, use_container_width=True)

with col_t2:
    st.write("##### Token Dağılım Tablosu")
    display_df = sym_df[['symbol', 'net_inflow_usdt', 'buy_ratio_pct', 'price_change_pct', 'total_volume_usdt']].copy()
    display_df.columns = ['Sembol', 'Net Giriş ($)', 'Alıcı %', 'Fiyat %', 'Toplam Hacim ($)']
    display_df['Net Giriş ($)'] = display_df['Net Giriş ($)'].apply(lambda x: f"${x:,.0f}")
    display_df['Alıcı %'] = display_df['Alıcı %'].apply(lambda x: f"%{x:.1f}")
    display_df['Fiyat %'] = display_df['Fiyat %'].apply(lambda x: f"%{x:+.2f}")
    display_df['Toplam Hacim ($)'] = display_df['Toplam Hacim ($)'].apply(lambda x: f"${x:,.0f}")
    st.dataframe(display_df, use_container_width=True)
