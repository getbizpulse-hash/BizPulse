import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.segmentation import assign_segments
from utils.data_loader import aggregate_to_customers
from utils.models import fit_zt_nbd

st.set_page_config(page_title="Latent Demand - Biz-Pulse", page_icon="🎯", layout="wide")

st.title("🎯 Latent Demand Analysis")

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
    start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="ld_start")
with col2:
    end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="ld_end")

# Filter and aggregate
customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
customer_df = assign_segments(customer_df)

st.markdown("---")

# Fit NBD model
with st.spinner("Fitting model..."):
    nbd_results = fit_zt_nbd(customer_df)

# The Big Picture
st.markdown("### 🎯 The Big Picture")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Current Customers", f"{nbd_results['n_observed']:,.0f}")
with col2:
    st.metric("Potential Customers", f"{nbd_results['f0']:,.0f}", help="Estimated customers who haven't found you yet")
with col3:
    st.metric("Market Captured", f"{nbd_results['market_reached']:.0%}")

st.info(f"""
**What this means:** You've captured about {nbd_results['market_reached']:.0%} of your potential market.
There are roughly {nbd_results['f0']:,.0f} people in your area who could become customers but haven't found you yet — that's real growth potential.
""")

st.markdown("---")

# Visit frequency chart
st.markdown("### 📊 How Often Do Customers Visit?")

freq_actual = nbd_results["freq_actual"]
freq_predicted = nbd_results["freq_predicted"]

fig = go.Figure()

fig.add_trace(go.Bar(
    x=freq_actual.index.astype(str),
    y=freq_actual.values,
    name="Actual",
    marker_color="#4ECDC4"
))

fig.add_trace(go.Bar(
    x=freq_predicted.index.astype(str),
    y=freq_predicted.values,
    name="Model Predicted",
    marker_color="#FF6B6B",
    opacity=0.7
))

fig.update_layout(
    barmode="group",
    xaxis_title="Number of Visits",
    yaxis_title="Number of Customers",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# Insights
one_timers = freq_actual.get(1, 0)
total = freq_actual.sum()
one_timer_pct = one_timers / total if total > 0 else 0

# Find mode (most common visit count)
mode_visits = freq_actual.idxmax()
mode_count = freq_actual.max()

st.markdown(f"""
**📝 What this means:**

- **{one_timers} customers ({one_timer_pct:.0%})** visited only once — these are "try and leave" visitors. Some may never return.
- **Most common pattern:** {mode_visits} visit(s) — {mode_count} customers fit this pattern.
- **Average customer** visits **{nbd_results['avg_visits']:.1f} times/year** (roughly once every {12/max(nbd_results['avg_visits'], 0.1):.0f} months).
""")

st.markdown("---")

# Customer Behavior Insights
st.markdown("### 🔬 Customer Behavior Insights")

# Heterogeneity visualization
hetero_pct = min(100, max(0, (1 - nbd_results["r"]) * 50 + 50)) if nbd_results["r"] < 2 else 20

st.markdown("**How different are your customers from each other?**")

col1, col2 = st.columns([3, 1])
with col1:
    st.progress(hetero_pct / 100)
with col2:
    st.markdown(f"**{nbd_results['heterogeneity'].title()}**")

st.markdown(f"""
*"{nbd_results['hetero_desc']}"*

**What this means for you:**
- {"One-size-fits-all marketing won't work well" if nbd_results['heterogeneity'] == 'high' else "Your marketing can be more standardized"}
- {"Consider different strategies for different segments" if nbd_results['heterogeneity'] != 'low' else "A single retention strategy may work for most customers"}
- Your loyal regulars need VIP treatment to keep them
""")

st.markdown("---")

# Model Reliability
st.markdown("### ⚠️ How Reliable Is This Analysis?")

fit_pct = {"good": 80, "moderate": 50, "poor": 25}[nbd_results["fit_quality"]]

col1, col2 = st.columns([3, 1])
with col1:
    st.progress(fit_pct / 100)
with col2:
    st.markdown(f"**{nbd_results['fit_quality'].title()}**")

st.markdown(f"""
*"{nbd_results['fit_desc']}"*

Treat "{nbd_results['f0']:,.0f} unseen customers" as a rough estimate, not an exact count.
""")

# Technical details (expandable)
with st.expander("🔧 Show technical details"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Model Parameters**")
        st.markdown(f"- r (shape): {nbd_results['r']:.3f}")
        st.markdown(f"- α (rate): {nbd_results['alpha']:.3f}")
        st.markdown(f"- Log-likelihood: {nbd_results['log_likelihood']:.2f}")
    with col2:
        st.markdown("**Goodness of Fit**")
        st.markdown(f"- Chi-square: {nbd_results['chi_square']:.2f}")
        st.markdown(f"- Degrees of freedom: {nbd_results['df']}")
        st.markdown(f"- Estimated f₀: {nbd_results['f0']:.1f}")
