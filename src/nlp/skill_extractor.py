"""Skill-extraction NER component.

Uses spaCy's PhraseMatcher over the skills taxonomy rather than John Snow Labs'
Spark NLP: same NER concept (entity recognition over free text), but no JVM/
Spark-version pinning and no licensed annotators to fight with solo in month 1.
In Month 2 this function is wrapped as a PySpark UDF to run over the full
postings dataset in local[*] mode - that's where the "distributed processing"
part of the Big Data story shows up, not here.
"""

from pathlib import Path

import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher

from src.nlp.skills_taxonomy import flat_skill_list, skill_to_category

ROOT = Path(__file__).resolve().parents[2]
JOB_POSTINGS_IN = ROOT / "data" / "raw" / "job_postings" / "job_postings.csv"
OUT = ROOT / "data" / "processed" / "job_postings_skills.csv"


def build_matcher(nlp) -> PhraseMatcher:
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in flat_skill_list()]
    matcher.add("SKILL", patterns)
    return matcher


def extract_skills(text: str, nlp, matcher: PhraseMatcher) -> list[str]:
    doc = nlp(text)
    matches = matcher(doc)
    # dedupe while preserving the taxonomy's canonical casing
    seen = set()
    skills = []
    for match_id, start, end in matches:
        span_text = doc[start:end].text
        canonical = _canonical(span_text)
        if canonical not in seen:
            seen.add(canonical)
            skills.append(canonical)
    return skills


def _canonical(matched_text: str) -> str:
    """Map a case-insensitive match back to the taxonomy's canonical spelling."""
    lower_to_canonical = {s.lower(): s for s in flat_skill_list()}
    return lower_to_canonical.get(matched_text.lower(), matched_text)


def evaluate(df: pd.DataFrame) -> None:
    """Quick precision/recall sanity check against the synthetic ground truth."""
    if "true_skills" not in df.columns:
        return
    precisions, recalls = [], []
    for _, row in df.iterrows():
        predicted = set(row["extracted_skills"].split(";")) if row["extracted_skills"] else set()
        truth = set(row["true_skills"].split(";")) if row["true_skills"] else set()
        if not predicted and not truth:
            continue
        tp = len(predicted & truth)
        precision = tp / len(predicted) if predicted else 0
        recall = tp / len(truth) if truth else 0
        precisions.append(precision)
        recalls.append(recall)
    print(f"Skill extraction sanity check (synthetic data only):")
    print(f"  mean precision: {sum(precisions) / len(precisions):.2%}")
    print(f"  mean recall:    {sum(recalls) / len(recalls):.2%}")


def main():
    nlp = spacy.blank("en")
    matcher = build_matcher(nlp)
    categories = skill_to_category()

    df = pd.read_csv(JOB_POSTINGS_IN)
    extracted_col, category_col = [], []
    for description in df["description"]:
        skills = extract_skills(description, nlp, matcher)
        extracted_col.append(";".join(skills))
        category_col.append(";".join(sorted({categories[s] for s in skills})))

    df["extracted_skills"] = extracted_col
    df["skill_categories"] = category_col

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df)} rows -> {OUT}")

    evaluate(df)


if __name__ == "__main__":
    main()
