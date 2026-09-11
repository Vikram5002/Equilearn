# SkillBridge Analytics — 4-Month Plan (solo)

Assumes ~project starts 2026-09 and you're working solo. See [ARCHITECTURE.md](ARCHITECTURE.md)
for the tech decisions behind each step.

## Month 1 — Data & NLP foundation
- Repo/env setup (done), finalize architecture
- Acquire data: Kaggle employability dataset(s) + Kaggle job-postings dataset,
  generate synthetic student profiles + synthetic job postings for MVP volume
- Define a skills taxonomy (~150-250 skills, categorized: languages, frameworks,
  cloud, data/ML, soft skills, certifications)
- Build the skill-extraction NLP component (spaCy PhraseMatcher/EntityRuler) and
  validate precision/recall by hand on a sample of postings
- **Milestone**: given a raw job posting, extract a clean list of skills

## Month 2 — Feature store & pipeline
- Wrap skill extraction as a PySpark UDF running over the full postings dataset
  in local mode (this is the "distributed processing" demonstration)
- Write Delta Lake tables: `job_skills`, `student_skills`, `market_skill_demand`
- Join student skill profiles against market demand → per-student skill-gap table
- Stand up Airflow locally via Docker Compose; one DAG: ingest → extract → feature build
- **Milestone**: end-to-end skill-gap output for any student ID, orchestrated by Airflow

## Month 3 — ML models & dashboard
- Train placement-probability classifier (Logistic Regression baseline → XGBoost)
  on the Kaggle employability dataset + engineered skill-gap/academic features
- Evaluate (AUC, calibration), pull feature importances for the report's "why"
- Build the Streamlit skill-gap dashboard: student's skills vs market-demanded
  skills, missing-skill ranking, placement probability, recommended next skills
- **Milestone**: MVP complete — static dataset, working classifier, working dashboard

## Month 4 — Polish, cloud touch, stretch, writeup
- Push processed tables + model artifacts to S3 (free tier) — cloud integration
  for the report, not load-bearing for the demo
- Stress-test the demo path end-to-end at least twice before presentation day
- **If time remains (stretch goals, in priority order)**:
  1. Local Kafka (Docker) replaying the static dataset as a simulated live feed
  2. Swap "live" feed source to the Adzuna API (ToS-compliant) instead of static replay
  3. Elasticsearch (Docker) for skill search in the dashboard
  4. Curriculum-recommendation engine that re-scores as market data changes
- Final report, slides, recorded demo video (backup in case live demo has issues)

## What's explicitly out of scope
- Live scraping of LinkedIn/Naukri (ToS risk — see ARCHITECTURE.md)
- Any AWS managed big-data service that isn't free-tier (EMR, MSK, SageMaker)
- Multi-tenant/production concerns (auth, scaling beyond demo load, CI/CD)
