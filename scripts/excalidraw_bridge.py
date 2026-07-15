#!/usr/bin/env python3
"""Minimal Excalidraw bridge CLI for Nichecraft.

Expose a small, deterministic public interface for creating .excalidraw 场景文件 from
常见结构化输入（流程图 / 表格 / 思维导图），并兼容 Nichecraft 的 doctor/API 验证链路。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.excalidraw_bridge.excalidraw_adapter import ExcalidrawBridge


def _load_input(payload: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    for key in ("nodes", "edges", "headers", "rows", "root", "branches", "layout", "output"):
        if key in payload:
            fallback[key] = payload[key]
    return fallback


def _build_default_flow_payload() -> dict[str, Any]:
    return {
        "mode": "flow",
        "nodes": [
            {"id": "start", "label": "开始", "shape": "ellipse"},
            {"id": "analyze", "label": "分析需求", "shape": "rectangle"},
            {"id": "draw", "label": "生成白板", "shape": "rectangle"},
            {"id": "review", "label": "导出复核", "shape": "diamond"},
            {"id": "done", "label": "完成", "shape": "rounded_rect"},
        ],
        "edges": [
            {"from": "start", "to": "analyze"},
            {"from": "analyze", "to": "draw"},
            {"from": "draw", "to": "review"},
            {"from": "review", "to": "done"},
        ],
        "layout": "vertical",
    }


def _build_default_table_payload() -> dict[str, Any]:
    return {
        "mode": "table",
        "title": "Nichecraft 组件映射",
        "headers": ["能力", "来源", "用途"],
        "rows": [
            ["流程图", "流程抽象层", "结构化图表落盘"],
            ["思维导图", "知识图谱", "头脑风暴白板化"],
            ["SVG 导出", "图形管线", "PPT/HTML 前置资产"],
        ],
    }


def _build_default_mindmap_payload() -> dict[str, Any]:
    return {
        "mode": "mindmap",
        "root": "Nichecraft",
        "branches": {
            "设计": ["配色", "布局", "组件"],
            "渲染": ["SVG", "PPTX", "HTML"],
            "协作": ["导出", "复用", "交付"],
        },
    }


def _load_payload(mode: str, input_path: Path | None, payload_text: str | None) -> dict[str, Any]:
    payload = {
        "mode": mode,
        "title": "nichecraft excalidraw sample",
    }
    if payload_text:
        data = json.loads(payload_text)
        return _load_input(data, payload)
    if input_path:
        data = json.loads(input_path.read_text(encoding="utf-8"))
        return _load_input(data, payload)

    if mode == "flow":
        return _build_default_flow_payload()
    if mode == "table":
        return _build_default_table_payload()
    if mode == "mindmap":
        return _build_default_mindmap_payload()
    raise ValueError(f"unsupported mode: {mode}")


def _to_excalidraw(payload: dict[str, Any]) -> dict[str, Any]:
    mode = payload.get("mode", "flow")
    bridge = ExcalidrawBridge(hand_drawn=True)

    if mode == "flow":
        scene = bridge.flowchart_to_scene(
            nodes=payload.get("nodes", []),
            edges=payload.get("edges", []),
            layout=payload.get("layout", "vertical"),
        )
    elif mode == "table":
        scene = bridge.table_to_scene(
            headers=payload.get("headers", []),
            rows=payload.get("rows", []),
            title=payload.get("title", ""),
        )
    elif mode == "mindmap":
        scene = bridge.mindmap_to_scene(
            root=payload.get("root", "Root"),
            branches=payload.get("branches", {}),
        )
    else:
        raise ValueError(f"unsupported mode: {mode}")

    return json.loads(scene.to_json(indent=None))


def run_once(mode: str, input_path: Path | None, payload_text: str | None, output: str | None, compact: bool) -> None:
    payload = _load_payload(mode, input_path, payload_text)
    doc = _to_excalidraw(payload)

    if not compact:
        printed = json.dumps(doc, ensure_ascii=False, indent=2)
    else:
        printed = json.dumps(doc, ensure_ascii=False)

    if output:
        out_path = Path(output)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        out_path.write_text(printed, encoding="utf-8")
        print(f"excalidraw saved: {out_path}")
    else:
        print(printed)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nichecraft Excalidraw bridge")
    parser.add_argument("--mode", choices=["flow", "table", "mindmap"], default="flow", help="bridge 场景类型")
    parser.add_argument("--input", type=Path, help="输入 JSON 文件（含 mode-specific payload）")
    parser.add_argument("--json", dest="payload", help="内联 JSON payload")
    parser.add_argument("--output", help="输出 .excalidraw 文件路径（缺省输出到 stdout）")
    parser.add_argument("--compact", action="store_true", help="输出紧凑 JSON")
    parser.add_argument("--sample", action="store_true", help="忽略输入并使用 mode 对应的内置样例")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    input_path = None if args.sample else args.input
    if args.input and not args.sample and not args.input.exists():
        raise FileNotFoundError(f"输入文件不存在: {args.input}")

    run_once(
        mode=args.mode,
        input_path=input_path,
        payload_text=args.payload,
        output=args.output,
        compact=args.compact,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
