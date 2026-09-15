"""Simulates a live job-postings feed by replaying job_postings.csv onto a
Kafka topic, one message at a time with a small delay.

Deliberately not scraping a real live source (LinkedIn/Naukri ToS - see
ARCHITECTURE.md). Swapping this for a real near-live feed later just means
replacing the CSV read below with an Adzuna API poll - the topic/consumer
side doesn't change.

Run: python -m src.ingestion.kafka_producer [--delay 0.5] [--limit 50]
"""

import argparse
import json
import time
from pathlib import Path

import pandas as pd
from kafka import KafkaProducer

ROOT = Path(__file__).resolve().parents[2]
JOB_POSTINGS_IN = ROOT / "data" / "raw" / "job_postings" / "job_postings.csv"
TOPIC = "job-postings"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-servers", default="localhost:9092")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds between messages")
    parser.add_argument("--limit", type=int, default=None, help="stop after N messages")
    args = parser.parse_args()

    df = pd.read_csv(JOB_POSTINGS_IN)
    if args.limit:
        df = df.head(args.limit)

    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"Streaming {len(df)} postings to topic '{TOPIC}' (delay={args.delay}s)...")
    for _, row in df.iterrows():
        message = row.where(pd.notna(row), None).to_dict()
        producer.send(TOPIC, value=message)
        print(f"  sent {message['posting_id']}: {message['title']} @ {message['company']}")
        time.sleep(args.delay)

    producer.flush()
    print("Done.")


if __name__ == "__main__":
    main()
