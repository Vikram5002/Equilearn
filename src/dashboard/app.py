"""SkillBridge Analytics dashboard.

Run with: streamlit run src/dashboard/app.py
"""

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # `streamlit run` doesn't put the repo root on sys.path
    sys.path.insert(0, str(ROOT))

from src.dashboard.core import (  # noqa: E402
    JOB_POSTING_REQUIRED_COLS, STUDENT_REQUIRED_COLS, category_coverage, feature_frame,
    market_alignment, predict_proba, risk_tier, split_skills, validate_and_prepare,
)
from src.nlp.skills_taxonomy import skill_to_category  # noqa: E402

JOB_POSTINGS = ROOT / "data" / "raw" / "job_postings" / "job_postings.csv"
STUDENTS = ROOT / "data" / "raw" / "students" / "students.csv"
JOB_SKILLS = ROOT / "data" / "processed" / "job_postings_skills.csv"
GAPS = ROOT / "data" / "processed" / "student_skill_gaps.csv"
MARKET_DEMAND = ROOT / "data" / "processed" / "market_skill_demand.csv"
MODEL = ROOT / "data" / "processed" / "placement_model.joblib"
METRICS = ROOT / "data" / "processed" / "model_metrics.json"

TIER_COLORS = {"On track": "#2DD4A4", "Needs a push": "#FFA94D", "At risk": "#FF5C7A"}
TIER_BADGE = {"On track": "green", "Needs a push": "orange", "At risk": "red"}

st.set_page_config(
    page_title="SkillBridge Analytics", page_icon=":material/hub:", layout="wide",
)


# --------------------------------------------------------------------------- data

def pipeline_ready() -> bool:
    return all(p.exists() for p in (STUDENTS, GAPS, MARKET_DEMAND))


@st.cache_data(show_spinner=False)
def load_data():
    students = pd.read_csv(STUDENTS, dtype={"student_id": str})
    gaps = pd.read_csv(GAPS, dtype={"student_id": str})
    market = pd.read_csv(MARKET_DEMAND)
    return students, gaps, market


@st.cache_data(show_spinner=False)
def load_postings():
    if not JOB_SKILLS.exists():
        return pd.DataFrame(columns=["title", "company", "extracted_skills"])
    return pd.read_csv(JOB_SKILLS, usecols=lambda c: c in {"posting_id", "title", "company", "extracted_skills"})


@st.cache_resource(show_spinner=False)
def load_model():
    if not MODEL.exists():
        return None
    try:
        bundle = joblib.load(MODEL)
        # smoke-test: a model pickled under a different scikit-learn/xgboost
        # version (e.g. trained inside the Airflow container) can load fine
        # and then fail on predict
        probe = pd.DataFrame([[0.0] * len(bundle["features"])], columns=bundle["features"])
        predict_proba(bundle, probe)
        return bundle
    except Exception as e:
        st.warning(
            f"Saved model couldn't be used ({type(e).__name__}) — probably trained with a different "
            "library version. Re-train it from **Data Studio → Re-run full pipeline**.",
            icon=":material/warning:",
        )
        return None


@st.cache_data(show_spinner=False)
def load_metrics():
    return json.loads(METRICS.read_text()) if METRICS.exists() else None


@st.cache_data(show_spinner=False)
def cohort_predictions(_bundle, students, gaps):
    df = feature_frame(students, gaps)
    df["probability"] = predict_proba(_bundle, df) if _bundle is not None else float("nan")
    df["tier"] = df["probability"].map(lambda p: risk_tier(p) if pd.notna(p) else "Unknown")
    return df


@st.cache_data(show_spinner=False)
def cohort_coverage(students, market):
    return (
        pd.concat([category_coverage(split_skills(x), market) for x in students["skills"]])
        .groupby("category", sort=False)["coverage"].mean().reset_index()
    )


def clear_caches():
    load_data.clear()
    load_postings.clear()
    load_model.clear()
    load_metrics.clear()
    cohort_predictions.clear()
    cohort_coverage.clear()


