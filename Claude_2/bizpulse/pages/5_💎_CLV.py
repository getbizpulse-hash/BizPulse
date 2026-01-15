import streamlit as st
import pandas as pd
import plotly.express as px
from utils.segmentation import assign_segments
from utils.data_loader import aggregate_to_customers
from utils.models import fit_gamma_gamma
from utils.outreach import build_email_link, build_whatsapp_link, generate_coupon_code

st.set_page_config(page_title="CLV - Biz-Pulse", page_icon="💎", layout="wide")

st.title("💎 Customer Lifetime Value")

# Check if logged in and data loaded
if not st.session_state.get("logged_in", False):
    st.warning("Please log in first from the home page.")
    st.stop()

if not st.session_state.get("data_loaded", False):
    st.warning("Please upload your data first.")
    st.stop()

# Get data
raw_df = st.session_state.raw_data
business_name = st.session_state.business_name

# Date range filter
st.markdown("### 📅 Select Date Range")
col1, col2 = st.columns(2)

min_date = raw_df["start"].min().date()
max_date = raw_df["start"].max().date()

with col1:
    start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="clv_start")
with col2:
    end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="clv_end")

# Filter and aggregate
customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
customer_df = assign_segments(customer_df)

st.markdown("---")

# Fit CLV model
clv_results = fit_gamma_gamma(customer_df)

if not clv_results["success"]:
    st.warning(clv_results["message"])
    st.stop()

# CLV Overview
st.markdown("### 💎 Customer Lifetime Value Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Average CLV", f"${clv_results['avg_clv']:,.0f}")
with col2:
    st.metric("Top 10% CLV", f"${clv_results['top_10_pct_clv']:,.0f}")
with col3:
    st.metric("Total Predicted", f"${clv_results['total_clv']:,.0f}")

multiplier = clv_results['top_10_pct_clv'] / clv_results['avg_clv'] if clv_results['avg_clv'] > 0 else 1

st.info(f"""
**Your average customer is worth ${clv_results['avg_clv']:,.0f}** over their lifetime.
But your top 10% are worth **{multiplier:.1f}x more** — focus on keeping them happy.
""")

st.markdown("---")

# CLV Distribution
st.markdown("### 📊 CLV Distribution")

repeat_df = clv_results["repeat_customers"]

fig = px.histogram(
    repeat_df,
    x="clv",
    nbins=20,
    color_discrete_sequence=["#4ECDC4"]
)
fig.update_layout(
    xaxis_title="Customer Lifetime Value ($)",
    yaxis_title="Number of Customers"
)
st.plotly_chart(fig, use_container_width=True)

# Insights
high_clv = repeat_df[repeat_df["clv"] > clv_results["avg_clv"] * 2]
pct_high = len(high_clv) / len(repeat_df) * 100 if len(repeat_df) > 0 else 0

st.markdown(f"""
**📝 What this means:**

- **{len(repeat_df) - len(high_clv)} customers ({100-pct_high:.0f}%)** have CLV under ${clv_results['avg_clv']*2:,.0f}
- **{len(high_clv)} customers ({pct_high:.0f}%)** have CLV over ${clv_results['avg_clv']*2:,.0f}
- These {len(high_clv)} represent a significant portion of your future revenue
""")

st.markdown("---")

# Most Valuable Customers
st.markdown("### 🏆 Your Most Valuable Customers")

top_customers = repeat_df.nlargest(10, "clv")[["client_name", "frequency", "total_spend", "clv"]].copy()
top_customers.columns = ["Name", "Visits", "Total Spend", "CLV"]
top_customers["Total Spend"] = top_customers["Total Spend"].apply(lambda x: f"${x:,.0f}")
top_customers["CLV"] = top_customers["CLV"].apply(lambda x: f"${x:,.0f}")

col1, col2 = st.columns([4, 1])
with col2:
    csv = repeat_df.to_csv(index=False)
    st.download_button("📥 Export CSV", csv, "valuable_customers.csv", "text/csv")

st.dataframe(top_customers, use_container_width=True, hide_index=True)

st.markdown("""
💡 *These customers deserve VIP treatment — a small thank-you gift or priority booking can go a long way in keeping them loyal.*
""")

st.markdown("---")

# Hidden Gems
st.markdown("### 🔮 Hidden Gems: High Potential, Low Visits")

hidden_gems = clv_results["hidden_gems"]

if len(hidden_gems) > 0:
    st.markdown("These customers spend big when they visit — if they came more often, they'd be your top earners:")

    gems_display = hidden_gems[["client_name", "frequency", "avg_spend", "projected_clv_if_regular"]].copy()
    gems_display.columns = ["Name", "Visits", "Avg/Visit", "If Regular → CLV"]
    gems_display["Avg/Visit"] = gems_display["Avg/Visit"].apply(lambda x: f"${x:,.0f}")
    gems_display["If Regular → CLV"] = gems_display["If Regular → CLV"].apply(lambda x: f"${x:,.0f}")

    st.dataframe(gems_display.head(5), use_container_width=True, hide_index=True)

    # Reach out button
    if "gem_coupon" not in st.session_state:
        st.session_state.gem_coupon = generate_coupon_code("GEM")

    st.markdown(f"**Coupon code for Hidden Gems:** `{st.session_state.gem_coupon}`")
else:
    st.info("No hidden gems identified yet — need more customer data.")

# Technical details
with st.expander("🔧 Show technical details"):
    st.markdown(f"""
    - **Model:** Simplified Gamma-Gamma estimation
    - **Repeat customers analyzed:** {clv_results['n_repeat']}
    - **CLV formula:** Avg Spend × Frequency × 1.2 (growth factor)
    """)
