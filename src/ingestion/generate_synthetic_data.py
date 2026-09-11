"""Generates synthetic job postings + student profiles for the MVP.

Deliberately not scraping LinkedIn/Naukri (ToS risk — see ARCHITECTURE.md).
This is the MVP data source; a Kaggle static dataset can be dropped into
data/external/ and merged in later without changing downstream code, since
the output schema here is what the rest of the pipeline consumes.
"""

import random
from pathlib import Path

import pandas as pd

from src.nlp.skills_taxonomy import SKILLS_TAXONOMY, flat_skill_list

ROOT = Path(__file__).resolve().parents[2]
JOB_POSTINGS_OUT = ROOT / "data" / "raw" / "job_postings" / "job_postings.csv"
STUDENTS_OUT = ROOT / "data" / "raw" / "students" / "students.csv"

random.seed(42)

JOB_TITLES = [
    "Software Engineer", "Data Analyst", "Data Scientist", "Backend Developer",
    "Frontend Developer", "Full Stack Developer", "Machine Learning Engineer",
    "Cloud Engineer", "DevOps Engineer", "QA Engineer", "Business Analyst",
]

COMPANIES = [
    "TCS", "Infosys", "Wipro", "Accenture", "Cognizant", "Amazon", "Flipkart",
    "Zoho", "Freshworks", "Capgemini", "IBM", "HCL",
]

DESC_TEMPLATES = [
    "We are looking for a {title} to join our team. Required skills: {skills}. "
    "Good to have: {nice_to_have}. Strong {soft} is expected.",
    "{company} is hiring a {title}. The candidate should be proficient in {skills}. "
    "Experience with {nice_to_have} is a plus. We value {soft}.",
    "Job Description: {title} role at {company}. Must have hands-on experience in "
    "{skills}. Familiarity with {nice_to_have} preferred. {soft} is essential.",
]


def _sample_skills(n_core=4, n_nice=2):
    pool = flat_skill_list()
    core = random.sample(pool, n_core)
    remaining = [s for s in pool if s not in core]
    nice = random.sample(remaining, n_nice)
    soft = random.choice(SKILLS_TAXONOMY["Soft Skills"])
    return core, nice, soft


def generate_job_postings(n=300) -> pd.DataFrame:
    rows = []
    for i in range(n):
        title = random.choice(JOB_TITLES)
        company = random.choice(COMPANIES)
        core, nice, soft = _sample_skills()
        template = random.choice(DESC_TEMPLATES)
        description = template.format(
            title=title, company=company,
            skills=", ".join(core), nice_to_have=", ".join(nice), soft=soft,
        )
        rows.append({
            "posting_id": f"JP{i:04d}",
            "title": title,
            "company": company,
            "description": description,
            # ground-truth skills kept alongside for validating extractor precision/recall
            "true_skills": ";".join(core + nice),
        })
    return pd.DataFrame(rows)


def generate_students(n=200) -> pd.DataFrame:
    pool = flat_skill_list()
    rows = []
    for i in range(n):
        n_skills = random.randint(3, 9)
        skills = random.sample(pool, n_skills)
        rows.append({
            "student_id": f"S{i:04d}",
            "cgpa": round(random.uniform(5.5, 9.8), 2),
            "projects_count": random.randint(0, 6),
            "certifications_count": random.randint(0, 4),
            "internships_count": random.randint(0, 3),
            "skills": ";".join(skills),
            # label for the Month 3 classifier - synthetic, weighted toward
            # more skills/CGPA/projects, with noise so it's not trivially separable
            "placed": None,
        })
    df = pd.DataFrame(rows)
    df["placed"] = _synthetic_placement_label(df)
    return df


def _synthetic_placement_label(df: pd.DataFrame) -> list[int]:
    labels = []
    for _, row in df.iterrows():
        score = (
            0.15 * row["cgpa"]
            + 0.3 * row["projects_count"]
            + 0.3 * row["certifications_count"]
            + 0.4 * row["internships_count"]
            + 0.2 * len(row["skills"].split(";"))
            + random.gauss(0, 1.5)
        )
        labels.append(1 if score > 4.5 else 0)
    return labels


def main():
    JOB_POSTINGS_OUT.parent.mkdir(parents=True, exist_ok=True)
    STUDENTS_OUT.parent.mkdir(parents=True, exist_ok=True)

    jobs = generate_job_postings()
    students = generate_students()

    jobs.to_csv(JOB_POSTINGS_OUT, index=False)
    students.to_csv(STUDENTS_OUT, index=False)

    print(f"Wrote {len(jobs)} job postings -> {JOB_POSTINGS_OUT}")
    print(f"Wrote {len(students)} student profiles -> {STUDENTS_OUT}")
    print(f"Placement rate in synthetic data: {students['placed'].mean():.2%}")


if __name__ == "__main__":
    main()
