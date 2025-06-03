import streamlit as st
import pandas as pd

st.set_page_config(page_title="Risk Assessment Builder", layout="wide")

st.title("Risk Assessment Builder (MVP)")

uploaded = st.file_uploader("Upload your risk template (.xlsx)", type=["xlsx"])

if uploaded:
    df = pd.read_excel(uploaded, sheet_name="Assessment")
    st.dataframe(df, use_container_width=True)
    
    if st.button("Download filtered High risks"):
        high = df[df["Risk Score"] >= 40]
        st.download_button("Download CSV", data=high.to_csv(index=False), file_name="high_risks.csv")
