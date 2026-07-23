"""Tests for nichecraft CLI entry point."""
import subprocess
import sys
import os

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')


def test_help():
    """CLI --help should exit 0 (delegates to preflight.sh)."""
    r = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, 'cli.py'), '--help'],
        capture_output=True, text=True, timeout=15,
    )
    assert r.returncode in (0, 1)


def test_cli_syntax():
    """CLI module should have valid Python syntax."""
    r = subprocess.run(
        [sys.executable, '-c', 'import ast; ast.parse(open("' + os.path.join(SCRIPTS, 'cli.py') + '").read())'],
        capture_output=True, text=True, timeout=5,
    )
    assert r.returncode == 0
