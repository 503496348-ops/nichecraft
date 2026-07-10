"""Nichecraft HTML Deck Engine — Markdown to single-file HTML presentation."""

import re
import sys
from pathlib import Path
from typing import Optional

try:
    from .motion_patterns import (
        animation_value,
        motion_attributes,
        recommend_motion,
        validate_motion_plan,
    )
except ImportError:  # Direct execution: python scripts/html_deck/engine.py
    from motion_patterns import (  # type: ignore
        animation_value,
        motion_attributes,
        recommend_motion,
        validate_motion_plan,
    )

# ── Themes ───────────────────────────────────────────────────────────
MAGAZINE_THEMES = {
    "ink": {
        "name": "墨水经典",
        "ink": "#0a0a0b", "ink_rgb": "10,10,11",
        "paper": "#f1efea", "paper_rgb": "241,239,234",
        "paper_tint": "#e8e5de", "ink_tint": "#18181a",
    },
    "sepia": {
        "name": "复古暖棕",
        "ink": "#2c2418", "ink_rgb": "44,36,24",
        "paper": "#f5efe4", "paper_rgb": "245,239,228",
        "paper_tint": "#ebe3d4", "ink_tint": "#3a3024",
    },
    "navy": {
        "name": "深海藏蓝",
        "ink": "#0d1b2a", "ink_rgb": "13,27,42",
        "paper": "#e8ecf1", "paper_rgb": "232,236,241",
        "paper_tint": "#d4dbe6", "ink_tint": "#1b2d44",
    },
    "forest": {
        "name": "森林墨绿",
        "ink": "#1a2e1a", "ink_rgb": "26,46,26",
        "paper": "#eef2ea", "paper_rgb": "238,242,234",
        "paper_tint": "#dde6d5", "ink_tint": "#2a4230",
    },
    "rose": {
        "name": "玫瑰灰",
        "ink": "#2a1a22", "ink_rgb": "42,26,34",
        "paper": "#f5eaef", "paper_rgb": "245,234,239",
        "paper_tint": "#edd8e2", "ink_tint": "#3e2a34",
    },
}

SWISS_THEMES = {
    "ikb": {
        "name": "克莱因蓝",
        "accent": "#002fa7", "accent_name": "IKB",
    },
    "lemon": {
        "name": "柠檬黄",
        "accent": "#f5e642", "accent_name": "Lemon",
    },
    "lime": {
        "name": "柠檬绿",
        "accent": "#b8d432", "accent_name": "Lime",
    },
    "safety": {
        "name": "安全橙",
        "accent": "#ff6b2b", "accent_name": "Safety Orange",
    },
}


# ── Markdown Parser ──────────────────────────────────────────────────

def parse_markdown_slides(md_text: str) -> list[dict]:
    """Split markdown into slide objects.

    Splitting rules:
    1. Lines with only `---` or `***` or `___` (horizontal rules) → slide break
    2. Level-2 headings (`## Title`) → new slide (unless first slide)
    """
    slides = []
    current_lines: list[str] = []
    current_title = ""

    for line in md_text.split("\n"):
        is_hr = re.match(r"^\s*[-*_]{3,}\s*$", line) is not None
        is_h2 = re.match(r"^##\s+(.+)$", line)

        if is_hr and current_lines:
            slides.append(_build_slide(current_title, current_lines))
            current_lines = []
            current_title = ""
        elif is_h2:
            if current_lines:
                slides.append(_build_slide(current_title, current_lines))
                current_lines = []
            current_title = is_h2.group(1).strip()
        else:
            current_lines.append(line)

    if current_lines:
        slides.append(_build_slide(current_title, current_lines))

    return slides


def _build_slide(title: str, lines: list[str]) -> dict:
    body = "\n".join(lines).strip()
    # Detect content type for layout selection
    has_image = bool(re.search(r"!\[.*?\]\(.*?\)", body))
    has_list = bool(re.search(r"^\s*[-*+]\s+", body, re.MULTILINE))
    has_table = bool(re.search(r"^\|.+\|$", body, re.MULTILINE))
    is_quote = bool(re.search(r"^>\s+", body, re.MULTILINE))

    # Pick layout
    if not title and not body:
        layout = "hero"
    elif is_quote and len(body) < 200:
        layout = "quote"
    elif has_image and has_list:
        layout = "img-text"
    elif has_image:
        layout = "img-hero"
    elif has_table:
        layout = "table"
    elif has_list and len(body.split("\n")) > 6:
        layout = "grid-list"
    else:
        layout = "text"

    return {
        "title": title,
        "body": body,
        "layout": layout,
        "is_hero": layout == "hero" or (not title and len(body) < 100),
    }


# ── HTML Slide Renderer ─────────────────────────────────────────────