def run_pipeline(steps):
    """steps: list of (label, callable). Shows live progress in an st.status."""
    with st.status("Running pipeline…", expanded=True) as status:
        for label, fn in steps:
            st.write(f":material/progress_activity: {label}")
            try:
                fn()
            except Exception as e:  # surface, don't crash the app
                status.update(label=f"Failed at: {label}", state="error")
                st.exception(e)
                return False
        status.update(label="Pipeline complete", state="complete", expanded=False)
    clear_caches()
    return True


def full_pipeline_steps(ingest=None, retrain=True):
    from src.features import build_feature_store
    from src.models import train_classifier
    from src.nlp import skill_extractor

    steps = []
    if ingest:
        steps.append(ingest)
    steps += [
        ("NLP skill extraction", skill_extractor.main),
        ("Building feature store", build_feature_store.main),
    ]
    if retrain:
        steps.append(("Training classifier (LogReg vs XGBoost)", train_classifier.main))
    return steps


# ------------------------------------------------------------------------ charts

def _style(fig, height=None):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=36, b=8), height=height,
        legend=dict(orientation="h", y=-0.15),
    )
    return fig


def gauge(prob: float, tier: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob * 100,
        number={"suffix": "%", "font": {"size": 52}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "rgba(0,0,0,0)"},
            "bar": {"color": TIER_COLORS[tier], "thickness": 0.28},
            "bgcolor": "rgba(127,127,127,0.12)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "rgba(255,92,122,0.12)"},
                {"range": [40, 70], "color": "rgba(255,169,77,0.12)"},
                {"range": [70, 100], "color": "rgba(45,212,164,0.12)"},
            ],
        },
    ))
    return _style(fig, height=250)


def radar(student_cov: pd.DataFrame, cohort_cov: pd.DataFrame):
    cats = student_cov["category"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=(cohort_cov["coverage"] * 100).tolist() + [cohort_cov["coverage"].iloc[0] * 100],
        theta=cats + cats[:1], name="Cohort average", line=dict(color="#94A3B8", dash="dot"),
    ))
    fig.add_trace(go.Scatterpolar(
        r=(student_cov["coverage"] * 100).tolist() + [student_cov["coverage"].iloc[0] * 100],
        theta=cats + cats[:1], name="This student", fill="toself",
        line=dict(color="#7C5CFF", width=3), fillcolor="rgba(124,92,255,0.25)",
    ))
    fig.update_layout(polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(range=[0, 100], ticksuffix="%", gridcolor="rgba(127,127,127,0.25)"),
        angularaxis=dict(gridcolor="rgba(127,127,127,0.25)"),
    ))
    return _style(fig, height=380)


# ------------------------------------------------------------------------- pages

def page_onboarding():
    st.title(":material/hub: SkillBridge Analytics")
    st.markdown("##### Placement & employability intelligence, powered by NLP over real job postings.")
    with st.container(border=True):
        st.subheader(":material/rocket_launch: No pipeline outputs yet")
        st.write(
            "Generate a demo dataset and run the full pipeline (ingest → NLP → feature store → "
            "classifier) right here, or upload your own CSVs from **Data Studio**."
        )
        if st.button("Generate demo data & run pipeline", type="primary", icon=":material/bolt:"):
            from src.ingestion import generate_synthetic_data
            if run_pipeline(full_pipeline_steps(("Generating synthetic data", generate_synthetic_data.main))):
                st.rerun()


