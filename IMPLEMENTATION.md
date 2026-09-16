# SkillBridge Analytics — Implementation Plan & Status

This file is the single source of truth for "what's built vs. what's left."
For narrative context see [PROJECT_PLAN.md](PROJECT_PLAN.md) (the original
4-month plan) and [ARCHITECTURE.md](ARCHITECTURE.md) (tech decisions).
[docs/STRETCH_GOALS.md](docs/STRETCH_GOALS.md) has step-by-step run
instructions for every component below.

## Status: all build work is done

Every item in the original MVP scope and every Advanced/stretch-goal item is
implemented, tested, and verified working end-to-end on real data. What's
left is submission prep (report, demo), not code.

---

## Part 1 — What's built

### 1.1 Data layer
| Component | File | Status |
|---|---|---|
| Synthetic data generator (fallback/dev) | `src/ingestion/generate_synthetic_data.py` | ✅ |
| Real Kaggle data loader | `src/ingestion/load_kaggle_data.py` | ✅ verified (AUC 0.947) |
| Skills taxonomy (~150 skills, 8 categories) | `src/nlp/skills_taxonomy.py` | ✅ |

Real datasets used: `benroshan/factors-affecting-campus-placement` (academic
+ placement outcomes) and `arshkon/linkedin-job-postings` (job descriptions,
1500-row sample). Scraping LinkedIn/Naukri directly was deliberately avoided
— see ARCHITECTURE.md's legal/ToS note.

### 1.2 NLP — skill extraction
`src/nlp/skill_extractor.py` — spaCy `PhraseMatcher` over the taxonomy.
Case-insensitive for most terms; case-sensitive for ambiguous short ones
(`Go`, `C`, `R`) after a real false-positive bug was found on real text
("go above and beyond" matching the Go language). Tested in
`tests/test_skill_extractor.py` (3 tests, all passing).

### 1.3 Feature engineering
`src/features/build_feature_store.py` — joins extracted job-posting skills
with student skill profiles into two tables: `market_skill_demand.csv`
(skill → % of postings asking for it) and `student_skill_gaps.csv`
(per-student matched/missing skills + a market-alignment score).

### 1.4 ML
`src/models/train_classifier.py` — Logistic Regression vs. XGBoost, keeps
whichever wins on held-out AUC. On real data: **AUC 0.947**, CGPA-proxy is
the dominant feature (expected — this Kaggle dataset's placement outcome is
strongly academic-driven).

### 1.5 Dashboard
`src/dashboard/app.py` (Streamlit) — per-student placement probability,
matched vs. missing skills ranked by market demand, top-20 market-demand
chart, and an Elasticsearch-backed "find real postings for this missing
skill" search box that fails soft if Elasticsearch isn't running.

### 1.6 Orchestration — Airflow
`infra/airflow/` — DAG `skillbridge_pipeline`
(`ingest_data >> extract_skills >> build_feature_store >> train_classifier`).
Runs LocalExecutor (not the default CeleryExecutor — that hit a reproducible
Celery/Docker-Desktop-on-Windows crash loop) on a custom image with
dependencies baked in (not `_PIP_ADDITIONAL_REQUIREMENTS`, which reinstalls
from scratch — and once got stuck — on every container start). Verified: all
4 tasks succeed in ~12s.

### 1.7 Streaming — Kafka
`infra/kafka/` — single-broker Kafka in KRaft mode (no Zookeeper).
`src/ingestion/kafka_producer.py` replays postings onto a topic with a
delay; `src/ingestion/kafka_consumer.py` runs the same skill extraction on
each message as it arrives. Verified: 10/10 messages produced and consumed
correctly in real time.

### 1.8 Search — Elasticsearch
`infra/elasticsearch/` — single-node ES, security disabled (demo-scale).
`src/features/index_to_elasticsearch.py` indexes postings; wired into the
dashboard. Verified: 1485/1500 real postings indexed, search tested.

### 1.9 Cloud — AWS S3
`src/ingestion/push_to_s3.py` uploads the 5 processed pipeline outputs to
`s3://skillbridge-analytics-vikram/skillbridge/latest/`. Uses whatever AWS
credentials are already configured locally (never hardcoded). Verified via
`aws s3 ls`.

### 1.10 Known gotcha (documented, not a bug to fix)
The Airflow DAG's `ingest_data` task calls the **synthetic** generator, so
triggering the DAG overwrites `data/raw/` back to synthetic data. If you've
switched to real data (§1.1), re-run
`python -m src.ingestion.load_kaggle_data` afterward before retraining or
pushing to S3. This bit us once already (a synthetic-data model got pushed
to S3 by mistake) — see the commit history for the fix.

---

## Part 2 — What's actually left (submission prep, not code)

None of this is "build the system" work — that part is done. This is what
turns a working repo into a gradeable deliverable.

| # | Task | Notes |
|---|---|---|
| 1 | **Write the project report** | Use this file + ARCHITECTURE.md + PROJECT_PLAN.md as source material. Sections: problem statement, architecture diagram, each component's design rationale (the "why X instead of Y" calls in ARCHITECTURE.md are exactly what a report wants), results (AUC 0.947, skill-gap examples), KPIs from the original brief (placement rate improvement, skill-gap closure rate — frame these as *what the dashboard enables measuring*, since there's no live cohort to measure them on yet). |
| 2 | **Prepare slides** | Mirror the report's structure; include the same screenshots as #3. |
| 3 | **Take screenshots for the report/slides** | Airflow DAG graph (green, all 4 tasks) at `localhost:8080`; dashboard (student view + skill-gap panel + ES search results); a `market_skill_demand` bar chart; S3 console showing the uploaded files. |
| 4 | **Decide live demo vs. recorded video** | Given how many Docker services are involved (Airflow, Kafka, Elasticsearch, Postgres), a **recorded backup video** is strongly recommended even if you also plan to demo live — one Docker hiccup shouldn't sink the presentation. |
| 5 | **Rehearse the demo end-to-end at least twice** | Cold-start all containers, confirm nothing broke since last run (see the Airflow/synthetic-data gotcha above), time it. |
| 6 | **Re-verify all Docker services boot cleanly** | Time has passed since these were last tested; do a full `docker compose down` + `up` cycle on all three (`infra/airflow`, `infra/kafka`, `infra/elasticsearch`) before demo day, not on demo day. |
| 7 | **Optional polish (only if time remains)** | More test coverage (currently 3 tests, all on the NLP extractor); dashboard error handling if a service is down (ES search already fails soft — Kafka/Airflow demos don't need dashboard integration); Adzuna API swap for the Kafka producer (documented but not implemented — see STRETCH_GOALS.md §3). |
| 8 | **Submit** | Share the GitHub link (`github.com/Vikram5002/Equilearn`); confirm the professor/evaluator can actually clone and run it (the README's Quickstart is the test — try it on a machine that hasn't seen this project before, if possible). |

### Suggested order for the remaining ~week(s)
Report and slides first (they don't block on anything and are usually the
long pole) → screenshots (quick, do alongside report writing) → demo
rehearsal + recorded video (do last, closest to submission, so it reflects
the final repo state) → final Docker re-verification the day before.
