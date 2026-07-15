---
name: nichecraft
version: 2.4.0
description: "飞书白板设计系统 + AI原生PPTX引擎 + HTML演示生成器。当需要创建白板、生成PPT、制作演示文稿时使用。"
author: AtomCollide-智械工坊团队
license: MIT
tags: [feishu, whiteboard, design-system, svg, pptx, html, presentation, 飞书, 白板, PPT, HTML]
requires_tools: [terminal, read_file, write_file]
requires_toolsets: [terminal, file]

triggers:
  - PPT生成
  - 白板设计
  - 演示文稿
  - nichecraft
  - 有点东西
---

# 有点东西 · Nichecraft 2.4

## HTML Deck 交互动效策略（v2.4.0）

新增 `scripts/html_deck/motion_patterns.py`，根据封面、数据表、图片、引用和正文等页面意图自动选择动效 profile，并把性能预算、静态降级和单页动效元素上限写入 HTML section。生成结果默认兼容 `prefers-reduced-motion` 与低性能模式，避免为了视觉效果牺牲可读性和移动端稳定性。

## Canvas Interaction Guard（v2.3.0）

新增 `scripts/canvas_interaction_guard.py`：为白板/PPT 画布提供视口锁定、只读态防误操作、工具栏拖拽防护与分组钻取可见性控制，降低编辑态误触和审阅态破坏风险。

> 35种配色方案 + 任意文档→SVG→原生PPTX + Markdown→HTML演示

## 核心能力

- **白板设计系统**：35种配色方案 + 画布状态管理 + 飞书原生集成
- **源文档转换**：PDF/DOC/DOCX/Excel/PPT/Web/EPUB → Markdown
- **SVG→PPTX**：原生DrawingML导出（非图片嵌入）+ 动画定制
- **HTML演示**：Markdown→单文件HTML（杂志风/瑞士风，WebGL背景，零依赖）
- **TTS旁白**：Edge/ElevenLabs/CosyVoice/MiniMax/Qwen 多后端
- **图片生成**：15种AI后端 + Pexels/Pixabay/Wikimedia搜索
- **Excalidraw 融合能力**：新增 `scripts/excalidraw_bridge.py`，支持流程图/表格/思维导图导出为 `.excalidraw`，可直接用于白板协作链路

## 操作流程

### 流程一：飞书白板设计

1. 阅读 `CATALOG.md` 选择配色方案
2. 按 `RULES.md` 规则在飞书白板中实施
3. 使用 `scripts/canvas_state.py` 保存/恢复状态

### 流程二：文档→PPTX

1. `scripts/source_to_md/` 转为 Markdown
2. `scripts/total_md_split.py` 拆分为幻灯片结构
3. 从 `templates/` 选择配色方案
4. 生成各页 SVG 信息图
5. `scripts/svg_to_pptx/pptx_cli.py` 导出原生PPTX
6. `scripts/pptx_animations.py` 添加动画
7. `scripts/notes_to_audio.py` 生成旁白音频
8. `scripts/batch_validate.py` 质量验收

### 流程三：Markdown→HTML演示

```python
from scripts.html_deck.engine import markdown_to_html_deck
html = markdown_to_html_deck(md_text=open('slides.md').read(),
    title='演示', style='magazine', theme='ink', output_path='output.html')
```

## 快速参考

| 场景 | 命令 |
|------|------|
| 查看配色方案 | `CATALOG.md` |
| PDF→MD | `python3 scripts/source_to_md/pdf_to_md.py input.pdf` |
| SVG→PPTX | `python3 scripts/svg_to_pptx/pptx_cli.py slide.svg` |
| HTML演示 | `python3 scripts/html_deck/engine.py slides.md -o out.html` |
| 旁白音频 | `python3 scripts/notes_to_audio.py deck.pptx` |
| 质量检查 | `python3 scripts/batch_validate.py output/` |

## 文件结构

```
scripts/
├── source_to_md/      # 源文档转换
├── svg_to_pptx/       # SVG→PPTX导出引擎
├── html_deck/         # HTML演示生成器
├── svg_finalize/      # SVG定稿工具链
├── tts_backends/      # TTS多后端
├── canvas_state.py    # 画布状态管理
├── template_fill_pptx.py
├── notes_to_audio.py
├── image_gen.py
└── pptx_animations.py
```

## 安装依赖

```bash
bash scripts/preflight.sh
pip install -r requirements.txt
```

MIT License · AtomCollide-智械工坊团队
## 2026-07-02 融合增强

- 有点东西新增可编辑 PPTX 四层资产契约：背景/框架/图标/文本分层 manifest、bbox 对齐校验、占位符文本门禁和 QA 汇总。

## 2026-07-03 产品收敛门禁

- 新增 `scripts/product_convergence_gate.py`：从远端干净 clone 后可运行 `python3 scripts/product_convergence_gate.py --json`，检查 SKILL/README、入口文件、smoke 目标、测试与外部融合引用是否自洽。
- 新增 `tests/test_product_convergence_gate.py`：确保门禁在产品仓库中真实可执行，避免后续增强只停留在孤岛模块。

## 一键开箱交付

本仓库提供标准一键入口：

- `install.sh`：用户的一条命令安装与冒烟入口。
- `scripts/setup.py`：安装声明依赖并串联 doctor。
- `scripts/doctor.py`：检查 README、SKILL、入口脚本、package scripts 与产品收敛门禁。
- `scripts/smoke.py`：运行 doctor、产品收敛门禁与 Python 编译级冒烟。
- `tests/test_one_click_open_box.py`：契约测试，防止 README 写了但脚本缺失。