def page_student():
    students, gaps, market = load_data()
    bundle = load_model()
    cohort = cohort_predictions(bundle, students, gaps)
    if cohort.empty:
        st.warning("No students match the skill-gap table. Re-run the pipeline from Data Studio.")
        return

    ids = cohort["student_id"].tolist()
    with st.sidebar:
        st.markdown("**Select a student**")
        student_id = st.selectbox("Student", ids, label_visibility="collapsed", key="student_id")
    s = cohort[cohort["student_id"] == student_id].iloc[0]
    gap = gaps[gaps["student_id"] == student_id].iloc[0]
    skills = split_skills(s["skills"])
    matched = split_skills(gap["matched_skills"])
    missing = split_skills(gap["missing_skills_ranked"])
    prob = s["probability"]
    tier = s["tier"]

    head_l, head_r = st.columns([3, 1], vertical_alignment="bottom")
    with head_l:
        st.title(f"Student {student_id}")
        st.caption("Placement outlook, skill gaps and the fastest path to closing them.")
    with head_r:
        if bundle is not None:
            st.badge(tier, color=TIER_BADGE[tier], icon=":material/flag:")

    med = cohort[["cgpa", "projects_count", "certifications_count", "internships_count",
                  "market_alignment_score"]].median()
    with st.container(horizontal=True):
        st.metric("CGPA", f"{s['cgpa']:.2f}", f"{s['cgpa'] - med['cgpa']:+.2f} vs median", border=True)
        st.metric("Projects", int(s["projects_count"]),
                  f"{s['projects_count'] - med['projects_count']:+.0f} vs median", border=True)
        st.metric("Certifications", int(s["certifications_count"]),
                  f"{s['certifications_count'] - med['certifications_count']:+.0f} vs median", border=True)
        st.metric("Internships", int(s["internships_count"]),
                  f"{s['internships_count'] - med['internships_count']:+.0f} vs median", border=True)
        st.metric("Market alignment", f"{s['market_alignment_score']:.1%}",
                  f"{(s['market_alignment_score'] - med['market_alignment_score']) * 100:+.1f} pts", border=True)

    left, right = st.columns([2, 3])
    with left, st.container(border=True, height="stretch"):
        st.subheader(":material/speed: Placement probability")
        if bundle is None:
            st.warning("No trained model yet — train one from Data Studio.")
        else:
            st.plotly_chart(gauge(prob, tier), width="stretch", config={"displayModeBar": False})
            pct_rank = (cohort["probability"] < prob).mean()
            st.caption(f"Higher than **{pct_rank:.0%}** of the cohort.")
    with right, st.container(border=True, height="stretch"):
        st.subheader(":material/radar: Skill coverage vs market")
        cohort_cov = cohort_coverage(students, market)
        st.plotly_chart(radar(category_coverage(skills, market), cohort_cov),
                        width="stretch", config={"displayModeBar": False})

    tab_gap, tab_sim, tab_jobs = st.tabs([
        ":material/troubleshoot: Skill gaps", ":material/science: What-if simulator",
        ":material/work: Matching postings",
    ])

    demand = market.set_index("skill")["pct_postings"]
    with tab_gap:
        c1, c2 = st.columns(2)
        with c1, st.container(border=True):
            st.markdown(f"**:green[:material/check_circle:] Market skills you have** · {len(matched)}")
            if matched:
                with st.container(horizontal=True, gap="small"):
                    for m in matched:
                        st.badge(m, color="green")
            else:
                st.caption("None of this student's skills appear in current postings yet.")
            other = [x for x in skills if x not in matched]
            if other:
                st.caption("Not seen in postings: " + ", ".join(other))
        with c2, st.container(border=True):
            st.markdown("**:orange[:material/trending_up:] Top skills to learn next**")
            if missing:
                gap_df = pd.DataFrame({
                    "Skill": missing,
                    "Category": [skill_to_category().get(m, "Other") for m in missing],
                    "Demand": [float(demand.get(m, 0)) for m in missing],
                })
                st.dataframe(
                    gap_df, hide_index=True, width="stretch",
                    column_config={"Demand": st.column_config.ProgressColumn(
                        "% of postings", format="percent", min_value=0,
                        max_value=float(market["pct_postings"].max() or 1))},
                )
            else:
                st.success("No gaps — this student covers every in-demand skill.")

    with tab_sim:
        if bundle is None:
            st.info("Train a model to use the simulator.")
        else:
            sim_l, sim_r = st.columns([3, 2])
            with sim_l:
                cgpa = st.slider("CGPA", 0.0, 10.0, float(s["cgpa"]), 0.05, key=f"cg_{student_id}")
                a, b, c = st.columns(3)
                proj = a.number_input("Projects", 0, 20, int(s["projects_count"]), key=f"p_{student_id}")
                cert = b.number_input("Certifications", 0, 20, int(s["certifications_count"]), key=f"c_{student_id}")
                intern = c.number_input("Internships", 0, 10, int(s["internships_count"]), key=f"i_{student_id}")
                add = st.multiselect("Learn these skills", market["skill"].tolist(),
                                     default=missing[:2], key=f"add_{student_id}",
                                     placeholder="Pick skills to add…")
            new_skills = list(dict.fromkeys(skills + add))
            sim = pd.DataFrame([{
                "cgpa": cgpa, "projects_count": proj, "certifications_count": cert,
                "internships_count": intern, "skill_count": len(new_skills),
                "market_alignment_score": market_alignment(new_skills, market),
            }])
            new_prob = float(predict_proba(bundle, sim)[0])
            with sim_r, st.container(border=True):
                st.metric("Simulated probability", f"{new_prob:.1%}",
                          f"{(new_prob - prob) * 100:+.1f} pts", border=False)
                st.metric("Simulated market alignment", f"{sim['market_alignment_score'][0]:.1%}",
                          f"{(sim['market_alignment_score'][0] - s['market_alignment_score']) * 100:+.1f} pts")
                st.badge(risk_tier(new_prob), color=TIER_BADGE[risk_tier(new_prob)])

            st.markdown("**:material/bolt: Highest-impact single skill to learn**")
            base = sim.assign(skill_count=len(skills),
                              market_alignment_score=s["market_alignment_score"],
                              cgpa=s["cgpa"], projects_count=s["projects_count"],
                              certifications_count=s["certifications_count"],
                              internships_count=s["internships_count"])
            lever = []
            for sk in missing:
                trial = base.assign(skill_count=len(skills) + 1,
                                    market_alignment_score=market_alignment(skills + [sk], market))
                lever.append({"Skill": sk, "Gain": float(predict_proba(bundle, trial)[0]) - prob})
            if lever:
                lever_df = pd.DataFrame(lever).sort_values("Gain", ascending=False)
                fig = px.bar(lever_df, x="Gain", y="Skill", orientation="h",
                             color="Gain", color_continuous_scale=["#4CC9F0", "#7C5CFF"])
                fig.update_layout(yaxis={"categoryorder": "total ascending", "title": None},
                                  xaxis={"tickformat": "+.1%", "title": "Δ placement probability"},
                                  coloraxis_showscale=False)
                st.plotly_chart(_style(fig, 320), width="stretch", config={"displayModeBar": False})
                if lever_df["Gain"].max() <= 0:
                    st.info(
                        "The current model doesn't reward extra skills — on this dataset its skill "
                        "features carry little or negative weight (see **Model**). That usually means the "
                        "training data has no real skill records (e.g. skills imputed from specialisation); "
                        "retrain on data with real student skills before using this ranking for advice.",
                        icon=":material/info:",
                    )

    with tab_jobs:
        if not missing:
            st.caption("No missing skills to search for.")
        else:
            skill_choice = st.segmented_control("Postings asking for", missing[:6],
                                                default=missing[0], key=f"seg_{student_id}")
            if skill_choice:
                hits, source = search_postings(skill_choice)
                st.caption(f"Source: {source}")
                if hits.empty:
                    st.info("No postings found for this skill.")
                for _, h in hits.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{h['title']}**  \n:material/apartment: {h['company']}")


