import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Import utilities
from utils.data_loader import load_and_process_csv, aggregate_to_customers
from utils.segmentation import assign_segments, get_segment_summary, SEGMENT_DEFINITIONS
from utils.models import fit_zt_nbd, fit_gamma_gamma, get_churn_summary
from utils.outreach import (
    generate_coupon_code, build_email_link, build_whatsapp_link,
    generate_upgrade_message, generate_winback_message, generate_explorer_message
)

# Page config
st.set_page_config(
    page_title="BizPulse",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# DESIGN SYSTEM - Editorial Modern
# Colors: Dark Green, Cream, White (3 colors only)
# Typography: Playfair Display (serif headlines) + Inter (sans body)
# =============================================================================

COLORS = {
    "bg_cream": "#FAF1E5",          # Cream background
    "bg_white": "#FFFFFF",          # White cards/panels
    "green": "#003D29",             # Dark green - primary accent
    "text_primary": "#003D29",      # Dark green for headings
    "text_body": "#1A1A1A",         # Near black for body
    "text_muted": "#6B6B6B",        # Muted gray
    "text_light": "#999999",        # Light gray
    "border": "#E8E0D5",            # Warm subtle border
    "success": "#003D29",           # Green (same as primary)
    "warning": "#B8860B",           # Dark goldenrod
    "danger": "#8B0000",            # Dark red
}

FONTS = {
    "display": "'Playfair Display', Georgia, serif",
    "body": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    "mono": "'SF Mono', 'Monaco', monospace",
}

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    /* ========== GLOBAL ========== */
    .stApp {{
        background-color: {COLORS["bg_cream"]};
    }}

    /* Hide Streamlit defaults */
    [data-testid="stSidebar"] {{ display: none; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}

    /* Typography base */
    html, body, [class*="css"] {{
        font-family: {FONTS["body"]};
        color: {COLORS["text_body"]};
    }}

    h1, h2, h3 {{
        font-family: {FONTS["display"]};
        font-weight: 600;
        color: {COLORS["text_primary"]};
    }}

    /* Container - adjust padding based on page */
    .block-container {{
        padding: 1rem 2rem;
        max-width: 100%;
    }}

    /* ========== SPLIT SCREEN LAYOUT ========== */
    .split-container {{
        display: flex;
        min-height: 100vh;
        width: 100vw;
        margin-left: calc(-50vw + 50%);
    }}

    .split-left {{
        flex: 0 0 58%;
        background: {COLORS["bg_cream"]};
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 4rem 6rem;
    }}

    .split-right {{
        flex: 0 0 42%;
        background: {COLORS["bg_white"]};
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 4rem 4rem;
    }}

    /* ========== EDITORIAL TYPOGRAPHY ========== */
    .wordmark {{
        font-family: {FONTS["body"]};
        font-size: 0.75rem;
        font-weight: 600;
        color: {COLORS["green"]};
        text-transform: uppercase;
        letter-spacing: 0.2em;
        margin-bottom: 2rem;
    }}

    .editorial-headline {{
        font-family: {FONTS["display"]};
        font-size: 3.25rem;
        font-weight: 600;
        color: {COLORS["text_primary"]};
        line-height: 1.15;
        margin-bottom: 1.25rem;
        letter-spacing: -0.02em;
    }}

    .editorial-subhead {{
        font-family: {FONTS["body"]};
        font-size: 1.2rem;
        font-weight: 400;
        color: {COLORS["text_muted"]};
        line-height: 1.6;
        max-width: 420px;
    }}

    /* ========== FORM PANEL ========== */
    .form-panel {{
        max-width: 360px;
    }}

    .form-title {{
        font-family: {FONTS["display"]};
        font-size: 1.5rem;
        font-weight: 600;
        color: {COLORS["text_primary"]};
        margin-bottom: 1.5rem;
    }}

    .form-footer {{
        font-family: {FONTS["body"]};
        font-size: 0.85rem;
        color: {COLORS["text_light"]};
        margin-top: 2rem;
    }}

    /* ========== DASHBOARD ========== */
    .dashboard-container {{
        padding: 1.5rem 3rem;
        max-width: 1400px;
        margin: 0 auto;
    }}

    /* Override Streamlit's default block container for dashboard */
    .stApp [data-testid="stAppViewContainer"] > section > div.block-container {{
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-top: 1rem !important;
        max-width: 1400px !important;
    }}

    .dashboard-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 0.5rem;
        margin-bottom: 0;
        border-bottom: none;
    }}

    .dashboard-wordmark {{
        font-family: {FONTS["display"]};
        font-size: 1.25rem;
        font-weight: 600;
        color: {COLORS["green"]};
        letter-spacing: -0.01em;
    }}

    .dashboard-business {{
        font-family: {FONTS["display"]};
        font-size: 1.25rem;
        font-weight: 600;
        color: {COLORS["text_primary"]};
        text-align: center;
    }}

    .dashboard-logout {{
        font-family: {FONTS["body"]};
        font-size: 0.75rem;
        color: {COLORS["text_muted"]};
        cursor: pointer;
    }}

    /* ========== INSIGHTS CONTAINER ========== */
    .insights-row {{
        background: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 0.5rem;
    }}

    .insights-grid {{
        display: grid;
        grid-template-columns: 1fr 2fr;
        gap: 2rem;
    }}

    /* ========== HEALTH SCORE ========== */
    .health-score-card {{
        background: transparent;
        padding: 1rem;
        text-align: center;
        border-right: 1px solid {COLORS["border"]};
    }}

    .health-score-label {{
        font-family: {FONTS["body"]};
        font-size: 0.65rem;
        font-weight: 600;
        color: {COLORS["text_muted"]};
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 0.75rem;
    }}

    .score-meter-container {{
        position: relative;
        width: 180px;
        height: 180px;
        margin: 0 auto 0.5rem auto;
    }}

    .score-meter-container svg {{
        position: absolute;
        top: 0;
        left: 0;
    }}

    .score-meter-value {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-family: {FONTS["display"]};
        font-size: 3.5rem;
        font-weight: 600;
        line-height: 1;
    }}

    .health-score-trend {{
        font-family: {FONTS["body"]};
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 0.25rem;
    }}

    /* ========== ACTIONS CARD ========== */
    .actions-card {{
        background: transparent;
        padding: 1rem 1.5rem;
    }}

    .actions-title {{
        font-family: {FONTS["display"]};
        font-size: 1.1rem;
        font-weight: 600;
        color: {COLORS["text_primary"]};
        margin-bottom: 0.75rem;
    }}

    .action-item {{
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid {COLORS["border"]};
    }}

    .action-item:last-child {{
        border-bottom: none;
        padding-bottom: 0;
    }}

    .action-number {{
        font-family: {FONTS["display"]};
        font-size: 1rem;
        font-weight: 600;
        color: {COLORS["green"]};
        min-width: 20px;
    }}

    .action-content {{
        flex: 1;
    }}

    .action-title {{
        font-family: {FONTS["body"]};
        font-size: 0.85rem;
        font-weight: 500;
        color: {COLORS["text_body"]};
        margin-bottom: 0.15rem;
    }}

    .action-impact {{
        font-family: {FONTS["body"]};
        font-size: 0.75rem;
        color: {COLORS["green"]};
        font-weight: 600;
    }}

    /* ========== STAT CARDS ========== */
    .stat-card {{
        background: {COLORS["bg_white"]};
        padding: 1.5rem;
        border-top: 2px solid {COLORS["green"]};
    }}

    .stat-label {{
        font-family: {FONTS["body"]};
        font-size: 0.65rem;
        font-weight: 600;
        color: {COLORS["text_muted"]};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
    }}

    .stat-value {{
        font-family: {FONTS["display"]};
        font-size: 2.5rem;
        font-weight: 600;
        color: {COLORS["text_primary"]};
        line-height: 1;
    }}

    .stat-value.success {{
        color: {COLORS["success"]};
    }}

    .stat-value.warning {{
        color: {COLORS["warning"]};
    }}

    .stat-value.danger {{
        color: {COLORS["danger"]};
    }}

    .stat-subtext {{
        font-family: {FONTS["body"]};
        font-size: 0.8rem;
        color: {COLORS["text_muted"]};
        margin-top: 0.5rem;
    }}

    /* ========== TAB NAVIGATION - Full Width Style ========== */
    .stTabs {{
        background: transparent;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.25rem;
        background: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        justify-content: space-between;
        padding: 6px;
        width: 100%;
    }}

    .stTabs [data-baseweb="tab"] {{
        font-family: {FONTS["body"]};
        font-size: 0.85rem;
        font-weight: 600;
        color: {COLORS["text_muted"]};
        background: transparent;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        transition: all 0.15s ease;
        flex: 1;
        text-align: center;
        justify-content: center;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        color: {COLORS["text_body"]};
        background: {COLORS["bg_cream"]};
    }}

    .stTabs [aria-selected="true"] {{
        color: {COLORS["bg_white"]};
        background: {COLORS["green"]};
    }}

    .stTabs [data-baseweb="tab-panel"] {{
        padding-top: 1.5rem;
    }}

    /* ========== SECTION HEADERS ========== */
    .section-header {{
        font-family: {FONTS["display"]};
        font-size: 1.5rem;
        font-weight: 600;
        color: {COLORS["text_primary"]};
        margin: 2.5rem 0 1.25rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid {COLORS["border"]};
    }}

    /* ========== INSIGHT BOX ========== */
    .insight-box {{
        background: {COLORS["bg_white"]};
        padding: 1.25rem 1.5rem;
        margin: 1.5rem 0;
        border-left: 3px solid {COLORS["green"]};
    }}

    .insight-box p {{
        font-family: {FONTS["body"]};
        font-size: 0.95rem;
        color: {COLORS["text_body"]};
        margin: 0;
        line-height: 1.6;
    }}

    .insight-box strong {{
        color: {COLORS["green"]};
        font-weight: 600;
    }}

    /* ========== DATA TABLES ========== */
    .stDataFrame {{
        background: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
    }}

    /* ========== BUTTONS ========== */
    .stButton > button {{
        font-family: {FONTS["body"]};
        font-weight: 600;
        border-radius: 4px;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
    }}

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stFormSubmitButton"] {{
        background: {COLORS["green"]} !important;
        border: none !important;
        color: white !important;
    }}

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stFormSubmitButton"]:hover {{
        background: #004D35 !important;
    }}

    /* Form submit button specifically */
    .stFormSubmitButton > button {{
        background: {COLORS["green"]} !important;
        border: none !important;
        color: white !important;
    }}

    .stFormSubmitButton > button:hover {{
        background: #004D35 !important;
    }}

    .stButton > button[kind="secondary"] {{
        background: transparent;
        border: 1px solid {COLORS["border"]};
        color: {COLORS["text_muted"]};
    }}

    .stLinkButton > a {{
        background: {COLORS["green"]} !important;
        color: white !important;
        font-weight: 600;
        border-radius: 4px;
        font-size: 0.8rem;
    }}

    /* ========== FORM INPUTS ========== */
    .stTextInput > div > div > input {{
        font-family: {FONTS["body"]};
        background: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        color: {COLORS["text_body"]};
        padding: 0.875rem 1rem;
        font-size: 1rem;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: {COLORS["green"]};
        box-shadow: none;
    }}

    .stTextInput > label {{
        font-family: {FONTS["body"]};
        font-weight: 500;
        color: {COLORS["text_body"]} !important;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }}

    /* ========== DATE INPUTS ========== */
    .stDateInput > div > div > input {{
        font-family: {FONTS["body"]};
        background: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        color: {COLORS["text_body"]};
    }}

    .stDateInput > label {{
        font-family: {FONTS["body"]};
        font-weight: 500;
        color: {COLORS["text_body"]} !important;
        font-size: 0.85rem;
    }}

    /* ========== FILE UPLOADER ========== */
    .stFileUploader > div {{
        background: {COLORS["bg_cream"]};
        border: 1px dashed {COLORS["border"]};
        border-radius: 4px;
        padding: 2rem;
    }}

    .stFileUploader label {{
        font-family: {FONTS["body"]};
    }}

    /* ========== EXPANDER ========== */
    .streamlit-expanderHeader {{
        font-family: {FONTS["body"]};
        font-weight: 500;
        background: transparent;
        color: {COLORS["text_muted"]};
    }}

    /* ========== RISK BADGES ========== */
    .risk-badge {{
        display: inline-block;
        font-family: {FONTS["body"]};
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.35rem 0.75rem;
        border-radius: 2px;
    }}

    .risk-badge.high {{
        background: #FFF5F5;
        color: {COLORS["danger"]};
    }}

    .risk-badge.medium {{
        background: #FFFBEB;
        color: {COLORS["warning"]};
    }}

    .risk-badge.low {{
        background: #F0FDF4;
        color: {COLORS["success"]};
    }}

    /* ========== CUSTOMER ROWS ========== */
    .customer-row {{
        padding: 1rem 0;
        border-bottom: 1px solid {COLORS["border"]};
    }}

    .customer-name {{
        font-family: {FONTS["body"]};
        font-weight: 600;
        color: {COLORS["text_primary"]};
        font-size: 0.95rem;
    }}

    .customer-meta {{
        font-family: {FONTS["body"]};
        font-size: 0.85rem;
        color: {COLORS["text_muted"]};
    }}

    /* ========== COUPON CODE ========== */
    .coupon-code {{
        font-family: {FONTS["mono"]};
        font-size: 1.1rem;
        font-weight: 600;
        color: {COLORS["green"]};
        background: {COLORS["bg_cream"]};
        padding: 0.75rem 1.25rem;
        border-radius: 2px;
        display: inline-block;
        letter-spacing: 0.05em;
    }}

    /* ========== UPLOAD INFO ========== */
    .upload-info {{
        font-family: {FONTS["body"]};
        font-size: 0.9rem;
        color: {COLORS["text_muted"]};
        line-height: 1.8;
    }}

    .upload-info strong {{
        color: {COLORS["text_body"]};
        font-weight: 600;
    }}

