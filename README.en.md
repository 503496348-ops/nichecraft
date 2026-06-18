# Nichecraft 2.0 — Feishu Whiteboard Design System + AI-Native PPTX Engine

> 35 color schemes · Any document → SVG → native PPTX pipeline

**Nichecraft** (有点东西) is a visual design toolkit that covers the full chain from concept to presentation. It combines a curated whiteboard design system for Feishu/Lark with an AI-native PPTX generation engine.

## Features

- **35 whiteboard color schemes** — carefully crafted palettes with typography rules and layout templates for Feishu whiteboards
- **Source document conversion** — PDF, DOCX, Excel, PPT, Web pages, EPUB → structured Markdown
- **SVG → native DrawingML PPTX** — true native shapes (not image embeds), compatible with all Office versions
- **Speaker notes → audio narration** — multi-backend TTS (Edge, ElevenLabs, CosyVoice, MiniMax, Qwen)
- **Object-level animation** — entrance, emphasis, and exit animations per shape
- **AI image generation** — 15 backends including Gemini, OpenAI, and more
- **Image search** — Pexels, Pixabay, Wikimedia, OpenVerse integration
- **Template fill pipeline** — inject Markdown content into SVG templates → PPTX
- **Quality checking** — SVG validation, annotation checks, batch verification

## Quick Start

```bash
# Check environment
bash scripts/preflight.sh

# Install dependencies
pip install -r requirements.txt

# Convert a PDF to Markdown
python3 scripts/source_to_md/pdf_to_md.py input.pdf

# Convert SVG slides to native PPTX
python3 scripts/svg_to_pptx/pptx_cli.py slide.svg -o deck.pptx

# Generate narration audio from speaker notes
python3 scripts/notes_to_audio.py deck.pptx
```

## Project Structure

```
scripts/
├── source_to_md/       # Document → Markdown converters
├── svg_to_pptx/        # SVG → DrawingML PPTX engine
├── svg_finalize/       # SVG finalization tools
├── svg_editor/         # Local web SVG editor
├── image_sources/      # Multi-backend image search
├── tts_backends/       # Multi-backend TTS
├── confirm_ui/         # Pre-execution confirmation UI
└── ...                 # Animation, quality check, project management
references/             # Design specs and architecture docs
workflows/              # End-to-end workflow guides
templates/              # Color schemes + layout templates
```

## Documentation

- `SKILL.md` — Complete capability reference and procedures
- `CATALOG.md` — All 35 color scheme previews and specifications
- `RULES.md` — Whiteboard design rules and constraints
- `workflows/` — Step-by-step guides for common tasks

## License

MIT License · AtomCollide-智械工坊团队
