# SkillBridge Analytics — Architecture (scaled-down, free-tier)

Goal: demonstrate real Big Data concepts (distributed processing, NLP pipelines,
feature engineering, orchestration) on a $0-$20 actual spend, reliably enough to demo.

## Pipeline

```
[Job postings: Kaggle static dataset + synthetic + (stretch) Adzuna API]
        │
        ▼
[Ingestion: src/ingestion]  →  data/raw/
        │
        ▼
[NLP Skill Extraction: spaCy PhraseMatcher/EntityRuler over a skills taxonomy]
   (runs as a Spark UDF over a local PySpark DataFrame for the "distributed" story)
        │
        ▼
[Feature Store: Delta Lake tables, local filesystem, no cluster]
   - job_skills (posting_id, skill, category)
   - student_skills (student_id, skill, proficiency)
   - market_skill_demand (skill, frequency, %postings)
        │
        ▼
[ML: scikit-learn / XGBoost placement-probability classifier]
[Gap analysis: student_skills vs market_skill_demand → ranked missing skills]
        │
        ▼
[Dashboard: Streamlit] — skill-gap view + placement probability + recommendations
```

## Deliberate substitutions vs. the original "full" stack, and why

| Original | Used instead | Why |
|---|---|---|
| Managed Kafka (MSK) | Local Kafka via Docker Compose (stretch only), or plain batch files for MVP | MSK costs real money; local Docker Kafka is free and still demonstrates streaming concepts |
| EMR Spark cluster | PySpark `local[*]` mode | Free, no cluster to manage, still exercises the DataFrame/partitioning API |
| Spark NLP (John Snow Labs) | spaCy (PhraseMatcher/EntityRuler, optional trained NER) called from a Spark UDF | Spark NLP needs a pinned JVM/Spark version and some annotators are licensed; spaCy is lighter, well-documented, and easier to get working solo in month 1 |
| Hive | Delta Lake in local mode (or plain Parquet if Delta setup adds friction) | ACID/versioned tables without a metastore or cluster |
| Elasticsearch (MVP) | Deferred to stretch goal (Docker local) | Not needed for MVP skill-gap dashboard; simple Parquet/pandas filtering is enough |
| Live scraping (Naukri/LinkedIn) | Kaggle job-postings datasets + synthetic data (MVP); Adzuna API (stretch, ToS-compliant) | See legal note below |

## AWS usage (kept minimal, free-tier eligible)

- **S3** (5GB free tier): store processed Parquet/Delta tables and trained model artifacts — mainly to legitimately show cloud integration in the report/demo.
- **EC2 t2.micro/t3.micro** (750 hrs/month free for 12 months, if your account is eligible): optional, only if you want to host the Streamlit demo somewhere other than your laptop. Streamlit Community Cloud (free, no AWS involved) is a lower-risk alternative for the final demo.
- **Explicitly avoided**: EMR, MSK, SageMaker, RDS — all can burn through $100 in credits fast and aren't needed for a laptop-scale demo dataset.

Do not paste AWS access keys into chat. Run `aws configure` yourself in a terminal,
or better, create an IAM user scoped only to the S3 bucket this project uses
(`s3:GetObject`, `s3:PutObject`, `s3:ListBucket` on one bucket ARN) and store the
credentials in a local `.env` / `~/.aws/credentials` that stays out of git
(already covered by `.gitignore`). AWS isn't needed until Month 4 — MVP work
(Months 1-3) runs entirely locally.

## Legal / ToS note on job-posting data

LinkedIn and Naukri both prohibit scraping in their Terms of Service and actively
rate-limit/block/suspend accounts that do it (LinkedIn has also pursued legal action
in some cases — see *hiQ Labs v. LinkedIn* for how contested even "public" scraping is).
For a student project, that risk isn't worth it. Use instead:

1. **Kaggle "LinkedIn Job Postings" / "Naukri" datasets** — these were collected and
   published by the dataset authors; you're consuming a published dataset, not scraping.
2. **Synthetic data** — generated postings with realistic skill mentions (see
   `src/ingestion/generate_synthetic_data.py`), used for the MVP by default.
3. **Adzuna API** (free developer tier, covers India) — a legitimate, ToS-compliant
   source if you want a "live" feed for the Month 4 streaming stretch goal, instead
   of scraping LinkedIn/Naukri directly.
4. **National Career Service (NCS) / data.gov.in** — government open datasets, worth
   checking for India-specific placement/skill-demand data to strengthen the report's
   "Skill India Mission" framing.
