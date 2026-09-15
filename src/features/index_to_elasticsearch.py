"""Indexes extracted job postings into Elasticsearch so the dashboard can
search "which real postings ask for skill X" for a student's missing skills.

Run: python -m src.features.index_to_elasticsearch
"""

from pathlib import Path

import pandas as pd
from elasticsearch import Elasticsearch, helpers

ROOT = Path(__file__).resolve().parents[2]
JOB_SKILLS_IN = ROOT / "data" / "processed" / "job_postings_skills.csv"
INDEX_NAME = "job_postings"


def build_documents(df: pd.DataFrame):
    for _, row in df.iterrows():
        yield {
            "_index": INDEX_NAME,
            "_id": row["posting_id"],
            "_source": {
                "posting_id": row["posting_id"],
                "title": row["title"],
                "company": row["company"],
                "extracted_skills": str(row["extracted_skills"]).split(";") if pd.notna(row["extracted_skills"]) else [],
            },
        }


def main(es_url="http://localhost:9200"):
    df = pd.read_csv(JOB_SKILLS_IN)
    es = Elasticsearch(es_url)

    es.indices.delete(index=INDEX_NAME, ignore_unavailable=True)
    es.indices.create(
        index=INDEX_NAME,
        mappings={
            "properties": {
                "title": {"type": "text"},
                "company": {"type": "keyword"},
                "extracted_skills": {"type": "keyword"},
            }
        },
    )

    success, errors = helpers.bulk(es, build_documents(df), stats_only=False, raise_on_error=False)
    print(f"Indexed {success} postings into '{INDEX_NAME}' ({len(errors)} errors)")


def search_by_skill(skill: str, size=5, es_url="http://localhost:9200"):
    es = Elasticsearch(es_url)
    result = es.search(
        index=INDEX_NAME,
        query={"term": {"extracted_skills": skill}},
        size=size,
    )
    return [hit["_source"] for hit in result["hits"]["hits"]]


if __name__ == "__main__":
    main()
