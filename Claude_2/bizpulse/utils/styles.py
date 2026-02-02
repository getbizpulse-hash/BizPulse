import streamlit as st

# =============================================================================
# DESIGN SYSTEM - Calm, Opinionated, Trustworthy
# Aesthetic: Apple Health + Stripe Clarity. 
# Colors: Soft grays, deep confident greens, ample whitespace.
# =============================================================================

COLORS = {
    # Base - Boutique Premium Palette
    "bg_app": "#FBFBFC",           # Ultra-light slate for app background
    "bg_white": "#FFFFFF",         # Pure white for cards
    "bg_subtle": "#F8FAFC",        # Subtle slate background
    
    # Text - Slate Scale
    "text_primary": "#0F172A",     # Slate-900 - Deep, confident text
    "text_secondary": "#475569",   # Slate-600 - Readable secondary
    "text_tertiary": "#94A3B8",    # Slate-400 - Muted labels
    "text_muted": "#CBD5E1",       # Slate-300 - Very light text
    
    # Brand - Indigo Primary
    "brand_primary": "#4F46E5",    # Indigo-600 - Primary brand color
    "indigo_primary": "#4F46E5",   # Indigo-600
    "indigo_light": "#EEF2FF",     # Indigo-50 - Light backgrounds
    "indigo_dark": "#3730A3",      # Indigo-800 - Dark accents
    
    # Slate Scale
    "slate_900": "#0F172A",        # Deep slate for dark cards
    "slate_800": "#1E293B",        # Dark slate
    "slate_700": "#334155",        # Medium-dark slate
    "slate_600": "#475569",        # Medium slate
    "slate_500": "#64748B",        # Mid slate
    "slate_400": "#94A3B8",        # Light slate
    "slate_300": "#CBD5E1",        # Very light slate
    "slate_200": "#E2E8F0",        # Ultra-light slate
    "slate_100": "#F1F5F9",        # Near-white slate
    "slate_50": "#F8FAFC",         # Lightest slate
    
    # Accent Colors
    "rose_accent": "#F43F5E",      # Rose-500 - Attention/urgent
    "rose_light": "#FFF1F2",       # Rose-50 - Light backgrounds
    "emerald_accent": "#10B981",   # Emerald-500 - Success/growth
    "emerald_light": "#ECFDF5",    # Emerald-50
    "amber_accent": "#F59E0B",     # Amber-500 - Warning
    "amber_light": "#FFFBEB",      # Amber-50
    
    # Status (Boutique versions)
    "success": "#10B981",          # Emerald-500
    "success_bg": "#ECFDF5",       # Emerald-50
    "warning": "#F59E0B",          # Amber-500
    "warning_bg": "#FFFBEB",       # Amber-50
    "danger": "#EF4444",           # Red-500
    "danger_bg": "#FEF2F2",        # Red-50
    
    # Borders
    "border": "#E2E8F0",           # Slate-200
    "border_light": "#F1F5F9",     # Slate-100
    
    # Header (Updated for boutique feel)
    "header_bg": "#FFFFFF",        # White with backdrop blur
    "header_text": "#0F172A",      # Slate-900
    "context_bg": "#F8FAFC",       # Slate-50
    
    # Shadows
    "card_shadow": "0 1px 3px rgba(0,0,0,0.05)",
    "card_shadow_lg": "0 10px 25px rgba(0,0,0,0.08)",
    "card_shadow_xl": "0 20px 50px rgba(0,0,0,0.12)",
    
    # Legacy mappings (for backward compatibility)
    "bg_cream": "#FBFBFC",
    "green": "#10B981",
    "text_body": "#0F172A",
    "text_light": "#94A3B8",
}

FONTS = {
    "display": "'-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Inter', 'Segoe UI', sans-serif",
    "body": "'-apple-system', 'BlinkMacSystemFont', 'SF Pro Text', 'Inter', 'Segoe UI', sans-serif",
    "mono": "'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace",
}

