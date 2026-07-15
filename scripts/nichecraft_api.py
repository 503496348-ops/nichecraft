#!/usr/bin/env python3
"""Optional FastAPI service for Nichecraft diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from typing import Any

from nichecraft_history_store import latest_runs, save_run
from anti_ai_style_guard import collect_style_guard_report
from doctor import ROOT

try:
    from fastapi import FastAPI
except Exception:
    FastAPI = None  # type: ignore


def _run_doctor() -> tuple[bool, list[dict[str, Any]]]:
    cp = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'doctor.py'), '--format', 'json'],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if cp.returncode == 0:
        try:
            payload = json.loads(cp.stdout)
            checks = payload.get('checks', []) if isinstance(payload, dict) else []
            return bool(payload.get('passed', False)), checks
        except Exception:
            pass
    return False, [
        {
            'name': 'doctor command',
            'ok': False,
            'fix': (cp.stderr or cp.stdout).strip()[:300] or 'doctor 检查执行失败',
        }
    ]


def _run_bridge_check() -> tuple[bool, dict[str, Any]]:
    script = ROOT / 'scripts' / 'excalidraw_bridge.py'
    if not script.exists():
        return False, {'error': 'excalidraw_bridge.py not found'}

    cp = subprocess.run(
        [
            sys.executable,
            str(script),
            '--mode',
            'flow',
            '--sample',
            '--compact',
        ],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=ROOT,
    )
    ok = cp.returncode == 0 and bool(cp.stdout.strip())
    payload = {
        'command': 'python3 scripts/excalidraw_bridge.py --mode flow --sample --compact',
        'output_preview': (cp.stdout[:500] if cp.stdout else ''),
        'stderr': (cp.stderr[:500] if cp.stderr else ''),
    }
    return ok, payload


def create_app() -> FastAPI:
    if FastAPI is None:
        raise RuntimeError('请先安装 fastapi 与 uvicorn（pip install fastapi uvicorn）')

    app = FastAPI(title='nichecraft api', version='0.1.0')

    @app.get('/health')
    def health() -> dict[str, str]:
        return {'status': 'ok', 'service': 'nichecraft'}

    @app.get('/diag')
    def diag() -> dict[str, Any]:
        from doctor import collect_run_report
        return collect_run_report(ROOT)

    @app.get('/diag/style')
    def diag_style() -> dict[str, object]:
        return collect_style_guard_report(ROOT)

    @app.get('/diag/excalidraw')
    def diag_excalidraw() -> dict[str, Any]:
        passed, payload = _run_bridge_check()
        return {
            'provider': 'nichecraft',
            'passed': passed,
            **payload,
        }

    @app.get('/diag/latest')
    def diag_latest(limit: int = 10) -> list[dict[str, Any]]:
        return latest_runs(limit=limit)

    @app.post('/diag/run')
    def diag_run() -> dict[str, Any]:
        passed, checks = _run_doctor()
        raw = str(checks)
        run_id = hashlib.sha1((str(len(checks)) + raw).encode()).hexdigest()[:16]
        save_run(run_id=run_id, checks=checks, passed=passed)
        return {
            'run_id': run_id,
            'passed': passed,
            'checks': checks,
            'checks_total': len(checks),
            'failed_checks': len([c for c in checks if not c.get('ok')]),
        }

    return app


def main() -> int:
    if FastAPI is None:
        raise RuntimeError('请先安装 fastapi 与 uvicorn（pip install fastapi uvicorn）')
    parser = argparse.ArgumentParser(description='Nichecraft API')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8761)
    args = parser.parse_args()

    import uvicorn
    uvicorn.run(create_app(), host=args.host, port=args.port)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
