import streamlit as st
import pandas as pd
import plotly.express as px
from utils.segmentation import assign_segments, SEGMENT_DEFINITIONS
from utils.data_loader import aggregate_to_customers

st.set_page_config(page_title="Retention - Biz-Pulse", page_icon="⚠️", layout="wide")

st.title("⚠️ Retention & Churn History")

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
    start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="ret_start")
with col2:
    end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="ret_end")

# Filter and aggregate
customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
customer_df = assign_segments(customer_df)

st.markdown("---")

# Calculate at-risk customers
overdue_30 = customer_df[customer_df["days_since_visit"] > 30]
overdue_60 = customer_df[customer_df["days_since_visit"] > 60]
overdue_90 = customer_df[customer_df["days_since_visit"] > 90]

# Customers at Risk
st.markdown("### 🚨 Customers at Risk")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Overdue (30+ days)", len(overdue_30), help="Customers who haven't visited in 30+ days")
with col2:
    st.metric("Slipping (60+ days)", len(overdue_60), help="Customers who haven't visited in 60+ days")
with col3:
    st.metric("Lost (90+ days)", len(overdue_90), help="Customers who haven't visited in 90+ days")

# Calculate value at risk
valuable_at_risk = overdue_30[overdue_30["segment"].isin(["Casual", "Regular", "Superuser"])]
value_at_risk = valuable_at_risk["total_spend"].sum() * 0.5  # Assume 50% of historical value at risk

st.info(f"""
**{len(valuable_at_risk)} valuable customers** (Casual or above) are overdue.
A quick check-in could bring them back and protect **${value_at_risk:,.0f}** in potential annual revenue.
""")

st.markdown("---")

# Who needs attention
st.markdown("### 📋 Who Needs Attention?")

# Prepare at-risk table
at_risk_df = overdue_30.copy()
at_risk_df["risk_value"] = at_risk_df["total_spend"]  # Simple proxy for now
at_risk_df = at_risk_df.sort_values("risk_value", ascending=False)

# Display columns
display_df = at_risk_df[["client_name", "segment", "recency", "days_since_visit", "risk_value"]].copy()
display_df.columns = ["Name", "Segment", "Last Visit", "Days Ago", "$ at Risk"]
display_df["Last Visit"] = display_df["Last Visit"].dt.strftime("%b %d, %Y")
display_df["$ at Risk"] = display_df["$ at Risk"].apply(lambda x: f"${x:,.0f}")

col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f"**Sort by:** Value at Risk (highest first)")
with col2:
    csv = at_risk_df.to_csv(index=False)
    st.download_button("📥 Export CSV", csv, "at_risk_customers.csv", "text/csv")

st.dataframe(display_df.head(20), use_container_width=True, hide_index=True)

st.caption('💡 "$ at Risk" = estimated annual value if this customer churns permanently')

st.markdown("---")

# Retention insights
st.markdown("### 📈 Retention Insights")

# Calculate retention metrics
total_customers = len(customer_df)
explorers = len(customer_df[customer_df["segment"] == "Explorer"])
repeaters = total_customers - explorers

repeat_rate = repeaters / total_customers if total_customers > 0 else 0

# Segment retention
regulars = customer_df[customer_df["segment"].isin(["Regular", "Superuser"])]
regular_active = regulars[regulars["days_since_visit"] <= 45]
regular_retention = len(regular_active) / len(regulars) if len(regulars) > 0 else 0

st.markdown(f"""
**📝 What this means:**

- **{repeat_rate:.0%} of customers** came back for a second visit (the rest are one-time Explorers)
- **Regulars have {regular_retention:.0%} retention** — your loyal base {"is solid" if regular_retention > 0.8 else "needs attention"}
- **Biggest drop-off:** After visit 1 → 2 ({100-repeat_rate*100:.0f}% never return)
""")

# Days since visit distribution
st.markdown("#### Days Since Last Visit")

fig = px.histogram(
    customer_df,
    x="days_since_visit",
    color="segment",
    color_discrete_map={seg: info["color"] for seg, info in SEGMENT_DEFINITIONS.items()},
    nbins=30,
    title=""
)
fig.update_layout(
    xaxis_title="Days Since Last Visit",
    yaxis_title="Number of Customers",
    legend_title="Segment"
)
fig.add_vline(x=30, line_dash="dash", line_color="orange", annotation_text="30 days")
fig.add_vline(x=60, line_dash="dash", line_color="red", annotation_text="60 days")

st.plotly_chart(fig, use_container_width=True)
