"""Pushes pipeline outputs (processed tables + trained model) to S3.

Month 4 stretch goal - the "cloud storage integration" checkbox for the
report. Not load-bearing for the live demo: everything runs fine locally
without this. Uses whatever AWS credentials are already configured
(`aws configure` / env vars / ~/.aws/credentials) - never pass keys on the
command line or hardcode them here.

Run: python -m src.ingestion.push_to_s3 --bucket skillbridge-analytics-vikram
"""

import argparse
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"

FILES_TO_PUSH = [
    "job_postings_skills.csv",
    "market_skill_demand.csv",
    "student_skill_gaps.csv",
    "placement_model.joblib",
    "model_metrics.json",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--prefix", default="skillbridge/latest")
    args = parser.parse_args()

    s3 = boto3.client("s3")

    for filename in FILES_TO_PUSH:
        path = PROCESSED_DIR / filename
        if not path.exists():
            print(f"Skipping {filename} (not found - run the pipeline first)")
            continue
        key = f"{args.prefix}/{filename}"
        s3.upload_file(str(path), args.bucket, key)
        print(f"Uploaded {filename} -> s3://{args.bucket}/{key}")


if __name__ == "__main__":
    main()
