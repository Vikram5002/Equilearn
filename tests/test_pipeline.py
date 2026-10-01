import numpy as np
import pandas as pd
import pytest
import spacy

from src.dashboard.core import (
    STUDENT_REQUIRED_COLS, category_coverage, market_alignment, risk_tier, split_skills,
    validate_and_prepare,
)
from src.features.build_feature_store import build_market_skill_demand, build_student_skill_gaps
from src.models.train_classifier import train
from src.nlp.skill_extractor import build_matcher, extract_skills


@pytest.fixture(scope="module")
def nlp_and_matchers():
    nlp = spacy.blank("en")
    return nlp, build_matcher(nlp)


def test_overlapping_matches_keep_longest_span(nlp_and_matchers):
    nlp, m = nlp_and_matchers
    skills = extract_skills("Holds the AWS Certified Solutions Architect badge.", nlp, m)
    assert skills == ["AWS Certified Solutions Architect"]


def test_extractor_handles_missing_text(nlp_and_matchers):
    nlp, m = nlp_and_matchers
    assert extract_skills(float("nan"), nlp, m) == []
    assert extract_skills("   ", nlp, m) == []


def test_extractor_returns_canonical_casing(nlp_and_matchers):
    nlp, m = nlp_and_matchers
    assert extract_skills("strong PYTHON and postgresql", nlp, m) == ["Python", "PostgreSQL"]


def test_market_demand_empty_input_has_columns():
    out = build_market_skill_demand(pd.DataFrame({"extracted_skills": [None, ""]}))
    assert list(out.columns) == ["skill", "posting_count", "pct_postings"]
    assert out.empty


def test_market_demand_percentages():
    jobs = pd.DataFrame({"extracted_skills": ["Python;SQL", "Python", None, "SQL;Docker"]})
    out = build_market_skill_demand(jobs).set_index("skill")
    assert out.loc["Python", "posting_count"] == 2
    assert out.loc["Python", "pct_postings"] == pytest.approx(0.5)


def test_student_gaps_tolerate_missing_skills():
    market = pd.DataFrame({"skill": ["Python", "SQL"], "posting_count": [3, 1], "pct_postings": [0.75, 0.25]})
    students = pd.DataFrame({"student_id": ["a", "b"], "skills": ["Python; Git", np.nan]})
    gaps = build_student_skill_gaps(students, market).set_index("student_id")
    assert gaps.loc["a", "matched_skills"] == "Python"
    assert gaps.loc["a", "market_alignment_score"] == pytest.approx(0.75)
    assert gaps.loc["b", "skill_count"] == 0
    assert gaps.loc["b", "missing_skills_ranked"] == "Python;SQL"


def test_split_skills_drops_nan_and_blanks():
    assert split_skills(np.nan) == []
    assert split_skills("Python; ;SQL;nan") == ["Python", "SQL"]


def test_market_alignment_matches_feature_store():
    market = pd.DataFrame({"skill": ["Python", "SQL"], "pct_postings": [0.75, 0.25]})
    assert market_alignment(["SQL"], market) == pytest.approx(0.25)
    assert market_alignment([], market.iloc[0:0]) == 0.0


def test_category_coverage_bounds():
    market = pd.DataFrame({"skill": ["Python", "Java", "Docker"], "pct_postings": [0.5, 0.5, 0.2]})
    cov = category_coverage(["Python"], market).set_index("category")["coverage"]
    assert cov["Programming Languages"] == pytest.approx(0.5)
    assert cov["Big Data & Cloud"] == 0
    assert cov.between(0, 1).all()


def test_validate_rejects_non_numeric_and_duplicates():
    good = pd.DataFrame({c: [1, 2] for c in STUDENT_REQUIRED_COLS[:-1]} | {"skills": ["Python", None]})
    df, err = validate_and_prepare(good, STUDENT_REQUIRED_COLS, "student_id", "S")
    assert err is None and list(df["student_id"]) == ["S0000", "S0001"] and df["skills"][1] == ""

    bad = good.assign(cgpa=["8.1", "abc"])
    assert "cgpa" in validate_and_prepare(bad, STUDENT_REQUIRED_COLS, "student_id", "S")[1]

    dup = good.assign(student_id=["x", "x"])
    assert "duplicate" in validate_and_prepare(dup, STUDENT_REQUIRED_COLS, "student_id", "S")[1]

    assert "Missing" in validate_and_prepare(good.drop(columns="skills"), STUDENT_REQUIRED_COLS, "student_id", "S")[1]


def test_risk_tiers():
    assert risk_tier(0.9) == "On track"
    assert risk_tier(0.5) == "Needs a push"
    assert risk_tier(0.1) == "At risk"


def test_train_refuses_single_class():
    df = pd.DataFrame({
        "cgpa": [7.0] * 10, "projects_count": [1] * 10, "certifications_count": [0] * 10,
        "internships_count": [0] * 10, "skill_count": [3] * 10, "market_alignment_score": [0.1] * 10,
        "placed": [1] * 10,
    })
    with pytest.raises(ValueError, match="placed"):
        train(df)