def search_postings(skill: str, size=6):
    """Elasticsearch first; falls back to the local extracted-postings table."""
    try:
        from src.features.index_to_elasticsearch import search_by_skill
        hits = search_by_skill(skill, size=size)
        if hits:
            return pd.DataFrame(hits), "Elasticsearch"
    except Exception:
        pass
    postings = load_postings()
    mask = postings["extracted_skills"].fillna("").map(lambda v: skill in split_skills(v))
    return postings[mask].head(size), "local feature store (Elasticsearch offline)"


def page_cohort():
    students, gaps, market = load_data()
    bundle = load_model()
    if bundle is None:
        st.warning("Train a model first (Data Studio).")
        return
    cohort = cohort_predictions(bundle, students, gaps)

    st.title(":material/groups: Cohort analytics")
    st.caption("Who needs help, how much, and with what — across every student.")
    counts = cohort["tier"].value_counts()
    with st.container(horizontal=True):
        st.metric("Students", len(cohort), border=True)
        st.metric("Avg. predicted placement", f"{cohort['probability'].mean():.1%}", border=True)
        if "placed" in cohort and cohort["placed"].notna().any():
            st.metric("Actual placement rate", f"{cohort['placed'].mean():.1%}", border=True)
        for t in TIER_COLORS:
            st.metric(t, int(counts.get(t, 0)), border=True)

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.subheader("Probability distribution")
        fig = px.histogram(cohort, x="probability", color="tier", nbins=25,
                           color_discrete_map=TIER_COLORS, labels={"probability": "Predicted probability"})
        fig.update_layout(bargap=0.05, xaxis_tickformat=".0%", yaxis_title="Students")
        st.plotly_chart(_style(fig, 360), width="stretch")
    with c2, st.container(border=True):
        st.subheader("Alignment vs outlook")
        fig = px.scatter(cohort, x="market_alignment_score", y="probability", color="tier",
                         size="skill_count", hover_name="student_id", color_discrete_map=TIER_COLORS,
                         labels={"market_alignment_score": "Market alignment", "probability": "Placement probability"})
        fig.update_layout(xaxis_tickformat=".0%", yaxis_tickformat=".0%")
        st.plotly_chart(_style(fig, 360), width="stretch")

    with st.container(border=True):
        st.subheader("Most common skill gaps across the cohort")
        gap_counts = pd.Series([g for v in gaps["missing_skills_ranked"] for g in split_skills(v)[:5]]).value_counts()
        gap_df = gap_counts.head(15).rename_axis("skill").reset_index(name="students")
        fig = px.bar(gap_df, x="students", y="skill", orientation="h", color="students",
                     color_continuous_scale=["#4CC9F0", "#7C5CFF"])
        fig.update_layout(yaxis={"categoryorder": "total ascending", "title": None}, coloraxis_showscale=False)
        st.plotly_chart(_style(fig, 420), width="stretch")

    with st.container(border=True):
        st.subheader(":material/priority_high: Intervention list")
        tiers = st.pills("Show tiers", list(TIER_COLORS), default=["At risk", "Needs a push"],
                         selection_mode="multi")
        view = cohort[cohort["tier"].isin(tiers or [])].sort_values("probability")
        view = view.merge(gaps[["student_id", "missing_skills_ranked"]], on="student_id")
        view["top_gaps"] = view["missing_skills_ranked"].map(lambda v: ", ".join(split_skills(v)[:3]))
        cols = ["student_id", "tier", "probability", "cgpa", "internships_count", "market_alignment_score", "top_gaps"]
        st.dataframe(
            view[cols], hide_index=True, width="stretch",
            column_config={
                "student_id": "Student", "tier": "Tier", "top_gaps": "Top gaps",
                "probability": st.column_config.ProgressColumn("Probability", format="percent", min_value=0, max_value=1),
                "market_alignment_score": st.column_config.NumberColumn("Alignment", format="percent"),
                "cgpa": st.column_config.NumberColumn("CGPA", format="%.2f"),
                "internships_count": "Internships",
            },
        )
        st.download_button("Download list (CSV)", view[cols].to_csv(index=False),
                           "intervention_list.csv", "text/csv", icon=":material/download:")


