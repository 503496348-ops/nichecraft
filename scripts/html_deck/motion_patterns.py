"""Intent-driven motion profiles for Nichecraft HTML decks.

The module keeps presentation motion deliberate and bounded. It recommends a
small interaction profile from slide structure, then exposes declarative data
attributes for the existing HTML runtime. No third-party component source or
runtime dependency is required.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping


@dataclass(frozen=True)
class MotionProfile:
    name: str
    entrance: str
    emphasis: str
    budget: str
    fallback: str = "static"
    max_animated_elements: int = 8

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_PROFILES: dict[str, MotionProfile] = {
    "quiet": MotionProfile("quiet", "fade", "none", "low", max_animated_elements=4),
    "editorial": MotionProfile("editorial", "cascade", "focus", "medium", max_animated_elements=8),
    "data": MotionProfile("data", "count", "highlight", "medium", max_animated_elements=10),
    "gallery": MotionProfile("gallery", "reveal", "depth", "medium", max_animated_elements=6),
    "hero": MotionProfile("hero", "hero", "spotlight", "high", max_animated_elements=5),
}


def recommend_motion(slide: Mapping[str, object], index: int = 0) -> MotionProfile:
    """Select a motion profile from a parsed slide without inspecting raw HTML."""
    layout = str(slide.get("layout", "text"))
    body = str(slide.get("body", ""))
    is_hero = bool(slide.get("is_hero", False))

    if index == 0:
        return _PROFILES["hero"]
    if is_hero:
        return _PROFILES["editorial"]
    if layout == "table" or any(marker in body for marker in ("%", "同比", "环比", "KPI")):
        return _PROFILES["data"]
    if layout in {"img-hero", "img-text"}:
        return _PROFILES["gallery"]
    if layout in {"quote", "grid-list"}:
        return _PROFILES["editorial"]
    return _PROFILES["quiet"]


def motion_attributes(profile: MotionProfile) -> str:
    """Render stable data attributes consumed by the deck runtime and QA tools."""
    return (
        f'data-motion-profile="{profile.name}" '
        f'data-motion-budget="{profile.budget}" '
        f'data-motion-fallback="{profile.fallback}" '
        f'data-motion-max-elements="{profile.max_animated_elements}"'
    )


def animation_value(profile: MotionProfile) -> str:
    """Map a profile to the existing data-anim vocabulary."""
    return {
        "fade": "cascade",
        "cascade": "cascade",
        "count": "cascade",
        "reveal": "left",
        "hero": "cascade",
    }[profile.entrance]


def validate_motion_plan(profiles: list[MotionProfile]) -> list[str]:
    """Return warnings for decks that exceed motion and accessibility budgets."""
    warnings: list[str] = []
    high_count = sum(profile.budget == "high" for profile in profiles)
    if high_count > 2:
        warnings.append("high_motion_budget_exceeded")
    if any(profile.fallback != "static" for profile in profiles):
        warnings.append("static_fallback_required")
    if any(profile.max_animated_elements > 12 for profile in profiles):
        warnings.append("per_slide_element_budget_exceeded")
    return warnings
