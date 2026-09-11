# SkillBridge Analytics

Placement & Employability Prediction Engine — a Big Data Analytics college major project.

Aggregates student academic/skill data with job-market skill demand to predict
individual employability and recommend skill-gap interventions.

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the month-by-month build plan and
[ARCHITECTURE.md](ARCHITECTURE.md) for the tech stack and why each choice was made
(scaled down to run on free-tier AWS + a laptop, no paid clusters).

## Project layout

```
data/
  raw/job_postings/   - static/synthetic job posting data
  raw/students/        - synthetic student profiles
  external/             - Kaggle datasets go here (gitignored)
  processed/            - pipeline outputs (gitignored)
src/
  ingestion/            - data generation / loading
  nlp/                  - skills taxonomy + skill extraction (NER)
  features/             - feature store build scripts (Month 2)
  models/               - placement-probability classifier (Month 3)
  dashboard/            - Streamlit skill-gap dashboard (Month 3)
notebooks/               - exploratory analysis
infra/                   - docker-compose for Kafka/Airflow/ES (stretch goals)
docs/                    - report/slides source
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Quickstart (Month 1 deliverable)

```bash
python -m src.ingestion.generate_synthetic_data
python -m src.nlp.skill_extractor
```

This generates synthetic job postings + student profiles under `data/raw/`, then
extracts skills from every posting and writes `data/processed/job_postings_skills.csv`.
