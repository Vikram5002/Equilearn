"""Month 2 feature store: joins extracted job-market skills with student
skill profiles.

Kept as flat Parquet/CSV tables rather than standing up Hive/Delta for this
pass - see ARCHITECTURE.md. The three tables produced here are exactly the
ones the dashboard and classifier read from, so this is the seam between the
NLP pipeline and everything downstream.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
JOB_SKILLS_IN = ROOT / "data" / "processed" / "job_postings_skills.csv"
STUDENTS_IN = ROOT / "data" / "raw" / "students" / "students.csv"

MARKET_DEMAND_OUT = ROOT / "data" / "processed" / "market_skill_demand.csv"
STUDENT_GAPS_OUT = ROOT / "data" / "processed" / "student_skill_gaps.csv"


def build_market_skill_demand(job_skills: pd.DataFrame) -> pd.DataFrame:
    n_postings = len(job_skills)
    skill_counts: dict[str, int] = {}
    for skills_str in job_skills["extracted_skills"].fillna(""):
        for skill in filter(None, skills_str.split(";")):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

    demand = pd.DataFrame(
        [{"skill": s, "posting_count": c, "pct_postings": c / n_postings}
         for s, c in skill_counts.items()]
    ).sort_values("posting_count", ascending=False).reset_index(drop=True)
    return demand


def build_student_skill_gaps(students: pd.DataFrame, market_demand: pd.DataFrame) -> pd.DataFrame:
    demand_lookup = market_demand.set_index("skill")["pct_postings"].to_dict()
    # only rank gaps against skills that actually appear in the market data,
    # so a niche taxonomy entry with zero postings doesn't drown out real gaps
    ranked_market_skills = market_demand["skill"].tolist()

    rows = []
    for _, student in students.iterrows():
        student_skills = set(filter(None, student["skills"].split(";")))
        missing = [s for s in ranked_market_skills if s not in student_skills]
        matched = [s for s in ranked_market_skills if s in student_skills]

        market_alignment = (
            sum(demand_lookup.get(s, 0) for s in matched)
            / sum(demand_lookup.values()) if demand_lookup else 0
        )

        rows.append({
            "student_id": student["student_id"],
            "matched_skills": ";".join(matched),
            "missing_skills_ranked": ";".join(missing[:10]),  # top 10 gaps by market demand
            "market_alignment_score": round(market_alignment, 4),
            "skill_count": len(student_skills),
        })
    return pd.DataFrame(rows)


def main():
    job_skills = pd.read_csv(JOB_SKILLS_IN)
    students = pd.read_csv(STUDENTS_IN)

    market_demand = build_market_skill_demand(job_skills)
    student_gaps = build_student_skill_gaps(students, market_demand)

    MARKET_DEMAND_OUT.parent.mkdir(parents=True, exist_ok=True)
    market_demand.to_csv(MARKET_DEMAND_OUT, index=False)
    student_gaps.to_csv(STUDENT_GAPS_OUT, index=False)

    print(f"Wrote {len(market_demand)} skills -> {MARKET_DEMAND_OUT}")
    print(f"Wrote {len(student_gaps)} student skill-gap rows -> {STUDENT_GAPS_OUT}")
    print("\nTop 10 in-demand skills:")
    print(market_demand.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