def page_market():
    _, _, market = load_data()
    postings = load_postings()
    st.title(":material/insights: Market pulse")
    st.caption("What employers are actually asking for, extracted from job-posting text with NLP.")
    role = st.text_input("Filter by job title", placeholder="e.g. Data, Engineer, Analyst — blank for all",
                         icon=":material/search:", key="role_filter").strip()
    if role and len(postings):
        from src.features.build_feature_store import build_market_skill_demand
        postings = postings[postings["title"].fillna("").str.contains(role, case=False, regex=False)]
        market = build_market_skill_demand(postings) if len(postings) else market.iloc[0:0]
        st.caption(f"Showing demand across **{len(postings):,}** postings whose title contains “{role}”.")
    if market.empty:
        st.warning("No skills found for this selection.")
        return

    cat_of = skill_to_category()
    market = market.assign(category=market["skill"].map(cat_of).fillna("Other"))
    with st.container(horizontal=True):
        st.metric("Job postings analysed", f"{len(postings):,}", border=True)
        st.metric("Distinct skills found", len(market), border=True)
        st.metric("#1 skill", market["skill"].iloc[0], f"{market['pct_postings'].iloc[0]:.0%} of postings", border=True)
        if "extracted_skills" in postings and len(postings):
            avg = postings["extracted_skills"].map(lambda v: len(split_skills(v))).mean()
            st.metric("Avg skills / posting", f"{avg:.1f}", border=True)

    c1, c2 = st.columns([3, 2])
    with c1, st.container(border=True):
        top_n = (st.slider("Top N skills", 5, min(40, len(market)), min(20, len(market)))
                 if len(market) > 5 else len(market))
        fig = px.bar(market.head(top_n), x="pct_postings", y="skill", orientation="h", color="category",
                     labels={"pct_postings": "% of job postings", "skill": ""})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_tickformat=".0%")
        st.plotly_chart(_style(fig, 28 * top_n + 120), width="stretch")
    with c2, st.container(border=True):
        st.subheader("Demand by category")
        fig = px.treemap(market, path=["category", "skill"], values="posting_count",
                         color="category")
        fig.update_traces(root_color="rgba(0,0,0,0)")
        st.plotly_chart(_style(fig, 520), width="stretch")

    with st.container(border=True):
        st.subheader("All extracted skills")
        st.dataframe(
            market, hide_index=True, width="stretch",
            column_config={
                "pct_postings": st.column_config.ProgressColumn(
                    "% of postings", format="percent", min_value=0, max_value=float(market["pct_postings"].max())),
                "posting_count": "Postings", "skill": "Skill", "category": "Category",
            },
        )