def apply_custom_css():
    st.markdown(f"""
    <style>
        /* ========== GLOBAL RESET & TYPOGRAPHY ========== */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: {FONTS["body"]};
            color: {COLORS["text_primary"]};
            -webkit-font-smoothing: antialiased;
        }}
        
        /* App Background */
        .stApp {{
            background-color: {COLORS["bg_app"]};
        }}

        /* Hide Streamlit Chrome */
        [data-testid="stSidebar"] {{ display: none; }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header {{ visibility: hidden; }}

        /* Layout Container */
        .block-container {{
            padding: 3rem 2rem !important;
            max-width: 1200px !important;
        }}

        /* Headings */
        h1, h2, h3 {{
            font-family: {FONTS["display"]};
            font-weight: 600;
            letter-spacing: -0.02em;
            color: {COLORS["text_primary"]};
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
            background: {COLORS["bg_app"]};
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
            border-left: 1px solid {COLORS["border"]};
        }}
        
        /* Wordmark */
        .wordmark {{
            font-size: 0.9rem;
            font-weight: 700;
            color: {COLORS["text_primary"]};
            letter-spacing: -0.02em;
            margin-bottom: 2rem;
        }}
        
        /* Headlines */
        .editorial-headline {{
            font-size: 3rem;
            font-weight: 700;
            color: {COLORS["text_primary"]};
            line-height: 1.1;
            margin-bottom: 1.5rem;
            letter-spacing: -0.03em;
        }}

        .editorial-subhead {{
            font-size: 1.25rem;
            color: {COLORS["text_secondary"]};
            line-height: 1.6;
            max-width: 480px;
        }}

        /* ========== COMPONENTS ========== */
        
        /* Cards (White containers with subtle shadow) */
        .card {{
            background-color: {COLORS["bg_white"]};
            border-radius: 12px;
            border: 1px solid {COLORS["border"]};
            padding: 1.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
            margin-bottom: 1.5rem;
        }}

        /* Metrics / key numbers */
        .metric-label {{
            font-size: 0.85rem;
            font-weight: 500;
            color: {COLORS["text_secondary"]};
            margin-bottom: 0.25rem;
        }}

        .metric-value {{
            font-size: 1.75rem;
            font-weight: 600;
            color: {COLORS["text_primary"]};
            letter-spacing: -0.03em;
        }}
        
        .metric-trend {{
            font-size: 0.85rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
        }}
        
        .trend-up {{ color: {COLORS["success"]}; }}
        .trend-down {{ color: {COLORS["danger"]}; }}
        .trend-neutral {{ color: {COLORS["text_secondary"]}; }}

        /* Badges */
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            line-height: 1;
        }}
        
        .badge-success {{ background: {COLORS["success_bg"]}; color: {COLORS["success"]}; }}
        .badge-warning {{ background: {COLORS["warning_bg"]}; color: {COLORS["warning"]}; }}
        .badge-danger {{ background: {COLORS["danger_bg"]}; color: {COLORS["danger"]}; }}
        .badge-neutral {{ background: {COLORS["bg_subtle"]}; color: {COLORS["text_secondary"]}; }}

        /* Buttons (Apple-like) */
        .stButton > button {{
            border-radius: 8px;
            font-weight: 500;
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            transition: all 0.15s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        
        /* Primary Action */
        .stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button {{
            background-color: {COLORS["brand_primary"]} !important;
            color: white !important;
            border: 1px solid {COLORS["brand_primary"]} !important;
        }}
        
        .stButton > button[kind="primary"]:hover {{
            background-color: #0B3D25 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        /* Secondary Action */
        .stButton > button[kind="secondary"] {{
            background-color: {COLORS["bg_white"]} !important;
            color: {COLORS["text_primary"]} !important;
            border: 1px solid {COLORS["border"]} !important;
        }}
        
        .stButton > button[kind="secondary"]:hover {{
            background-color: {COLORS["bg_subtle"]} !important;
            border-color: {COLORS["text_tertiary"]} !important;
        }}

        /* Inputs */
        input, select {{
            border-radius: 8px !important;
            border: 1px solid {COLORS["border"]} !important;
            padding: 0.6rem 1rem !important;
            font-size: 0.95rem !important;
        }}
        
        input:focus {{
            border-color: {COLORS["brand_primary"]} !important;
            box-shadow: 0 0 0 2px {COLORS["indigo_light"]} !important;
        }}

        /* TABS - VISUAL OVERRIDE */
        
        /* 1. Hide Streamlit's Default Red Highlight & Borders */
        [data-baseweb="tab-highlight"],
        [data-baseweb="tab-border"] {{
            visibility: hidden !important;
            display: none !important;
        }}
        
        /* 2. Reset the container */
        .stTabs {{
            background-color: transparent !important;
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            justify-content: center !important;
            gap: 3rem !important; /* Spread out horizontally */
            border-bottom: 1px solid {COLORS["border"]} !important;
            padding-bottom: 0px !important;
            margin-bottom: 2rem !important;
        }}

        /* 3. Style the Tab Element (Wrapper) */
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent !important;
            border: none !important;
            padding: 1rem 0.5rem !important; /* Vertical padding, minimal horizontal to rely on gap */
            background: transparent !important;
            color: {COLORS["text_secondary"]} !important;
            border-radius: 0 !important;
            flex-grow: 0 !important;
            position: relative !important;
            transition: all 0.2s ease !important;
            box-shadow: none !important;
            outline: none !important;
        }}
        
        /* 4. Force Text Styling (p tag inside tab) */
        .stTabs [data-baseweb="tab"] p {{
            font-family: {FONTS["display"]} !important; /* Use Display font for labels */
            font-size: 0.9rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            color: inherit !important;
        }}

        /* 5. Hover State */
        .stTabs [data-baseweb="tab"]:hover {{
            color: {COLORS["text_primary"]} !important;
            background-color: transparent !important; /* No bg on hover, just text change */
        }}
        
        .stTabs [data-baseweb="tab"]:hover p {{
            color: {COLORS["brand_primary"]} !important;
        }}

        /* 6. Active State */
        .stTabs [aria-selected="true"] {{
            background-color: transparent !important;
            border-bottom: 2px solid {COLORS["brand_primary"]} !important;
        }}
        
        /* Ensure the paragraph inside active tab is also bold/green */
        .stTabs [aria-selected="true"] p {{
            font-weight: 700 !important;
            color: {COLORS["brand_primary"]} !important;
        }}
        
        /* Focus State Clean up */
        .stTabs [data-baseweb="tab"]:focus {{
            outline: none !important;
        }}

        /* Hover Hints (Tooltips) */
        button[data-baseweb="tab"]:hover::before {{
            position: absolute;
            top: -32px;
            left: 50%;
            transform: translateX(-50%);
            background-color: {COLORS["text_primary"]};
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
            white-space: nowrap;
            opacity: 0;
            animation: fadeIn 0.2s forwards 0.2s; /* Slight delay */
            pointer-events: none;
            z-index: 999;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; top: -25px; }}
            to {{ opacity: 1; top: -32px; }}
        }}

        /* Content for specific tabs */
        button[data-baseweb="tab"]:nth-of-type(1):hover::before {{ content: "Executive summary"; }}
        button[data-baseweb="tab"]:nth-of-type(2):hover::before {{ content: "Customer types"; }}
        button[data-baseweb="tab"]:nth-of-type(3):hover::before {{ content: "Who needs attention"; }}
        button[data-baseweb="tab"]:nth-of-type(4):hover::before {{ content: "Grow revenue"; }}
        button[data-baseweb="tab"]:nth-of-type(5):hover::before {{ content: "Long-term value"; }}
        button[data-baseweb="tab"]:nth-of-type(6):hover::before {{ content: "Revenue at risk"; }}

        /* Dataframes */
        .stDataFrame {{
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            overflow: hidden;
        }}
        
        /* ========== SCOPED UTILITIES ========== */
        .text-sm {{ font-size: 0.8rem; }}
        .text-muted {{ color: {COLORS["text_tertiary"]}; }}
        .text-right {{ text-align: right; }}
        .mb-2 {{ margin-bottom: 0.5rem; }}
        .mb-4 {{ margin-bottom: 1rem; }}
        
        /* Action Card Specifics */
        .action-card {{
            background: {COLORS["bg_white"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 12px;
            padding: 1.25rem;
            transition: border-color 0.15s;
        }}
        
        .action-card:hover {{
            border-color: {COLORS["brand_primary"]};
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        }}
        
        /* Action Card specific hover effect */
        .action-card-hover:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        }}

        /* Dashboard Header */
        .dashboard-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 1.5rem;
        }}
        
        .dashboard-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: {COLORS["text_primary"]};
        }}
        
        /* ========== BOUTIQUE PREMIUM UTILITIES ========== */
        
        /* Rounded Corners - Premium Scale */
        .rounded-xl {{ border-radius: 0.75rem; }}
        .rounded-2xl {{ border-radius: 1rem; }}
        .rounded-3xl {{ border-radius: 2.5rem; }}  /* Premium boutique */
        
        /* Glassmorphism Effects */
        .glass {{
            background: rgba(255, 255, 255, 0.4);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.6);
        }}
        
        .glass-dark {{
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        /* Asymmetric Grid Utilities */
        .grid-asymmetric-3-2 {{
            display: grid;
            grid-template-columns: 3fr 2fr;
            gap: 1.5rem;
        }}
        
        .grid-asymmetric-2-3 {{
            display: grid;
            grid-template-columns: 2fr 3fr;
            gap: 1.5rem;
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        @keyframes slideInFromBottom {{
            from {{ 
                opacity: 0;
                transform: translateY(1rem);
            }}
            to {{ 
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .animate-in {{
            animation: fadeIn 0.7s ease-out;
        }}
        
        .slide-in {{
            animation: slideInFromBottom 0.7s ease-out;
        }}
        
        .animate-pulse {{
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }}
        
        /* Premium Card Variants */
        .card-premium {{
            background: {COLORS["bg_white"]};
            border-radius: 2.5rem;
            border: 1px solid {COLORS["border"]};
            padding: 2rem;
            box-shadow: {COLORS["card_shadow"]};
            transition: all 0.3s ease;
        }}
        
        .card-premium:hover {{
            box-shadow: {COLORS["card_shadow_lg"]};
            transform: translateY(-2px);
        }}
        
        .card-dark {{
            background: {COLORS["slate_900"]};
            color: white;
            border-radius: 2.5rem;
            padding: 2rem;
            box-shadow: {COLORS["card_shadow_xl"]};
            position: relative;
            overflow: hidden;
        }}
        
        .card-glass {{
            background: rgba(255, 255, 255, 0.4);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 2.5rem;
            border: 1px solid rgba(255, 255, 255, 0.6);
            padding: 2.5rem;
            box-shadow: {COLORS["card_shadow_xl"]};
        }}
        
        /* Gradient Backgrounds */
        .gradient-mesh {{
            background: linear-gradient(135deg, {COLORS["indigo_light"]} 0%, {COLORS["rose_light"]} 100%);
            filter: blur(60px);
            opacity: 0.5;
        }}
        
        /* Badge Variants - Boutique */
        .badge-urgent {{
            background: {COLORS["slate_900"]};
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        
        .badge-growth {{
            background: {COLORS["emerald_light"]};
            color: {COLORS["emerald_accent"]};
            padding: 0.25rem 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        
        .badge-efficiency {{
            background: {COLORS["indigo_light"]};
            color: {COLORS["indigo_primary"]};
            padding: 0.25rem 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        
        /* Sidebar Navigation Styles */
        .nav-sidebar {{
            position: fixed;
            left: 0;
            top: 4rem;
            bottom: 0;
            width: 6rem;
            background: {COLORS["bg_white"]};
            border-right: 1px solid {COLORS["border"]};
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem 0;
            gap: 2rem;
            z-index: 50;
        }}
        
        .nav-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem;
            border-radius: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            color: {COLORS["text_tertiary"]};
        }}
        
        .nav-item:hover {{
            background: {COLORS["slate_50"]};
            color: {COLORS["text_secondary"]};
        }}
        
        .nav-item.active {{
            background: {COLORS["indigo_light"]};
            color: {COLORS["indigo_primary"]};
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
        }}
        
        .nav-label {{
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        
        /* Mobile Bottom Nav */
        @media (max-width: 768px) {{
            .nav-sidebar {{
                top: auto;
                bottom: 0;
                left: 0;
                right: 0;
                width: 100%;
                height: 4rem;
                flex-direction: row;
                justify-content: space-around;
                padding: 0 1rem;
                border-right: none;
                border-top: 1px solid {COLORS["border"]};
                backdrop-filter: blur(10px);
                background: rgba(255, 255, 255, 0.8);
            }}
            
            .grid-asymmetric-3-2,
            .grid-asymmetric-2-3 {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)
