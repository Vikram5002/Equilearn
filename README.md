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

## Quickstart (full MVP pipeline)

```bash
python -m src.ingestion.generate_synthetic_data   # job postings + student profiles
python -m src.nlp.skill_extractor                 # NLP skill extraction (NER)
python -m src.features.build_feature_store        # market demand + per-student skill gaps
python -m src.models.train_classifier              # placement-probability classifier
streamlit run src/dashboard/app.py                  # skill-gap dashboard
```

Run in order — each step reads the previous step's output from `data/`:

| Step | Script | Produces |
|---|---|---|
| 1 | `src.ingestion.generate_synthetic_data` | `data/raw/job_postings/job_postings.csv`, `data/raw/students/students.csv` |
| 2 | `src.nlp.skill_extractor` | `data/processed/job_postings_skills.csv` |
| 3 | `src.features.build_feature_store` | `data/processed/market_skill_demand.csv`, `data/processed/student_skill_gaps.csv` |
| 4 | `src.models.train_classifier` | `data/processed/placement_model.joblib`, `data/processed/model_metrics.json` |
| 5 | `src.dashboard.app` | Streamlit UI at `localhost:8501` |

## Tests

```bash
pytest tests/
```
