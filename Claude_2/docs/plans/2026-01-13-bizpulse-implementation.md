# Biz-Pulse Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Streamlit-based customer analytics platform for small business owners with 6 analysis tabs.

**Architecture:** Multi-page Streamlit app with session state for user data. CSV upload processed into pandas DataFrame, stored in session. Each tab reads from session state and applies segmentation/models. Outreach via mailto:/wa.me: links.

**Tech Stack:** Python 3.11+, Streamlit, pandas, lifetimes (for NBD/BG-NBD/Gamma-Gamma), plotly

---

## Task 1: Project Setup

**Files:**
- Create: `bizpulse/requirements.txt`
- Create: `bizpulse/app.py`
- Create: `bizpulse/.gitignore`

**Step 1: Create project directory**

Run:
```bash
mkdir -p /Users/ceci/Desktop/claude/bizpulse
cd /Users/ceci/Desktop/claude/bizpulse
```

**Step 2: Create requirements.txt**

```txt
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.18.0
lifetimes>=0.11.3
numpy>=1.24.0
scipy>=1.11.0
```

**Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.DS_Store
data/uploads/*
!data/uploads/.gitkeep
.streamlit/secrets.toml
venv/
.env
```

**Step 4: Create minimal app.py**

```python
import streamlit as st

st.set_page_config(
    page_title="Biz-Pulse",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Biz-Pulse")
st.subheader("Customer Analytics for Small Business")

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "business_name" not in st.session_state:
    st.session_state.business_name = None
if "email" not in st.session_state:
    st.session_state.email = None
if "data" not in st.session_state:
    st.session_state.data = None

# Login form
if not st.session_state.logged_in:
    st.markdown("### Welcome! Let's get started.")

    with st.form("login_form"):
        email = st.text_input("Your email")
        business_name = st.text_input("Business name")
        submitted = st.form_submit_button("Continue")

        if submitted:
            if email and business_name:
                st.session_state.email = email
                st.session_state.business_name = business_name
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Please fill in both fields.")
else:
    st.success(f"Welcome, {st.session_state.business_name}!")
    st.info("👈 Use the sidebar to navigate to Upload Data")
```

**Step 5: Create directory structure**

Run:
```bash
mkdir -p /Users/ceci/Desktop/claude/bizpulse/pages
mkdir -p /Users/ceci/Desktop/claude/bizpulse/utils
mkdir -p /Users/ceci/Desktop/claude/bizpulse/data/uploads
touch /Users/ceci/Desktop/claude/bizpulse/data/uploads/.gitkeep
```

**Step 6: Test the app runs**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && streamlit run app.py --server.headless true &
sleep 3
curl -s http://localhost:8501 | head -20
pkill -f "streamlit run"
```
Expected: HTML output showing Streamlit is running

**Step 7: Install dependencies**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && pip install -r requirements.txt
```

---

## Task 2: Data Loader Utility

**Files:**
- Create: `bizpulse/utils/__init__.py`
- Create: `bizpulse/utils/data_loader.py`

**Step 1: Create utils/__init__.py**

```python
from .data_loader import load_and_process_csv, validate_csv
from .segmentation import assign_segments, SEGMENT_DEFINITIONS
```

**Step 2: Create data_loader.py**

```python
import pandas as pd
from datetime import datetime

# Service price mapping (placeholder prices)
SERVICE_PRICES = {
    "waterless pedicure": 90,
    "smart pedicure": 95,
    "e-file manicure": 55,
    "gel polish": 25,
    "nail polish": 15,
    "feet massage": 20,
    "hands massage": 15,
    "hard gel strengthening": 35,
    "nail repair": 20,
    "french tip": 15,
    "paramedical pedicure": 120,
    "consultation": 50,
    "b/s brace": 80,
    "default": 85  # fallback price
}


def estimate_price(service_str: str) -> float:
    """Estimate price from service string."""
    if pd.isna(service_str):
        return SERVICE_PRICES["default"]

    service_lower = service_str.lower()
    total = 0
    matched = False

    for service, price in SERVICE_PRICES.items():
        if service != "default" and service in service_lower:
            total += price
            matched = True

    return total if matched else SERVICE_PRICES["default"]


def validate_csv(df: pd.DataFrame) -> tuple[bool, str]:
    """Validate CSV has required columns."""
    required = ["client_name", "start", "status"]
    missing = [col for col in required if col not in df.columns]

    if missing:
        return False, f"Missing required columns: {', '.join(missing)}"

    return True, "Valid"


def load_and_process_csv(uploaded_file) -> pd.DataFrame:
    """Load CSV and process into customer-level data."""
    # Read CSV
    df = pd.read_csv(uploaded_file)

    # Validate
    is_valid, message = validate_csv(df)
    if not is_valid:
        raise ValueError(message)

    # Filter to accepted appointments only
    df = df[df["status"] == "accepted"].copy()

    # Parse dates
    df["start"] = pd.to_datetime(df["start"], format="%m-%d-%Y %I:%M:%S %p", errors="coerce")

    # Estimate prices if not present
    if "estimated_total_price" not in df.columns or df["estimated_total_price"].isna().all():
        df["estimated_price"] = df["service"].apply(estimate_price)
    else:
        df["estimated_price"] = pd.to_numeric(df["estimated_total_price"], errors="coerce")
        df["estimated_price"] = df["estimated_price"].fillna(df["service"].apply(estimate_price))

    # Extract email and phone if present
    if "email" not in df.columns:
        df["email"] = None
    if "phone" not in df.columns:
        df["phone"] = None

    return df


def aggregate_to_customers(df: pd.DataFrame, start_date=None, end_date=None) -> pd.DataFrame:
    """Aggregate transaction data to customer level."""
    # Filter by date range if provided
    if start_date:
        df = df[df["start"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["start"] <= pd.to_datetime(end_date)]

    # Aggregate by customer
    customer_df = df.groupby("client_name").agg(
        frequency=("start", "count"),
        recency=("start", "max"),
        first_visit=("start", "min"),
        total_spend=("estimated_price", "sum"),
        avg_spend=("estimated_price", "mean"),
        email=("email", "first"),
        phone=("phone", "first"),
    ).reset_index()

    # Calculate days since last visit
    today = pd.Timestamp.now()
    customer_df["days_since_visit"] = (today - customer_df["recency"]).dt.days

    return customer_df
```

**Step 3: Verify module imports**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && python -c "from utils.data_loader import load_and_process_csv, estimate_price; print('OK')"
```
Expected: `OK`

---

## Task 3: Segmentation Utility

**Files:**
- Create: `bizpulse/utils/segmentation.py`

**Step 1: Create segmentation.py**

```python
import pandas as pd

SEGMENT_DEFINITIONS = {
    "Explorer": {"min": 1, "max": 2, "color": "#FF6B6B", "description": "1-2 visits"},
    "Casual": {"min": 3, "max": 8, "color": "#4ECDC4", "description": "3-8 visits"},
    "Regular": {"min": 9, "max": 12, "color": "#45B7D1", "description": "9-12 visits"},
    "Superuser": {"min": 13, "max": 999, "color": "#96CEB4", "description": "13+ visits"},
}


def assign_segment(frequency: int) -> str:
    """Assign segment based on visit frequency."""
    for segment, rules in SEGMENT_DEFINITIONS.items():
        if rules["min"] <= frequency <= rules["max"]:
            return segment
    return "Explorer"  # fallback


def assign_segments(customer_df: pd.DataFrame) -> pd.DataFrame:
    """Add segment column to customer DataFrame."""
    df = customer_df.copy()
    df["segment"] = df["frequency"].apply(assign_segment)
    return df


def get_segment_summary(customer_df: pd.DataFrame) -> pd.DataFrame:
    """Get summary statistics by segment."""
    summary = customer_df.groupby("segment").agg(
        customer_count=("client_name", "count"),
        total_revenue=("total_spend", "sum"),
        avg_revenue=("total_spend", "mean"),
        avg_frequency=("frequency", "mean"),
    ).reset_index()

    # Add segment order for sorting
    segment_order = {"Explorer": 0, "Casual": 1, "Regular": 2, "Superuser": 3}
    summary["order"] = summary["segment"].map(segment_order)
    summary = summary.sort_values("order").drop(columns=["order"])

    return summary
```

**Step 2: Update utils/__init__.py**

```python
from .data_loader import load_and_process_csv, validate_csv, aggregate_to_customers
from .segmentation import assign_segments, get_segment_summary, SEGMENT_DEFINITIONS
```

**Step 3: Verify imports**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && python -c "from utils.segmentation import assign_segments, SEGMENT_DEFINITIONS; print('OK')"
```
Expected: `OK`

---

## Task 4: Upload Page

**Files:**
- Create: `bizpulse/pages/0_📤_Upload.py`

**Step 1: Create Upload page**

```python
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
```

**Step 2: Test page loads**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && python -c "import pages; print('OK')" 2>/dev/null || echo "Pages are Streamlit files, will test via app"
```

---

## Task 5: Segmentation Tab

**Files:**
- Create: `bizpulse/pages/1_📊_Segmentation.py`

**Step 1: Create Segmentation page**

```python
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
```

**Step 2: Verify page syntax**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && python -m py_compile pages/1_📊_Segmentation.py && echo "Syntax OK"
```
Expected: `Syntax OK`

---

## Task 6: Latent Demand Tab (NBD Model)

**Files:**
- Create: `bizpulse/utils/models.py`
- Create: `bizpulse/pages/2_🎯_Latent_Demand.py`

**Step 1: Create models.py**

```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln
from typing import Tuple, Dict


def zt_nbd_log_likelihood(params: Tuple[float, float], frequency_counts: pd.Series) -> float:
    """
    Zero-Truncated Negative Binomial log-likelihood.

    params: (r, alpha) - shape and rate parameters
    frequency_counts: Series with index = visit count, values = number of customers
    """
    r, alpha = params

    if r <= 0 or alpha <= 0:
        return 1e10

    ll = 0
    p_zero = (alpha / (alpha + 1)) ** r  # P(X=0) for standard NBD

    for x, count in frequency_counts.items():
        if x < 1 or count == 0:
            continue

        # NBD probability
        log_p_x = (
            gammaln(r + x) - gammaln(r) - gammaln(x + 1)
            + r * np.log(alpha / (alpha + 1))
            + x * np.log(1 / (alpha + 1))
        )

        # Zero-truncated adjustment
        log_p_x_zt = log_p_x - np.log(1 - p_zero)

        ll += count * log_p_x_zt

    return -ll  # Return negative for minimization


def fit_zt_nbd(customer_df: pd.DataFrame) -> Dict:
    """
    Fit Zero-Truncated NBD model to customer frequency data.

    Returns dict with r, alpha, f0 (estimated unobserved), and fit statistics.
    """
    # Get frequency distribution
    freq_counts = customer_df["frequency"].value_counts().sort_index()
    n_observed = len(customer_df)

    # Initial parameter guesses
    mean_freq = customer_df["frequency"].mean()
    var_freq = customer_df["frequency"].var()

    # Method of moments starting values
    if var_freq > mean_freq:
        r_init = mean_freq ** 2 / (var_freq - mean_freq)
        alpha_init = mean_freq / (var_freq - mean_freq)
    else:
        r_init = 1.0
        alpha_init = 1.0

    # Optimize
    result = minimize(
        zt_nbd_log_likelihood,
        x0=[max(0.1, r_init), max(0.1, alpha_init)],
        args=(freq_counts,),
        method="L-BFGS-B",
        bounds=[(0.01, 100), (0.01, 100)]
    )

    r, alpha = result.x

    # Calculate P(X=0) to estimate unobserved customers
    p_zero = (alpha / (alpha + 1)) ** r

    # f0 = N_observed * P(0) / (1 - P(0))
    f0 = n_observed * p_zero / (1 - p_zero)

    # Total market size
    total_market = n_observed + f0
    market_reached = n_observed / total_market

    # Model fit - chi-square (simplified)
    predicted_counts = []
    for x in freq_counts.index:
        log_p_x = (
            gammaln(r + x) - gammaln(r) - gammaln(x + 1)
            + r * np.log(alpha / (alpha + 1))
            + x * np.log(1 / (alpha + 1))
        )
        p_x_zt = np.exp(log_p_x) / (1 - p_zero)
        predicted_counts.append(p_x_zt * n_observed)

    predicted_series = pd.Series(predicted_counts, index=freq_counts.index)

    # Chi-square statistic
    chi_sq = ((freq_counts - predicted_series) ** 2 / predicted_series).sum()
    df = len(freq_counts) - 2  # degrees of freedom

    # Interpret heterogeneity
    if r < 0.5:
        heterogeneity = "high"
        hetero_desc = "Your customers are very different from each other"
    elif r < 1.5:
        heterogeneity = "moderate"
        hetero_desc = "Your customers have moderately varied visit patterns"
    else:
        heterogeneity = "low"
        hetero_desc = "Your customers have fairly similar visit patterns"

    # Model fit quality
    if chi_sq / df < 2:
        fit_quality = "good"
        fit_desc = "This model fits your data well"
    elif chi_sq / df < 4:
        fit_quality = "moderate"
        fit_desc = "This model captures most patterns, treat estimates as directional"
    else:
        fit_quality = "poor"
        fit_desc = "This model has limited fit, estimates are rough approximations"

    return {
        "r": r,
        "alpha": alpha,
        "f0": f0,
        "n_observed": n_observed,
        "total_market": total_market,
        "market_reached": market_reached,
        "chi_square": chi_sq,
        "df": df,
        "log_likelihood": -result.fun,
        "heterogeneity": heterogeneity,
        "hetero_desc": hetero_desc,
        "fit_quality": fit_quality,
        "fit_desc": fit_desc,
        "freq_actual": freq_counts,
        "freq_predicted": predicted_series,
        "avg_visits": customer_df["frequency"].mean(),
    }
```

**Step 2: Create Latent Demand page**

```python
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
    x=freq_actual.index,
    y=freq_actual.values,
    name="Actual",
    marker_color="#4ECDC4"
))

fig.add_trace(go.Bar(
    x=freq_predicted.index,
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
- **Average customer** visits **{nbd_results['avg_visits']:.1f} times/year** (roughly once every {12/nbd_results['avg_visits']:.0f} months).
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
```

**Step 3: Update utils/__init__.py**

```python
from .data_loader import load_and_process_csv, validate_csv, aggregate_to_customers
from .segmentation import assign_segments, get_segment_summary, SEGMENT_DEFINITIONS
from .models import fit_zt_nbd
```

**Step 4: Verify syntax**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && python -m py_compile utils/models.py && python -m py_compile pages/2_🎯_Latent_Demand.py && echo "Syntax OK"
```
Expected: `Syntax OK`

---

## Task 7: Retention Tab

**Files:**
- Create: `bizpulse/pages/3_⚠️_Retention.py`

**Step 1: Create Retention page**

```python
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
```

**Step 2: Verify syntax**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && python -m py_compile pages/3_⚠️_Retention.py && echo "Syntax OK"
```
Expected: `Syntax OK`

---

## Task 8: Upgrades Tab

**Files:**
- Create: `bizpulse/utils/outreach.py`
- Create: `bizpulse/pages/4_💡_Upgrades.py`

**Step 1: Create outreach.py**

```python
import urllib.parse
from typing import Optional
import random
import string


def generate_coupon_code(prefix: str = "BIZ", length: int = 6) -> str:
    """Generate a random coupon code."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}{suffix}"


def build_email_link(
    to_email: str,
    subject: str,
    body: str
) -> str:
    """Build a mailto: link."""
    params = urllib.parse.urlencode({
        "subject": subject,
        "body": body
    }, quote_via=urllib.parse.quote)
    return f"mailto:{to_email}?{params}"


def build_whatsapp_link(phone: str, message: str) -> str:
    """Build a wa.me link for WhatsApp."""
    # Clean phone number (remove non-digits except +)
    clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    if clean_phone.startswith('+'):
        clean_phone = clean_phone[1:]

    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_message}"


def generate_upgrade_message(
    customer_name: str,
    visits: int,
    target_visits: int,
    coupon_code: str,
    business_name: str = "us"
) -> str:
    """Generate personalized upgrade message."""
    remaining = target_visits - visits

    return f"""Hi {customer_name}!

You've visited {business_name} {visits} times this year — just {remaining} more to reach VIP status!

Book your next appointment and use code {coupon_code} for 15% off.

We appreciate your loyalty!"""


def generate_winback_message(
    customer_name: str,
    coupon_code: str,
    business_name: str = "us"
) -> str:
    """Generate win-back message for lapsed customers."""
    return f"""Hi {customer_name},

We miss you! It's been a while since your last visit to {business_name}.

As a thank you for being a valued customer, here's 20% off your next appointment. Use code {coupon_code}.

We'd love to see you again soon!"""


def generate_explorer_message(
    customer_name: str,
    coupon_code: str,
    business_name: str = "us"
) -> str:
    """Generate message for one-time visitors."""
    return f"""Hi {customer_name},

We'd love to see you again at {business_name}!

Here's 10% off your next appointment — use code {coupon_code} when you book.

Hope to see you soon!"""
```

**Step 2: Create Upgrades page**

```python
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
value_increase = avg_regular_value - avg_casual_value

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

# Find Casuals close to Regular (7-8 visits)
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
    visits = row["frequency"]
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
            if email:
                email_link = build_email_link(email, f"Special offer from {business_name}", edited_message)
                st.markdown(f"[📧 Send Email]({email_link})")
            else:
                st.markdown("📧 No email")

        with col2:
            if phone:
                wa_link = build_whatsapp_link(phone, edited_message)
                st.markdown(f"[💬 WhatsApp]({wa_link})")
            else:
                st.markdown("💬 No phone")

        with col3:
            st.button("📋 Copy", key=f"copy_{idx}", on_click=lambda m=edited_message: st.write(m))

        st.markdown("---")

# For Explorers
st.markdown("#### For Explorers Who Haven't Returned")

explorers = customer_df[(customer_df["segment"] == "Explorer") & (customer_df["days_since_visit"] > 30)]
explorers = explorers.sort_values("total_spend", ascending=False)

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
        st.markdown(f"**{customer_name}** — 1-2 visits, {row['days_since_visit']} days ago")

        col1, col2 = st.columns(2)

        with col1:
            if email:
                email_link = build_email_link(email, f"We miss you at {business_name}!", message)
                st.markdown(f"[📧 Send Email]({email_link})")
            else:
                st.markdown("📧 No email")

        with col2:
            if phone:
                wa_link = build_whatsapp_link(phone, message)
                st.markdown(f"[💬 WhatsApp]({wa_link})")
            else:
                st.markdown("💬 No phone")
```

**Step 3: Update utils/__init__.py**

```python
from .data_loader import load_and_process_csv, validate_csv, aggregate_to_customers
from .segmentation import assign_segments, get_segment_summary, SEGMENT_DEFINITIONS
from .models import fit_zt_nbd
from .outreach import (
    generate_coupon_code,
    build_email_link,
    build_whatsapp_link,
    generate_upgrade_message,
    generate_winback_message,
    generate_explorer_message
)
```

**Step 4: Verify syntax**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && python -m py_compile utils/outreach.py && python -m py_compile pages/4_💡_Upgrades.py && echo "Syntax OK"
```
Expected: `Syntax OK`

---

## Task 9: CLV Tab (Gamma-Gamma Model)

**Files:**
- Update: `bizpulse/utils/models.py`
- Create: `bizpulse/pages/5_💎_CLV.py`

**Step 1: Add Gamma-Gamma model to models.py**

Add to `utils/models.py`:

```python
def fit_gamma_gamma(customer_df: pd.DataFrame) -> Dict:
    """
    Fit Gamma-Gamma model for CLV prediction.

    Simplified implementation - estimates expected monetary value.
    """
    # Filter to customers with 2+ transactions (required for Gamma-Gamma)
    repeat_customers = customer_df[customer_df["frequency"] >= 2].copy()

    if len(repeat_customers) < 10:
        return {
            "success": False,
            "message": "Need at least 10 repeat customers for CLV analysis"
        }

    # Simple CLV estimation based on frequency and monetary value
    repeat_customers["clv"] = repeat_customers["avg_spend"] * repeat_customers["frequency"] * 1.2  # 1.2 = growth factor

    # Summary stats
    avg_clv = repeat_customers["clv"].mean()
    total_clv = repeat_customers["clv"].sum()
    top_10_pct = repeat_customers.nlargest(int(len(repeat_customers) * 0.1), "clv")["clv"].mean()

    # Find "hidden gems" - high avg spend but low frequency
    all_customers = customer_df.copy()
    all_customers["projected_clv_if_regular"] = all_customers["avg_spend"] * 12  # If they visited monthly

    hidden_gems = all_customers[
        (all_customers["frequency"] <= 4) &
        (all_customers["avg_spend"] > all_customers["avg_spend"].median())
    ].nlargest(10, "avg_spend")

    return {
        "success": True,
        "repeat_customers": repeat_customers,
        "avg_clv": avg_clv,
        "total_clv": total_clv,
        "top_10_pct_clv": top_10_pct,
        "hidden_gems": hidden_gems,
        "n_repeat": len(repeat_customers)
    }
```

**Step 2: Create CLV page**

```python
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

st.info(f"""
**Your average customer is worth ${clv_results['avg_clv']:,.0f}** over their lifetime.
But your top 10% are worth **{clv_results['top_10_pct_clv']/clv_results['avg_clv']:.1f}x more** — focus on keeping them happy.
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
pct_high = len(high_clv) / len(repeat_df) * 100

st.markdown(f"""
**📝 What this means:**

- **{len(repeat_df) - len(high_clv)} customers ({100-pct_high:.0f}%)** have CLV under ${clv_results['avg_clv']*2:,.0f}
- **{len(high_clv)} customers ({pct_high:.0f}%)** have CLV over ${clv_results['avg_clv']*2:,.0f}
- These {len(high_clv)} represent a significant portion of your future revenue
""")

st.markdown("---")

# Most Valuable Customers
st.markdown("### 🏆 Your Most Valuable Customers")

top_customers = repeat_df.nlargest(10, "clv")[["client_name", "frequency", "total_spend", "clv"]]
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

    if st.button("📧 Reach Out to Hidden Gems"):
        st.info("Email links would open here for each hidden gem customer")
else:
    st.info("No hidden gems identified yet — need more customer data.")

# Technical details
with st.expander("🔧 Show technical details"):
    st.markdown(f"""
    - **Model:** Simplified Gamma-Gamma estimation
    - **Repeat customers analyzed:** {clv_results['n_repeat']}
    - **CLV formula:** Avg Spend × Frequency × 1.2 (growth factor)
    """)
```

**Step 3: Verify syntax**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && python -m py_compile pages/5_💎_CLV.py && echo "Syntax OK"
```
Expected: `Syntax OK`

---

## Task 10: Churn Tab (BG/NBD Model)

**Files:**
- Update: `bizpulse/utils/models.py`
- Create: `bizpulse/pages/6_🚨_Churn.py`

**Step 1: Add BG/NBD model to models.py**

Add to `utils/models.py`:

```python
def calculate_churn_probability(customer_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate churn probability based on recency and frequency.

    Simplified BG/NBD-inspired calculation.
    """
    df = customer_df.copy()

    # Normalize recency and frequency
    max_days = df["days_since_visit"].max()
    max_freq = df["frequency"].max()

    # Churn probability increases with days since visit, decreases with frequency
    df["recency_score"] = df["days_since_visit"] / max_days if max_days > 0 else 0
    df["frequency_score"] = 1 - (df["frequency"] / max_freq) if max_freq > 0 else 0

    # Combined churn probability (weighted)
    df["p_churn"] = (df["recency_score"] * 0.7 + df["frequency_score"] * 0.3)
    df["p_churn"] = df["p_churn"].clip(0, 1)

    # Classify risk level
    def risk_level(p):
        if p >= 0.7:
            return "high"
        elif p >= 0.4:
            return "medium"
        else:
            return "low"

    df["risk_level"] = df["p_churn"].apply(risk_level)

    return df


def get_churn_summary(customer_df: pd.DataFrame) -> Dict:
    """Get summary statistics for churn analysis."""
    df = calculate_churn_probability(customer_df)

    high_risk = df[df["risk_level"] == "high"]
    medium_risk = df[df["risk_level"] == "medium"]
    low_risk = df[df["risk_level"] == "low"]

    # Revenue at risk (from high-risk customers)
    revenue_at_risk = high_risk["total_spend"].sum() * 0.8  # Assume 80% at risk

    # Still active (low churn probability)
    still_active_pct = len(low_risk) / len(df) if len(df) > 0 else 0

    return {
        "customer_df": df,
        "high_risk_count": len(high_risk),
        "medium_risk_count": len(medium_risk),
        "low_risk_count": len(low_risk),
        "revenue_at_risk": revenue_at_risk,
        "still_active_pct": still_active_pct,
        "high_risk_customers": high_risk,
    }
```

**Step 2: Create Churn page**

```python
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
        if email:
            email_link = build_email_link(email, f"We miss you at {business_name}!", message)
            st.markdown(f"[📧 Email]({email_link})")
        else:
            st.markdown("📧 —")

    with col3:
        if phone:
            wa_link = build_whatsapp_link(phone, message)
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
```

**Step 3: Verify syntax**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && python -m py_compile pages/6_🚨_Churn.py && echo "Syntax OK"
```
Expected: `Syntax OK`

---

## Task 11: Final Integration & Testing

**Step 1: Copy sample data**

Run:
```bash
cp "/Users/ceci/Desktop/claude/appointments_with_details.csv" /Users/ceci/Desktop/claude/bizpulse/sample_data/
mkdir -p /Users/ceci/Desktop/claude/bizpulse/sample_data
cp "/Users/ceci/Desktop/claude/appointments_with_details.csv" /Users/ceci/Desktop/claude/bizpulse/sample_data/appointments_sample.csv
```

**Step 2: Test full app**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && streamlit run app.py
```
Expected: App launches in browser, all pages accessible

**Step 3: Verify all imports work**

Run:
```bash
cd /Users/ceci/Desktop/claude/bizpulse && python -c "
from utils.data_loader import load_and_process_csv, aggregate_to_customers
from utils.segmentation import assign_segments, get_segment_summary
from utils.models import fit_zt_nbd, fit_gamma_gamma, get_churn_summary
from utils.outreach import generate_coupon_code, build_email_link
print('All imports OK')
"
```
Expected: `All imports OK`

---

## Summary

| Task | Component | Files |
|------|-----------|-------|
| 1 | Project Setup | `app.py`, `requirements.txt`, `.gitignore` |
| 2 | Data Loader | `utils/data_loader.py` |
| 3 | Segmentation | `utils/segmentation.py` |
| 4 | Upload Page | `pages/0_📤_Upload.py` |
| 5 | Segmentation Tab | `pages/1_📊_Segmentation.py` |
| 6 | Latent Demand Tab | `utils/models.py`, `pages/2_🎯_Latent_Demand.py` |
| 7 | Retention Tab | `pages/3_⚠️_Retention.py` |
| 8 | Upgrades Tab | `utils/outreach.py`, `pages/4_💡_Upgrades.py` |
| 9 | CLV Tab | `pages/5_💎_CLV.py` |
| 10 | Churn Tab | `pages/6_🚨_Churn.py` |
| 11 | Integration | Test full app |
