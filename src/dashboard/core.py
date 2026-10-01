"""Pure (Streamlit-free) logic behind the dashboard, kept separate so it can be
unit-tested without spinning up a Streamlit runtime.
"""

import pandas as pd

from src.nlp.skills_taxonomy import SKILLS_TAXONOMY, skill_to_category

JOB_POSTING_REQUIRED_COLS = ["title", "company", "description"]
STUDENT_REQUIRED_COLS = ["cgpa", "projects_count", "certifications_count", "internships_count", "skills"]
STUDENT_NUMERIC_COLS = ["cgpa", "projects_count", "certifications_count", "internships_count"]


def split_skills(value) -> list[str]:
    """';'-joined skills cell -> list. NaN / empty / 'nan' -> []."""
    if not isinstance(value, str):
        return []
    return [s.strip() for s in value.split(";") if s.strip() and s.strip().lower() != "nan"]


def validate_and_prepare(df: pd.DataFrame, required_cols: list, id_col: str, id_prefix: str):
    """Returns (df, None) on success or (None, error_message)."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        return None, f"Missing required column(s): {', '.join(missing_cols)}"
    if df.empty:
        return None, "File has no rows"

    for col in STUDENT_NUMERIC_COLS:
        if col in required_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            bad = int(df[col].isna().sum())
            if bad:
                return None, f"Column '{col}' has {bad} non-numeric/empty value(s)"
    if "skills" in required_cols:
        df["skills"] = df["skills"].fillna("").astype(str)
    if "description" in required_cols:
        df = df.dropna(subset=["description"])
        if df.empty:
            return None, "Every row has an empty description"

    if id_col not in df.columns:
        df[id_col] = [f"{id_prefix}{i:04d}" for i in range(len(df))]
    elif df[id_col].duplicated().any():
        return None, f"Column '{id_col}' has duplicate values"
    df[id_col] = df[id_col].astype(str)
    return df, None


def market_alignment(skills: list[str], market: pd.DataFrame) -> float:
    """Same formula as build_feature_store: share of total market demand the
    student's skills cover."""
    total = market["pct_postings"].sum()
    if not total:
        return 0.0
    have = set(skills)
    return float(market.loc[market["skill"].isin(have), "pct_postings"].sum() / total)


def feature_frame(students: pd.DataFrame, gaps: pd.DataFrame) -> pd.DataFrame:
    return students.merge(
        gaps[["student_id", "skill_count", "market_alignment_score"]], on="student_id", how="inner"
    )


def predict_proba(bundle, features: pd.DataFrame):
    X = features[bundle["features"]]
    return bundle["model"].predict_proba(bundle["scaler"].transform(X))[:, 1]


def category_coverage(skills: list[str], market: pd.DataFrame) -> pd.DataFrame:
    """Per taxonomy category: share of that category's market demand the
    student covers. Drives the radar chart."""
    cat_of = skill_to_category()
    m = market.assign(category=market["skill"].map(cat_of).fillna("Other"))
    have = set(skills)
    rows = []
    for cat in SKILLS_TAXONOMY:
        sub = m[m["category"] == cat]
        total = sub["pct_postings"].sum()
        covered = sub.loc[sub["skill"].isin(have), "pct_postings"].sum()
        rows.append({"category": cat, "coverage": float(covered / total) if total else 0.0})
    return pd.DataFrame(rows)


def risk_tier(prob: float) -> str:
    if prob >= 0.7:
        return "On track"
    if prob >= 0.4:
        return "Needs a push"
    return "At risk"
