# Remaining Work — Step-by-Step

The MVP (data → NLP skill extraction → feature store → classifier → dashboard)
is done and verified. This is the checklist for everything listed as
"Advanced Scope" in the original spec, plus swapping in real data. Do them in
this order — each one is optional but builds on the last.

---

## 1. Swap in a real Kaggle dataset — ✅ DONE

Used `benroshan/factors-affecting-campus-placement` (real academic + placement
outcomes) and `arshkon/linkedin-job-postings` (real postings, 1500-row sample).
See the README's "Using real Kaggle data" section and
`src/ingestion/load_kaggle_data.py`. Result: classifier AUC went from 0.66
(synthetic) to 0.947 (real). The steps below are kept for reference / in case
you want a different or additional dataset.

Why first: your classifier and skill taxonomy are currently validated only
against data you generated yourself. A real dataset is what makes the report
credible.

**Steps:**
1. Get a Kaggle API key: kaggle.com → Account → "Create New API Token" →
   downloads `kaggle.json`. Put it at `C:\Users\<you>\.kaggle\kaggle.json`.
2. `pip install kaggle`
3. Pick datasets (search on kaggle.com):
   - Job postings with descriptions: search `"linkedin job postings"` or
     `"naukri job postings"` — pick one with a free `description`/`text` column.
   - Employability: search `"campus placement"` or `"student employability"` —
     pick one with academic + outcome (placed/not placed) columns.
4. Download into `data/external/`:
   ```bash
   kaggle datasets download -d <dataset-slug> -p data/external --unzip
   ```
5. Write `src/ingestion/load_kaggle_data.py` that reads the downloaded CSV(s)
   and reshapes them into the **same schema** `generate_synthetic_data.py`
   already produces (`posting_id,title,company,description,true_skills` for
   postings; `student_id,cgpa,projects_count,certifications_count,
   internships_count,skills,placed` for students). Because downstream code
   (`skill_extractor.py`, `build_feature_store.py`, `train_classifier.py`)
   only cares about that schema, nothing else needs to change.
6. Re-run the pipeline (README Quickstart) pointing at the new files, check:
   - Does the skill taxonomy in `src/nlp/skills_taxonomy.py` cover skills that
     actually show up in real postings? Extend it if extraction recall looks low.
   - Does the classifier's AUC hold up on real placement outcomes?

---

## 2. Airflow orchestration — ✅ DONE

Set up under `infra/airflow/`, DAG `skillbridge_pipeline`
(`ingest_data >> extract_skills >> build_feature_store >> train_classifier`).
Deviated from the plan below in two ways, both documented in the commit that
added this:
- **LocalExecutor instead of CeleryExecutor** — the official CeleryExecutor
  compose template hit a reproducible Celery/Docker-Desktop-on-Windows bug
  (worker hostname resolution crash loop). LocalExecutor has no such issue
  and this DAG doesn't need distributed workers at this scale.
- **Custom Dockerfile instead of `_PIP_ADDITIONAL_REQUIREMENTS`** — the
  latter reinstalls all deps from scratch on every container start (minutes
  per boot, got stuck once). `infra/airflow/Dockerfile` bakes them in once.

Run it:
```bash
cd infra/airflow
docker compose up airflow-init   # one-time
docker compose up -d
# open http://localhost:8080 (airflow / airflow), trigger skillbridge_pipeline
```
Verified: all 4 tasks succeed in ~12s. Screenshot the green DAG graph
(Grid or Graph view) for your report.

The original plan (kept for reference):

**Steps:**
1. Get Docker Desktop running (needed for everything below).
2. Create `infra/docker-compose.airflow.yml` using the official Airflow
   quick-start compose file (`curl -O https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml`),
   adjusted to mount this repo's `src/` and `data/` into the containers.
