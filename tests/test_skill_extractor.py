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
