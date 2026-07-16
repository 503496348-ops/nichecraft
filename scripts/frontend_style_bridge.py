#!/usr/bin/env python3
"""FrontEnd Slides 风格桥接策略工具（轻量）.

目标：将 frontend-slides 的 STYLE_PRESETS/selection-index 策略用于 nichecraft 的
决策面，不做整库导入。
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class FrontendStyleMatch:
    slug: str
    name: str
    score: int
    rationale: list[str]
    metadata: dict[str, Any]


def _load_bridge_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or Path(__file__).resolve().parent.parent / "references" / "frontend-slides-style-bridge.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return payload


def _normalize_token(v: Any) -> str:
    return str(v).strip().lower().replace(" ", "_")


def _token_overlap(a: Iterable[Any], b: Iterable[Any]) -> int:
    seta = {_normalize_token(x) for x in a if str(x).strip()}
    setb = {_normalize_token(x) for x in b if str(x).strip()}
    return len(seta & setb)


def recommend_bold_templates(
    *,
    mood: str | None = None,
    tone: str | None = None,
    formality: str | None = None,
    density: str | None = None,
    avoid_for: list[str] | None = None,
    top_n: int = 4,
    manifest: dict[str, Any] | None = None,
) -> list[FrontendStyleMatch]:
    avoid = {_normalize_token(x) for x in (avoid_for or [])}
    manifest = manifest or _load_bridge_manifest()
    matches: list[FrontendStyleMatch] = []
    for item in manifest.get("bold_pack_overlap_with_nichecraft", []):
        score = 0
        reasons: list[str] = []

        if mood:
            overlap = _token_overlap(item.get("mood", []), [mood])
            if overlap:
                score += overlap * 5
                reasons.append(f"mood match: {mood}")

        if tone:
            # tone often appears in `best_for`/`avoid_for`
            overlap = _token_overlap(item.get("tone", []), [tone])
            score += overlap * 4
            if overlap:
                reasons.append(f"tone match: {tone}")

        for k in ["formality", "density", "scheme"]:
            val = locals().get(k)
            if val:
                bucket = item.get(k, "")
                overlap = _token_overlap([bucket], [val])
                if overlap:
                    score += 4
                    reasons.append(f"{k} match: {val}")

        if item.get("avoid_for"):
            avd = { _normalize_token(x) for x in item.get("avoid_for", []) }
            if avoid & avd:
                score -= 6
                reasons.append("avoid_for conflict")

        if item.get("best_for"):
            if _token_overlap(item.get("best_for", []), [x for x in (tone, mood, formality, density) if x]):
                score += 2

        matches.append(
            FrontendStyleMatch(
                slug=item.get("slug", ""),
                name=item.get("name", ""),
                score=score,
                rationale=reasons,
                metadata={
                    "mood": item.get("mood", []),
                    "best_for": item.get("best_for", []),
                    "avoid_for": item.get("avoid_for", []),
                    "formality": item.get("formality", ""),
                    "density": item.get("density", ""),
                    "scheme": item.get("scheme", ""),
                },
            )
        )

    matches.sort(key=lambda x: (x.score, x.slug), reverse=True)
    return matches[:top_n]


def recommend_safe_presets(*, keywords: str = "", top_n: int = 4, manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    manifest = manifest or _load_bridge_manifest()
    kws = { _normalize_token(x) for x in keywords.split() if x.strip() }
    scored = []
    for preset in manifest.get("safe_style_presets", []):
        fields = [preset.get("title", ""), preset.get("vibe", ""), preset.get("layout", ""), preset.get("signature_elements", "")]
        joined = " ".join(str(x) for x in fields)
        hay = {_normalize_token(w) for w in joined.split()}
        score = len(kws & hay)
        scored.append((score, preset["title"], preset))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [p for _, __, p in scored[:top_n]]


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recommend Frontend-Slides style presets from metadata")
    parser.add_argument("--mood")
    parser.add_argument("--tone")
    parser.add_argument("--formality")
    parser.add_argument("--density")
    parser.add_argument("--avoid", action="append", default=[])
    parser.add_argument("--keywords", default="")
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args(argv)

    manifest = _load_bridge_manifest()
    bold = recommend_bold_templates(
        mood=args.mood,
        tone=args.tone,
        formality=args.formality,
        density=args.density,
        avoid_for=args.avoid,
        top_n=max(1, args.top),
        manifest=manifest,
    )

    safe = recommend_safe_presets(keywords=f"{args.mood or ''} {args.tone or ''} {args.keywords}".strip(), top_n=max(1, args.top), manifest=manifest)

    payload = {
        "safe_candidates": safe,
        "bold_candidates": [
            {
                "slug": m.slug,
                "name": m.name,
                "score": m.score,
                "rationale": m.rationale,
                "metadata": m.metadata,
            }
            for m in bold
        ],
        "policy": manifest.get("selection_policy", {}),
        "stage_policy": manifest.get("stage_policy", {}),
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
