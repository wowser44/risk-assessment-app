import pandas as pd
import streamlit as st
from pathlib import Path
import io

# ---- Load default template ----
TEMPLATE_PATH = Path(__file__).with_name("risk_template.xlsx")

if TEMPLATE_PATH.exists():
    default_df = pd.read_excel(TEMPLATE_PATH, sheet_name="Assessment")
else:
    default_df = pd.DataFrame()       # empty fallback

st.set_page_config(page_title="Risk Assessment Builder", layout="wide")

st.title("Risk Assessment Builder (MVP)")

uploaded = st.file_uploader("Upload your risk template (.xlsx)", type=["xlsx"])

if uploaded is not None:
    df = pd.read_excel(uploaded, sheet_name="Assessment")
else:
    st.info("No file uploaded – using blank template")
    df = default_df.copy()
    st.dataframe(df, use_container_width=True)

if "Risk Score" in df.columns and st.button("Download filtered High risks"):
    high = df[df["Risk Score"] >= 40]
    st.download_button(
        "Download CSV",
        data=high.to_csv(index=False),
        file_name="high_risks.csv"
    )
