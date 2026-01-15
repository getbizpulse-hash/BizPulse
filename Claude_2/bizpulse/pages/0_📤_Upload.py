import streamlit as st
import pandas as pd
from utils.data_loader import load_and_process_csv, aggregate_to_customers
from utils.segmentation import assign_segments

st.set_page_config(page_title="Upload Data - Biz-Pulse", page_icon="📤", layout="wide")

st.title("📤 Upload Your Data")

# Check if logged in
if not st.session_state.get("logged_in", False):
    st.warning("Please log in first from the home page.")
    st.stop()

st.markdown(f"**Business:** {st.session_state.business_name}")

st.markdown("""
### Upload your customer appointment data

Upload a CSV file exported from Square or your booking system. The file should include:
- `client_name` - Customer name or ID
- `start` - Appointment date/time
- `status` - Appointment status (we'll filter to "accepted")
- `service` - Service name (optional, for price estimation)
""")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    try:
        # Load and process
        with st.spinner("Processing your data..."):
            raw_df = load_and_process_csv(uploaded_file)

            # Store raw data in session
            st.session_state.raw_data = raw_df

            # Show preview
            st.success(f"✅ Loaded {len(raw_df)} appointments")

            # Date range
            min_date = raw_df["start"].min()
            max_date = raw_df["start"].max()
            st.info(f"📅 Date range: {min_date.strftime('%b %d, %Y')} to {max_date.strftime('%b %d, %Y')}")

            # Unique customers
            unique_customers = raw_df["client_name"].nunique()
            st.info(f"👥 Unique customers: {unique_customers}")

            # Preview table
            with st.expander("Preview raw data"):
                st.dataframe(raw_df.head(10))

        # Generate insights button
        st.markdown("---")
        if st.button("🚀 Generate Insights", type="primary", use_container_width=True):
            # Aggregate to customer level
            customer_df = aggregate_to_customers(raw_df)
            customer_df = assign_segments(customer_df)

            # Store in session
            st.session_state.customer_data = customer_df
            st.session_state.data_loaded = True

            st.success("✅ Insights generated! Navigate to the analysis tabs in the sidebar.")
            st.balloons()

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.markdown("Please check that your CSV has the required columns.")

# Show status if data already loaded
if st.session_state.get("data_loaded", False):
    st.markdown("---")
    st.success("✅ Data is loaded. Use the sidebar to explore insights.")

    if st.button("🔄 Upload new data"):
        st.session_state.data_loaded = False
        st.session_state.raw_data = None
        st.session_state.customer_data = None
        st.rerun()
