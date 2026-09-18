"""Month 3 MVP deliverable: skill-gap dashboard.

Run with: streamlit run src/dashboard/app.py
"""

from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
JOB_POSTINGS = ROOT / "data" / "raw" / "job_postings" / "job_postings.csv"
STUDENTS = ROOT / "data" / "raw" / "students" / "students.csv"
GAPS = ROOT / "data" / "processed" / "student_skill_gaps.csv"
MARKET_DEMAND = ROOT / "data" / "processed" / "market_skill_demand.csv"
MODEL = ROOT / "data" / "processed" / "placement_model.joblib"

st.set_page_config(page_title="SkillBridge Analytics", layout="wide")

JOB_POSTING_REQUIRED_COLS = ["title", "company", "description"]
STUDENT_REQUIRED_COLS = ["cgpa", "projects_count", "certifications_count", "internships_count", "skills"]


def _validate_and_prepare(df: pd.DataFrame, required_cols: list, id_col: str, id_prefix: str) -> tuple:
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        return None, f"Missing required column(s): {', '.join(missing_cols)}"
    if id_col not in df.columns:
        df = df.copy()
        df[id_col] = [f"{id_prefix}{i:04d}" for i in range(len(df))]
    return df, None


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

    with st.sidebar.expander("Upload your own data", expanded=False):
        st.caption(
            "Job postings CSV needs columns: title, company, description "
            "(posting_id optional, auto-generated if missing)."
        )
        jd_file = st.file_uploader("Job postings (JD) CSV", type="csv", key="jd_upload")

        st.caption(
            "Students CSV needs: cgpa, projects_count, certifications_count, "
            "internships_count, skills (semicolon-separated, e.g. 'Python;SQL;Teamwork'). "
            "student_id optional, auto-generated. Leave out 'placed' for students "
            "still awaiting placement — retraining is skipped without it."
        )
        student_file = st.file_uploader("Students CSV", type="csv", key="student_upload")

        if st.button("Process uploaded data", disabled=not (jd_file or student_file)):
            errors = []
            if jd_file:
                jd_df, err = _validate_and_prepare(
                    pd.read_csv(jd_file), JOB_POSTING_REQUIRED_COLS, "posting_id", "JP"
                )
                if err:
                    errors.append(f"Job postings: {err}")
                else:
                    JOB_POSTINGS.parent.mkdir(parents=True, exist_ok=True)
                    jd_df.to_csv(JOB_POSTINGS, index=False)

            if student_file:
                st_df, err = _validate_and_prepare(
                    pd.read_csv(student_file), STUDENT_REQUIRED_COLS, "student_id", "S"
                )
                if err:
                    errors.append(f"Students: {err}")
                else:
                    STUDENTS.parent.mkdir(parents=True, exist_ok=True)
                    st_df.to_csv(STUDENTS, index=False)

            if errors:
                for e in errors:
                    st.error(e)
            else:
                with st.spinner("Running skill extraction + feature store..."):
                    from src.nlp import skill_extractor
                    from src.features import build_feature_store

                    skill_extractor.main()
                    build_feature_store.main()

                retrain = student_file and "placed" in pd.read_csv(STUDENTS).columns
                if retrain:
                    with st.spinner("Retraining classifier (placed column found)..."):
                        from src.models import train_classifier
                        train_classifier.main()
                    load_model.clear()

                load_data.clear()
                st.success(
                    "Processed. "
                    + ("Model retrained. " if retrain else "Using existing model for predictions. ")
                    + "Reloading..."
                )
                st.rerun()

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
