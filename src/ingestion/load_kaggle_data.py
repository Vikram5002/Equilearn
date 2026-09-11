"""Loads the real Kaggle datasets in data/external/ and reshapes them into
the exact schema generate_synthetic_data.py produces, so nothing downstream
(skill_extractor.py, build_feature_store.py, train_classifier.py) needs to
change.

Datasets used (see docs/STRETCH_GOALS.md step 1):
- benroshan/factors-affecting-campus-placement -> data/external/Placement_Data_Full_Class.csv
  Real academic records + real placement outcomes. Has NO skills field, so
  skills are imputed from `specialisation`/`degree_t` via SPECIALISATION_SKILLS
  below - documented here, not silently faked as measured data.
- arshkon/linkedin-job-postings -> data/external/linkedin_job_postings/postings.csv
  Real job postings with free-text descriptions (3.4M rows - we sample a
  subset for a laptop-scale demo). No skills ground truth, so the extractor's
  precision/recall sanity check is skipped for this data (same as it already
  does when `true_skills` is absent).

Run: python -m src.ingestion.load_kaggle_data
Then re-run the pipeline (README Quickstart) as usual - it reads data/raw/,
which this script overwrites.
"""

import random
from pathlib import Path

import pandas as pd

from src.nlp.skills_taxonomy import flat_skill_list

ROOT = Path(__file__).resolve().parents[2]
CAMPUS_PLACEMENT_IN = ROOT / "data" / "external" / "Placement_Data_Full_Class.csv"
LINKEDIN_POSTINGS_IN = ROOT / "data" / "external" / "linkedin_job_postings" / "postings.csv"

JOB_POSTINGS_OUT = ROOT / "data" / "raw" / "job_postings" / "job_postings.csv"
STUDENTS_OUT = ROOT / "data" / "raw" / "students" / "students.csv"

N_POSTINGS_SAMPLE = 1500  # keep the demo laptop-scale; full file is 3.4M rows

random.seed(42)

# The campus-placement dataset has no skills field. We impute a plausible
# skill set per student from their specialisation, so the skill-gap dashboard
# still has something to show. This is clearly a proxy, not observed data -
# call this out in the report if you use it.
SPECIALISATION_SKILLS = {
    "Mkt&HR": ["Communication", "Leadership", "Teamwork", "Critical Thinking",
               "Time Management", "Problem Solving"],
    "Mkt&Fin": ["Communication", "SQL", "Data Analysis", "Statistics",
                "Critical Thinking", "Problem Solving"],
}
DEGREE_SKILLS = {
    "Sci&Tech": ["Python", "Java", "SQL", "Machine Learning", "Data Analysis", "Git"],
    "Comm&Mgmt": ["Communication", "Leadership", "Teamwork", "Time Management"],
    "Others": ["Communication", "Problem Solving", "Teamwork"],
}


def load_real_job_postings(n=N_POSTINGS_SAMPLE) -> pd.DataFrame:
    # 3.4M rows - read only the columns we need, then sample
    usecols = ["job_id", "company_name", "title", "description"]
    df = pd.read_csv(LINKEDIN_POSTINGS_IN, usecols=usecols)
    df = df.dropna(subset=["description"]).sample(n=min(n, len(df)), random_state=42)

    out = pd.DataFrame({
        "posting_id": "JP" + df["job_id"].astype(str),
        "title": df["title"],
        "company": df["company_name"],
        "description": df["description"],
        "true_skills": "",  # unlabeled real data - extractor skips the sanity check
    })
    return out.reset_index(drop=True)


def load_real_students() -> pd.DataFrame:
    df = pd.read_csv(CAMPUS_PLACEMENT_IN)

    rows = []
    for _, r in df.iterrows():
        cgpa_proxy = round((r["ssc_p"] + r["hsc_p"] + r["degree_p"]) / 3 / 10, 2)
        skills = set(DEGREE_SKILLS.get(r["degree_t"], []))
        skills |= set(SPECIALISATION_SKILLS.get(r["specialisation"], []))

        rows.append({
            "student_id": f"S{int(r['sl_no']):04d}",
            "cgpa": cgpa_proxy,  # proxy: avg of ssc_p/hsc_p/degree_p, not a real CGPA
            "projects_count": 0,  # not present in source data
            "certifications_count": 0,  # not present in source data
            "internships_count": 1 if r["workex"] == "Yes" else 0,
            "skills": ";".join(sorted(skills)),
            "placed": 1 if r["status"] == "Placed" else 0,
        })
    return pd.DataFrame(rows)


def main():
    if not CAMPUS_PLACEMENT_IN.exists() or not LINKEDIN_POSTINGS_IN.exists():
        raise SystemExit(
            "Missing source files. Run:\n"
            "  kaggle datasets download -d benroshan/factors-affecting-campus-placement "
            "-p data/external --unzip\n"
            "  kaggle datasets download -d arshkon/linkedin-job-postings "
            "-p data/external/linkedin_job_postings --unzip"
        )

    jobs = load_real_job_postings()
    students = load_real_students()

    JOB_POSTINGS_OUT.parent.mkdir(parents=True, exist_ok=True)
    STUDENTS_OUT.parent.mkdir(parents=True, exist_ok=True)
    jobs.to_csv(JOB_POSTINGS_OUT, index=False)
    students.to_csv(STUDENTS_OUT, index=False)

    print(f"Wrote {len(jobs)} real job postings -> {JOB_POSTINGS_OUT}")
    print(f"Wrote {len(students)} real student records -> {STUDENTS_OUT}")
    print(f"Real placement rate: {students['placed'].mean():.2%}")
    print("\nNote: skills for students are IMPUTED from degree/specialisation, "
          "not observed - see the SPECIALISATION_SKILLS/DEGREE_SKILLS maps in this file.")


if __name__ == "__main__":
    main()
