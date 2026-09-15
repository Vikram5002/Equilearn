"""SkillBridge Analytics pipeline DAG.

Deliberately thin: each task just shells out to a script that already works
and is already tested standalone (see src/). Rewriting that logic as
Airflow-native operators would be pure overhead for a demo DAG - the point
here is to show orchestration (ingest -> extract -> features -> train),
not to relocate business logic into Airflow.
"""

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"

with DAG(
    dag_id="skillbridge_pipeline",
    description="Ingest -> NLP skill extraction -> feature store -> classifier",
    start_date=datetime(2026, 1, 1),
    schedule=None,  # trigger manually for the demo; set a cron string for real runs
    catchup=False,
    tags=["skillbridge"],
) as dag:

    ingest = BashOperator(
        task_id="ingest_data",
        bash_command=f"cd {PROJECT_DIR} && python -m src.ingestion.generate_synthetic_data",
    )

    extract_skills = BashOperator(
        task_id="extract_skills",
        bash_command=f"cd {PROJECT_DIR} && python -m src.nlp.skill_extractor",
    )

    build_features = BashOperator(
        task_id="build_feature_store",
        bash_command=f"cd {PROJECT_DIR} && python -m src.features.build_feature_store",
    )

    train_model = BashOperator(
        task_id="train_classifier",
        bash_command=f"cd {PROJECT_DIR} && python -m src.models.train_classifier",
    )

    ingest >> extract_skills >> build_features >> train_model
