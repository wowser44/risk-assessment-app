# ---------- 1. imports ----------
import json
from pathlib import Path
import io
import pandas as pd
import streamlit as st

# ---------- 2. load template workbook ----------
TEMPLATE_PATH = Path(__file__).with_name("risk_template.xlsx")
if TEMPLATE_PATH.exists():
    default_df = pd.read_excel(TEMPLATE_PATH, sheet_name="Assessment")
else:
    default_df = pd.DataFrame()          # empty fallback

# ---------- 3. load question library ----------
QUESTION_FILE = Path(__file__).with_name("questions.json")
with open(QUESTION_FILE, "r") as f:
    QUESTIONS = json.load(f)

# ---------- 4. page config ----------
st.set_page_config(page_title="Risk Assessment Builder", layout="wide")
st.title("Risk Assessment Builder (MVP)")

# ------------------------------------------------------------------
# SECTION A ─────────────────────────────────────────────────────────
# GUIDED Q&A “wizard”  (Sprint-1 feature)
# ------------------------------------------------------------------
st.header("🧭 Guided risk entry")

# initialise a blank session-state frame once per browser session
if "wizard_df" not in st.session_state:
    st.session_state.wizard_df = default_df.copy().iloc[0:0]

# pick which question we’re on
if "q_idx" not in st.session_state:
    st.session_state.q_idx = 0            # start at first question

def go(step: int):
    st.session_state.q_idx = (
        st.session_state.q_idx + step
    ) % len(QUESTIONS)                    # wrap around

col_prev, col_next = st.columns(2)
with col_prev:
    st.button("⬅️ Prev", on_click=go, args=(-1,))
with col_next:
    st.button("Next ➡️", on_click=go, args=(+1,))

q = QUESTIONS[st.session_state.q_idx]

# draw the right input control
if q["type"] == "text":
    answer = st.text_area("Answer")
elif q["type"] == "select":
    friendly = list(q["options"].values())
    choice = st.selectbox("Choose one", friendly)
    answer = int({v: k for k, v in q["options"].items()}[choice])  # numeric int

# save the answer into the hidden DataFrame
if st.button("Save answer"):
    if st.session_state.wizard_df.empty:                       # first row
        new_row = default_df.iloc[0:0].copy()
        st.session_state.wizard_df = pd.concat(
            [st.session_state.wizard_df, new_row], ignore_index=True
        )

    row_idx = 0
    target_col = q["field"]
    st.session_state.wizard_df.at[row_idx, target_col] = answer

    # auto-calculate risk score when S, P, D present
    row = st.session_state.wizard_df.iloc[row_idx]
    if all(pd.notna(row[c]) for c in ["Severity (S)", "Probability (P)", "Detectability (D)"]):
        st.session_state.wizard_df.at[row_idx, "Risk Score"] = (
            int(row["Severity (S)"]) *
            int(row["Probability (P)"]) *
            int(row["Detectability (D)"])
        )
    st.success("Saved!")

# show wizard DataFrame so far
st.dataframe(st.session_state.wizard_df, use_container_width=True)

st.markdown("---")                # visual divider between sections

# ------------------------------------------------------------------
# SECTION B ─────────────────────────────────────────────────────────
# FILE-UPLOAD fallback (your original feature)
# ------------------------------------------------------------------
st.header("📤 Upload an existing assessment")

uploaded = st.file_uploader("Upload your risk template (.xlsx)", type=["xlsx"])

if uploaded is not None:
    df = pd.read_excel(uploaded, sheet_name="Assessment")
else:
    st.info("No file uploaded – using blank template")
    df = default_df.copy()

st.dataframe(df, use_container_width=True)

# download red risks if present
if "Risk Score" in df.columns and st.button("Download filtered High risks"):
    high = df[df["Risk Score"] >= 40]
    st.download_button("Download CSV", data=high.to_csv(index=False), file_name="high_risks.csv")
