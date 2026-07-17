#!/usr/bin/env python3
"""Excalidraw Import Adapter for Nichecraft.

从外部 .excalidraw 文档提取文本与形状，转为 Nichecraft 可消费的
excalidraw bridge 场景（默认生成流程图）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.excalidraw_bridge.excalidraw_adapter import ExcalidrawBridge


def _extract_labels(payload: Dict[str, Any]) -> List[str]:
    labels: List[str] = []
    for element in payload.get("elements", []):
        if element.get("type") != "text":
            continue
        text = str(element.get("text", "")).strip().replace("\n", " ")
        if text:
            labels.append(text)
    return labels


def _extract_shapes(payload: Dict[str, Any]) -> List[str]:
    # 备用能力：把常见图元映射为语义节点
    mapping = {
        "rectangle": "rect",
        "ellipse": "ellipse",
        "diamond": "diamond",
        "arrow": "arrow",
        "line": "line",
        "text": "text",
    }
    labels: List[str] = []
    for element in payload.get("elements", []):
        if element.get("type") == "text":
            continue
        kind = mapping.get(element.get("type"), "node")
        eid = str(element.get("id", ""))[:6]
        labels.append(f"[{kind}:{eid}]" if eid else f"[{kind}]")
    return labels


def convert_to_flow(payload: Dict[str, Any], title: str) -> Dict[str, Any]:
    labels = []
    txt = _extract_labels(payload)
    if txt:
        labels.extend(txt)
    else:
        labels = _extract_shapes(payload)

    if title:
        labels = [title, *labels]

    if not labels:
        labels = ["excalidraw empty scene"]

    nodes = []
    edges = []
    for i, label in enumerate(labels):
        nodes.append({
            "id": f"n{i}",
            "label": label,
            "shape": "diamond" if i == 0 else "rounded_rect",
        })
        if i:
            edges.append({
                "from": f"n{i - 1}",
                "to": f"n{i}",
            })

    bridge = ExcalidrawBridge(hand_drawn=True)
    scene = bridge.flowchart_to_scene(nodes=nodes, edges=edges)
    return json.loads(scene.to_json(indent=None))


def run_once(input_path: Path, output: Path | None, compact: bool, title: str) -> None:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    doc = convert_to_flow(payload, title=title)
    if output:
        output.write_text(json.dumps(doc, ensure_ascii=False, indent=None if compact else 2), encoding="utf-8")
        print(f"excalidraw scene imported: {output}")
    else:
        print(json.dumps(doc, ensure_ascii=False, indent=None if compact else 2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Import external .excalidraw file into Nichecraft")
    parser.add_argument("--input", required=True, type=Path, help="Path of source .excalidraw")
    parser.add_argument("--output", type=Path, help="Output scene path")
    parser.add_argument("--compact", action="store_true", help="compact JSON output")
    parser.add_argument("--title", default="excalidraw import", help="scene title")
    args = parser.parse_args()

    run_once(
        input_path=args.input,
        output=args.output,
        compact=args.compact,
        title=args.title,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