</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE
# =============================================================================
def init_session_state():
    defaults = {
        "logged_in": False,
        "data_loaded": False,
        "business_name": None,
        "email": None,
        "raw_data": None,
        "customer_data": None,
        "current_view": "login",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def calculate_health_score(customer_df, raw_df):
    scores = []
    active_60 = len(customer_df[customer_df["days_since_visit"] <= 60])
    retention_rate = active_60 / len(customer_df) if len(customer_df) > 0 else 0
    scores.append(min(retention_rate * 100, 30))

    loyal = len(customer_df[customer_df["segment"].isin(["Regular", "Superuser"])])
    loyalty_rate = loyal / len(customer_df) if len(customer_df) > 0 else 0
    scores.append(min(loyalty_rate * 100 * 1.25, 25))

    if len(raw_df) > 0:
        recent_cutoff = raw_df["start"].max() - pd.Timedelta(days=90)
        first_visits = raw_df.groupby("client_name")["start"].min()
        new_customers = (first_visits >= recent_cutoff).sum()
        growth_rate = new_customers / len(customer_df) if len(customer_df) > 0 else 0
        scores.append(min(growth_rate * 100 * 2.5, 25))
    else:
        scores.append(12.5)

    avg_value = customer_df["total_spend"].mean() if len(customer_df) > 0 else 0
    scores.append(min((avg_value / 200) * 10, 20))

    return int(min(sum(scores), 100))


def get_health_trend(score):
    if score >= 70:
        return "+5 vs last month", COLORS["success"]
    elif score >= 50:
        return "Stable", COLORS["text_muted"]
    else:
        return "-3 vs last month", COLORS["danger"]


def get_top_actions(customer_df, churn_results, segment_summary):
    actions = []

    if churn_results["high_risk_count"] > 0:
        impact = churn_results["revenue_at_risk"] * 0.3
        actions.append({
            "title": f"Re-engage {churn_results['high_risk_count']} at-risk customers",
            "impact": f"+${impact:,.0f} potential"
        })

    casuals = customer_df[customer_df["segment"] == "Casual"]
    candidates = casuals[casuals["frequency"] >= 5]
    if len(candidates) > 0:
        impact = len(candidates) * 300 * 0.2
        actions.append({
            "title": f"Upgrade {len(candidates)} casuals to regulars",
            "impact": f"+${impact:,.0f} annual"
        })

    dormant = customer_df[customer_df["days_since_visit"] > 45]
    if len(dormant) > 0:
        impact = dormant["total_spend"].sum() * 0.15
        actions.append({
            "title": f"Check in with {len(dormant)} overdue customers",
            "impact": f"${impact:,.0f} at stake"
        })

    while len(actions) < 3:
        actions.append({"title": "Expand your market reach", "impact": "Grow customer base"})

    return actions[:3]


# =============================================================================
# LOGIN VIEW
# =============================================================================
def render_login():
    # Split screen layout using columns
    left_col, right_col = st.columns([58, 42], gap="small")

    with left_col:
        st.markdown(f"""
        <div style="height: 80vh; display: flex; flex-direction: column; justify-content: center; padding: 2rem 3rem;">
            <div class="wordmark">BizPulse</div>
            <h1 class="editorial-headline">Know your<br>business before<br>it surprises you.</h1>
            <p class="editorial-subhead">Turn customer data into clarity — in 60 seconds.</p>
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        # Add vertical spacing to center the form
        st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: {COLORS["bg_white"]}; padding: 2.5rem;">
            <div class="form-panel">
                <div class="form-title" style="margin-bottom: 1.25rem;">Get your free Health Score</div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@business.com")
            business_name = st.text_input("Business name", placeholder="Acme Coffee Shop")

            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Continue", use_container_width=True, type="primary")

            if submitted:
                if email and business_name:
                    st.session_state.email = email
                    st.session_state.business_name = business_name
                    st.session_state.logged_in = True
                    st.session_state.current_view = "upload"
                    st.rerun()
                else:
                    st.error("Please fill in both fields")

        st.markdown(f"""
                <div class="form-footer">Free forever for basic insights.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# UPLOAD VIEW
# =============================================================================
def render_upload():
    # Split screen layout using columns
    left_col, right_col = st.columns([58, 42], gap="small")

    with left_col:
        st.markdown(f"""
        <div style="height: 80vh; display: flex; flex-direction: column; justify-content: center; padding: 2rem 3rem;">
            <div class="wordmark">BizPulse</div>
            <h1 class="editorial-headline">One file.<br>Complete<br>clarity.</h1>
            <p class="editorial-subhead">Export from Square, Toast, or your booking system. We'll handle the rest.</p>
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        # Add vertical spacing to center the form
        st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: {COLORS["bg_white"]}; padding: 2.5rem;">
            <div class="form-panel" style="max-width: 400px;">
                <div class="form-title" style="margin-bottom: 1.25rem;">Upload your data</div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload CSV", type="csv", label_visibility="collapsed")

        st.markdown(f"""
        <div class="upload-info" style="margin: 1rem 0;">
            <strong>We need:</strong><br>
            • client_name — Customer name or ID<br>
            • start — Transaction date<br>
            • status — We filter to completed
        </div>
        """, unsafe_allow_html=True)

        if uploaded_file is not None:
            try:
                with st.spinner("Analyzing your data..."):
                    raw_df = load_and_process_csv(uploaded_file)
                    st.session_state.raw_data = raw_df

                    unique_customers = raw_df["client_name"].nunique()
                    min_date = raw_df["start"].min()
                    max_date = raw_df["start"].max()

                    st.markdown(f"""
                    <div class="insight-box" style="margin: 0.75rem 0;">
                        <p><strong>Data loaded:</strong> {len(raw_df):,} visits from {unique_customers:,} customers
                        ({min_date.strftime('%b %Y')} – {max_date.strftime('%b %Y')})</p>
                    </div>
                    """, unsafe_allow_html=True)

                if st.button("Calculate Health Score", type="primary", use_container_width=True):
                    customer_df = aggregate_to_customers(raw_df)
                    customer_df = assign_segments(customer_df)
                    st.session_state.customer_data = customer_df
                    st.session_state.data_loaded = True
                    st.session_state.current_view = "dashboard"
                    st.rerun()

            except Exception as e:
                st.error(f"Could not process file: {str(e)}")

        st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

        if st.button("← Back", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.current_view = "login"
            st.rerun()

        st.markdown(f"""
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# DASHBOARD VIEW
# =============================================================================
def render_dashboard():
    raw_df = st.session_state.raw_data
    customer_df = st.session_state.customer_data
    business_name = st.session_state.business_name

    # Dashboard container with padding
    st.markdown("""<div class="dashboard-container">""", unsafe_allow_html=True)

    # Header - three column layout
    header_left, header_center, header_right = st.columns([1, 2, 1])

    with header_left:
        st.markdown("""<div class="dashboard-wordmark">BizPulse</div>""", unsafe_allow_html=True)

    with header_center:
        st.markdown(f"""<div class="dashboard-business">{business_name}</div>""", unsafe_allow_html=True)

    with header_right:
        col_spacer, col_btn = st.columns([2, 1])
        with col_btn:
            if st.button("Logout", type="secondary", key="logout_btn"):
                st.session_state.logged_in = False
                st.session_state.data_loaded = False
                st.session_state.current_view = "login"
                st.rerun()

    st.markdown(f"""<div style="border-bottom: 1px solid {COLORS['border']}; margin: 0.25rem 0 0.75rem 0;"></div>""", unsafe_allow_html=True)

    # Calculate metrics
    health_score = calculate_health_score(customer_df, raw_df)
    trend_text, trend_color = get_health_trend(health_score)
    churn_results = get_churn_summary(customer_df)
    segment_summary = get_segment_summary(customer_df)
    top_actions = get_top_actions(customer_df, churn_results, segment_summary)

    # Score color
    if health_score >= 70:
        score_color = COLORS["success"]
    elif health_score >= 50:
        score_color = COLORS["warning"]
    else:
        score_color = COLORS["danger"]

    # Health Score + Actions Row - full HTML for proper containment
    actions_html = ""
    for i, action in enumerate(top_actions, 1):
        actions_html += f'<div class="action-item"><div class="action-number">{i}.</div><div class="action-content"><div class="action-title">{action["title"]}</div><div class="action-impact">{action["impact"]}</div></div></div>'

    # SVG circular progress meter
    # Circle parameters
    radius = 70
    stroke_width = 8
    circumference = 2 * 3.14159 * radius
    progress = health_score / 100
    stroke_dashoffset = circumference * (1 - progress)

    circle_meter = f'''<svg width="180" height="180" viewBox="0 0 180 180" style="transform: rotate(-90deg);">
        <circle cx="90" cy="90" r="{radius}" fill="none" stroke="{COLORS["border"]}" stroke-width="{stroke_width}"/>
        <circle cx="90" cy="90" r="{radius}" fill="none" stroke="{score_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dashoffset}" style="transition: stroke-dashoffset 0.5s ease;"/>
    </svg>'''

    health_score_html = f'''<div class="health-score-card">
        <div class="health-score-label">Business Health Score</div>
        <div class="score-meter-container">
            {circle_meter}
            <div class="score-meter-value" style="color: {score_color};">{health_score}</div>
        </div>
        <div class="health-score-trend" style="color: {trend_color};">{trend_text}</div>
    </div>'''

    insights_html = f'''<div class="insights-row"><div class="insights-grid">{health_score_html}<div class="actions-card"><div class="actions-title">Your Top 3 Actions</div>{actions_html}</div></div></div>'''

    st.markdown(insights_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # Tabs
    tabs = st.tabs(["Overview", "Segments", "Retention", "Upgrades", "CLV", "Churn"])

    with tabs[0]:
        render_overview_tab(customer_df, raw_df, segment_summary)
    with tabs[1]:
        render_segments_tab(raw_df)
    with tabs[2]:
        render_retention_tab(raw_df)
    with tabs[3]:
        render_upgrades_tab(raw_df)
    with tabs[4]:
        render_clv_tab(raw_df)
    with tabs[5]:
        render_churn_tab(raw_df)


# =============================================================================
# TAB: OVERVIEW
# =============================================================================
def render_overview_tab(customer_df, raw_df, segment_summary):
    total_customers = len(customer_df)
    total_revenue = customer_df["total_spend"].sum()
    avg_visits = customer_df["frequency"].mean()
    active_rate = len(customer_df[customer_df["days_since_visit"] <= 60]) / total_customers if total_customers > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Customers</div>
            <div class="stat-value">{total_customers:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Revenue</div>
            <div class="stat-value accent">${total_revenue:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Avg Visits</div>
            <div class="stat-value">{avg_visits:.1f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Active Rate</div>
            <div class="stat-value success">{active_rate:.0%}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Customer Segments</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        colors = [COLORS["green"], "#00574B", "#007A5E", "#00A376"]

        for i, (idx, row) in enumerate(segment_summary.iterrows()):
            fig.add_trace(go.Bar(
                y=[row["segment"]],
                x=[row["customer_count"]],
                orientation='h',
                marker_color=colors[i % len(colors)],
                text=f'{row["customer_count"]:,}',
                textposition='outside',
                textfont=dict(color=COLORS["text_body"], size=12, family="Inter"),
                showlegend=False
            ))

        fig.update_layout(
            height=250,
            margin=dict(t=10, b=20, l=100, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor=COLORS["border"], showline=False, tickfont=dict(color=COLORS["text_muted"], family="Inter")),
            yaxis=dict(showgrid=False, showline=False, tickfont=dict(color=COLORS["text_body"], family="Inter", size=12)),
            font=dict(family="Inter, sans-serif", color=COLORS["text_body"])
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=segment_summary["segment"],
            y=segment_summary["total_revenue"],
            marker_color=COLORS["green"],
            text=segment_summary["total_revenue"].apply(lambda x: f"${x/1000:.0f}k" if x >= 1000 else f"${x:.0f}"),
            textposition='outside',
            textfont=dict(color=COLORS["text_body"], size=12, family="Inter")
        ))

        fig.update_layout(
            height=250,
            margin=dict(t=10, b=40, l=60, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, showline=True, linecolor=COLORS["border"], tickfont=dict(color=COLORS["text_body"], family="Inter")),
            yaxis=dict(showgrid=True, gridcolor=COLORS["border"], showline=False, tickfont=dict(color=COLORS["text_muted"], family="Inter"), title=""),
            showlegend=False,
            font=dict(family="Inter, sans-serif", color=COLORS["text_body"])
        )
        st.plotly_chart(fig, use_container_width=True)

    superusers = segment_summary[segment_summary["segment"] == "Superuser"]
    if len(superusers) > 0:
        su_revenue = superusers.iloc[0]["total_revenue"]
        su_pct = su_revenue / total_revenue if total_revenue > 0 else 0
        st.markdown(f"""
        <div class="insight-box">
            <p><strong>Key insight:</strong> Your Superusers generate {su_pct:.0%} of total revenue.
            Keeping them happy should be your top priority.</p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# TAB: SEGMENTS
# =============================================================================
def render_segments_tab(raw_df):
    col1, col2, col3 = st.columns([1, 1, 3])
    min_date = raw_df["start"].min().date()
    max_date = raw_df["start"].max().date()

    with col1:
        start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="seg_start")
    with col2:
        end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="seg_end")

    customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
    customer_df = assign_segments(customer_df)
    segment_summary = get_segment_summary(customer_df)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    cols = st.columns(4)
    segment_colors = {"Explorer": "#00A376", "Casual": "#007A5E", "Regular": "#00574B", "Superuser": COLORS["green"]}

    for i, (idx, row) in enumerate(segment_summary.iterrows()):
        with cols[i]:
            pct = row["customer_count"] / len(customer_df) * 100 if len(customer_df) > 0 else 0
            st.markdown(f"""
            <div class="stat-card" style="border-top: 4px solid {segment_colors.get(row['segment'], COLORS['green'])};">
                <div class="stat-label">{row['segment']}</div>
                <div class="stat-value">{row['customer_count']:,}</div>
                <div class="stat-subtext">{pct:.0f}% of customers</div>
            </div>
            """, unsafe_allow_html=True)

    with st.expander("How segments are defined"):
        st.markdown("""
        | Segment | Visits | Description |
        |---------|--------|-------------|
        | **Explorer** | 1-2 | Trying you out |
        | **Casual** | 3-8 | Occasional customer |
        | **Regular** | 9-12 | Consistent visitor |
        | **Superuser** | 13+ | Your best customers |
        """)


# =============================================================================
# TAB: RETENTION
# =============================================================================
def render_retention_tab(raw_df):
    col1, col2, col3 = st.columns([1, 1, 3])
    min_date = raw_df["start"].min().date()
    max_date = raw_df["start"].max().date()

    with col1:
        start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="ret_start")
    with col2:
        end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="ret_end")

    customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
    customer_df = assign_segments(customer_df)

    overdue_30 = customer_df[customer_df["days_since_visit"] > 30]
    overdue_60 = customer_df[customer_df["days_since_visit"] > 60]
    overdue_90 = customer_df[customer_df["days_since_visit"] > 90]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Overdue (30+ days)</div>
            <div class="stat-value warning">{len(overdue_30)}</div>
            <div class="stat-subtext">Worth checking in</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Slipping (60+ days)</div>
            <div class="stat-value warning">{len(overdue_60)}</div>
            <div class="stat-subtext">Need attention</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">At Risk (90+ days)</div>
            <div class="stat-value danger">{len(overdue_90)}</div>
            <div class="stat-subtext">May have churned</div>
        </div>
        """, unsafe_allow_html=True)

    valuable = overdue_30[overdue_30["segment"].isin(["Casual", "Regular", "Superuser"])]
    value_at_risk = valuable["total_spend"].sum() * 0.5

    st.markdown(f"""
    <div class="insight-box">
        <p><strong>{len(valuable)} valuable customers</strong> are overdue.
        A quick check-in could protect <strong>${value_at_risk:,.0f}</strong> in annual revenue.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Customers Needing Attention</div>', unsafe_allow_html=True)

    at_risk = overdue_30.sort_values("total_spend", ascending=False).head(10)

    if len(at_risk) > 0:
        display_df = at_risk[["client_name", "segment", "days_since_visit", "total_spend"]].copy()
        display_df.columns = ["Customer", "Segment", "Days Overdue", "Annual Value"]
        display_df["Annual Value"] = display_df["Annual Value"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.success("All customers are active!")


# =============================================================================
# TAB: UPGRADES
# =============================================================================
def render_upgrades_tab(raw_df):
    business_name = st.session_state.business_name

    col1, col2, col3 = st.columns([1, 1, 3])
    min_date = raw_df["start"].min().date()
    max_date = raw_df["start"].max().date()

    with col1:
        start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="upg_start")
    with col2:
        end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="upg_end")

    customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
    customer_df = assign_segments(customer_df)

    casuals = customer_df[customer_df["segment"] == "Casual"]
    regulars = customer_df[customer_df["segment"] == "Regular"]

    avg_casual = casuals["total_spend"].mean() if len(casuals) > 0 else 0
    avg_regular = regulars["total_spend"].mean() if len(regulars) > 0 else 0
    upgrade_value = max(avg_regular - avg_casual, 300)

    st.markdown(f"""
    <div class="insight-box">
        <p><strong>Upgrade opportunity:</strong> Each Casual who becomes a Regular adds <strong>${upgrade_value:,.0f}</strong>.
        Converting just 5 = <strong>${upgrade_value * 5:,.0f}</strong> more revenue.</p>
    </div>
    """, unsafe_allow_html=True)

    if "coupon_loyal" not in st.session_state:
        st.session_state.coupon_loyal = generate_coupon_code("LOYAL")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Coupon Code</div>
            <div class="coupon-code">{st.session_state.coupon_loyal}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("New Code"):
            st.session_state.coupon_loyal = generate_coupon_code("LOYAL")
            st.rerun()

    st.markdown('<div class="section-header">Best Upgrade Candidates</div>', unsafe_allow_html=True)

    candidates = casuals[casuals["frequency"] >= 5].sort_values("frequency", ascending=False)

    if len(candidates) > 0:
        for idx, row in candidates.head(5).iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"""
                <div class="customer-name">{row['client_name']}</div>
                <div class="customer-meta">{int(row['frequency'])} visits · ${row['total_spend']:,.0f} spent</div>
                """, unsafe_allow_html=True)

            with col2:
                visits_to_regular = 9 - int(row['frequency'])
                st.markdown(f"""
                <div style="color: {COLORS["green"]}; font-weight: 600; font-size: 0.9rem;">{visits_to_regular} visits to Regular</div>
                """, unsafe_allow_html=True)

            with col3:
                message = generate_upgrade_message(row['client_name'].split()[0], int(row['frequency']), 9, st.session_state.coupon_loyal, business_name)
                email = row.get('email', '')
                if email and pd.notna(email):
                    link = build_email_link(str(email), f"Special offer from {business_name}", message)
                    st.link_button("Email", link)
    else:
        st.info("No casuals close to Regular status yet.")


# =============================================================================
# TAB: CLV
# =============================================================================
def render_clv_tab(raw_df):
    col1, col2, col3 = st.columns([1, 1, 3])
    min_date = raw_df["start"].min().date()
    max_date = raw_df["start"].max().date()

    with col1:
        start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="clv_start")
    with col2:
        end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="clv_end")

    customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
    customer_df = assign_segments(customer_df)

    clv_results = fit_gamma_gamma(customer_df)

    if not clv_results["success"]:
        st.warning(clv_results["message"])
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Average CLV</div>
            <div class="stat-value">${clv_results['avg_clv']:,.0f}</div>
            <div class="stat-subtext">Per customer</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Top 10% CLV</div>
            <div class="stat-value accent">${clv_results['top_10_pct_clv']:,.0f}</div>
            <div class="stat-subtext">Your best customers</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Predicted</div>
            <div class="stat-value success">${clv_results['total_clv']:,.0f}</div>
            <div class="stat-subtext">Future revenue</div>
        </div>
        """, unsafe_allow_html=True)

    multiplier = clv_results['top_10_pct_clv'] / clv_results['avg_clv'] if clv_results['avg_clv'] > 0 else 1

    st.markdown(f"""
    <div class="insight-box">
        <p>Your top 10% are worth <strong>{multiplier:.1f}x more</strong> than average.
        Focus on keeping them happy.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">CLV Distribution</div>', unsafe_allow_html=True)

    repeat_df = clv_results["repeat_customers"]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=repeat_df["clv"],
        nbinsx=20,
        marker_color=COLORS["green"],
        marker_line_color=COLORS["bg_white"],
        marker_line_width=1
    ))

    fig.update_layout(
        height=280,
        margin=dict(t=10, b=40, l=60, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Customer Lifetime Value ($)", showgrid=False, showline=True, linecolor=COLORS["border"], tickfont=dict(color=COLORS["text_muted"], family="Inter")),
        yaxis=dict(title="Customers", showgrid=True, gridcolor=COLORS["border"], showline=False, tickfont=dict(color=COLORS["text_muted"], family="Inter")),
        font=dict(family="Inter, sans-serif", color=COLORS["text_body"])
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">Most Valuable Customers</div>', unsafe_allow_html=True)

    top = repeat_df.nlargest(8, "clv")[["client_name", "frequency", "total_spend", "clv"]].copy()
    top.columns = ["Customer", "Visits", "Spent", "Predicted CLV"]
    top["Spent"] = top["Spent"].apply(lambda x: f"${x:,.0f}")
    top["Predicted CLV"] = top["Predicted CLV"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(top, use_container_width=True, hide_index=True)


# =============================================================================
# TAB: CHURN
# =============================================================================
def render_churn_tab(raw_df):
    business_name = st.session_state.business_name

    col1, col2, col3 = st.columns([1, 1, 3])
    min_date = raw_df["start"].min().date()
    max_date = raw_df["start"].max().date()

    with col1:
        start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="churn_start")
    with col2:
        end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="churn_end")

    customer_df = aggregate_to_customers(raw_df, start_date=start_date, end_date=end_date)
    customer_df = assign_segments(customer_df)

    churn_results = get_churn_summary(customer_df)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Likely to Churn</div>
            <div class="stat-value danger">{churn_results['high_risk_count']}</div>
            <div class="stat-subtext">High probability</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Revenue at Risk</div>
            <div class="stat-value warning">${churn_results['revenue_at_risk']:,.0f}</div>
            <div class="stat-subtext">If all churn</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Still Active</div>
            <div class="stat-value success">{churn_results['still_active_pct']:.0%}</div>
            <div class="stat-subtext">Healthy customers</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="insight-box">
        <p><strong>{churn_results['high_risk_count']} customers</strong> have high churn risk.
        Winning them back could recover <strong>${churn_results['revenue_at_risk'] * 0.3:,.0f}</strong> (30% win-back rate).</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Churn Risk Map</div>', unsafe_allow_html=True)

    plot_df = churn_results["customer_df"]

    fig = go.Figure()

    low_risk = plot_df[plot_df["p_churn"] < 0.4]
    med_risk = plot_df[(plot_df["p_churn"] >= 0.4) & (plot_df["p_churn"] < 0.7)]
    high_risk_df = plot_df[plot_df["p_churn"] >= 0.7]

    fig.add_trace(go.Scatter(
        x=low_risk["days_since_visit"], y=low_risk["frequency"],
        mode='markers', name='Low risk',
        marker=dict(color=COLORS["success"], size=10, opacity=0.8),
        hovertemplate='%{customdata[0]}<br>%{x} days ago<br>%{y} visits<extra></extra>',
        customdata=low_risk[["client_name"]].values
    ))

    fig.add_trace(go.Scatter(
        x=med_risk["days_since_visit"], y=med_risk["frequency"],
        mode='markers', name='Medium risk',
        marker=dict(color=COLORS["warning"], size=10, opacity=0.8),
        hovertemplate='%{customdata[0]}<br>%{x} days ago<br>%{y} visits<extra></extra>',
        customdata=med_risk[["client_name"]].values
    ))

    fig.add_trace(go.Scatter(
        x=high_risk_df["days_since_visit"], y=high_risk_df["frequency"],
        mode='markers', name='High risk',
        marker=dict(color=COLORS["danger"], size=10, opacity=0.8),
        hovertemplate='%{customdata[0]}<br>%{x} days ago<br>%{y} visits<extra></extra>',
        customdata=high_risk_df[["client_name"]].values
    ))

    fig.update_layout(
        height=320,
        margin=dict(t=10, b=40, l=60, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Days Since Last Visit", showgrid=True, gridcolor=COLORS["border"], showline=True, linecolor=COLORS["border"], tickfont=dict(color=COLORS["text_muted"], family="Inter")),
        yaxis=dict(title="Number of Visits", showgrid=True, gridcolor=COLORS["border"], showline=False, tickfont=dict(color=COLORS["text_muted"], family="Inter")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=COLORS["text_body"], family="Inter")),
        font=dict(family="Inter, sans-serif", color=COLORS["text_body"])
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">High-Risk Customers</div>', unsafe_allow_html=True)

    if "winback_coupon" not in st.session_state:
        st.session_state.winback_coupon = generate_coupon_code("MISS")

    high_risk = churn_results["high_risk_customers"].sort_values("total_spend", ascending=False)

    if len(high_risk) > 0:
        for idx, row in high_risk.head(5).iterrows():
            churn_pct = row["p_churn"] * 100
            risk_class = "high" if churn_pct >= 70 else "medium"

            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"""
                <div class="customer-name">{row['client_name']}</div>
                <div class="customer-meta">${row['total_spend']:,.0f} lifetime value</div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f'<span class="risk-badge {risk_class}">{churn_pct:.0f}% churn risk</span>', unsafe_allow_html=True)

            with col3:
                message = generate_winback_message(row['client_name'].split()[0], st.session_state.winback_coupon, business_name)
                email = row.get('email', '')
                if email and pd.notna(email):
                    link = build_email_link(str(email), f"We miss you at {business_name}!", message)
                    st.link_button("Win back", link)
    else:
        st.success("No high-risk customers identified!")


# =============================================================================
# MAIN
# =============================================================================
def main():
    if st.session_state.current_view == "login":
        render_login()
    elif st.session_state.current_view == "upload":
        render_upload()
    elif st.session_state.current_view == "dashboard":
        render_dashboard()
    else:
        render_login()

if __name__ == "__main__":
    main()