def page_model():
    metrics = load_metrics()
    st.title(":material/model_training: Model")
    st.caption("Logistic Regression and XGBoost are trained head-to-head; the higher held-out AUC wins.")
    if not metrics:
        st.warning("No trained model yet — train one from Data Studio.")
        return
    with st.container(horizontal=True):
        st.metric("Selected model", metrics["best_model"].replace("_", " ").title(), border=True)
        st.metric("ROC AUC", f"{metrics['auc']:.3f}", border=True)
        st.metric("Accuracy", f"{metrics['accuracy']:.1%}", border=True)

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.subheader("Model comparison")
        comp = pd.DataFrame(metrics["all_models"]).T.rename_axis("model").reset_index()
        comp = comp.melt("model", var_name="metric")
        fig = px.bar(comp, x="metric", y="value", color="model", barmode="group", text_auto=".3f")
        fig.update_layout(yaxis_range=[0, 1])
        st.plotly_chart(_style(fig, 360), width="stretch")
    with c2, st.container(border=True):
        st.subheader("Feature importance")
        imp = pd.DataFrame(metrics["feature_importances"].items(), columns=["feature", "weight"])
        imp["abs"] = imp["weight"].abs()
        fig = px.bar(imp.sort_values("abs"), x="weight", y="feature", orientation="h",
                     color="weight", color_continuous_scale=["#FF5C7A", "#94A3B8", "#2DD4A4"],
                     color_continuous_midpoint=0)
        fig.update_layout(coloraxis_showscale=False, yaxis_title=None)
        st.plotly_chart(_style(fig, 360), width="stretch")
        if metrics["best_model"] == "logistic_regression":
            st.caption("Logistic regression: signed coefficients on standardized features.")


