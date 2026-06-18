import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Page setup
st.set_page_config(
    page_title="BizAnalytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title & Subtitle
st.title("📊 Business Sales Analytics")
st.markdown("Real-time revenue metrics and product performance insights.")

# Cache data loading
@st.cache_data(show_spinner=False)
def load_data():
    conn = sqlite3.connect("data.db")
    df_products = pd.read_sql("SELECT * FROM products", conn)
    df_orders = pd.read_sql("SELECT * FROM orders", conn)
    conn.close()
    df_orders["order_date"] = pd.to_datetime(df_orders["order_date"])
    return df_products, df_orders

with st.spinner("Loading data..."):
    df_products, df_orders = load_data()

# Sidebar filters
st.sidebar.header("Filter Options")

# Category filter
all_categories = sorted(df_orders["category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Product Category",
    options=all_categories,
    default=all_categories
)

# Date filter
min_date = df_orders["order_date"].min().date()
max_date = df_orders["order_date"].max().date()
date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Quality filter
min_rating = st.sidebar.slider(
    "Minimum Product Rating",
    min_value=1.0,
    max_value=5.0,
    value=1.0,
    step=0.1
)

# Guards
if not selected_categories:
    st.warning("Please select at least one category to display dashboard results.")
    st.stop()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0] if date_range else min_date

# Apply Filters
filtered_orders = df_orders[
    (df_orders["category"].isin(selected_categories)) &
    (df_orders["order_date"].dt.date >= start_date) &
    (df_orders["order_date"].dt.date <= end_date)
]
filtered_products = df_products[df_products["avg_rating"] >= min_rating]

# KPI metrics section
total_revenue = filtered_orders["revenue"].sum()
total_profit = filtered_orders["profit"].sum()
total_orders = filtered_orders["order_id"].nunique()
total_units_sold = filtered_orders["quantity"].sum()
avg_rating = filtered_products["avg_rating"].mean()
avg_discount = filtered_products["discount_pct"].mean()

metric_cols = st.columns(6)
metric_cols[0].metric("Total Revenue", f"${total_revenue:,.0f}")
metric_cols[1].metric("Est. Profit", f"${total_profit:,.0f}")
metric_cols[2].metric("Total Orders", f"{total_orders:,}")
metric_cols[3].metric("Units Sold", f"{total_units_sold:,}")
metric_cols[4].metric("Avg Rating", f"{avg_rating:.2f} / 5")
metric_cols[5].metric("Avg Discount", f"{avg_discount:.1f}%")

st.markdown("---")

# Main Charts Layout
tab1, tab2 = st.tabs(["📊 Revenue Analysis", "🏆 Product Intelligence"])

with tab1:
    col1, col2 = st.columns([1, 1.5], gap="large")
    
    with col1:
        # Revenue by Category
        cat_revenue = (
            filtered_orders.groupby("category")["revenue"].sum()
            .reset_index()
            .sort_values("revenue", ascending=True)
        )
        fig_bar = px.bar(
            cat_revenue,
            x="revenue",
            y="category",
            orientation="h",
            title="Revenue by Category",
            labels={"revenue": "Revenue ($)", "category": "Category"},
            color="revenue",
            color_continuous_scale="Viridis"
        )
        fig_bar.update_layout(showlegend=False, height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col2:
        # Daily Revenue Trend
        daily = (
            filtered_orders.groupby(filtered_orders["order_date"].dt.date)["revenue"].sum()
            .reset_index()
            .rename(columns={"order_date": "Date", "revenue": "Daily Revenue ($)"})
        )
        daily["7-Day Avg"] = daily["Daily Revenue ($)"].rolling(7).mean()
        
        fig_line = px.line(
            daily,
            x="Date",
            y=["Daily Revenue ($)", "7-Day Avg"],
            title="Daily Revenue Trend",
            labels={"value": "Revenue ($)", "variable": "Metric"}
        )
        fig_line.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    col3, col4 = st.columns([1.5, 1], gap="large")
    
    with col3:
        # Top 10 Products by Revenue
        top_products = (
            filtered_orders.groupby("product_name")["revenue"].sum()
            .reset_index()
            .sort_values("revenue", ascending=False)
            .head(10)
            .sort_values("revenue", ascending=True)
        )
        fig_top = px.bar(
            top_products,
            x="revenue",
            y="product_name",
            orientation="h",
            title="Top 10 Products by Revenue",
            labels={"revenue": "Revenue ($)", "product_name": "Product"},
            color="revenue",
            color_continuous_scale="Plasma"
        )
        fig_top.update_layout(showlegend=False, height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_top, use_container_width=True)
        
    with col4:
        # Price vs Rating scatter chart
        fig_scatter = px.scatter(
            filtered_products,
            x="price_usd",
            y="avg_rating",
            color="category",
            size="units_in_stock",
            hover_name="product_name",
            title="Product Price vs. Rating",
            labels={"price_usd": "Price (USD)", "avg_rating": "Rating", "category": "Category"}
        )
        fig_scatter.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# Raw Data Section
with st.expander("🔍 Explore Raw Order Data"):
    display_cols = ["order_id", "order_date", "product_name", "category",
                    "brand", "quantity", "unit_price", "revenue", "profit"]
    display_cols = [c for c in display_cols if c in filtered_orders.columns]
    
    st.dataframe(
        filtered_orders[display_cols].sort_values("order_date", ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=300
    )
    
    csv_data = filtered_orders[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Filtered Data (CSV)",
        data=csv_data,
        file_name="filtered_sales_data.csv",
        mime="text/csv"
    )