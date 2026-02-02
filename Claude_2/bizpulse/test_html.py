import streamlit as st

# Test if HTML rendering works
st.set_page_config(page_title="HTML Test", layout="wide")

st.markdown("# HTML Rendering Test")

# Test 1: Simple HTML
st.markdown("""
<div style="background: red; padding: 20px; color: white;">
    Simple HTML Test
</div>
""", unsafe_allow_html=True)

# Test 2: HTML with f-string
test_var = "Hello World"
st.markdown(f"""
<div style="background: blue; padding: 20px; color: white;">
    F-String Test: {test_var}
</div>
""", unsafe_allow_html=True)

# Test 3: Complex HTML like in the app
COLORS = {"slate_900": "#0F172A", "indigo_primary": "#4F46E5"}
narrative = "Your business is thriving."
narrative_accent = "thriving"

st.markdown(f"""
<div style="background: green; padding: 20px; color: white;">
    <h2>{narrative.split(narrative_accent)[0]}<span style="color: yellow;">{narrative_accent}</span></h2>
</div>
""", unsafe_allow_html=True)

st.success("If you see colored boxes above, HTML rendering is working!")
