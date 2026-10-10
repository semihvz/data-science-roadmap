import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="E-Commerce Executive Analytics Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #3B82F6;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #0F172A;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# Path configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ecommerce.db")

@st.cache_data
def load_db_data():
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at `{DB_PATH}`. Please run `python src/run_pipeline.py` first.")
        return None, None, None

    conn = sqlite3.connect(DB_PATH)
    
    # Orders dataframe
    orders_df = pd.read_sql_query("""
        SELECT 
            o.order_id, o.customer_id, o.order_date, o.order_status, 
            o.payment_method, o.shipping_cost, o.discounts_applied, o.total_amount,
            c.acquisition_channel, c.city, c.first_name || ' ' || c.last_name AS customer_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
    """, conn)
    
    # Items & Products dataframe
    items_df = pd.read_sql_query("""
        SELECT 
            oi.order_item_id, oi.order_id, oi.product_id, oi.quantity, oi.unit_price, oi.total_price,
            p.product_name, p.category, p.sub_category, p.cost_price
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
    """, conn)

    # Customers dataframe
    customers_df = pd.read_sql_query("SELECT * FROM customers", conn)

    conn.close()

    orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
    return orders_df, items_df, customers_df

def main():
    st.markdown('<div class="main-header">🛍️ E-Commerce Executive Analytics & Data Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Uçtan Uca Müşteri Segmentasyonu, Satış Metrikleri, Cohort Retention ve Churn Analiz Portalı</div>', unsafe_allow_html=True)

    orders_df, items_df, customers_df = load_db_data()

    if orders_df is None:
        st.stop()

    completed_orders = orders_df[orders_df['order_status'] == 'Completed']

    # Sidebar Filters
    st.sidebar.header("🎯 Analiz Filtreleri")
    
    min_date = orders_df['order_date'].min().date()
    max_date = orders_df['order_date'].max().date()

    date_range = st.sidebar.date_input(
        "Tarih Aralığı",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    all_channels = ["Tümü"] + list(customers_df['acquisition_channel'].unique())
    selected_channel = st.sidebar.selectbox("Kazanım Kanalı (Acquisition Channel)", all_channels)

    # Apply filters
    filtered_orders = completed_orders.copy()
    if len(date_range) == 2:
        start_d, end_d = date_range
        filtered_orders = filtered_orders[
            (filtered_orders['order_date'].dt.date >= start_d) & 
            (filtered_orders['order_date'].dt.date <= end_d)
        ]

    if selected_channel != "Tümü":
        filtered_orders = filtered_orders[filtered_orders['acquisition_channel'] == selected_channel]

    # KPI Summary Row
    total_rev = filtered_orders['total_amount'].sum()
    total_ord = filtered_orders['order_id'].nunique()
    total_cust = filtered_orders['customer_id'].nunique()
    aov = total_rev / total_ord if total_ord > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Toplam Brüt Gelir</div>
            <div class="metric-value">${total_rev:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Ortalama Sipariş Değeri (AOV)</div>
            <div class="metric-value">${aov:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Tamamlanan Sipariş Sayısı</div>
            <div class="metric-value">{total_ord:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Aktif Müşteri Sayısı</div>
            <div class="metric-value">{total_cust:,}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Satış & KPI Performansı", 
        "👥 RFM Müşteri Segmentasyonu", 
        "📅 Cohort Retention Analizi", 
        "🔮 Churn & CLV Tahminleme"
    ])

    # Tab 1: Satış Performansı
    with tab1:
        st.subheader("Aylık Gelir Trendi & Kategori Performansı")
        
        monthly_df = filtered_orders.set_index('order_date').resample('M')['total_amount'].sum().reset_index()
        monthly_df['order_date'] = monthly_df['order_date'].dt.strftime('%Y-%m')

        fig_trend = px.line(
            monthly_df, x='order_date', y='total_amount',
            labels={'order_date': 'Ay', 'total_amount': 'Aylık Gelir ($)'},
            title="Aylık Gelir Değişimi (MoM Trend)",
            markers=True
        )
        fig_trend.update_traces(line_color='#2563EB', line_width=3)
        st.plotly_chart(fig_trend, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            merged_items = items_df[items_df['order_id'].isin(filtered_orders['order_id'])]
            cat_df = merged_items.groupby('category').agg({'total_price': 'sum', 'quantity': 'sum'}).reset_index()
            fig_cat = px.bar(
                cat_df, x='category', y='total_price', color='category',
                title="Ürün Kategorilerine Göre Toplam Satış",
                labels={'category': 'Kategori', 'total_price': 'Gelir ($)'}
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with col_b:
            pay_df = filtered_orders.groupby('payment_method')['total_amount'].sum().reset_index()
            fig_pay = px.pie(
                pay_df, values='total_amount', names='payment_method',
                title="Ödeme Yöntemleri Dağılımı",
                hole=0.4
            )
            st.plotly_chart(fig_pay, use_container_width=True)

    # Tab 2: RFM Analysis
    with tab2:
        st.subheader("Recency, Frequency, Monetary (RFM) Segmentasyonu")
        ref_dt = filtered_orders['order_date'].max() + pd.Timedelta(days=1)
        
        rfm = filtered_orders.groupby('customer_id').agg({
            'order_date': lambda x: (ref_dt - x.max()).days,
            'order_id': 'count',
            'total_amount': 'sum'
        }).reset_index()
        
        rfm.columns = ['customer_id', 'recency', 'frequency', 'monetary']
        
        if len(rfm) > 5:
            rfm['r_score'] = pd.qcut(rfm['recency'], q=5, labels=[5, 4, 3, 2, 1])
            rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])
            rfm['m_score'] = pd.qcut(rfm['monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])

            def segment_fun(row):
                r, f, m = int(row['r_score']), int(row['f_score']), int(row['m_score'])
                if r >= 4 and f >= 4 and m >= 4: return 'Champions'
                elif r >= 3 and f >= 3 and m >= 3: return 'Loyal Customers'
                elif r >= 4 and f <= 2: return 'Promising / New'
                elif r <= 2 and f >= 3 and m >= 3: return 'At Risk'
                elif r <= 2 and f <= 2 and m <= 2: return 'Lost Customers'
                else: return 'Need Attention'

            rfm['segment'] = rfm.apply(segment_fun, axis=1)

            seg_summary = rfm.groupby('segment').agg({
                'customer_id': 'count',
                'monetary': 'sum',
                'recency': 'mean',
                'frequency': 'mean'
            }).reset_index()

            fig_seg = px.treemap(
                seg_summary, path=['segment'], values='monetary',
                color='recency', color_continuous_scale='RdYlGn_r',
                title="Müşteri Segmentleri Treemap (Büyüklük: Gelir, Renk: Ort. Son Sipariş Günü)"
            )
            st.plotly_chart(fig_seg, use_container_width=True)

            st.dataframe(seg_summary.rename(columns={
                'segment': 'Segment',
                'customer_id': 'Müşteri Sayısı',
                'monetary': 'Toplam Gelir ($)',
                'recency': 'Ort. Recency (Gün)',
                'frequency': 'Ort. Sipariş Frekansı'
            }), use_container_width=True)

    # Tab 3: Cohort Retention
    with tab3:
        st.subheader("Aylık Müşteri Tutundurma (Cohort Retention) Matrisi")
        
        cohort_df = filtered_orders[['customer_id', 'order_date']].copy()
        cohort_df['order_month'] = cohort_df['order_date'].dt.to_period('M')
        cohort_df['cohort_month'] = cohort_df.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')

        cohort_group = cohort_df.groupby(['cohort_month', 'order_month']).agg({'customer_id': 'nunique'}).reset_index()
        cohort_group['period_number'] = (cohort_group['order_month'].dt.year - cohort_group['cohort_month'].dt.year) * 12 + \
                                       (cohort_group['order_month'].dt.month - cohort_group['cohort_month'].dt.month)

        cohort_pivot = cohort_group.pivot(index='cohort_month', columns='period_number', values='customer_id')
        cohort_sizes = cohort_pivot.iloc[:, 0]
        retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0) * 100.0

        fig_heat = px.imshow(
            retention_matrix.astype(float),
            labels=dict(x="Dönem (Ay)", y="Cohort Katılım Ayı", color="Retention (%)"),
            x=[f"Ay {i}" for i in retention_matrix.columns],
            y=[str(m) for m in retention_matrix.index],
            color_continuous_scale='Blues',
            text_auto=".1f",
            aspect="auto"
        )
        fig_heat.update_layout(title="Aylık Cohort Retention Haritası (%)")
        st.plotly_chart(fig_heat, use_container_width=True)

    # Tab 4: Churn & CLV
    with tab4:
        st.subheader("Müşteri Yaşam Boyu Değeri (CLV) ve Terk (Churn) Riski Analizi")
        
        ref_dt = completed_orders['order_date'].max() + pd.Timedelta(days=1)
        clv = completed_orders.groupby('customer_id').agg({
            'customer_name': 'first',
            'acquisition_channel': 'first',
            'order_date': ['min', 'max', 'count'],
            'total_amount': 'sum'
        }).reset_index()

        clv.columns = ['customer_id', 'customer_name', 'channel', 'first_order', 'last_order', 'order_count', 'historical_clv']
        clv['days_since_last'] = (ref_dt - clv['last_order']).dt.days

        clv['churn_risk'] = clv['days_since_last'].apply(
            lambda x: 'Yüksek Risk (Terk Edilmiş)' if x > 180 else ('Orta Risk' if x > 90 else 'Düşük Risk (Aktif)')
        )

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            risk_counts = clv['churn_risk'].value_counts().reset_index()
            fig_risk = px.pie(
                risk_counts, values='count', names='churn_risk',
                title="Müşteri Churn Riski Dağılımı",
                color='churn_risk',
                color_discrete_map={
                    'Düşük Risk (Aktif)': '#10B981',
                    'Orta Risk': '#F59E0B',
                    'Yüksek Risk (Terk Edilmiş)': '#EF4444'
                }
            )
            st.plotly_chart(fig_risk, use_container_width=True)

        with col_c2:
            st.write("##### En Yüksek Yaşam Boyu Değerine (CLV) Sahip İlk 10 Müşteri")
            top_10_clv = clv.sort_values(by='historical_clv', ascending=False).head(10)
            st.dataframe(top_10_clv[['customer_id', 'customer_name', 'channel', 'order_count', 'historical_clv', 'churn_risk']].rename(columns={
                'customer_name': 'Müşteri',
                'channel': 'Kanal',
                'order_count': 'Sipariş Sayısı',
                'historical_clv': 'Toplam Harcama ($)',
                'churn_risk': 'Churn Durumu'
            }), use_container_width=True)

if __name__ == "__main__":
    main()