def page_data():
    st.title(":material/database: Data Studio")
    st.caption("Bring your own job postings and students, or reset to demo data.")

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.subheader(":material/work: Job postings")
        st.caption("Required: `title`, `company`, `description`. `posting_id` optional.")
        jd_file = st.file_uploader("Job postings CSV", type="csv", key="jd_upload")
    with c2, st.container(border=True):
        st.subheader(":material/school: Students")
        st.caption(
            "Required: `cgpa`, `projects_count`, `certifications_count`, `internships_count`, "
            "`skills` (`;`-separated). Optional `student_id`, `placed` (0/1 — enables retraining)."
        )
        student_file = st.file_uploader("Students CSV", type="csv", key="student_upload")

    if st.button("Process uploaded data", type="primary", icon=":material/play_arrow:",
                 disabled=not (jd_file or student_file)):
        errors, jd_df, st_df = [], None, None
        for f, req, idc, pre, label in (
            (jd_file, JOB_POSTING_REQUIRED_COLS, "posting_id", "JP", "Job postings"),
            (student_file, STUDENT_REQUIRED_COLS, "student_id", "S", "Students"),
        ):
            if not f:
                continue
            try:
                df, err = validate_and_prepare(pd.read_csv(f), req, idc, pre)
            except Exception as e:
                df, err = None, f"Could not read CSV ({e})"
            if err:
                errors.append(f"{label}: {err}")
            elif label == "Students":
                st_df = df
            else:
                jd_df = df
        if not errors and st_df is None and not STUDENTS.exists():
            errors.append("Students: no existing student data — upload a students CSV too.")
        if not errors and jd_df is None and not JOB_POSTINGS.exists():
            errors.append("Job postings: no existing postings — upload a postings CSV too.")
        for e in errors:
            st.error(e, icon=":material/error:")
        if not errors:
            if jd_df is not None:
                JOB_POSTINGS.parent.mkdir(parents=True, exist_ok=True)
                jd_df.to_csv(JOB_POSTINGS, index=False)
            if st_df is not None:
                STUDENTS.parent.mkdir(parents=True, exist_ok=True)
                st_df.to_csv(STUDENTS, index=False)
            students_now = pd.read_csv(STUDENTS)
            retrain = "placed" in students_now.columns and students_now["placed"].notna().all()
            if run_pipeline(full_pipeline_steps(retrain=retrain)):
                st.toast("Data processed" + (" and model retrained" if retrain else ""), icon=":material/check:")
                st.rerun()

    st.divider()
    with st.container(border=True):
        st.subheader(":material/restart_alt: Rebuild")
        a, b = st.columns(2)
        if a.button("Re-run full pipeline on current data", icon=":material/sync:", width="stretch",
                    disabled=not (STUDENTS.exists() and JOB_POSTINGS.exists())):
            if run_pipeline(full_pipeline_steps()):
                st.rerun()
        if b.button("Reset to synthetic demo data", icon=":material/science:", width="stretch"):
            from src.ingestion import generate_synthetic_data
            if run_pipeline(full_pipeline_steps(("Generating synthetic data", generate_synthetic_data.main))):
                st.rerun()


# -------------------------------------------------------------------------- main

def main():
    with st.sidebar:
        st.markdown("### :material/hub: SkillBridge")
        st.caption("Placement & employability analytics")

    if not pipeline_ready():
        pages = [st.Page(page_onboarding, title="Get started", icon=":material/rocket_launch:", default=True),
                 st.Page(page_data, title="Data Studio", icon=":material/database:", url_path="data")]
    else:
        pages = {
            "Insights": [
                st.Page(page_student, title="Student 360", icon=":material/person_search:", default=True),
                st.Page(page_cohort, title="Cohort analytics", icon=":material/groups:", url_path="cohort"),
                st.Page(page_market, title="Market pulse", icon=":material/insights:", url_path="market"),
            ],
            "System": [
                st.Page(page_model, title="Model", icon=":material/model_training:", url_path="model"),
                st.Page(page_data, title="Data Studio", icon=":material/database:", url_path="data"),
            ],
        }
    st.navigation(pages, position="sidebar").run()


if __name__ == "__main__":
    main()
