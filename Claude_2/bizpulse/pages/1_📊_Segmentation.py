import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.segmentation import SEGMENT_DEFINITIONS, get_segment_summary, assign_segments
from utils.data_loader import aggregate_to_customers

st.set_page_config(page_title="Segmentation - Biz-Pulse", page_icon="📊", layout="wide")

st.title("📊 Customer Segmentation")

# Check if logged in and data loaded
if not st.session_state.get("logged_in", False):
    st.warning("Please log in first from the home page.")
    st.stop()

if not st.session_state.get("data_loaded", False):
    st.warning("Please upload your data first.")
    st.stop()

# Get data
raw_df = st.session_state.raw_data

# Date range filter
st.markdown("### 📅 Select Date Range")
col1, col2 = st.columns(2)

min_date = raw_df["start"].min().date()
max_date = raw_df["start"].max().date()

with col1:
    start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
with col2:
    end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

# Filter and aggregate
customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
customer_df = assign_segments(customer_df)

st.markdown("---")

# Key Metrics
st.markdown("### 📈 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Customers", f"{len(customer_df):,}")
with col2:
    total_revenue = customer_df["total_spend"].sum()
    st.metric("Total Revenue", f"${total_revenue:,.0f}")
with col3:
    avg_visits = customer_df["frequency"].mean()
    st.metric("Avg Visits", f"{avg_visits:.1f}")
with col4:
    avg_ltv = customer_df["total_spend"].mean()
    st.metric("Avg Customer Value", f"${avg_ltv:,.0f}")

st.markdown("---")

# Charts
st.markdown("### 📊 Segment Analysis")

segment_summary = get_segment_summary(customer_df)

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Customers by Segment")
    fig_customers = px.pie(
        segment_summary,
        values="customer_count",
        names="segment",
        color="segment",
        color_discrete_map={seg: info["color"] for seg, info in SEGMENT_DEFINITIONS.items()},
        hole=0.4
    )
    fig_customers.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_customers, use_container_width=True)

with col2:
    st.markdown("#### Revenue by Segment")
    fig_revenue = px.bar(
        segment_summary,
        x="segment",
        y="total_revenue",
        color="segment",
        color_discrete_map={seg: info["color"] for seg, info in SEGMENT_DEFINITIONS.items()},
        text=segment_summary["total_revenue"].apply(lambda x: f"${x:,.0f}")
    )
    fig_revenue.update_traces(textposition="outside")
    fig_revenue.update_layout(showlegend=False, yaxis_title="Revenue ($)")
    st.plotly_chart(fig_revenue, use_container_width=True)

# Segment summary table
st.markdown("### 📋 Segment Summary")

summary_display = segment_summary.copy()
summary_display["total_revenue"] = summary_display["total_revenue"].apply(lambda x: f"${x:,.0f}")
summary_display["avg_revenue"] = summary_display["avg_revenue"].apply(lambda x: f"${x:,.0f}")
summary_display["avg_frequency"] = summary_display["avg_frequency"].apply(lambda x: f"{x:.1f}")
summary_display.columns = ["Segment", "Customers", "Total Revenue", "Avg Revenue", "Avg Visits"]

st.dataframe(summary_display, use_container_width=True, hide_index=True)

# Segment definitions
st.markdown("---")
st.markdown("### 📖 Segment Definitions")
def_cols = st.columns(4)
for i, (seg, info) in enumerate(SEGMENT_DEFINITIONS.items()):
    with def_cols[i]:
        st.markdown(f"**{seg}**")
        st.markdown(f"{info['description']}")
