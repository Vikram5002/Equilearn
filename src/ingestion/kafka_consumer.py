"""Consumes the simulated live job-postings feed and runs the same NLP skill
extraction used by the batch pipeline (src.nlp.skill_extractor) on each
message as it arrives, appending results to a CSV as it goes.

This is the "streaming skill extraction" demo: run this first, then run
kafka_producer.py in another terminal and watch the output file grow.

Run: python -m src.ingestion.kafka_consumer [--timeout 60]
"""

import argparse
import csv
import json
from pathlib import Path

import spacy
from kafka import KafkaConsumer

from src.nlp.skill_extractor import build_matcher, extract_skills
from src.nlp.skills_taxonomy import skill_to_category

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed" / "job_postings_skills_streaming.csv"
TOPIC = "job-postings"
FIELDNAMES = ["posting_id", "title", "company", "description", "extracted_skills", "skill_categories"]


def process_posting(posting: dict, nlp, matchers, categories) -> dict:
    """Runs batch-pipeline skill extraction on one streamed posting."""
    skills = extract_skills(posting.get("description"), nlp, matchers)
    return {
        "posting_id": posting.get("posting_id"),
        "title": posting.get("title"),
        "company": posting.get("company"),
        "description": posting.get("description"),
        "extracted_skills": ";".join(skills),
        "skill_categories": ";".join(sorted({categories.get(s, "Other") for s in skills})),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-servers", default="localhost:9092")
    parser.add_argument("--timeout", type=int, default=60,
                         help="stop after this many seconds of no new messages")
    args = parser.parse_args()

    nlp = spacy.blank("en")
    matchers = build_matcher(nlp)
    categories = skill_to_category()

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=args.bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        consumer_timeout_ms=args.timeout * 1000,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    print(f"Listening on topic '{TOPIC}', writing to {OUT} ...")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        count = 0
        for message in consumer:
            row = process_posting(message.value, nlp, matchers, categories)
            writer.writerow(row)
            f.flush()
            count += 1
            print(f"  [{count}] {row['posting_id']}: extracted {row['extracted_skills'] or '-'}")

    print(f"Done - stopped after {args.timeout}s with no new messages. Wrote {count} rows.")


if __name__ == "__main__":
    main()