3. Write one DAG, `dags/skillbridge_pipeline.py`, with four tasks that just
   shell out to the scripts you already have:
   `ingest >> extract_skills >> build_features >> train_model`
   (use `BashOperator` calling `python -m src.X.Y` — don't rewrite the logic
   as Airflow-native code, that's unnecessary rework for a demo DAG).
4. `docker compose -f infra/docker-compose.airflow.yml up`, open
   `localhost:8080`, trigger the DAG manually, confirm all four tasks go green.
5. Screenshot the green DAG graph for your report — that's usually what's graded.

---

## 3. Local Kafka streaming simulation — ✅ DONE

`infra/kafka/docker-compose.yml` runs a single-broker Kafka in KRaft mode
(no Zookeeper). `src/ingestion/kafka_producer.py` replays job postings onto
the `job-postings` topic with a delay; `src/ingestion/kafka_consumer.py`
runs the same `extract_skills()` used by the batch pipeline on each message
as it arrives, writing to `data/processed/job_postings_skills_streaming.csv`.

Run it:
```bash
cd infra/kafka && docker compose up -d && cd ../..
python -m src.ingestion.kafka_consumer --timeout 30   # run first, in one terminal
python -m src.ingestion.kafka_producer --delay 0.5     # then this, in another
```
Verified: 10 messages produced, all 10 consumed and skill-extracted in real time.

Swap-to-real-feed stretch (not done): replace the CSV read in
`kafka_producer.py` with an Adzuna API poll - the consumer side is unchanged.

The original plan (kept for reference):

Do this instead of ever touching LinkedIn/Naukri scraping — see legal note
in ARCHITECTURE.md.

**Steps:**
1. Add a Kafka + Zookeeper service to `infra/docker-compose.yml` (use the
   `confluentinc/cp-kafka` + `cp-zookeeper` images — single broker, no auth,
   this is a demo not production).
2. `docker compose up -d`, confirm broker is reachable on `localhost:9092`.
3. Write `src/ingestion/kafka_producer.py`: reads `job_postings.csv` row by
   row and publishes each row as a JSON message to a `job-postings` topic,
   with a small sleep between messages to simulate a live feed.
4. Write `src/ingestion/kafka_consumer.py`: subscribes to `job-postings`,
   and for each message calls the same `extract_skills()` function from
   `src/nlp/skill_extractor.py` you already have, appending results to
   `data/processed/job_postings_skills.csv` instead of doing it as one batch.
5. Demo script: run the consumer, then the producer, watch the CSV grow in
   real time. This is the "streaming skill extraction" story for your report.
6. **Stretch on the stretch**: replace step 3's CSV source with the **Adzuna
   API** (free tier, ToS-compliant — see ARCHITECTURE.md) so the producer is
   pulling real near-live postings instead of replaying a static file.

---

## 4. Elasticsearch skill search (optional, lowest priority)

**Steps:**
1. Add `elasticsearch:8.x` (single-node, security disabled for local demo)
   to `infra/docker-compose.yml`.
2. Write `src/features/index_to_elasticsearch.py`: reads
   `data/processed/job_postings_skills.csv` and indexes each posting
   (title, company, extracted_skills) into an `job_postings` index.
3. Add a search box to the Streamlit dashboard (`src/dashboard/app.py`) that
   queries Elasticsearch for postings matching a skill the student is missing
   — "here are 5 real postings asking for X" is a nice demo moment.

---

## 5. Push to AWS S3 (Month 4 — do this last, costs nothing if scoped right)

**Do not paste AWS keys into a chat with me or anyone.** Steps to do yourself:

1. In the AWS Console, create an S3 bucket, e.g. `skillbridge-analytics-<yourname>`.
2. Create an IAM user (or better, an IAM role if running from EC2) with a
   policy scoped to **only that bucket**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
       "Resource": [
         "arn:aws:s3:::skillbridge-analytics-<yourname>",
         "arn:aws:s3:::skillbridge-analytics-<yourname>/*"
       ]
     }]
   }
   ```
3. On your machine: `aws configure` (enter the access key/secret yourself,
   in your own terminal — never in a chat).
4. Write `src/ingestion/push_to_s3.py` using `boto3` (already in
   `requirements.txt`) to upload `data/processed/*.csv` and
   `placement_model.joblib` to the bucket.
5. In your report, this is the "cloud storage integration" checkbox — it
   doesn't need to be load-bearing for the live demo.

**Explicitly skip**: EMR, MSK (managed Kafka), SageMaker — all cost real
money beyond free tier and nothing above requires them at this scale.

---

## Suggested order given a typical remaining timeline

1. Real Kaggle data swap — do this regardless of time left, it's what makes results defensible
2. Airflow DAG — cheap to demo, "orchestration" is usually explicitly graded
3. Kafka streaming simulation — the most visually impressive stretch goal
4. S3 push — quick, do it near the end
5. Elasticsearch — only if time remains after everything else
