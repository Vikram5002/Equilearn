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


def push(s3, bucket: str, prefix: str, processed_dir: Path = PROCESSED_DIR) -> list[str]:
    """Uploads whichever FILES_TO_PUSH exist; returns the S3 keys written."""
    prefix = prefix.strip("/")
    uploaded = []
    for filename in FILES_TO_PUSH:
        path = processed_dir / filename
        if not path.exists():
            print(f"Skipping {filename} (not found - run the pipeline first)")
            continue
        key = f"{prefix}/{filename}" if prefix else filename
        s3.upload_file(str(path), bucket, key)
        print(f"Uploaded {filename} -> s3://{bucket}/{key}")
        uploaded.append(key)
    return uploaded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--prefix", default="skillbridge/latest")
    args = parser.parse_args()

    push(boto3.client("s3"), args.bucket, args.prefix)


if __name__ == "__main__":
    main()
