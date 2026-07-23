#!/usr/bin/env python3
"""Wave-7 Hallmark PoC bridge for style-rule enrichment.

This PoC aggregates local hallmark reference snippets and reports hit counts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HAL_MARK_REPO_CANDIDATES = [
    Path(__file__).resolve().parents[1] / 'vendor' / 'hallmark',
    Path(__file__).resolve().parents[1] / 'references' / 'hallmark',
    Path.cwd() / 'hallmark',
    Path.home() / '.hermes' / 'skills' / 'hallmark',
]


def resolve_hallmark_repo() -> Path:
    env = __import__('os').environ.get('HALLMARK_REPO')
    if env:
        p = Path(env).expanduser()
        if p.exists():
            return p
    for p in HAL_MARK_REPO_CANDIDATES:
        if p.exists():
            return p
    return HAL_MARK_REPO_CANDIDATES[-1]


HAL_MARK_REPO = resolve_hallmark_repo()



def load_rules() -> dict:
    files = []
    for p in [HAL_MARK_REPO / 'references', HAL_MARK_REPO]:
        if p.exists():
            files.extend(sorted(p.glob('**/*.md')))
    if not files:
        return {
            'anti_patterns': [],
            'structure_rules': [],
            'microinteractions': [],
            'motion': [],
            'responsive': [],
        }

    anti_patterns = []
    structure_rules = []
    micro = []
    motion = []
    responsive = []

    for f in files:
        txt = f.read_text(encoding='utf-8', errors='ignore').lower()
        if 'anti-pattern' in txt or '反模式' in txt:
            anti_patterns.append(str(f.relative_to(HAL_MARK_REPO)))
        if 'structure' in txt or '结构' in txt:
            structure_rules.append(str(f.relative_to(HAL_MARK_REPO)))
        if 'micro' in txt or '微交互' in txt or 'microinteraction' in txt:
            micro.append(str(f.relative_to(HAL_MARK_REPO)))
        if 'motion' in txt or '节奏' in txt:
            motion.append(str(f.relative_to(HAL_MARK_REPO)))
        if 'responsive' in txt or '响应' in txt or '移动端' in txt:
            responsive.append(str(f.relative_to(HAL_MARK_REPO)))

    return {
        'anti_patterns': sorted(set(anti_patterns)),
        'structure_rules': sorted(set(structure_rules)),
        'microinteractions': sorted(set(micro)),
        'motion': sorted(set(motion)),
        'responsive': sorted(set(responsive)),
    }


def run_smoke() -> int:
    rules = load_rules()
    out = {
        'status': 'ok',
        'repo': 'nichecraft',
        'hallmark_rules_found': any(v for v in rules.values()),
        'counts': {k: len(v) for k, v in rules.items()},
        'hits': rules,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description='Hallmark PoC bridge')
    p.add_argument('--smoke', action='store_true')
    p.add_argument('--repo', default=str(Path.cwd()))
    p.add_argument('--sample', default='')
    ns = p.parse_args()
    if ns.smoke:
        return run_smoke()
    rules = load_rules()
    print(json.dumps({'status': 'ok', 'repo': Path(ns.repo).name, 'counts': {k: len(v) for k, v in rules.items()}}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
