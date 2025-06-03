import pkgutil
import io
import pandas as pd
import streamlit as st
from tempfile import NamedTemporaryFile

# ---- Load default template ----
DEFAULT_XLS = pkgutil.get_data(__name__, "risk_template.xlsx")
if DEFAULT_XLS is not None:
    default_df = pd.read_excel(io.BytesIO(DEFAULT_XLS), sheet_name="Assessment")
else:
    default_df = pd.DataFrame()

st.set_page_config(page_title="Risk Assessment Builder", layout="wide")

st.title("Risk Assessment Builder (MVP)")

uploaded = st.file_uploader("Upload your risk template (.xlsx)", type=["xlsx"])

if uploaded is not None:
    df = pd.read_excel(uploaded, sheet_name="Assessment")
else:
    st.info("No file uploaded – using blank template")
    df = default_df.copy()
    st.dataframe(df, use_container_width=True)
    
    if st.button("Download filtered High risks"):
        high = df[df["Risk Score"] >= 40]
        st.download_button("Download CSV", data=high.to_csv(index=False), file_name="high_risks.csv")
