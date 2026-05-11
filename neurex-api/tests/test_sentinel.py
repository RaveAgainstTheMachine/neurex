"""
tests/test_sentinel.py
Tests for the Security Sentinel AST analysis.
"""

import pytest

from core.security.sentinel import SecuritySentinel


@pytest.fixture
def sentinel(tmp_path):
    return SecuritySentinel(workspace_path=str(tmp_path))


def test_sentinel_detects_shell_true(sentinel, tmp_path):
    code = "import subprocess\nsubprocess.run('ls -la', shell=True)"
    f = tmp_path / "unsafe.py"
    f.write_text(code)

    issues = sentinel.scan_file("unsafe.py")
    assert len(issues) == 1
    assert issues[0]["type"] == "INSECURE_SUBPROCESS"


def test_sentinel_detects_os_system(sentinel, tmp_path):
    code = "import os\nos.system('rm -rf /')"
    f = tmp_path / "very_unsafe.py"
    f.write_text(code)

    issues = sentinel.scan_file("very_unsafe.py")
    assert len(issues) == 1
    assert issues[0]["type"] == "INSECURE_OS_SYSTEM"


def test_sentinel_detects_eval(sentinel, tmp_path):
    code = 'eval(\'__import__("os").system("ls")\')'
    f = tmp_path / "eval_unsafe.py"
    f.write_text(code)

    issues = sentinel.scan_file("eval_unsafe.py")
    assert len(issues) == 1
    assert issues[0]["type"] == "DYNAMIC_EXECUTION"


def test_sentinel_ignores_safe_code(sentinel, tmp_path):
    code = "import subprocess\nsubprocess.run(['ls', '-la'], shell=False)"
    f = tmp_path / "safe.py"
    f.write_text(code)

    issues = sentinel.scan_file("safe.py")
    assert len(issues) == 0
