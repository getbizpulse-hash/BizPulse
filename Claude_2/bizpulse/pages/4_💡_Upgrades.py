import streamlit as st
import pandas as pd
from utils.segmentation import assign_segments, SEGMENT_DEFINITIONS
from utils.data_loader import aggregate_to_customers
from utils.outreach import (
    generate_coupon_code,
    build_email_link,
    build_whatsapp_link,
    generate_upgrade_message,
    generate_explorer_message
)

st.set_page_config(page_title="Upgrades - Biz-Pulse", page_icon="💡", layout="wide")

st.title("💡 Upgrade Suggestions")

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
    start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="upg_start")
with col2:
    end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="upg_end")

# Filter and aggregate
customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
customer_df = assign_segments(customer_df)

st.markdown("---")

# Calculate upgrade opportunity
casuals = customer_df[customer_df["segment"] == "Casual"]
regulars = customer_df[customer_df["segment"] == "Regular"]

avg_casual_value = casuals["total_spend"].mean() if len(casuals) > 0 else 0
avg_regular_value = regulars["total_spend"].mean() if len(regulars) > 0 else 0
value_increase = avg_regular_value - avg_casual_value if avg_regular_value > avg_casual_value else 500

# Upgrade Opportunity
st.markdown("### 💰 Upgrade Opportunity")

st.markdown(f"""
**If you convert just 5 Casuals into Regulars, you'd gain ~${value_increase * 5:,.0f} in annual revenue.**
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Casual**")
    st.markdown(f"${avg_casual_value:,.0f}/yr")
    st.markdown(f"{len(casuals)} customers")
with col2:
    st.markdown("**→**")
    st.markdown(f"+${value_increase:,.0f}")
    st.markdown("per customer")
with col3:
    st.markdown("**Regular**")
    st.markdown(f"${avg_regular_value:,.0f}/yr")
    st.markdown(f"{len(regulars)} customers")

st.markdown("---")

# Best candidates to upgrade
st.markdown("### 🎯 Best Candidates to Upgrade")

# Find Casuals close to Regular (6-8 visits)
upgrade_candidates = casuals[casuals["frequency"] >= 6].copy()
upgrade_candidates = upgrade_candidates.sort_values("frequency", ascending=False)

if len(upgrade_candidates) > 0:
    st.markdown("These Casuals are closest to becoming Regulars:")

    display_df = upgrade_candidates[["client_name", "frequency", "total_spend"]].head(10).copy()
    display_df["visits_to_regular"] = 9 - display_df["frequency"]
    display_df.columns = ["Name", "Visits", "Spend", "Visits to Regular"]
    display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.0f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("No Casuals are close to Regular status yet.")

st.markdown("---")

# Suggested Actions
st.markdown("### 💬 Suggested Actions")

# Coupon codes
if "coupon_loyal" not in st.session_state:
    st.session_state.coupon_loyal = generate_coupon_code("LOYAL")
if "coupon_comeback" not in st.session_state:
    st.session_state.coupon_comeback = generate_coupon_code("BACK")

st.markdown(f"**Coupon codes:** `{st.session_state.coupon_loyal}` (loyalty), `{st.session_state.coupon_comeback}` (comeback)")

if st.button("🔄 Generate new codes"):
    st.session_state.coupon_loyal = generate_coupon_code("LOYAL")
    st.session_state.coupon_comeback = generate_coupon_code("BACK")
    st.rerun()

st.markdown("---")

# For Casuals close to Regular
st.markdown("#### For Casuals Close to Regular (6-8 visits)")

for idx, row in upgrade_candidates.head(5).iterrows():
    customer_name = row["client_name"]
    visits = int(row["frequency"])
    email = row.get("email", "")
    phone = row.get("phone", "")

    message = generate_upgrade_message(
        customer_name=customer_name.split()[0] if customer_name else "there",
        visits=visits,
        target_visits=12,
        coupon_code=st.session_state.coupon_loyal,
        business_name=business_name
    )

    with st.container():
        st.markdown(f"**{customer_name}** — {visits} visits")

        # Editable message
        edited_message = st.text_area(
            "Message",
            value=message,
            key=f"msg_{idx}",
            height=120,
            label_visibility="collapsed"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if email and pd.notna(email):
                email_link = build_email_link(str(email), f"Special offer from {business_name}", edited_message)
                st.markdown(f"[📧 Send Email]({email_link})")
            else:
                st.markdown("📧 No email")

        with col2:
            if phone and pd.notna(phone):
                wa_link = build_whatsapp_link(str(phone), edited_message)
                st.markdown(f"[💬 WhatsApp]({wa_link})")
            else:
                st.markdown("💬 No phone")

        with col3:
            st.text_input("Copy message", value=edited_message, key=f"copy_{idx}", label_visibility="collapsed")

        st.markdown("---")

# For Explorers
st.markdown("#### For Explorers Who Haven't Returned")

explorers = customer_df[(customer_df["segment"] == "Explorer") & (customer_df["days_since_visit"] > 30)]
explorers = explorers.sort_values("total_spend", ascending=False)

if len(explorers) > 0:
    for idx, row in explorers.head(3).iterrows():
        customer_name = row["client_name"]
        email = row.get("email", "")
        phone = row.get("phone", "")

        message = generate_explorer_message(
            customer_name=customer_name.split()[0] if customer_name else "there",
            coupon_code=st.session_state.coupon_comeback,
            business_name=business_name
        )

        with st.container():
            st.markdown(f"**{customer_name}** — 1-2 visits, {int(row['days_since_visit'])} days ago")

            col1, col2 = st.columns(2)

            with col1:
                if email and pd.notna(email):
                    email_link = build_email_link(str(email), f"We miss you at {business_name}!", message)
                    st.markdown(f"[📧 Send Email]({email_link})")
                else:
                    st.markdown("📧 No email")

            with col2:
                if phone and pd.notna(phone):
                    wa_link = build_whatsapp_link(str(phone), message)
                    st.markdown(f"[💬 WhatsApp]({wa_link})")
                else:
                    st.markdown("💬 No phone")
else:
    st.info("No Explorers overdue for follow-up.")
