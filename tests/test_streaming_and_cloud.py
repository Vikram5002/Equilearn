import json

import numpy as np
import pandas as pd
import spacy

from src.ingestion.kafka_consumer import process_posting
from src.ingestion.kafka_producer import postings_to_messages
from src.ingestion.push_to_s3 import FILES_TO_PUSH, push
from src.nlp.skill_extractor import build_matcher
from src.nlp.skills_taxonomy import skill_to_category


def test_producer_messages_are_json_safe():
    df = pd.DataFrame({"posting_id": ["JP1", "JP2"], "title": ["Dev", np.nan],
                       "company": ["X", "Y"], "description": ["Python", np.nan]})
    msgs = list(postings_to_messages(df))
    assert msgs[1]["title"] is None and msgs[1]["description"] is None
    # strict JSON (no NaN) must round-trip, since that's what goes on the wire
    assert json.loads(json.dumps(msgs, allow_nan=False)) == msgs


def test_consumer_extracts_like_batch_pipeline():
    nlp = spacy.blank("en")
    row = process_posting(
        {"posting_id": "JP1", "title": "Dev", "company": "X",
         "description": "Need Python, Docker and Teamwork."},
        nlp, build_matcher(nlp), skill_to_category(),
    )
    assert row["extracted_skills"].split(";") == ["Python", "Docker", "Teamwork"]
    assert "Programming Languages" in row["skill_categories"]


def test_consumer_survives_missing_description():
    nlp = spacy.blank("en")
    row = process_posting({"posting_id": "JP2", "description": None},
                          nlp, build_matcher(nlp), skill_to_category())
    assert row["extracted_skills"] == "" and row["skill_categories"] == ""


class FakeS3:
    def __init__(self):
        self.calls = []

    def upload_file(self, path, bucket, key):
        self.calls.append((path, bucket, key))


def test_push_uploads_existing_files_only(tmp_path):
    (tmp_path / FILES_TO_PUSH[0]).write_text("x")
    (tmp_path / FILES_TO_PUSH[1]).write_text("y")
    s3 = FakeS3()
    keys = push(s3, "bucket", "/skillbridge/latest/", tmp_path)
    assert keys == [f"skillbridge/latest/{FILES_TO_PUSH[0]}", f"skillbridge/latest/{FILES_TO_PUSH[1]}"]
    assert all(b == "bucket" for _, b, _ in s3.calls)