def render_slide_html(slide: dict, index: int, style: str) -> str:
    """Convert a slide dict to HTML section."""
    is_hero = slide["is_hero"]
    dark = "dark" if (index == 0 or is_hero) else "light"
    hero_cls = " hero" if is_hero else ""
    title = slide["title"]
    body = slide["body"]
    motion = recommend_motion(slide, index)
    section_motion_attrs = motion_attributes(motion)
    anim = animation_value(motion)

    # Convert markdown body to HTML
    body_html = _md_to_html(body)

    if style == "swiss":
        return _render_swiss_slide(
            title, body_html, dark, hero_cls, slide["layout"], index,
            section_motion_attrs, anim,
        )
    return _render_magazine_slide(
        title, body_html, dark, hero_cls, slide["layout"], index,
        section_motion_attrs, anim,
    )


def _render_magazine_slide(
    title: str,
    body_html: str,
    dark: str,
    hero_cls: str,
    layout: str,
    index: int,
    section_motion_attrs: str,
    anim: str,
) -> str:
    chrome = f'<div class="chrome">SLIDE {index + 1:02d}</div>'
    title_html = f'<h1 class="h1-zh" data-anim="{anim}">{title}</h1>' if title else ""

    if layout == "quote":
        content = f'<blockquote class="pull-quote" data-anim>{body_html}</blockquote>'
    elif layout in ("img-hero", "img-text"):
        content = f'{title_html}<div class="frame grid-2-7-5" data-anim>{body_html}</div>'
    elif layout == "grid-list":
        content = f'{title_html}<div class="grid-3-3" data-anim>{_list_to_cards(body_html)}</div>'
    elif layout == "table":
        content = f'{title_html}<div class="frame" data-anim>{body_html}</div>'
    else:
        content = f'{title_html}<div class="frame" data-anim>{body_html}</div>'

    return (
        f'<section class="slide {dark}{hero_cls}" {section_motion_attrs}>\n'
        f'  {chrome}\n'
        f'  {content}\n'
        f'</section>\n'
    )


def _render_swiss_slide(
    title: str,
    body_html: str,
    dark: str,
    hero_cls: str,
    layout: str,
    index: int,
    section_motion_attrs: str,
    anim: str,
) -> str:
    chrome = f'<div class="chrome-min"><span>NICHECRAFT</span><span>{index + 1:02d}</span></div>'
    title_html = f'<h2 class="lead" data-anim="{anim}">{title}</h2>' if title else ""

    if layout == "quote":
        content = f'<div class="canvas-card" data-anim="cascade">{body_html}</div>'
    elif layout == "grid-list":
        items = re.findall(r"<li>(.*?)</li>", body_html, re.DOTALL)
        if items:
            cards = "".join(f'<div class="canvas-card"><p>{item.strip()}</p></div>' for item in items)
            content = f'{title_html}<div class="split-half">{cards}</div>'
        else:
            content = f'{title_html}<div class="canvas-card" data-anim="cascade">{body_html}</div>'
    elif layout == "table":
        content = f'{title_html}<div class="canvas-card" data-anim="cascade">{body_html}</div>'
    else:
        content = f'{title_html}<div class="canvas-card" data-anim="cascade">{body_html}</div>'

    return (
        f'<section class="slide {dark}{hero_cls}" {section_motion_attrs}>\n'
        f'  {chrome}\n'
        f'  {content}\n'
        f'</section>\n'
    )


def _list_to_cards(html: str) -> str:
    """Convert list items to card grid."""
    items = re.findall(r"<li>(.*?)</li>", html, re.DOTALL)
    if not items:
        return html
    cards = []
    for item in items:
        cards.append(f'<div class="card"><p>{item.strip()}</p></div>')
    return "\n".join(cards)


def _md_to_html(md: str) -> str:
    """Minimal markdown → HTML converter."""
    lines = md.strip().split("\n")
    html_lines = []
    in_list = False
    in_table = False

    for line in lines:
        stripped = line.strip()

        # Empty line
        if not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if in_table:
                html_lines.append("</table>")
                in_table = False
            continue

        # Headings
        h_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if h_match:
            level = len(h_match.group(1))
            text = _inline(h_match.group(2))
            html_lines.append(f"<h{level}>{text}</h{level}>")
            continue

        # Blockquote
        if stripped.startswith("> "):
            text = _inline(stripped[2:])
            html_lines.append(f"<blockquote><p>{text}</p></blockquote>")
            continue

        # List items
        list_match = re.match(r"^[-*+]\s+(.+)$", stripped)
        if list_match:
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{_inline(list_match.group(1))}</li>")
            continue

        # Table rows
        if stripped.startswith("|") and stripped.endswith("|"):
            if not in_table:
                html_lines.append("<table>")
                in_table = True
            # Skip separator rows
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            tag = "th" if not in_table else "td"
            row = "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells)
            html_lines.append(f"<tr>{row}</tr>")
            continue

        # Images
        img_match = re.match(r"^!\[(.*?)\]\((.*?)\)$", stripped)
        if img_match:
            html_lines.append(f'<figure class="frame-img"><img src="{img_match.group(2)}" alt="{img_match.group(1)}"><figcaption class="img-cap">{img_match.group(1)}</figcaption></figure>')
            continue

        # Paragraph
        html_lines.append(f"<p>{_inline(stripped)}</p>")

    if in_list:
        html_lines.append("</ul>")
    if in_table:
        html_lines.append("</table>")

    return "\n".join(html_lines)


