from streamlit.testing.v1 import AppTest


def test_dashboard_app_executes_with_builtin_demo():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception, [str(error.value) for error in app.exception]
