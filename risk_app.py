# ---------- 1. Imports ----------
import json
from pathlib import Path
import pandas as pd
import streamlit as st

# ---------- 2. Page config (must be FIRST Streamlit call) ----------
st.set_page_config(page_title="Risk Assessment Builder", layout="wide")
st.title("Risk Assessment Builder (MVP)")

# ---------- 3. Load template workbook ----------
TEMPLATE_PATH = Path(__file__).with_name("risk_template.xlsx")
default_df = (
    pd.read_excel(TEMPLATE_PATH, sheet_name="Assessment")
    if TEMPLATE_PATH.exists()
    else pd.DataFrame()
)

# ---------- 4. Load question library ----------
QUESTION_FILE = Path(__file__).with_name("questions.json")
with open(QUESTION_FILE, "r") as f:
    QUESTIONS = json.load(f)

# ---------- 5. Ensure session keys ----------
if "q_idx" not in st.session_state:
    st.session_state.q_idx = 0
if "wizard_df" not in st.session_state:
    st.session_state.wizard_df = default_df.copy().iloc[0:0]

# ---------- 6. Helper: colour scores in DataFrame ----------
def colour_scores(val):
    try:
        v = float(val)
    except (TypeError, ValueError):
        return ""
    if v >= 40:
        return "background-color:#FFC7CE"
    if v >= 15:
        return "background-color:#FFEB9C"
    if v > 0:
        return "background-color:#C6EFCE"
    return ""

# ------------------------------------------------------------------
# SECTION A – GUIDED Q&A WIZARD
# ------------------------------------------------------------------
st.header("🧭 Guided risk entry")

# Role filter
roles = sorted({q["role"] for q in QUESTIONS if q["role"] != "All"})
chosen_role = st.selectbox("Role filter", ["All"] + roles)

visible_questions = [
    q for q in QUESTIONS
    if chosen_role == "All" or q["role"] == chosen_role
]

if st.session_state.q_idx >= len(visible_questions):
    st.session_state.q_idx = 0

# Navigation buttons
def go(step: int):
    st.session_state.q_idx = (
        st.session_state.q_idx + step
    ) % len(visible_questions)

col_prev, col_next = st.columns(2)
with col_prev:
    st.button("⬅️ Prev", on_click=go, args=(-1,))
with col_next:
    st.button("Next ➡️", on_click=go, args=(+1,))

# Current question
q = visible_questions[st.session_state.q_idx]
st.subheader(f"{q['role']} Q: {q['prompt']}")

# Input control
if q["type"] == "text":
    answer = st.text_area("Answer")
elif q["type"] == "select":
    friendly = list(q["options"].values())
    choice = st.selectbox("Choose one", friendly)
    answer = int({v: k for k, v in q["options"].items()}[choice])

# Save answer
if st.button("Save answer"):
    if st.session_state.wizard_df.empty:
        blank = default_df.iloc[0:0].copy()
        st.session_state.wizard_df = pd.concat(
            [st.session_state.wizard_df, blank], ignore_index=True
        )

    row_idx = 0
    st.session_state.wizard_df.at[row_idx, q["field"]] = answer

    # ----- Inherent score -----
    row = st.session_state.wizard_df.iloc[row_idx]
    ready = all(
        pd.notna(row[c])
        for c in ["Severity (S)", "Probability (P)", "Detectability (D)"]
    )
    if ready:
        st.session_state.wizard_df.at[row_idx, "Risk Score"] = (
            int(row["Severity (S)"])
            * int(row["Probability (P)"])
            * int(row["Detectability (D)"])
        )

    # ----- Residual score when Mitigation saved -----
    if q["field"] == "Mitigation" and ready:
        for col in ["S", "P", "D"]:
            st.session_state.wizard_df.at[row_idx, f"Residual {col}"] = row[f"{'Severity' if col=='S' else 'Probability' if col=='P' else 'Detectability'} ({col})"]
        st.session_state.wizard_df.at[row_idx, "Residual Score"] = (
            int(row["Residual S"])
            * int(row["Residual P"])
            * int(row["Residual D"])
        )
    st.success("Saved!")

# Display wizard DataFrame with colours
st.dataframe(
    st.session_state.wizard_df.style.applymap(
        colour_scores, subset=["Risk Score", "Residual Score"]
    ),
    use_container_width=True,
)

st.markdown("---")

# ------------------------------------------------------------------
# SECTION B – FILE UPLOAD (fallback / review)
# ------------------------------------------------------------------
st.header("📤 Upload an existing assessment")

uploaded = st.file_uploader(
    "Upload your risk template (.xlsx)", type=["xlsx"]
)

df = (
    pd.read_excel(uploaded, sheet_name="Assessment")
    if uploaded is not None
    else default_df.copy()
)

st.dataframe(
    df.style.applymap(colour_scores, subset=["Risk Score", "Residual Score"]),
    use_container_width=True,
)

# Download high risks
if "Risk Score" in df.columns and st.button("Download filtered High risks"):
    high = df[df["Risk Score"] >= 40]
    st.download_button(
        "Download CSV",
        data=high.to_csv(index=False),
        file_name="high_risks.csv",
    )
