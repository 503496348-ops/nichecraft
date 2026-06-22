# 有点东西 · Nichecraft

> 飞书白板设计系统 + AI原生PPTX生成引擎 + HTML演示生成器

## 三大核心能力

### Part A: 飞书白板设计系统
- 35种精心设计的配色方案
- 色彩系统、字体建议、排版规则、布局模板
- 画布状态管理（跨会话持续设计）

### Part B: AI原生PPTX生成引擎
- 任意源文档 → Markdown → SVG → 原生DrawingML PPTX
- 源文档转换：PDF/DOCX/Excel/PPT/Web/EPUB
- 15种AI图片后端 + 5种TTS引擎
- 对象级动画定制 + 旁白音频生成

### Part C: HTML演示生成器（v2.1 新增）
- Markdown → 单文件HTML横向翻页演示（零依赖）
- 两种风格：杂志风（衬线+WebGL）/ 瑞士风（无衬线+网格+高亮色）
- 9种主题色 + 自动布局推断
- 源自 [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)（歸藏，18.3K⭐）

## 快速开始

```python
# HTML演示
from scripts.html_deck.engine import markdown_to_html_deck
html = markdown_to_html_deck(md_text, title='演示', style='magazine', output_path='output.html')

# PPTX生成
python3 scripts/svg_to_pptx/pptx_cli.py slide.svg
```

## 安装

```bash
pip install mammoth openpyxl python-pptx PyMuPDF requests beautifulsoup4 markdownify
```

## 许可证

MIT © AtomCollide-智械工坊团队
