#!/usr/bin/env python3
"""Content-style anti-AI slop static guard for nichecraft outputs/inputs."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 简单但稳定的规则：对“可疑 AI 痕迹”做静态扫描，不阻塞关键业务流程
SLUR = {
    "emoji_overuse": {
        "desc": "文本中 emoji 过密（可能偏机器默认语气）",
        "pattern": re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]"),
        "limit": 20,
    },
    "flat_gradient": {
        "desc": "过多单色/大面积渐变表达（需评估是否缺少层次）",
        "pattern": re.compile(r"linear-gradient\(|radial-gradient", re.IGNORECASE),
        "limit": 18,
    },
    "all_caps_blocks": {
        "desc": "过量全大写词（常见“AI风格口号化”表达）",
        "pattern": re.compile(r"\b[A-Z]{5,}\b"),
        "limit": 14,
    },
}

TARGET_FILES = [
    "references/QUICKSTART.md",
    "references/visual-review.md",
    "references/anti-ai-slop.md",
    "CHANGELOG.md",
    "README.md",
]


def _scan_text(text: str, rule: dict) -> int:
    return len(rule["pattern"].findall(text or ""))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def collect_style_guard_report(root: Path | None = None) -> dict:
    root = root or ROOT
    checks = []
    all_ok = True

    for name, rule in SLUR.items():
        count = 0
        sample_hits = []
        for p in sorted(root.glob("**/*")):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".md", ".html", ".css", ".js", ".ts", ".json", ".yml", ".yaml", ".tsx", ".jsx", ".txt"}:
                continue
            rel = str(p.relative_to(root))
            # 只扫描仓库文本与资源引用，避开隐藏和大文件
            if any(seg.startswith('.') for seg in p.parts) and '/.' not in rel:
                continue
            txt = _read_text(p)
            c = _scan_text(txt, rule)
            if c:
                count += c
                if len(sample_hits) < 2:
                    sample_hits.append(rel)

        ok = count <= rule["limit"]
        if not ok:
            all_ok = False
        checks.append({
            "name": rule["desc"],
            "ok": ok,
            "count": count,
            "limit": rule["limit"],
            "sample_files": sample_hits,
            "fix": ("降低风格指纹，结合 jakub/kill-ai-slop 建议做分层配色+排版提效" if not ok else ""),
        })

    # 外部技能文档映射：给出可落地入口
    skill_docs = [root / "references" / "anti-ai-slop.md", root / "references" / "visual-review.md"]
    docs_exist = all(p.exists() for p in [root / "references" / "visual-review.md"])
    checks.append({
        "name": "Anti-AI visual doc",
        "ok": docs_exist,
        "fix": "补齐 visual-review 与反AI风格条目，接入 kill-ai-slop 扫描提示" if not docs_exist else "",
        "sample_files": [str(p.relative_to(root)) for p in skill_docs if p.exists()],
    })

    return {
        "checks": checks,
        "passed": all_ok,
        "found_targets": [str((ROOT / t).relative_to(ROOT)) for t in TARGET_FILES if (ROOT / t).exists()],
    }


if __name__ == '__main__':
    print(collect_style_guard_report())
