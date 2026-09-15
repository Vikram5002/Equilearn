"""Month 3 MVP deliverable: skill-gap dashboard.

Run with: streamlit run src/dashboard/app.py
"""

from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
STUDENTS = ROOT / "data" / "raw" / "students" / "students.csv"
GAPS = ROOT / "data" / "processed" / "student_skill_gaps.csv"
MARKET_DEMAND = ROOT / "data" / "processed" / "market_skill_demand.csv"
MODEL = ROOT / "data" / "processed" / "placement_model.joblib"

st.set_page_config(page_title="SkillBridge Analytics", layout="wide")


@st.cache_data
def load_data():
    students = pd.read_csv(STUDENTS)
    gaps = pd.read_csv(GAPS)
    market = pd.read_csv(MARKET_DEMAND)
    return students, gaps, market


@st.cache_resource
def load_model():
    if not MODEL.exists():
        return None
    return joblib.load(MODEL)


def predict_placement(bundle, student_row, gap_row):
    features = pd.DataFrame([{
        "cgpa": student_row["cgpa"],
        "projects_count": student_row["projects_count"],
        "certifications_count": student_row["certifications_count"],
        "internships_count": student_row["internships_count"],
        "skill_count": gap_row["skill_count"],
        "market_alignment_score": gap_row["market_alignment_score"],
    }])[bundle["features"]]
    scaled = bundle["scaler"].transform(features)
    return bundle["model"].predict_proba(scaled)[0, 1]


def main():
    st.title("SkillBridge Analytics — Placement & Employability Prediction")
    st.caption(
        "MVP demo running on a static/synthetic job-postings dataset. "
        "See ARCHITECTURE.md for the production data-source plan."
    )

    students, gaps, market = load_data()
    bundle = load_model()

    student_id = st.sidebar.selectbox("Student", students["student_id"])
    student = students[students["student_id"] == student_id].iloc[0]
    gap = gaps[gaps["student_id"] == student_id].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CGPA", f"{student['cgpa']:.2f}")
    col2.metric("Projects", int(student["projects_count"]))
    col3.metric("Certifications", int(student["certifications_count"]))
    col4.metric("Internships", int(student["internships_count"]))

    if bundle is not None:
        prob = predict_placement(bundle, student, gap)
        st.subheader("Placement Probability")
        st.progress(min(max(prob, 0.0), 1.0))
        st.metric("Predicted probability of placement", f"{prob:.1%}")
    else:
        st.warning("Train a model first: `python -m src.models.train_classifier`")

    st.subheader("Skill Gap Analysis")
    matched = [s for s in str(gap["matched_skills"]).split(";") if s]
    missing = [s for s in str(gap["missing_skills_ranked"]).split(";") if s]

    left, right = st.columns(2)
    with left:
        st.markdown(f"**Skills you have that the market wants** ({len(matched)})")
        st.write(", ".join(matched) if matched else "None matched yet")
    with right:
        st.markdown(f"**Top recommended skills to learn** (ranked by market demand)")
        for skill in missing[:10]:
            row = market[market["skill"] == skill]
            pct = row["pct_postings"].iloc[0] if not row.empty else 0
            st.write(f"- **{skill}** — in {pct:.0%} of job postings")

    st.subheader("Find Real Postings for a Missing Skill")
    try:
        from src.features.index_to_elasticsearch import search_by_skill

        skill_choice = st.selectbox("Search postings asking for:", missing[:10] if missing else ["-"])
        if missing and st.button("Search"):
            hits = search_by_skill(skill_choice)
            if hits:
                for hit in hits:
                    st.write(f"- **{hit['title']}** @ {hit['company']}")
            else:
                st.info("No postings found (is Elasticsearch running and indexed?)")
    except Exception:
        st.caption(
            "Skill search unavailable (Elasticsearch not running). "
            "See docs/STRETCH_GOALS.md step 4."
        )

    st.subheader("Overall Market Skill Demand")
    top_market = market.head(20)
    fig = px.bar(
        top_market, x="pct_postings", y="skill", orientation="h",
        labels={"pct_postings": "% of job postings", "skill": ""},
        title="Top 20 in-demand skills across current postings",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
