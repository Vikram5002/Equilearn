"""Smoke-tests every dashboard page against the real pipeline outputs."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    not (ROOT / "data" / "processed" / "placement_model.joblib").exists(),
    reason="run the pipeline first",
)

SCRIPT = """
import sys
sys.path.insert(0, {root!r})
from src.dashboard import app
app.{page}()
"""


def _run(page, **state):
    at = AppTest.from_string(SCRIPT.format(root=str(ROOT), page=page), default_timeout=120)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


@pytest.mark.parametrize("page", ["page_onboarding", "page_student", "page_cohort", "page_market", "page_model", "page_data"])
def test_page_renders_without_exceptions(page):
    _run(page)


def test_student_page_switching_students_and_simulator():
    ids = _run("page_student").sidebar.selectbox(key="student_id").options
    for sid in ids[1:6]:
        at = _run("page_student", student_id=sid)
        assert at.title[0].value == f"Student {sid}"
        assert any(m.label == "Simulated probability" for m in at.metric)
        at.multiselect(key=f"add_{sid}").set_value(at.multiselect(key=f"add_{sid}").options[:5]).run()
        assert not at.exception, [e.value for e in at.exception]


def test_cohort_tier_filter_empty_selection():
    at = _run("page_cohort")
    at.pills[0].set_value([]).run()
    assert not at.exception
