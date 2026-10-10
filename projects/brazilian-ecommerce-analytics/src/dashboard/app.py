"""
Streamlit Web Analytics Dashboard: Olist Brazilian E-Commerce
Enterprise-Grade Business Intelligence & Data Analyst Platform
"""

import os
import sys
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Configure path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from src.analytics.sales_kpi import compute_overview_kpis, compute_monthly_sales_trend, compute_state_distribution, compute_day_and_hour_patterns
from src.analytics.rfm_segmentation import calculate_rfm_metrics, segment_customers, get_segment_summary, compute_cohort_retention, get_segment_playbook
from src.analytics.logistics_sla import compute_logistics_kpis, analyze_regional_logistics, delay_impact_on_reviews
from src.analytics.payments_finance import compute_payment_method_breakdown, analyze_installments
from src.analytics.product_intelligence import compute_category_pareto, top_categories_metrics

DB_PATH = BASE_DIR / "data" / "olist.db"

# Page config
st.set_page_config(
    page_title="Olist E-Commerce Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark/Modern Slate Aesthetic)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 12px;
    }
    .metric-card .title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
    }
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 4px;
        color: #38bdf8;
    }
    .metric-card .sub {
        font-size: 0.8rem;
        color: #cbd5e1;
        margin-top: 2px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data():
    conn = sqlite3.connect(DB_PATH)
    orders_df = pd.read_sql_query("SELECT * FROM vw_orders_summary", conn)
    categories_df = pd.read_sql_query("SELECT * FROM vw_category_sales", conn)
    payments_df = pd.read_sql_query("SELECT * FROM order_payments", conn)
    reviews_df = pd.read_sql_query("SELECT * FROM order_reviews", conn)
    conn.close()
    return orders_df, categories_df, payments_df, reviews_df


@st.cache_data(show_spinner=False)
def load_rfm(df_orders):
    rfm = calculate_rfm_metrics(df_orders)
    segmented = segment_customers(rfm)
    summary = get_segment_summary(segmented)
    return segmented, summary


def render_metric_card(title, value, sub=""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="title">{title}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


# Main App Execution
def main():
    if not DB_PATH.exists():
        st.error(f"Veritabanı bulunamadı ({DB_PATH}). Lütfen önce ETL sürecini tamamlayın: `python3 src/etl/build_database.py`")
        return

    orders_df, categories_df, payments_df, reviews_df = load_data()
    segmented_rfm, rfm_summary = load_rfm(orders_df)

    # Sidebar
    st.sidebar.title("🛍️ Olist Analytics")
    st.sidebar.caption("Brazilian E-Commerce BI Platform (2016-2018)")
    st.sidebar.markdown("---")

    menu = st.sidebar.radio(
        "Navigasyon Paneli",
        [
            "📊 Yönetici Özeti (Executive KPIs)",
            "👥 Müşteri & RFM Segmentasyonu",
            "🚚 Lojistik & SLA Teslimat Radarı",
            "💳 Ödeme Ekosistemi & Taksitler",
            "📦 Ürün Kategori Analizi (Pareto 80/20)",
            "💻 İnteraktif SQL Studio"
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Veri Seti Bilgisi:**
    - 99,441 Sipariş
    - 93,471 Tekil Müşteri
    - 3,095 Aktif Satıcı
    - 74 Farklı Ürün Kategorisi
    """)

    # ----------------------------------------------------
    # TAB 1: EXECUTIVE KPIS
    # ----------------------------------------------------
    if menu == "📊 Yönetici Özeti (Executive KPIs)":
        st.title("📊 Yönetici Satış & Gelir Özeti (Executive Overview)")
        st.markdown("Brezilya E-Ticaret Pazar Yeri genel satış dinamikleri, büyüme eğrileri ve bölgesel performans göstergeleri.")

        kpis = compute_overview_kpis(orders_df)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card("Toplam GMV (Mal Değeri)", f"R$ {kpis['gross_merchandise_value']:,.0f}", "Ürün Satış Hacmi")
        with c2:
            render_metric_card("Brüt Sipariş Geliri", f"R$ {kpis['gross_revenue']:,.0f}", f"Kargo: R$ {kpis['total_freight']:,.0f}")
        with c3:
            render_metric_card("Teslim Edilen Sipariş", f"{kpis['delivered_orders']:,}", f"İptal Oranı: %{kpis['cancellation_rate_pct']}")
        with c4:
            render_metric_card("Ortalama Sepet (AOV)", f"R$ {kpis['average_order_value']:.2f}", f"Sipariş Başı Ürün: {kpis['average_items_per_order']}")

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            render_metric_card("Tekil Müşteri Sayısı", f"{kpis['unique_customers']:,}", "93.4k aktif alıcı")
        with c6:
            render_metric_card("Müşteri Memnuniyeti", f"{kpis['average_review_score']} / 5.0", "Ortalama Değerlendirme")
        with c7:
            render_metric_card("Zamanında Teslimat", f"%{kpis['ontime_delivery_rate_pct']}", "SLA Başarı Oranı")
        with c8:
            render_metric_card("Gecikmeli Teslimat", f"%{kpis['late_delivery_rate_pct']}", "Termin Aşımı")

        st.markdown("---")

        # Monthly Trend Chart
        st.subheader("📈 Aylık Satış (GMV) ve Sipariş Hacmi Eğrisi")
        monthly_df = compute_monthly_sales_trend(orders_df)

        fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
        fig_trend.add_trace(
            go.Bar(
                x=monthly_df["year_month"],
                y=monthly_df["gmv"],
                name="GMV (R$)",
                marker_color="#38bdf8",
                opacity=0.85
            ),
            secondary_y=False
        )
        fig_trend.add_trace(
            go.Scatter(
                x=monthly_df["year_month"],
                y=monthly_df["orders"],
                name="Sipariş Sayısı",
                marker=dict(color="#f97316", size=7),
                line=dict(color="#f97316", width=2.5),
                mode="lines+markers"
            ),
            secondary_y=True
        )
        fig_trend.update_layout(
            title="Aylık Ciro ve Sipariş Adetleri (Kasım 2017 Black Friday Zirvesi Dahil)",
            xaxis_title="Yıl-Ay",
            template="plotly_dark",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_trend.update_yaxes(title_text="GMV (R$)", secondary_y=False)
        fig_trend.update_yaxes(title_text="Sipariş Sayısı", secondary_y=True)
        st.plotly_chart(fig_trend, use_container_width=True)

        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("🗺️ Eyalet Bazında Ciro Dağılımı")
            state_df = compute_state_distribution(orders_df).head(10)
            fig_state = px.bar(
                state_df,
                x="customer_state",
                y="total_revenue",
                text="revenue_share_pct",
                labels={"customer_state": "Eyalet (UF)", "total_revenue": "Toplam Ciro (R$)"},
                color="total_revenue",
                color_continuous_scale="Viridis",
                template="plotly_dark"
            )
            fig_state.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_state.update_layout(title="İlk 10 Eyalet (SP Güneydoğu Hakimiyeti)")
            st.plotly_chart(fig_state, use_container_width=True)

        with col_r:
            st.subheader("⏰ Sipariş Yoğunluk Haritası (Haftanın Günü & Saat)")
            pivot_matrix = compute_day_and_hour_patterns(orders_df)
            fig_heat = px.imshow(
                pivot_matrix,
                labels=dict(x="Günün Saati", y="Haftanın Günü", color="Sipariş"),
                x=pivot_matrix.columns,
                y=pivot_matrix.index,
                color_continuous_scale="YlGnBu",
                template="plotly_dark"
            )
            fig_heat.update_layout(title="Müşteri Satın Alma Zamanı Yoğunluğu")
            st.plotly_chart(fig_heat, use_container_width=True)

    # ----------------------------------------------------
    # TAB 2: RFM SEGMENTATION
    # ----------------------------------------------------
    elif menu == "👥 Müşteri & RFM Segmentasyonu":
        st.title("👥 Müşteri Yaşam Boyu Değeri & RFM Segmentasyonu")
        st.markdown("Müşterilerin Satın Alma Tazeliği (Recency), Sıklığı (Frequency) ve Harcama Tutarı (Monetary) bazlı stratejik sınıflandırması.")

        # Summary KPIs
        r1, r2, r3, r4 = st.columns(4)
        champions = rfm_summary[rfm_summary["segment"] == "Champions"]
        champ_rev = champions["total_revenue"].values[0] if len(champions) > 0 else 0
        at_risk = rfm_summary[rfm_summary["segment"].str.contains("At Risk")]
        at_risk_cust = at_risk["customer_count"].values[0] if len(at_risk) > 0 else 0

        with r1:
            render_metric_card("Analiz Edilen Müşteri", f"{len(segmented_rfm):,}", "Tekil Müşteri Havuzu")
        with r2:
            render_metric_card("Tek Seferlik Alıcı Oranı", "%96.9", "Brezilya e-ticaret normu")
        with r3:
            render_metric_card("Şampiyon Segment Cirosu", f"R$ {champ_rev:,.0f}", "VIP Müşteri Katkısı")
        with r4:
            render_metric_card("Risk Altındaki Müşteri", f"{at_risk_cust:,}", "Kazanım Gerekli")

        st.markdown("---")

        c_treemap, c_bar = st.columns([1.2, 1])
        with c_treemap:
            st.subheader("🗺️ Segment Gelir & Boyut Ağaç Haritası (Treemap)")
            fig_tree = px.treemap(
                rfm_summary,
                path=["segment"],
                values="total_revenue",
                color="customer_count",
                color_continuous_scale="Blues",
                custom_data=["customer_pct", "avg_recency_days", "avg_monetary"],
                template="plotly_dark"
            )
            fig_tree.update_traces(
                hovertemplate="<b>%{label}</b><br>Toplam Gelir: R$ %{value:,.0f}<br>Müşteri Payı: %{customdata[0]}%<br>Ort. Recency: %{customdata[1]} gün<br>Ort. Harcama: R$ %{customdata[2]}"
            )
            st.plotly_chart(fig_tree, use_container_width=True)

        with c_bar:
            st.subheader("📊 Müşteri Dağılımı ve Gelir Katkısı")
            fig_bar = px.bar(
                rfm_summary,
                x="segment",
                y=["revenue_pct", "customer_pct"],
                barmode="group",
                labels={"value": "Oran (%)", "variable": "Metrik", "segment": "Segment"},
                template="plotly_dark",
                color_discrete_map={"revenue_pct": "#38bdf8", "customer_pct": "#94a3b8"}
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        st.subheader("📋 Segment Detayları & CRM Eylem Planı (Playbook)")
        playbook = get_segment_playbook()
        
        selected_seg = st.selectbox("İncelemek istediğiniz segmenti seçin:", list(playbook.keys()))
        seg_info = playbook[selected_seg]
        seg_data = rfm_summary[rfm_summary["segment"] == selected_seg]

        p1, p2, p3 = st.columns([1, 1, 1.5])
        with p1:
            if not seg_data.empty:
                st.metric("Segmentteki Müşteri", f"{seg_data['customer_count'].values[0]:,} (%{seg_data['customer_pct'].values[0]})")
                st.metric("Toplam Harcama", f"R$ {seg_data['total_revenue'].values[0]:,.0f} (%{seg_data['revenue_pct'].values[0]})")
        with p2:
            if not seg_data.empty:
                st.metric("Ortalama Son Alışveriş", f"{seg_data['avg_recency_days'].values[0]:.0f} gün önce")
                st.metric("Ortalama Sepet Tutarı", f"R$ {seg_data['avg_monetary'].values[0]:.2f}")
        with p3:
            st.markdown(f"**Öncelik:** `{seg_info['priority']}`")
            st.markdown(f"**Profil:** {seg_info['description']}")
            st.info(f"**Pazarlama Stratejisi:** {seg_info['strategy']}")

        st.markdown("---")
        st.subheader("📅 Aylık Müşteri Edinme Kohort Analizi (Retention Matrix)")
        cohort_matrix = compute_cohort_retention(orders_df).iloc[4:16, :8]  # Focus on key 2017-2018 window
        fig_cohort = px.imshow(
            cohort_matrix,
            labels=dict(x="Geçen Ay (Month Offset)", y="Edinme Ayı (Cohort)", color="Tutundurma %"),
            color_continuous_scale="Blues",
            text_auto=".1f",
            template="plotly_dark"
        )
        st.plotly_chart(fig_cohort, use_container_width=True)

    # ----------------------------------------------------
    # TAB 3: LOGISTICS & SLA AUDIT
    # ----------------------------------------------------
    elif menu == "🚚 Lojistik & SLA Teslimat Radarı":
        st.title("🚚 Lojistik Operasyonları & Teslimat SLA Denetimi")
        st.markdown("Teslimat süreleri, gecikme oranları, kargo maliyet yükü ve gecikmelerin müşteri değerlendirmelerine yıkıcı etkisi.")

        log_kpi = compute_logistics_kpis(orders_df)

        l1, l2, l3, l4 = st.columns(4)
        with l1:
            render_metric_card("Ort. Gerçek Teslimat Süresi", f"{log_kpi['average_delivery_days']} Gün", "Satın alma - Kapıya varış")
        with l2:
            render_metric_card("Taahhüt Edilen Süre (SLA)", f"{log_kpi['average_estimated_days']} Gün", f"Güvenlik marjı: +{log_kpi['avg_early_buffer_days']} gün")
        with l3:
            render_metric_card("Gecikmeli Sipariş Oranı", f"%{log_kpi['late_delivery_rate_pct']}", "Termin Aşımı")
        with l4:
            render_metric_card("Ortalama Kargo Ücreti", f"R$ {log_kpi['average_freight_cost']:.2f}", f"Sepete Oranı: %{log_kpi['average_freight_ratio_pct']}")

        st.markdown("---")

        col_sla1, col_sla2 = st.columns(2)
        with col_sla1:
            st.subheader("⚠️ Kritik Analiz: Teslimat Gecikmesi & Yorum Puanı Düşüşü")
            delay_impact = delay_impact_on_reviews(orders_df)
            fig_di = px.bar(
                delay_impact,
                x="delay_bucket",
                y="avg_review_score",
                text="avg_review_score",
                labels={"delay_bucket": "Teslimat Durumu", "avg_review_score": "Ort. Yorum Puanı (1-5)"},
                color="avg_review_score",
                color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"],
                template="plotly_dark"
            )
            fig_di.update_traces(texttemplate='%{text:.2f} ★', textposition='outside')
            fig_di.update_layout(yaxis_range=[0, 5])
            st.plotly_chart(fig_di, use_container_width=True)
            st.warning("**Data Insight:** Zamanında veya erken gelen siparişlerde ortalama memnuniyet **4.27 ★** iken, 7 günü aşan gecikmelerde puan dramatik şekilde **1.62 ★** seviyesine düşmektedir! Lojistik gecikmeleri churn oranının en büyük belirleyicisidir.")

        with col_sla2:
            st.subheader("🗺️ Eyalet Bazında Ortalama Teslimat Günleri (Kuzey vs Güneydoğu)")
            state_log = analyze_regional_logistics(orders_df)
            fig_sl = px.scatter(
                state_log,
                x="avg_delivery_days",
                y="late_rate_pct",
                size="orders",
                color="freight_ratio_pct",
                hover_name="customer_state",
                labels={
                    "avg_delivery_days": "Ortalama Teslimat Süresi (Gün)",
                    "late_rate_pct": "Gecikme Oranı (%)",
                    "freight_ratio_pct": "Kargo/Sepet Oranı (%)"
                },
                color_continuous_scale="Reds",
                template="plotly_dark"
            )
            st.plotly_chart(fig_sl, use_container_width=True)
            st.caption("Kuzey eyaletleri (RR, AP, AM) 25-30 güne varan teslimat ve yüksek kargo oranına sahipken, Güneydoğu (SP) ortalama 8 günde teslim edilmektedir.")

        st.markdown("---")
        st.subheader("📊 Eyalet Lojistik Performans Tablosu")
        st.dataframe(state_log, use_container_width=True)

    # ----------------------------------------------------
    # TAB 4: PAYMENTS & FINANCING
    # ----------------------------------------------------
    elif menu == "💳 Ödeme Ekosistemi & Taksitler":
        st.title("💳 Ödeme Yöntemleri & Brezilya Taksitli Finansman Davranışı")
        st.markdown("Kredi kartı, Boleto (banka fişi), hediye çeki ve banka kartı tercihleri; taksit kullanımının sepet tutarına etkisi.")

        pay_summary = compute_payment_method_breakdown(payments_df)
        inst_summary = analyze_installments(payments_df)

        p1, p2, p3 = st.columns(3)
        with p1:
            render_metric_card("Kredi Kartı Hacim Payı", "%73.9", "Brezilya'nın en baskın ödeme türü")
        with p2:
            render_metric_card("Boleto (Banka Fişi) Payı", "%19.0", "Bankasız nüfus ve nakit alternatifi")
        with p3:
            render_metric_card("Ortalama Kredi Kartı Taksiti", "3.5 Taksit", "Taksitlendirme alışkanlığı")

        st.markdown("---")

        cp1, cp2 = st.columns(2)
        with cp1:
            st.subheader("🍩 Ödeme Kanalı İşlem Hacmi Payı")
            fig_donut = px.pie(
                pay_summary,
                values="total_volume",
                names="payment_type",
                hole=0.45,
                color_discrete_sequence=["#38bdf8", "#f97316", "#10b981", "#a855f7"],
                template="plotly_dark"
            )
            fig_donut.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_donut, use_container_width=True)

        with cp2:
            st.subheader("📈 Taksit Sayısına Göre Ortalama Sepet Değeri (R$)")
            fig_inst = px.bar(
                inst_summary,
                x="installment_tier",
                y="avg_order_value",
                text="avg_order_value",
                labels={"installment_tier": "Taksit Aralığı", "avg_order_value": "Ortalama Sepet Tutarı (R$)"},
                color="avg_order_value",
                color_continuous_scale="Purples",
                template="plotly_dark"
            )
            fig_inst.update_traces(texttemplate='R$ %{text:.0f}', textposition='outside')
            st.plotly_chart(fig_inst, use_container_width=True)
            st.info("**Finansal Trend:** Tek çekim alışverişlerde ortalama sepet **R$ 95** iken, 10 taksit ve üzeri işlemlerde sepet ortalaması **R$ 440+** seviyesine çıkmaktadır. Taksit imkanı sunmak yüksek tutarlı ürünlerin dönüşümünü doğrudan artırmaktadır.")

    # ----------------------------------------------------
    # TAB 5: PRODUCT CATEGORY INTELLIGENCE
    # ----------------------------------------------------
    elif menu == "📦 Ürün Kategori Analizi (Pareto 80/20)":
        st.title("📦 Ürün Kategori Zekası & Pareto 80/20 Analizi")
        st.markdown("Hangi kategorilerin toplam gelirin %80'ini oluşturduğu, ABC sınıflandırması ve kategori bazlı birim fiyat/kargo oranları.")

        pareto_df = compute_category_pareto(categories_df)

        top_10 = pareto_df.head(10)
        class_a = pareto_df[pareto_df["abc_class"].str.contains("Class A")]
        
        pk1, pk2, pk3, pk4 = st.columns(4)
        with pk1:
            render_metric_card("Toplam Aktif Kategori", f"{len(pareto_df)} Kategori", "Pazar Yeri Çeşitliliği")
        with pk2:
            render_metric_card("Class A (Çekirdek %80)", f"{len(class_a)} Kategori", f"Toplam kategorilerin yalnızca %{len(class_a)/len(pareto_df)*100:.1f}'i")
        with pk3:
            render_metric_card("Lider Kategori", f"{top_10.iloc[0]['category_name']}", f"R$ {top_10.iloc[0]['total_revenue']:,.0f}")
        with pk4:
            render_metric_card("Top 10 Gelir Payı", f"%{top_10['revenue_share_pct'].sum():.1f}", "Yüksek ciro yoğunlaşması")

        st.markdown("---")

        st.subheader("📉 Kategori Pareto Eğrisi (Kümülatif Gelir Payı)")
        fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
        fig_pareto.add_trace(
            go.Bar(
                x=pareto_df.head(25)["category_name"],
                y=pareto_df.head(25)["total_revenue"],
                name="Kategori Cirosu (R$)",
                marker_color="#38bdf8",
                opacity=0.85
            ),
            secondary_y=False
        )
        fig_pareto.add_trace(
            go.Scatter(
                x=pareto_df.head(25)["category_name"],
                y=pareto_df.head(25)["cumulative_revenue_pct"],
                name="Kümülatif Gelir %",
                marker=dict(color="#ef4444", size=7),
                line=dict(color="#ef4444", width=2.5),
                mode="lines+markers"
            ),
            secondary_y=True
        )
        fig_pareto.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Pareto %80 Sınırı", secondary_y=True)
        fig_pareto.update_layout(
            title="İlk 25 Kategori İçin Pareto Eğrisi",
            xaxis_tickangle=-45,
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_pareto.update_yaxes(title_text="Kategori Cirosu (R$)", secondary_y=False)
        fig_pareto.update_yaxes(title_text="Kümülatif Gelir Payı (%)", secondary_y=True)
        st.plotly_chart(fig_pareto, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Tüm Kategoriler Performans Tablosu")
        st.dataframe(pareto_df, use_container_width=True)

    # ----------------------------------------------------
    # TAB 6: INTERACTIVE SQL STUDIO
    # ----------------------------------------------------
    elif menu == "💻 İnteraktif SQL Studio":
        st.title("💻 İnteraktif SQL Studio & Veri Konsolu")
        st.markdown("Olist SQLite veritabanı (`data/olist.db`) üzerinde hazır analitik iş sorularını çalıştırın veya özel SQL sorgusu yazın.")

        queries_dict = {
            "01_sales_revenue_growth.sql": "1. Aylık Ciro, Sipariş Hacmi ve MoM Büyüme Oranları",
            "02_rfm_customer_segments.sql": "2. SQL Tabanlı RFM Müşteri Segmentasyonu ve Gelir Dağılımı",
            "03_logistics_sla_delays.sql": "3. Eyalet Lojistik SLA Performansı ve Gecikmenin Yorumlara Etkisi",
            "04_product_pareto_revenue.sql": "4. Ürün Kategori Pareto 80/20 ve ABC Gelir Sınıflandırması",
            "05_payment_installment_patterns.sql": "5. Ödeme Yöntemi Dağılımı ve Kredi Kartı Taksit Analizi",
            "06_seller_sla_performance.sql": "6. En Çok Ciro Yapan Satıcılar ve Eyalet Dağılımı"
        }

        selected_q_file = st.selectbox(
            "Hazır İş Sorgusu Seçin:",
            list(queries_dict.keys()),
            format_func=lambda x: queries_dict[x]
        )

        query_file_path = BASE_DIR / "sql" / "queries" / selected_q_file
        with open(query_file_path, "r", encoding="utf-8") as f:
            default_sql = f.read()

        sql_input = st.text_area("SQL Sorgusu (Düzenlenebilir):", value=default_sql, height=220)

        if st.button("🚀 Sorguyu Çalıştır (Execute SQL)", type="primary"):
            try:
                conn = sqlite3.connect(DB_PATH)
                # Split and execute the first statement
                statements = [s.strip() for s in sql_input.split(";") if s.strip()]
                for i, stmt in enumerate(statements):
                    st.write(f"**Sonuç (İfade {i+1}):**")
                    result_df = pd.read_sql_query(stmt, conn)
                    st.dataframe(result_df, use_container_width=True)
                    st.caption(f"Dönen Satır Sayısı: {len(result_df):,}")
                conn.close()
            except Exception as e:
                st.error(f"SQL Çalıştırma Hatası: {e}")


if __name__ == "__main__":
    main()
