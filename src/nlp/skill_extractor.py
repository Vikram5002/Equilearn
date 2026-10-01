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
from spacy.util import filter_spans

from src.nlp.skills_taxonomy import flat_skill_list, skill_to_category

ROOT = Path(__file__).resolve().parents[2]
JOB_POSTINGS_IN = ROOT / "data" / "raw" / "job_postings" / "job_postings.csv"
OUT = ROOT / "data" / "processed" / "job_postings_skills.csv"

# Short taxonomy entries that are also common English words ("go", "r", "c")
# produce false positives in real free text ("go above and beyond") under
# case-insensitive matching. Require exact case for these instead of folding
# to lowercase - cheap fix, no taxonomy entries need to be dropped.
CASE_SENSITIVE_SKILLS = {"Go", "C", "R"}


def build_matcher(nlp) -> tuple[PhraseMatcher, PhraseMatcher]:
    lower_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    exact_matcher = PhraseMatcher(nlp.vocab, attr="ORTH")

    lower_patterns = [nlp.make_doc(s) for s in flat_skill_list() if s not in CASE_SENSITIVE_SKILLS]
    exact_patterns = [nlp.make_doc(s) for s in flat_skill_list() if s in CASE_SENSITIVE_SKILLS]

    lower_matcher.add("SKILL", lower_patterns)
    if exact_patterns:
        exact_matcher.add("SKILL", exact_patterns)
    return lower_matcher, exact_matcher


def extract_skills(text: str, nlp, matchers) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    lower_matcher, exact_matcher = matchers
    doc = nlp(text)
    matches = lower_matcher(doc) + exact_matcher(doc)
    # keep only the longest non-overlapping spans, so "AWS Certified Solutions
    # Architect" doesn't also count as a separate "AWS" mention
    spans = filter_spans([doc[start:end] for _, start, end in matches])
    # dedupe while preserving the taxonomy's canonical casing
    seen = set()
    skills = []
    for span in sorted(spans, key=lambda sp: sp.start):
        canonical = _canonical(span.text)
        if canonical not in seen:
            seen.add(canonical)
            skills.append(canonical)
    return skills


_LOWER_TO_CANONICAL = {s.lower(): s for s in flat_skill_list()}


def _canonical(matched_text: str) -> str:
    """Map a case-insensitive match back to the taxonomy's canonical spelling."""
    return _LOWER_TO_CANONICAL.get(matched_text.lower(), matched_text)


def evaluate(df: pd.DataFrame) -> None:
    """Quick precision/recall sanity check against the synthetic ground truth."""
    if "true_skills" not in df.columns or df["true_skills"].isna().all():
        return
    precisions, recalls = [], []
    for _, row in df.iterrows():
        predicted = set(row["extracted_skills"].split(";")) if pd.notna(row["extracted_skills"]) and row["extracted_skills"] else set()
        truth = set(row["true_skills"].split(";")) if pd.notna(row["true_skills"]) and row["true_skills"] else set()
        if not predicted and not truth:
            continue
        tp = len(predicted & truth)
        precision = tp / len(predicted) if predicted else 0
        recall = tp / len(truth) if truth else 0
        precisions.append(precision)
        recalls.append(recall)
    if not precisions:
        return
    print("Skill extraction sanity check (synthetic data only):")
    print(f"  mean precision: {sum(precisions) / len(precisions):.2%}")
    print(f"  mean recall:    {sum(recalls) / len(recalls):.2%}")


def main():
    nlp = spacy.blank("en")
    matchers = build_matcher(nlp)
    categories = skill_to_category()

    df = pd.read_csv(JOB_POSTINGS_IN)
    extracted_col, category_col = [], []
    for description in df["description"]:
        skills = extract_skills(description, nlp, matchers)
        extracted_col.append(";".join(skills))
        category_col.append(";".join(sorted({categories.get(s, "Other") for s in skills})))

    df["extracted_skills"] = extracted_col
    df["skill_categories"] = category_col

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df)} rows -> {OUT}")

    evaluate(df)


if __name__ == "__main__":
    main()