def _inline(text: str) -> str:
    """Convert inline markdown to HTML."""
    # Bold + italic
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # Code
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # Links
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


# ── Template Assembly ────────────────────────────────────────────────

def get_template_path(style: str) -> Path:
    """Get the HTML template file path."""
    base = Path(__file__).parent.parent.parent / "assets" / "html_templates"
    if style == "swiss":
        return base / "template-swiss.html"
    return base / "template-magazine.html"


def build_html(slides_html: list[str], title: str, style: str, theme: Optional[str] = None) -> str:
    """Assemble final HTML from slide sections."""
    template_path = get_template_path(style)
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template = template_path.read_text(encoding="utf-8")

    # Replace title
    template = template.replace("[必填] 替换为 PPT 标题 · Deck Title", title)

    # Apply theme if specified
    if theme and style == "magazine" and theme in MAGAZINE_THEMES:
        t = MAGAZINE_THEMES[theme]
        template = template.replace("--ink:#0a0a0b;", f"--ink:{t['ink']};")
        template = template.replace("--ink-rgb:10,10,11;", f"--ink-rgb:{t['ink_rgb']};")
        template = template.replace("--paper:#f1efea;", f"--paper:{t['paper']};")
        template = template.replace("--paper-rgb:241,239,234;", f"--paper-rgb:{t['paper_rgb']};")
        template = template.replace("--paper-tint:#e8e5de;", f"--paper-tint:{t['paper_tint']};")
        template = template.replace("--ink-tint:#18181a;", f"--ink-tint:{t['ink_tint']};")

    if theme and style == "swiss" and theme in SWISS_THEMES:
        t = SWISS_THEMES[theme]
        template = template.replace("--accent:#002fa7;", f"--accent:{t['accent']};")

    # Inject slides (handle both template placeholder formats)
    slides_block = "\n\n".join(slides_html)
    if "<!-- SLIDES_HERE -->" in template:
        template = template.replace("<!-- SLIDES_HERE -->", slides_block)
    else:
        # Swiss template uses extended placeholder
        template = re.sub(r"<!-- SLIDES_HERE[^\n]*\n.*?-->", slides_block, template, count=1, flags=re.DOTALL)

    return template


# ── Public API ───────────────────────────────────────────────────────

def markdown_to_html_deck(
    md_text: str,
    title: str = "Presentation",
    style: str = "magazine",
    theme: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    """Convert markdown text to a complete HTML presentation file.

    Args:
        md_text: Markdown content. Split slides with `---` or `## headings`.
        title: Presentation title shown in browser tab.
        style: 'magazine' (editorial serif) or 'swiss' (grid sans-serif).
        theme: Theme name. Magazine: ink/sepia/navy/forest/rose. Swiss: ikb/lemon/lime/safety.
        output_path: If provided, write HTML to this path.

    Returns:
        Complete HTML string.
    """
    slides = parse_markdown_slides(md_text)
    if not slides:
        raise ValueError("No slides found in markdown. Use --- or ## to split slides.")

    motion_profiles = [recommend_motion(slide, index) for index, slide in enumerate(slides)]
    motion_warnings = validate_motion_plan(motion_profiles)
    if motion_warnings:
        raise ValueError(f"Motion plan violates deck budgets: {', '.join(motion_warnings)}")

    slides_html = [render_slide_html(s, i, style) for i, s in enumerate(slides)]
    html = build_html(slides_html, title, style, theme)

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")

    return html


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Nichecraft HTML Deck — Markdown → HTML Presentation")
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("-o", "--output", default="output.html", help="Output HTML file (default: output.html)")
    parser.add_argument("-t", "--title", default="Presentation", help="Presentation title")
    parser.add_argument("-s", "--style", choices=["magazine", "swiss"], default="magazine", help="Visual style")
    parser.add_argument("--theme", help="Theme name (magazine: ink/sepia/navy/forest/rose, swiss: ikb/lemon/lime/safety)")
    parser.add_argument("--list-themes", action="store_true", help="List available themes")

    args = parser.parse_args()

    if args.list_themes:
        print("Magazine themes: ink, sepia, navy, forest, rose")
        print("Swiss themes: ikb, lemon, lime, safety")
        return

    md_text = Path(args.input).read_text(encoding="utf-8")
    html = markdown_to_html_deck(md_text, args.title, args.style, args.theme, args.output)
    print(f"✅ Generated {args.output} ({len(html)} bytes, {args.style} style)")


if __name__ == "__main__":
    main()
