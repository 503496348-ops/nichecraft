---
name: nichecraft
version: 2.1.0
description: >
  有点东西（Nichecraft）— 飞书白板设计系统 + AI原生PPTX生成引擎 + HTML演示生成器。
  35种配色方案 + 任意文档→SVG→原生PPTX全链路 + Markdown→单文件HTML演示。
  飞书白板渲染 + 源文档转换 + DrawingML导出 + 动画定制 + 旁白音频 + 图片生成 + 杂志风/瑞士风HTML演示。
author: AtomCollide-智械工坊团队
license: MIT
tags: [feishu, whiteboard, design-system, svg, pptx, html, presentation, infographic, visual, lark, 飞书, 白板, PPT, HTML, 设计]
requires_tools: [terminal, read_file, write_file]
requires_toolsets: [terminal, file]
---

# 有点东西 · Nichecraft 2.1 — 飞书白板设计 + AI原生PPTX引擎 + HTML演示生成器

> 35种配色方案 + 任意文档→SVG→原生PPTX全链路 + Markdown→HTML演示

Nichecraft 是一套覆盖视觉设计全链路的工具系统，包含两大部分：

- **Part A** — 飞书白板设计系统：35种精心设计的配色方案 + 画布渲染能力
- **Part B** — AI原生PPTX生成引擎：任意源文档 → Markdown → SVG → 原生DrawingML PPTX
- **Part C** — HTML演示生成器：Markdown → 单文件HTML演示（杂志风/瑞士风，WebGL背景，零依赖）

---

## Part A: 飞书白板设计系统

Nichecraft 原创的白板设计体系，提供 35 种经过精心调配的配色方案，每种方案包含完整的色彩系统、字体建议、排版规则和布局模板。

### 配色方案一览

完整的方案列表与预览请参见 `CATALOG.md`。包括：soft-editorial、cobalt-bloom、riso-brut、pin-and-paper、grove-block、papier-bleu、court-press、crayon-stack、block-frame、avocado-press、reading-room、grove、monochrome、raw-grid、mint-brut、long-table 等 35 种。

### 核心规则

白板设计的所有规范和约束定义在 `RULES.md` 中，包括：

- 色彩使用规则（主色/辅色/强调色配比）
- 排版层级规范
- 元素间距与对齐标准
- 飞书白板渲染限制与兼容性

### 画布状态管理

`scripts/canvas_state.py` 提供画布状态的序列化与恢复，支持跨会话持续设计。

---

## Part B: AI原生PPTX生成引擎

从任意源文档出发，经过 Markdown 中间态，生成 SVG 信息图，最终导出为原生 DrawingML PPTX 演示文稿。

### 核心能力

| 能力 | 说明 | 关键文件 |
|------|------|----------|
| 源文档转换 | PDF/DOC/DOCX/Excel/PPT/Web/EPUB → Markdown | `scripts/source_to_md/` |
| SVG → PPTX | 原生 DrawingML 导出，非图片嵌入 | `scripts/svg_to_pptx/` |
| 旁白音频 | 演讲者备注 → 多后端 TTS 语音 | `scripts/notes_to_audio.py` |
| 动画定制 | 对象级入场/强调/退出动画 | `scripts/pptx_animations.py`、`scripts/animation_config.py` |
| 图片生成 | 15 种 AI 图片后端（Gemini、OpenAI等） | `scripts/image_gen.py` |
| 图片搜索 | Pexels / Pixabay / Wikimedia / OpenVerse | `scripts/image_sources/` |
| TTS 后端 | Edge / ElevenLabs / CosyVoice / MiniMax / Qwen | `scripts/tts_backends/` |
| 模板填充 | Markdown 内容注入 SVG 模板 → PPTX | `scripts/template_fill_pptx.py` |
| 质量检查 | SVG 结构验证、标注检查、批量校验 | `scripts/svg_quality_checker.py`、`scripts/batch_validate.py` |
| SVG 编辑器 | 本地 Web 编辑器，可视化标注 SVG 元素 | `scripts/svg_editor/` |
| 确认界面 | 执行前预览确认 UI | `scripts/confirm_ui/` |
| 项目管理 | 多项目目录管理、状态持久化 | `scripts/project_manager.py` |

### 源文档转换详情

| 格式 | 转换器 | 依赖 |
|------|--------|------|
| PDF | `scripts/source_to_md/pdf_to_md.py` | PyMuPDF |
| DOCX | `scripts/source_to_md/doc_to_md.py` | mammoth |
| Excel | `scripts/source_to_md/excel_to_md.py` | openpyxl |
| PPT | `scripts/source_to_md/ppt_to_md.py` | python-pptx |
| Web | `scripts/source_to_md/web_to_md.py` | requests + beautifulsoup4 |
| EPUB/HTML | 同上 | markdownify + ebooklib |

---


---

## Part C: HTML演示生成器（v2.1 新增）

从 Markdown 内容直接生成**单文件 HTML** 横向翻页演示文稿，零依赖、零构建工具。

### 两种视觉风格

| 风格 | 特点 | 适用场景 | 模板 |
|------|------|---------|------|
| **杂志风 (magazine)** | 衬线标题 + WebGL流体背景 + 暖色 | 人文分享、行业观察、商业发布 | `assets/html_templates/template-magazine.html` |
| **瑞士风 (swiss)** | 无衬线 + 网格点阵 + IKB高亮 | 科技产品、数据汇报、工程分享 | `assets/html_templates/template-swiss.html` |

