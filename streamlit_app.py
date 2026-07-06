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


def clean_prompt(prompt):
    return prompt.lower().replace("@bot", " ").replace("@", " ").strip()


def find_brand_mentions(prompt, dataframe):
    prompt_lower = clean_prompt(prompt)
    brand_names = sorted(dataframe["name"].dropna().unique(), key=len, reverse=True)
    return [brand for brand in brand_names if brand.lower() in prompt_lower]


def normalize_lookup_text(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def available_values(dataframe, column):
    return sorted(str(value) for value in dataframe[column].dropna().unique())


def format_available_values(values):
    return ", ".join(f"**{value}**" for value in values)


def find_value_mentions(prompt, values, aliases=None):
    prompt_text = f" {normalize_lookup_text(prompt)} "
    aliases = aliases or {}
    matches = []

    for value in values:
        terms = [value] + aliases.get(value.lower(), [])
        for term in terms:
            term_text = f" {normalize_lookup_text(term)} "
            if term_text in prompt_text:
                matches.append(value)
                break

    return matches


def category_aliases(dataframe):
    aliases = {
        "fashion": ["apparel", "clothing", "clothes", "wear"],
        "footwear": ["shoe", "shoes", "sneaker", "sneakers"],
        "lifestyle": ["home", "living", "decor"],
    }
    available_categories = {category.lower() for category in available_values(dataframe, "category")}
    return {category: terms for category, terms in aliases.items() if category in available_categories}


def filter_by_values(dataframe, column, values):
    if not values:
        return dataframe
    return dataframe[dataframe[column].isin(values)]


def unsupported_slice_message(kind, requested, available):
    if kind == "filter":
        categories, platforms, regions = available
        return (
            f"BrandBot Analysis: I do not have a BrandPulse data slice for **{requested}**. "
            f"Available categories: {format_available_values(categories)}. "
            f"Available platforms: {format_available_values(platforms)}. "
            f"Available regions: {format_available_values(regions)}."
        )

    return (
        f"BrandBot Analysis: I do not have data for **{requested}** as a {kind}. "
        f"Available {kind}s are: {format_available_values(available)}."
    )


def extract_requested_slice(prompt, dataframe):
    prompt_lower = clean_prompt(prompt)
    categories = available_values(dataframe, "category")
    platforms = available_values(dataframe, "platform")
    regions = available_values(dataframe, "region")

    category_matches = find_value_mentions(prompt_lower, categories, category_aliases(dataframe))
    platform_matches = find_value_mentions(prompt_lower, platforms)
    region_matches = find_value_mentions(prompt_lower, regions)

    if category_matches:
        return "category", category_matches[0], filter_by_values(dataframe, "category", category_matches)
    if platform_matches:
        return "platform", platform_matches[0], filter_by_values(dataframe, "platform", platform_matches)
    if region_matches:
        return "region", region_matches[0], filter_by_values(dataframe, "region", region_matches)

    if "food" in prompt_lower or "beverage" in prompt_lower:
        return "unsupported_filter", "food and beverages", dataframe.iloc[0:0]

    slice_query_match = re.search(
        r"\b(?:top|best|highest|lowest|worst|least|rank|revenue|sales|units|anomaly|anomalies|trend)\b.*\b(?:in|for|from)\s+(.+)$",
        prompt_lower,
    )
    if slice_query_match:
        requested = slice_query_match.group(1).strip(" ?.!:")
        ignored_phrases = ["each category", "all categories", "revenue", "sales", "units"]
        if requested and not any(phrase in requested for phrase in ignored_phrases):
            return "unsupported_filter", requested, dataframe.iloc[0:0]

    return None, None, dataframe


def slice_label(kind, value):
    if kind == "category":
        return f"category **{value}**"
    if kind == "platform":
        return f"platform **{value}**"
    if kind == "region":
        return f"region **{value}**"
    return None


def help_summary():
    return (
        "BrandBot Analysis: You can ask me direct questions about the loaded BrandPulse data. "
        "For example:\n\n"
        "1. **Top brands** - `list top 3 brands`\n"
        "2. **Filtered rankings** - `top brands in footwear` or `top brands in West India`\n"
        "3. **Category leaders** - `top brands in each category`\n"
        "4. **Anomalies** - `show anomalies by platform`\n"
        "5. **Revenue** - `total revenue` or `revenue by platform`\n"
        "6. **Brand details** - `tell me about SoleStrike`\n"
        "7. **Compare brands** - `compare SoleStrike and TrailBlaze`"
    )


def top_brands_summary(dataframe, limit, ascending=False, scope_label=None):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any sales rows loaded to rank brands."

    top_brands = (
        dataframe.groupby("name", as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units_sold", "sum"))
        .sort_values(by="revenue", ascending=ascending)
        .head(limit)
    )

    lines = [
        f"{idx}. **{row['name']}** - {format_in_inr(row['revenue'])} revenue, {int(row['units']):,} units"
        for idx, row in enumerate(top_brands.to_dict("records"), start=1)
    ]
    label = "Lowest brands by revenue" if ascending else "Top brands by revenue"
    if scope_label:
        label = f"{label} for {scope_label}"
    return f"BrandBot Analysis: {label}:\n\n" + "\n".join(lines)


def top_brands_by_category_summary(dataframe, limit):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any sales rows loaded to rank categories."

    category_totals = (
        dataframe.groupby(["category", "name"], as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units_sold", "sum"))
        .sort_values(["category", "revenue"], ascending=[True, False])
    )

    lines = []
    for category, category_df in category_totals.groupby("category", sort=True):
        leaders = category_df.head(limit)
        leader_text = "; ".join(
            f"**{row['name']}** ({format_in_inr(row['revenue'])}, {int(row['units']):,} units)"
            for row in leaders.to_dict("records")
        )
        lines.append(f"- **{category.title()}**: {leader_text}")

    return "BrandBot Analysis: Top brands in each category:\n\n" + "\n".join(lines)


def category_summary(dataframe):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any sales rows loaded to summarize categories."

    category_totals = (
        dataframe.groupby("category", as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units_sold", "sum"), brands=("brand_id", "nunique"))
        .sort_values("revenue", ascending=False)
    )
    lines = [
        f"{idx}. **{row['category'].title()}** - {format_in_inr(row['revenue'])}, {int(row['units']):,} units, {int(row['brands'])} brands"
        for idx, row in enumerate(category_totals.to_dict("records"), start=1)
    ]
    return "BrandBot Analysis: Category performance:\n\n" + "\n".join(lines)


def anomaly_summary(dataframe, scope_label=None):
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

    brand_lines = [
        f"{idx}. **{brand}** - {count} records"
        for idx, (brand, count) in enumerate(brand_counts.head(3).items(), start=1)
    ]
    platform_lines = [
        f"{idx}. **{platform}** - {count} records"
        for idx, (platform, count) in enumerate(platform_counts.head(3).items(), start=1)
    ]

    scope_text = f" for {scope_label}" if scope_label else ""
    return (
        f"BrandBot Analysis: Anomalies{scope_text}. "
        f"Detected **{total_anomalies}** anomalous sales records. "
        f"Highest anomaly platform: **{top_platform}** ({top_platform_count} records). "
        f"Most affected brand: **{top_brand}** ({top_brand_count} records).\n\n"
        "Top anomaly brands:\n"
        + "\n".join(brand_lines)
        + "\n\nTop anomaly platforms:\n"
        + "\n".join(platform_lines)
    )


def revenue_summary(dataframe, scope_label=None):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any sales rows loaded to summarize revenue."

    total_revenue = dataframe["revenue"].sum()
    total_units = int(dataframe["units_sold"].sum())
    active_brands = dataframe["brand_id"].nunique()
    scope_text = f" for {scope_label}" if scope_label else ""
    return (
        "BrandBot Analysis: "
        f"Total revenue{scope_text} is **{format_in_inr(total_revenue)}** across "
        f"**{total_units:,}** units and **{active_brands}** active brands."
    )


def platform_summary(dataframe):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any sales rows loaded to summarize platforms."

    platform_totals = (
        dataframe.groupby("platform", as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units_sold", "sum"), anomalies=("is_anomalous", "sum"))
        .sort_values("revenue", ascending=False)
    )
    lines = [
        f"{idx}. **{row['platform']}** - {format_in_inr(row['revenue'])}, {int(row['units']):,} units, {int(row['anomalies'])} anomalies"
        for idx, row in enumerate(platform_totals.to_dict("records"), start=1)
    ]
    return "BrandBot Analysis: Revenue by platform:\n\n" + "\n".join(lines)


def region_summary(dataframe):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any sales rows loaded to summarize regions."

    region_totals = (
        dataframe.groupby("region", as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units_sold", "sum"), brands=("brand_id", "nunique"))
        .sort_values("revenue", ascending=False)
    )
    lines = [
        f"{idx}. **{row['region']}** - {format_in_inr(row['revenue'])}, {int(row['units']):,} units, {int(row['brands'])} brands"
        for idx, row in enumerate(region_totals.to_dict("records"), start=1)
    ]
    return "BrandBot Analysis: Regional performance:\n\n" + "\n".join(lines)


def brand_detail_summary(dataframe, brand_name):
    brand_df = dataframe[dataframe["name"] == brand_name]
    if brand_df.empty:
        return f"BrandBot Analysis: I could not find sales data for **{brand_name}**."

    row = brand_df.iloc[0]
    revenue = brand_df["revenue"].sum()
    units = int(brand_df["units_sold"].sum())
    anomalies = int(brand_df["is_anomalous"].sum())
    avg_return_rate = brand_df["return_rate"].mean() * 100
    top_platform = brand_df.groupby("platform")["revenue"].sum().sort_values(ascending=False).index[0]

    return (
        f"BrandBot Analysis: **{brand_name}** is a **{row['category']}** brand in **{row['region']}**. "
        f"It has **{format_in_inr(revenue)}** revenue, **{units:,}** units sold, "
        f"**{anomalies}** anomalous records, and an average return rate of **{avg_return_rate:.1f}%**. "
        f"Top platform by revenue: **{top_platform}**."
    )


def unknown_brand_message(dataframe):
    return (
        "BrandBot Analysis: I could not match that to a known BrandPulse brand. "
        f"Available brands are: {format_available_values(available_values(dataframe, 'name'))}."
    )


def compare_brands_summary(dataframe, brands):
    rows = []
    for brand in brands[:4]:
        brand_df = dataframe[dataframe["name"] == brand]
        if brand_df.empty:
            continue
        rows.append({
            "name": brand,
            "revenue": brand_df["revenue"].sum(),
            "units": int(brand_df["units_sold"].sum()),
            "anomalies": int(brand_df["is_anomalous"].sum()),
            "return_rate": brand_df["return_rate"].mean() * 100,
        })

    if len(rows) < 2:
        return "BrandBot Analysis: Please mention at least two known brand names to compare."

    rows = sorted(rows, key=lambda row: row["revenue"], reverse=True)
    lines = [
        f"{idx}. **{row['name']}** - {format_in_inr(row['revenue'])}, {row['units']:,} units, {row['anomalies']} anomalies, {row['return_rate']:.1f}% avg return rate"
        for idx, row in enumerate(rows, start=1)
    ]
    return "BrandBot Analysis: Brand comparison:\n\n" + "\n".join(lines)


def trend_summary(dataframe, scope_label=None):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any sales rows loaded to summarize trends."

    monthly = (
        dataframe.groupby(dataframe["date"].dt.to_period("M"))
        .agg(revenue=("revenue", "sum"), units=("units_sold", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    best = monthly.iloc[0]
    latest = monthly.sort_values("date").iloc[-1]
    scope_text = f" for {scope_label}" if scope_label else ""
    return (
        "BrandBot Analysis: "
        f"Best revenue month{scope_text} was **{best['date']}** with **{format_in_inr(best['revenue'])}**. "
        f"Latest month in the data is **{latest['date']}** with **{format_in_inr(latest['revenue'])}** "
        f"and **{int(latest['units']):,}** units."
    )


def list_brands_summary(dataframe):
    if dataframe.empty:
        return "BrandBot Analysis: I do not have any brands loaded."

    brands = sorted(dataframe["name"].dropna().unique())
    return "BrandBot Analysis: Available brands are:\n\n" + ", ".join(f"**{brand}**" for brand in brands)


def answer_brandbot(prompt, dataframe):
    prompt_lower = clean_prompt(prompt)
    mentioned_brands = find_brand_mentions(prompt, dataframe)
    slice_kind, slice_value, scoped_df = extract_requested_slice(prompt, dataframe)

    if slice_kind == "unsupported_filter":
        return unsupported_slice_message(
            "filter",
            slice_value,
            (
                available_values(dataframe, "category"),
                available_values(dataframe, "platform"),
                available_values(dataframe, "region"),
            ),
        )

    scoped_label = slice_label(slice_kind, slice_value)

    if any(phrase in prompt_lower for phrase in ["how can i use", "what can you do", "help", "examples", "guide"]):
        return help_summary()

    if len(mentioned_brands) >= 2 and any(word in prompt_lower for word in ["compare", "versus", "vs", "difference"]):
        return compare_brands_summary(dataframe, mentioned_brands)

    if any(word in prompt_lower for word in ["compare", "versus", "vs", "difference"]) and len(mentioned_brands) < 2:
        return "BrandBot Analysis: Please mention two known BrandPulse brands to compare."

    if len(mentioned_brands) == 1 and any(word in prompt_lower for word in ["about", "tell", "detail", "performance", "summary", "revenue", "sales", "anomaly"]):
        return brand_detail_summary(dataframe, mentioned_brands[0])

    analytics_terms = [
        "category", "revenue", "sales", "unit", "anomaly", "anomalies", "outlier",
        "return", "platform", "region", "trend", "top", "best", "highest"
    ]
    if any(word in prompt_lower for word in ["about", "tell", "detail"]) and not any(term in prompt_lower for term in analytics_terms):
        return unknown_brand_message(dataframe)

    if (
        any(phrase in prompt_lower for phrase in ["each category", "all categories", "by category", "category wise", "category-wise"])
        and any(word in prompt_lower for word in ["top", "best", "highest", "leader", "rank"])
    ):
        return top_brands_by_category_summary(dataframe, extract_requested_limit(prompt, default=1))

    if scoped_label and any(word in prompt_lower for word in ["lowest", "worst", "least"]):
        return top_brands_summary(scoped_df, extract_requested_limit(prompt), ascending=True, scope_label=scoped_label)

    if scoped_label and any(word in prompt_lower for word in ["top", "best", "highest", "rank", "leader"]):
        return top_brands_summary(scoped_df, extract_requested_limit(prompt), scope_label=scoped_label)

    if "category" in prompt_lower:
        return category_summary(dataframe)

    if any(word in prompt_lower for word in ["anomaly", "anomalies", "outlier", "return"]):
        return anomaly_summary(scoped_df if scoped_label else dataframe, scoped_label)

    if "platform" in prompt_lower or "channel" in prompt_lower:
        return platform_summary(dataframe)

    if "region" in prompt_lower or "regional" in prompt_lower:
        return region_summary(dataframe)

    if any(word in prompt_lower for word in ["trend", "month", "monthly", "time"]):
        return trend_summary(scoped_df if scoped_label else dataframe, scoped_label)

    if "list" in prompt_lower and "brand" in prompt_lower and not any(word in prompt_lower for word in ["top", "best", "highest"]):
        return list_brands_summary(dataframe)

    if any(word in prompt_lower for word in ["lowest", "worst", "least"]):
        return top_brands_summary(dataframe, extract_requested_limit(prompt), ascending=True)

    if any(word in prompt_lower for word in ["top", "best", "highest", "rank", "leader"]):
        return top_brands_summary(dataframe, extract_requested_limit(prompt))

    if any(word in prompt_lower for word in ["revenue", "sales", "units", "total"]):
        return revenue_summary(scoped_df if scoped_label else dataframe, scoped_label)

    return (
        "BrandBot Analysis: I answer questions from the loaded BrandPulse sales data. "
        "Try **list top 3 brands**, **top brands in each category**, **show anomalies**, "
        "**revenue by platform**, or **how can I use you?**"
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
            {"role": "assistant", "content": "Welcome to the BrandPulse Intelligence Feed. I am BrandBot. Ask me about brands, categories, revenue, platforms, regions, trends, or anomalies."}
        ]
        
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    if prompt := st.chat_input("Ask about BrandPulse data... e.g. 'top brands in each category'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        response = answer_brandbot(prompt, merged_df)
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)
