# Bakes in the deps the skillbridge_pipeline DAG's BashOperator tasks need,
# instead of relying on _PIP_ADDITIONAL_REQUIREMENTS (which reinstalls from
# scratch on every container start - too slow/flaky for repeated demo runs).
FROM apache/airflow:2.9.3

COPY requirements-airflow.txt /requirements-airflow.txt
RUN pip install --no-cache-dir -r /requirements-airflow.txt
