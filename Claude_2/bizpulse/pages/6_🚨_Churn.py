import streamlit as st
import pandas as pd
import plotly.express as px
from utils.segmentation import assign_segments
from utils.data_loader import aggregate_to_customers
from utils.models import get_churn_summary, fit_gamma_gamma
from utils.outreach import (
    build_email_link,
    build_whatsapp_link,
    generate_winback_message,
    generate_coupon_code
)

st.set_page_config(page_title="Churn - Biz-Pulse", page_icon="🚨", layout="wide")

st.title("🚨 Churn Prediction")

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
    start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="churn_start")
with col2:
    end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="churn_end")

# Filter and aggregate
customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
customer_df = assign_segments(customer_df)

st.markdown("---")

# Get churn summary
churn_results = get_churn_summary(customer_df)

# Churn Risk Summary
st.markdown("### ⚠️ Churn Risk Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Likely to Churn", churn_results["high_risk_count"], help="High probability of not returning")
with col2:
    st.metric("Revenue at Risk", f"${churn_results['revenue_at_risk']:,.0f}")
with col3:
    st.metric("Still Active", f"{churn_results['still_active_pct']:.0%}")

st.info(f"""
**{churn_results['high_risk_count']} customers** have a high chance of not coming back.
If they all churn, you'd lose ~**${churn_results['revenue_at_risk']:,.0f}** in annual revenue.
But there's still time to win them back.
""")

st.markdown("---")

# Scatter plot
st.markdown("### 🎯 Customers by Churn Probability")

plot_df = churn_results["customer_df"].copy()

fig = px.scatter(
    plot_df,
    x="days_since_visit",
    y="frequency",
    color="p_churn",
    color_continuous_scale=["green", "yellow", "red"],
    hover_data=["client_name", "total_spend"],
    labels={
        "days_since_visit": "Days Since Last Visit",
        "frequency": "Number of Visits",
        "p_churn": "Churn Probability"
    }
)
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**📝 What this means:**

- **Red dots (top-left):** Visited long ago, rarely came → probably already gone
- **Yellow dots (middle):** Haven't visited recently but were regulars → worth reaching out
- **Green dots (bottom-right):** Visited recently, often → your healthy core
""")

st.markdown("---")

# High-Value Customers at Risk
st.markdown("### 🚨 High-Value Customers at Risk")

# Get CLV data
clv_results = fit_gamma_gamma(customer_df)

high_risk = churn_results["high_risk_customers"].copy()

if clv_results["success"]:
    # Merge CLV data
    clv_df = clv_results["repeat_customers"][["client_name", "clv"]]
    high_risk = high_risk.merge(clv_df, on="client_name", how="left")
    high_risk["clv"] = high_risk["clv"].fillna(high_risk["total_spend"])
    high_risk = high_risk.sort_values("clv", ascending=False)
else:
    high_risk["clv"] = high_risk["total_spend"]

if len(high_risk) > 0:
    # Display table
    display_df = high_risk[["client_name", "clv", "recency", "p_churn"]].head(10).copy()
    display_df["recency"] = display_df["recency"].dt.strftime("%b %d, %Y")
    display_df["p_churn"] = display_df["p_churn"].apply(lambda x: f"{x:.0%}")
    display_df["clv"] = display_df["clv"].apply(lambda x: f"${x:,.0f}")
    display_df.columns = ["Name", "CLV", "Last Visit", "P(Churn)"]

    col1, col2 = st.columns([4, 1])
    with col2:
        csv = high_risk.to_csv(index=False)
        st.download_button("📥 Export CSV", csv, "churn_risk_customers.csv", "text/csv")

    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.success("No high-risk customers identified!")

st.markdown("---")

# Win-back Messages
st.markdown("### 💬 Suggested Win-Back Messages")

if "winback_coupon" not in st.session_state:
    st.session_state.winback_coupon = generate_coupon_code("MISS")

st.markdown(f"**Coupon code:** `{st.session_state.winback_coupon}`")

if st.button("🔄 Generate new code", key="winback_regen"):
    st.session_state.winback_coupon = generate_coupon_code("MISS")
    st.rerun()

# Template
template = generate_winback_message(
    customer_name="[Name]",
    coupon_code=st.session_state.winback_coupon,
    business_name=business_name
)

st.text_area("Message template", value=template, height=150, key="winback_template")

# Individual customer actions
if len(high_risk) > 0:
    st.markdown("#### Send to Individual Customers")

    for idx, row in high_risk.head(5).iterrows():
        customer_name = row["client_name"]
        email = row.get("email", "")
        phone = row.get("phone", "")

        message = generate_winback_message(
            customer_name=customer_name.split()[0] if customer_name else "there",
            coupon_code=st.session_state.winback_coupon,
            business_name=business_name
        )

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            churn_pct = row["p_churn"] * 100
            risk_emoji = "🔴" if churn_pct >= 70 else "🟠" if churn_pct >= 50 else "🟡"
            st.markdown(f"**{customer_name}** — {risk_emoji} {churn_pct:.0f}% churn risk")

        with col2:
            if email and pd.notna(email):
                email_link = build_email_link(str(email), f"We miss you at {business_name}!", message)
                st.markdown(f"[📧 Email]({email_link})")
            else:
                st.markdown("📧 —")

        with col3:
            if phone and pd.notna(phone):
                wa_link = build_whatsapp_link(str(phone), message)
                st.markdown(f"[💬 WhatsApp]({wa_link})")
            else:
                st.markdown("💬 —")

# Technical details
with st.expander("🔧 Show technical details"):
    st.markdown(f"""
    - **Model:** Simplified BG/NBD-inspired probability
    - **Churn formula:** 0.7 × Recency Score + 0.3 × (1 - Frequency Score)
    - **High risk threshold:** P(Churn) ≥ 70%
    - **Medium risk threshold:** P(Churn) ≥ 40%
    """)
