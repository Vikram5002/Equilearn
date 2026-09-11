import spacy

from src.nlp.skill_extractor import build_matcher, extract_skills


def test_extracts_known_skills_from_text():
    nlp = spacy.blank("en")
    matcher = build_matcher(nlp)
    text = "We need someone strong in Python, React and Docker, with good Teamwork."

    skills = extract_skills(text, nlp, matcher)

    assert "Python" in skills
    assert "React" in skills
    assert "Docker" in skills
    assert "Teamwork" in skills


def test_no_false_matches_on_unrelated_text():
    nlp = spacy.blank("en")
    matcher = build_matcher(nlp)
    text = "The weather today is sunny with a light breeze."

    skills = extract_skills(text, nlp, matcher)

    assert skills == []


def test_ambiguous_short_skills_require_exact_case():
    nlp = spacy.blank("en")
    matcher = build_matcher(nlp)

    lowercase_text = "We need someone who can go above and beyond."
    assert extract_skills(lowercase_text, nlp, matcher) == []

    real_skill_text = "Backend written in Go, with a C client library."
    skills = extract_skills(real_skill_text, nlp, matcher)
    assert "Go" in skills
    assert "C" in skills
