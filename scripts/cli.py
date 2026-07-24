#!/usr/bin/env python3
"""Unified CLI for nichecraft. Delegates to scripts/preflight.sh."""
import subprocess
import sys
import os


def main() -> None:
    """Entry point."""
    script = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'preflight.sh')
    result = subprocess.run(['bash', script] + sys.argv[1:])
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
