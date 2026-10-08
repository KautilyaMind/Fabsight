"""UI contract for the interviewer-friendly final report."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_report_view_renders_key_sections_without_raw_json_as_primary_output():
    app = AppTest.from_file(ROOT / "tests" / "fixtures" / "report_view_app.py").run(timeout=30)
    assert not app.exception
    visible = " ".join(x.value for x in [*app.header, *app.subheader, *app.markdown])
    for expected in ("Executive summary", "Evidence findings", "Investigation hypotheses", "Recommended next investigation steps", "Limitations and uncertainty"):
        assert expected in visible
    assert len(app.download_button) == 1
