"""
Unit tests for the AST coordinates boundary extractor helper.
"""

from __future__ import annotations

from core.intelligence.ast_helper import get_ast_bounds


def test_ast_bounds_python_function(tmp_path, monkeypatch):
    from api.routes import files as api_files

    monkeypatch.setattr(api_files, "get_workspace", lambda: tmp_path)

    # Create a mock Python file with clear function boundaries
    source_code = (
        "def hello_world():\n"
        "    x = 10\n"
        "    y = 20\n"
        "    return x + y\n"
        "\n"
        "class TestClass:\n"
        "    def method_one(self):\n"
        "        pass\n"
    )

    file_path = tmp_path / "mock_app.py"
    file_path.write_text(source_code, encoding="utf-8")

    # Cursor inside hello_world (line 3, column 5)
    start, end = get_ast_bounds(file_path, line=3, column=5)
    assert start == 1
    assert end == 4

    # Cursor inside method_one (line 7, column 9)
    start_method, end_method = get_ast_bounds(file_path, line=7, column=9)
    assert start_method == 7
    assert end_method == 8

    # Cursor inside TestClass class body but outside method_one (line 6, column 1)
    start_class, end_class = get_ast_bounds(file_path, line=6, column=1)
    assert start_class == 6
    assert end_class == 8
