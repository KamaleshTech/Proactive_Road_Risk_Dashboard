from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_app_executes_with_builtin_demo():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=30).run()
    assert not app.exception, [str(error.value) for error in app.exception]
