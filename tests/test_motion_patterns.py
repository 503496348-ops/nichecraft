from scripts.html_deck.engine import markdown_to_html_deck, parse_markdown_slides
from scripts.html_deck.motion_patterns import (
    MotionProfile,
    animation_value,
    motion_attributes,
    recommend_motion,
    validate_motion_plan,
)


def test_motion_profiles_follow_slide_intent():
    slides = parse_markdown_slides(
        "# Cover\nShort intro\n---\n## Metrics\n| KPI | Value |\n| --- | --- |\n| Growth | 42% |\n---\n## Notes\nPlain explanation"
    )
    assert recommend_motion(slides[0], 0).name == "hero"
    assert recommend_motion(slides[1], 1).name == "data"
    assert recommend_motion(slides[2], 2).name == "quiet"


def test_motion_attributes_always_include_static_fallback():
    profile = recommend_motion({"layout": "img-hero", "body": "", "is_hero": False}, 2)
    attrs = motion_attributes(profile)
    assert 'data-motion-profile="gallery"' in attrs
    assert 'data-motion-fallback="static"' in attrs
    assert animation_value(profile) == "left"


def test_motion_budget_rejects_too_many_high_cost_slides():
    high = MotionProfile("hero", "hero", "spotlight", "high")
    assert validate_motion_plan([high, high]) == []
    assert validate_motion_plan([high, high, high]) == ["high_motion_budget_exceeded"]


def test_html_deck_emits_motion_contract_for_both_styles():
    md = "# Cover\nShort intro\n---\n## Details\n- One\n- Two\n- Three"
    for style in ("magazine", "swiss"):
        html = markdown_to_html_deck(md, title="Motion Test", style=style)
        assert html.count("data-motion-profile=") == 2
        assert 'data-motion-profile="hero"' in html
        assert 'data-motion-fallback="static"' in html
        assert 'data-motion-max-elements=' in html
