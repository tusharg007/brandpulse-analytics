import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os
import re
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Setup Page Config
st.set_page_config(
    page_title="BrandPulse Analytics Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Dark Premium Look
st.markdown("""
<style>
    /* Dark Theme Core Adjustments */
    .stApp {
        background-color: #0A0B0F;
        color: #F1F5F9;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #F1F5F9;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94A3B8;
    }
    /* Card design */
    .metric-card {
        background-color: #12141A;
        border: 1px solid #252836;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Format Currency (Defined globally to avoid NameErrors in different views)
def format_in_inr(v):
    if v >= 10000000:
        return f"₹{v / 10000000:.2f} Cr"
    elif v >= 100000:
        return f"₹{v / 100000:.2f} L"
    else:
        return f"₹{v:,.2f}"

# Dashboard and chatbot helpers
def normalize_date_range(date_range, min_date, max_date):
    if isinstance(date_range, (tuple, list)):
        if len(date_range) >= 2:
            start_date, end_date = date_range[0], date_range[1]
        elif len(date_range) == 1:
            start_date = end_date = date_range[0]
        else:
            start_date, end_date = min_date, max_date
    else:
        start_date = end_date = date_range

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    return start_date, end_date


def extract_requested_limit(prompt, default=3, maximum=10):
    match = re.search(r"\btop\s+(\d+)\b|\b(\d+)\s+brands?\b", prompt.lower())
    if not match:
        return default

    requested = int(next(group for group in match.groups() if group))
    return max(1, min(requested, maximum))


def top_brands_summary(dataframe, limit):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any sales rows loaded to rank brands."

    top_brands = (
        dataframe.groupby("name", as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units_sold", "sum"))
        .sort_values(by="revenue", ascending=False)
        .head(limit)
    )

    lines = [
        f"{idx}. **{row['name']}** - {format_in_inr(row['revenue'])} revenue, {int(row['units']):,} units"
        for idx, row in enumerate(top_brands.to_dict("records"), start=1)
    ]
    return "BrandBot Analysis: Top brands by revenue:\n\n" + "\n".join(lines)


def anomaly_summary(dataframe):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any sales rows loaded to analyze anomalies."

    anomalous_df = dataframe[dataframe["is_anomalous"] == 1]
    total_anomalies = int(anomalous_df.shape[0])
    if total_anomalies == 0:
        return "BrandBot Analysis: No sales anomalies are currently flagged in the loaded data."

    platform_counts = anomalous_df["platform"].value_counts()
    top_platform = platform_counts.index[0]
    top_platform_count = int(platform_counts.iloc[0])
    brand_counts = anomalous_df["name"].value_counts()
    top_brand = brand_counts.index[0]
    top_brand_count = int(brand_counts.iloc[0])

    return (
        "BrandBot Analysis: "
        f"Detected **{total_anomalies}** anomalous sales records. "
        f"Highest anomaly platform: **{top_platform}** ({top_platform_count} records). "
        f"Most affected brand: **{top_brand}** ({top_brand_count} records)."
    )


def revenue_summary(dataframe):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any sales rows loaded to summarize revenue."

    total_revenue = dataframe["revenue"].sum()
    total_units = int(dataframe["units_sold"].sum())
    active_brands = dataframe["brand_id"].nunique()
    return (
        "BrandBot Analysis: "
        f"Total revenue is **{format_in_inr(total_revenue)}** across "
        f"**{total_units:,}** units and **{active_brands}** active brands."
    )


def answer_brandbot(prompt, dataframe):
    prompt_lower = prompt.lower()
    if "@bot" not in prompt_lower and "bot" not in prompt_lower:
        return "For AI assistant feedback, please prepend your prompt with **@bot**."

    if any(word in prompt_lower for word in ["top", "best", "highest", "rank", "leader"]):
        return top_brands_summary(dataframe, extract_requested_limit(prompt))

    if any(word in prompt_lower for word in ["anomaly", "anomalies", "outlier", "return"]):
        return anomaly_summary(dataframe)

    if any(word in prompt_lower for word in ["revenue", "sales", "units", "total"]):
        return revenue_summary(dataframe)

    return (
        "BrandBot Analysis: I answer only from the loaded BrandPulse sales data. "
        "Try asking **@bot list top 3 brands**, **@bot show anomalies**, or "
        "**@bot total revenue**."
    )


# Helper function to get database connection
def get_db_data():
    db_path = os.path.join("backend", "brandpulse_local.db")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            # Read Brands
            brands_df = pd.read_sql_query("SELECT * FROM brands", conn)
            # Read Sales
            sales_df = pd.read_sql_query("SELECT * FROM sales_records", conn)
            # Read ETL logs
            etl_df = pd.read_sql_query("SELECT * FROM etl_logs", conn)
            conn.close()
            return brands_df, sales_df, etl_df
        except Exception:
            pass
    
    # Fallback/Standalone Mock Data Generation
    np.random.seed(42)
    categories = ["fashion", "footwear", "lifestyle"]
    regions = ["North India", "West India", "South India", "East India", "Pan India"]
    brand_names = ["UrbanWeave", "SoleStrike", "AuraLiving", "ThreadCraft", "StrideX", "ZenNest", "VogueFlare", "TrailBlaze", "PureEssence", "NovaStitch"]
    
    brands_data = []
    for i, name in enumerate(brand_names):
        brands_data.append({
            "id": i + 1,
            "name": name,
            "category": categories[i % len(categories)],
            "region": regions[i % len(regions)],
            "launch_date": (date(2020, 1, 1) + timedelta(days=int(np.random.randint(0, 1000)))).isoformat()
        })
    brands_df = pd.DataFrame(brands_data)
    
    sales_data = []
    platforms = ["Amazon", "Flipkart", "Direct"]
    base_price = {"fashion": 1200, "footwear": 2500, "lifestyle": 800}
    
    start_date = date(2024, 1, 1)
    end_date = date(2025, 6, 1)
    days_range = (end_date - start_date).days
    
    seen = set()
    count = 0
    while count < 800:
        brand = brands_df.iloc[np.random.randint(0, len(brands_df))]
        dt = start_date + timedelta(days=int(np.random.randint(0, days_range)))
        platform = np.random.choice(platforms)
        
        key = (brand["id"], dt, platform)
        if key in seen:
            continue
        seen.add(key)
        
        units_sold = int(np.random.randint(5, 500))
        price = base_price[brand["category"]] * np.random.uniform(0.7, 1.3)
        revenue = round(units_sold * price, 2)
        return_rate = round(float(np.random.uniform(0.01, 0.45)), 4)
        is_anomalous = 1 if return_rate > 0.3 else 0
        
        sales_data.append({
            "id": count + 1,
            "brand_id": brand["id"],
            "date": dt.isoformat(),
            "revenue": revenue,
            "units_sold": units_sold,
            "platform": platform,
            "return_rate": return_rate,
            "revenue_per_unit": round(revenue / units_sold, 2),
            "is_anomalous": is_anomalous
        })
        count += 1
        
    sales_df = pd.DataFrame(sales_data)
    
    # Mock ETL Logs
    etl_data = [
        {"id": 1, "run_timestamp": datetime.now().isoformat(), "status": "success", "records_processed": len(sales_df), "anomalies_detected": int(sales_df["is_anomalous"].sum()), "duration_seconds": 1.42}
    ]
    etl_df = pd.DataFrame(etl_data)
    
    return brands_df, sales_df, etl_df

# Load Data
brands_df, sales_df, etl_df = get_db_data()

# Process Data
sales_df['date'] = pd.to_datetime(sales_df['date'])
merged_df = sales_df.merge(brands_df, left_on='brand_id', right_on='id', suffixes=('', '_brand'))

# Sidebar Navigation & Filters
st.sidebar.title("⚡ BrandPulse")
st.sidebar.caption("Real-Time D2C Analytics & Intelligence")

app_mode = st.sidebar.selectbox("Choose the View", ["Dashboard", "Brands Directory", "AI Intelligence Chat"])

if app_mode == "Dashboard":
    st.title("⚡ BrandPulse Analytics")
    st.caption("Live insights and sales anomalies")
    
    # Filters
    st.sidebar.subheader("Filters")
    selected_brand_name = st.sidebar.selectbox("Select Brand", ["All Brands"] + list(brands_df["name"].unique()))
    
    # Date Filter
    min_date = sales_df['date'].min().date()
    max_date = sales_df['date'].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    start_date, end_date = normalize_date_range(date_range, min_date, max_date)
    
    # Apply filters
    filtered_df = merged_df[
        (merged_df['date'].dt.date >= start_date) & 
        (merged_df['date'].dt.date <= end_date)
    ]
    if selected_brand_name != "All Brands":
        filtered_df = filtered_df[filtered_df['name'] == selected_brand_name]
        
    # KPIs
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    total_rev = filtered_df["revenue"].sum()
    total_units = filtered_df["units_sold"].sum()
    active_brands_count = filtered_df["brand_id"].nunique()
    anomalies_count = filtered_df["is_anomalous"].sum()
    
    with kpi_col1:
        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Revenue", format_in_inr(total_rev))
        st.markdown('</div>', unsafe_allow_html=True)
    with kpi_col2:
        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Units", f"{total_units:,}")
        st.markdown('</div>', unsafe_allow_html=True)
    with kpi_col3:
        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Active Brands", f"{active_brands_count}")
        st.markdown('</div>', unsafe_allow_html=True)
    with kpi_col4:
        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Anomalies", f"{anomalies_count}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    if filtered_df.empty:
        st.warning("No sales data matches the selected brand and date range.")
    else:
        # Main Trend Chart
        st.subheader("Revenue Trend Over Time")
        trend_df = filtered_df.groupby(filtered_df['date'].dt.to_period('M')).agg({'revenue': 'sum'}).reset_index()
        trend_df['date'] = trend_df['date'].dt.to_timestamp()
        
        fig_trend = px.area(
            trend_df, x="date", y="revenue",
            color_discrete_sequence=["#6366F1"],
            template="plotly_dark"
        )
        fig_trend.update_layout(
            plot_bgcolor="#12141A",
            paper_bgcolor="#0A0B0F",
            margin=dict(l=20, r=20, t=10, b=10),
            height=320,
            xaxis_title=None,
            yaxis_title=None
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Columns for secondary charts
        col_left, col_right = st.columns([1.5, 1])
        
        with col_left:
            st.subheader("Top Brands by Revenue")
            top_b_df = filtered_df.groupby("name").agg({"revenue": "sum"}).reset_index().sort_values(by="revenue", ascending=False).head(5)
            # Use simple string representation for color scale to avoid Plotly version discrepancies
            fig_bar = px.bar(
                top_b_df, x="revenue", y="name", orientation="h",
                color="revenue", color_continuous_scale="Purples",
                template="plotly_dark"
            )
            fig_bar.update_layout(
                plot_bgcolor="#12141A",
                paper_bgcolor="#0A0B0F",
                margin=dict(l=20, r=20, t=10, b=10),
                height=280,
                xaxis_title=None,
                yaxis_title=None,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_right:
            st.subheader("Platform Revenue Split")
            plat_df = filtered_df.groupby("platform").agg({"revenue": "sum"}).reset_index()
            fig_pie = px.pie(
                plat_df, values="revenue", names="platform", hole=0.5,
                color_discrete_sequence=["#6366F1", "#F59E0B", "#10B981"],
                template="plotly_dark"
            )
            fig_pie.update_layout(
                plot_bgcolor="#12141A",
                paper_bgcolor="#0A0B0F",
                margin=dict(l=20, r=20, t=10, b=10),
                height=280
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # ETL Log Status Table
    st.subheader("Pipeline status logs")
    st.dataframe(etl_df, hide_index=True, use_container_width=True)

elif app_mode == "Brands Directory":
    st.title("📦 Brands Directory")
    st.caption("Expandable view of active brands portfolio")
    
    for idx, row in brands_df.iterrows():
        # Get brand-specific sales metrics
        brand_sales = merged_df[merged_df["brand_id"] == row["id"]]
        total_brand_rev = brand_sales["revenue"].sum()
        total_brand_units = brand_sales["units_sold"].sum()
        
        with st.expander(f"🏢 {row['name']} ({row['category'].upper()} | Region: {row['region']})"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Brand Revenue", format_in_inr(total_brand_rev))
            with col2:
                st.metric("Units Sold", f"{total_brand_units:,}")
            with col3:
                st.metric("Launch Date", row["launch_date"])

elif app_mode == "AI Intelligence Chat":
    st.title("💬 BrandBot Intelligence Feed")
    st.caption("Ask questions about anomalies, performance, or general statistics")
    
    # Simple simulated conversation state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to the BrandPulse Intelligence Feed. I am BrandBot. Ask me about our top brands or anomalies!"}
        ]
        
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    if prompt := st.chat_input("Type something... e.g. '@bot list top 3 brands'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        response = answer_brandbot(prompt, merged_df)
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)