### 主题色

**杂志风**：ink(墨水经典)、sepia(复古暖棕)、navy(深海藏蓝)、forest(森林墨绿)、rose(玫瑰灰)

**瑞士风**：ikb(克莱因蓝)、lemon(柠檬黄)、lime(柠檬绿)、safety(安全橙)

### 使用方式

```python
from scripts.html_deck.engine import markdown_to_html_deck

html = markdown_to_html_deck(
    md_text=open('slides.md').read(),
    title='我的演示',
    style='magazine',   # 或 'swiss'
    theme='ink',        # 可选
    output_path='output.html'
)
```

**CLI**：
```bash
python3 scripts/html_deck/engine.py slides.md -o output.html -t "演示标题" -s magazine --theme ink
python3 scripts/html_deck/engine.py --list-themes
```

### Markdown 分页规则

- `---`（水平线）→ 强制分页
- `## 标题`（二级标题）→ 新幻灯片
- 第一页自动识别为 Hero 封面页

### 布局自动推断

引擎根据内容自动选择布局：
- 有图片+列表 → 图文混排
- 有表格 → 表格布局
- 列表项 > 6 → 卡片网格
- 引用块 → 居中引用
- 无标题短文本 → Hero 封面

### 融合来源

HTML演示引擎提供多种模板系统和设计参考。

## 快速参考

| 场景 | 命令 / 操作 |
|------|-------------|
| 查看所有配色方案 | 阅读 `CATALOG.md` |
| 查看设计规则 | 阅读 `RULES.md` |
| 预检环境依赖 | `bash scripts/preflight.sh` |
| PDF → Markdown | `python3 scripts/source_to_md/pdf_to_md.py input.pdf` |
| Web → Markdown | `python3 scripts/source_to_md/web_to_md.py https://...` |
| SVG → PPTX | `python3 scripts/svg_to_pptx/pptx_cli.py slide.svg` |
| 批量 SVG → PPTX | `python3 scripts/svg_to_pptx/pptx_cli.py *.svg -o deck.pptx` |
| Markdown → 模板填充 | `python3 scripts/template_fill_pptx.py spec.md` |
| 生成旁白音频 | `python3 scripts/notes_to_audio.py deck.pptx` |
| AI 生成图片 | `python3 scripts/image_gen.py --prompt "..."` |
| 质量检查 | `python3 scripts/batch_validate.py output/` |
| 动画配置 | 阅读 `workflows/customize-animations.md` |
| 模板填充工作流 | 阅读 `workflows/template-fill-pptx.md` |

---

## 操作流程

### 流程一：飞书白板设计

1. 阅读 `CATALOG.md` 选择配色方案
2. 阅读对应方案的 `templates/<name>/design.md` 获取设计规范
3. 按 `RULES.md` 中的规则在飞书白板中实施设计
4. 使用 `scripts/canvas_state.py` 保存/恢复画布状态

### 流程二：文档 → PPTX 生成

1. **源文档转换**：使用 `scripts/source_to_md/` 将源文件转为 Markdown
2. **内容规划**：拆分 Markdown 为幻灯片结构（`scripts/total_md_split.py`）
3. **模板选择**：从 `templates/` 中选择配色方案与布局
4. **SVG 生成**：按模板规范生成各页 SVG 信息图
5. **图片处理**：使用 `scripts/image_gen.py` 或 `scripts/image_search.py` 获取配图
6. **SVG 定稿**：通过 `scripts/finalize_svg.py` 和 `scripts/svg_finalize/` 处理嵌入与优化
7. **PPTX 导出**：`scripts/svg_to_pptx/pptx_cli.py` 将 SVG 转为原生 DrawingML PPTX
8. **动画定制**：`scripts/pptx_animations.py` 添加对象级动画效果
9. **旁白生成**：`scripts/notes_to_audio.py` 将备注转为语音旁白
10. **质量验收**：`scripts/batch_validate.py` + `scripts/visual_review.py` 最终检查

---

## 文件结构参考

```
scripts/
├── source_to_md/          # 源文档转换（PDF/DOC/Excel/PPT/Web）
├── svg_to_pptx/           # SVG → 原生 DrawingML PPTX 导出引擎
├── svg_finalize/          # SVG 定稿工具链（嵌入图片/图标/路径转换）
├── svg_editor/            # 本地 Web SVG 编辑器
├── image_sources/         # 图片搜索多后端
├── tts_backends/          # TTS 语音合成多后端
├── confirm_ui/            # 执行前确认界面
├── template_import/       # 模板导入工具
├── canvas_state.py        # 画布状态管理
├── preflight.sh           # 环境预检
├── template_fill_pptx.py  # 模板填充 → PPTX
├── notes_to_audio.py      # 备注 → 音频旁白
├── image_gen.py           # AI 图片生成
├── pptx_animations.py     # PPTX 动画配置
└── ...

references/                # 设计规范与架构文档
workflows/                 # 端到端工作流指南
templates/                 # 配色方案 + 布局模板
CATALOG.md                 # 配色方案目录
RULES.md                   # 白板设计规则
```

---

## 安装依赖

```bash
bash scripts/preflight.sh          # 检查环境
pip install -r requirements.txt    # 安装 Python 依赖
```

部分功能（如 pandoc 转换 .doc/.rtf）需要系统级安装，详见 `requirements.txt` 注释。

---

## 许可证

MIT License · AtomCollide-智械工坊团队
