"""
Excalidraw Bridge — excalidraw 白板集成适配器
融合自 excalidraw (126K⭐) 的开放格式与嵌入模式。
为「有点东西」提供手绘风格白板导出能力。

集成评估结论：
- excalidraw 的 .excalidraw JSON 格式是开放标准，无需许可
- npm 包 @excalidraw/excalidraw 可嵌入 React 应用（MIT 许可）
- tldraw 生产环境需付费许可，不适合直接集成
- 推荐方案：通过 JSON 格式互操作，不直接依赖前端 SDK
"""

from __future__ import annotations

import json
import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# excalidraw 元素类型
ELEMENT_TYPES = {
    "rectangle", "ellipse", "diamond", "arrow", "line", "text",
    "freedraw", "image", "frame", "embeddable",
}


@dataclass
class ExcalidrawElement:
    """excalidraw 元素"""
    type: str
    x: float
    y: float
    width: float = 100.0
    height: float = 100.0
    stroke_color: str = "#1e1e1e"
    background_color: str = "transparent"
    fill_style: str = "hachure"  # hachure, cross-hatch, solid
    stroke_width: int = 1
    roughness: int = 1  # 0=精细, 1=中等, 2=粗糙（手绘感）
    opacity: int = 100
    angle: float = 0.0
    text: str = ""
    font_size: int = 20
    font_family: int = 1  # 1=Virgil(手写), 2=Helvetica, 3=Cascadia
    text_align: str = "left"
    vertical_align: str = "top"
    group_id: Optional[str] = None
    locked: bool = False
    custom_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为 excalidraw JSON 格式"""
        elem = {
            "id": str(uuid.uuid4()),
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "angle": self.angle,
            "strokeColor": self.stroke_color,
            "backgroundColor": self.background_color,
            "fillStyle": self.fill_style,
            "strokeWidth": self.stroke_width,
            "roughness": self.roughness,
            "opacity": self.opacity,
            "groupIds": [self.group_id] if self.group_id else [],
            "locked": self.locked,
            "updated": int(time.time() * 1000),
            "version": 1,
            "versionNonce": int(uuid.uuid4().int % 2**32),
            "isDeleted": False,
            "boundElements": None,
            "link": None,
        }

        if self.type == "text":
            elem["text"] = self.text
            elem["fontSize"] = self.font_size
            elem["fontFamily"] = self.font_family
            elem["textAlign"] = self.text_align
            elem["verticalAlign"] = self.vertical_align
            elem["baseline"] = 0

        if self.type in ("arrow", "line"):
            elem["points"] = [[0, 0], [self.width, self.height]]
            elem["startBinding"] = None
            elem["endBinding"] = None

        return elem


@dataclass
class ExcalidrawScene:
    """excalidraw 场景"""
    elements: List[ExcalidrawElement] = field(default_factory=list)
    app_state: Dict[str, Any] = field(default_factory=dict)
    files: Dict[str, Any] = field(default_factory=dict)

    def add(self, element: ExcalidrawElement) -> "ExcalidrawScene":
        """添加元素"""
        self.elements.append(element)
        return self

    def add_rectangle(self, x: float, y: float, w: float, h: float, **kwargs) -> "ExcalidrawScene":
        """添加矩形"""
        self.elements.append(ExcalidrawElement(type="rectangle", x=x, y=y, width=w, height=h, **kwargs))
        return self

    def add_text(self, x: float, y: float, text: str, font_size: int = 20, **kwargs) -> "ExcalidrawScene":
        """添加文本"""
        self.elements.append(ExcalidrawElement(
            type="text", x=x, y=y, width=len(text) * font_size * 0.6,
            height=font_size * 1.2, text=text, font_size=font_size, **kwargs,
        ))
        return self

    def add_arrow(self, x1: float, y1: float, x2: float, y2: float, **kwargs) -> "ExcalidrawScene":
        """添加箭头"""
        self.elements.append(ExcalidrawElement(
            type="arrow", x=x1, y=y1, width=x2 - x1, height=y2 - y1, **kwargs,
        ))
        return self

    def add_ellipse(self, x: float, y: float, w: float, h: float, **kwargs) -> "ExcalidrawScene":
        """添加椭圆"""
        self.elements.append(ExcalidrawElement(type="ellipse", x=x, y=y, width=w, height=h, **kwargs))
        return self

    def add_diamond(self, x: float, y: float, w: float, h: float, **kwargs) -> "ExcalidrawScene":
        """添加菱形"""
        self.elements.append(ExcalidrawElement(type="diamond", x=x, y=y, width=w, height=h, **kwargs))
        return self

    def to_json(self, indent: int = 2) -> str:
        """导出为 .excalidraw JSON 格式"""
        data = {
            "type": "excalidraw",
            "version": 2,
            "source": "nichecraft-excalidraw-bridge",
            "elements": [e.to_dict() for e in self.elements],
            "appState": {
                "gridSize": None,
                "viewBackgroundColor": "#ffffff",
                **self.app_state,
            },
            "files": self.files,
        }
        return json.dumps(data, indent=indent, ensure_ascii=False)

    def save(self, path: str) -> str:
        """保存为 .excalidraw 文件"""
        content = self.to_json()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"[Excalidraw] Saved {len(self.elements)} elements to {path}")
        return path

    @classmethod
    def load(cls, path: str) -> "ExcalidrawScene":
        """从 .excalidraw 文件加载"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        scene = cls()
        for elem_data in data.get("elements", []):
            scene.elements.append(ExcalidrawElement(
                type=elem_data.get("type", "rectangle"),
                x=elem_data.get("x", 0),
                y=elem_data.get("y", 0),
                width=elem_data.get("width", 100),
                height=elem_data.get("height", 100),
                stroke_color=elem_data.get("strokeColor", "#1e1e1e"),
                background_color=elem_data.get("backgroundColor", "transparent"),
                fill_style=elem_data.get("fillStyle", "hachure"),
                stroke_width=elem_data.get("strokeWidth", 1),
                roughness=elem_data.get("roughness", 1),
                opacity=elem_data.get("opacity", 100),
                text=elem_data.get("text", ""),
                font_size=elem_data.get("fontSize", 20),
                font_family=elem_data.get("fontFamily", 1),
            ))
        return scene

    @property
    def element_count(self) -> int:
        return len(self.elements)

    def clear(self) -> "ExcalidrawScene":
        self.elements.clear()
        return self


class ExcalidrawBridge:
    """
    excalidraw 集成桥。

    能力：
    1. 将结构化数据（表格、流程图、思维导图）转换为 excalidraw 白板
    2. 生成 .excalidraw JSON 文件，可在 excalidraw.com 打开编辑
    3. 手绘风格渲染（roughness=2, font_family=1/Virgil）

    集成路径：
    - 本地生成：Nichecraft → ExcalidrawBridge → .excalidraw 文件 → 用户在 excalidraw.com 打开
    - 嵌入方案（未来）：React 组件嵌入需要 @excalidraw/excalidraw npm 包

    注意事项：
    - .excalidraw 格式是开放的 JSON 标准，无需许可
    - excalidraw.com 的实时协作功能需要 E2E 加密，我们不涉及
    - tldraw 的生产许可限制决定了我们不采用 tldraw 方案
    """

    def __init__(self, hand_drawn: bool = True, color_scheme: str = "default"):
        self._roughness = 2 if hand_drawn else 0
        self._font_family = 1 if hand_drawn else 2  # Virgil vs Helvetica
        self._color_scheme = color_scheme

    def flowchart_to_scene(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        layout: str = "vertical",
    ) -> ExcalidrawScene:
        """
        将流程图数据转换为 excalidraw 场景。

        Args:
            nodes: [{"id": "n1", "label": "开始", "shape": "rounded_rect"}]
            edges: [{"from": "n1", "to": "n2", "label": "下一步"}]
            layout: "vertical" 或 "horizontal"

        Returns:
            ExcalidrawScene
        """
        scene = ExcalidrawScene()
        node_positions: Dict[str, Tuple[float, float]] = {}

        # 自动布局
        col_width = 250
        row_height = 150
        node_width = 180
        node_height = 60

        for i, node in enumerate(nodes):
            if layout == "vertical":
                x = 100
                y = 80 + i * row_height
            else:
                x = 80 + i * col_width
                y = 100

            node_positions[node["id"]] = (x, y)
            shape = node.get("shape", "rounded_rect")

            if shape in ("rect", "rounded_rect", "rectangle"):
                scene.add_rectangle(x, y, node_width, node_height,
                                   background_color="#ffffff", roughness=self._roughness)
            elif shape == "ellipse":
                scene.add_ellipse(x, y, node_width, node_height,
                                 background_color="#ffffff", roughness=self._roughness)
            elif shape == "diamond":
                scene.add_diamond(x, y, node_width, node_height,
                                 background_color="#ffffff", roughness=self._roughness)

            # 标签
            scene.add_text(
                x + node_width / 2 - len(node["label"]) * 6,
                y + node_height / 2 - 12,
                node["label"],
                font_size=16,
                roughness=self._roughness,
            )

        # 箭头
        for edge in edges:
            from_pos = node_positions.get(edge["from"])
            to_pos = node_positions.get(edge["to"])
            if from_pos and to_pos:
                scene.add_arrow(
                    from_pos[0] + node_width / 2, from_pos[1] + node_height,
                    to_pos[0] + node_width / 2, to_pos[1],
                    roughness=self._roughness,
                )

        return scene

    def table_to_scene(
        self,
        headers: List[str],
        rows: List[List[str]],
        title: str = "",
    ) -> ExcalidrawScene:
        """将表格转换为 excalidraw 场景"""
        scene = ExcalidrawScene()
        cell_width = 150
        cell_height = 40
        start_x, start_y = 50, 50

        if title:
            scene.add_text(start_x, start_y - 40, title, font_size=24,
                          roughness=self._roughness)

        # 表头
        for j, header in enumerate(headers):
            x = start_x + j * cell_width
            scene.add_rectangle(x, start_y, cell_width, cell_height,
                               background_color="#e8e8e8", roughness=self._roughness)
            scene.add_text(x + 8, start_y + 10, header, font_size=14,
                          roughness=self._roughness)

        # 数据行
        for i, row in enumerate(rows):
            for j, cell in enumerate(row):
                x = start_x + j * cell_width
                y = start_y + (i + 1) * cell_height
                scene.add_rectangle(x, y, cell_width, cell_height,
                                   background_color="#ffffff", roughness=self._roughness)
                scene.add_text(x + 8, y + 10, cell, font_size=12,
                              roughness=self._roughness)

        return scene

    def mindmap_to_scene(
        self,
        root: str,
        branches: Dict[str, List[str]],
    ) -> ExcalidrawScene:
        """将思维导图转换为 excalidraw 场景"""
        scene = ExcalidrawScene()
        center_x, center_y = 400, 300

        # 根节点
        scene.add_rectangle(center_x - 80, center_y - 25, 160, 50,
                           background_color="#a5d8ff", roughness=self._roughness)
        scene.add_text(center_x - 60, center_y - 10, root, font_size=20,
                      roughness=self._roughness)

        # 分支
        branch_count = len(branches)
        angle_step = 2 * math.pi / max(branch_count, 1)
        radius = 200

        for i, (branch_name, items) in enumerate(branches.items()):
            angle = angle_step * i - math.pi / 2
            bx = center_x + radius * math.cos(angle)
            by = center_y + radius * math.sin(angle)

            scene.add_rectangle(bx - 70, by - 20, 140, 40,
                               background_color="#d0bfff", roughness=self._roughness)
            scene.add_text(bx - 55, by - 8, branch_name, font_size=16,
                          roughness=self._roughness)
            scene.add_arrow(center_x, center_y, bx, by, roughness=self._roughness)

            # 子节点
            sub_radius = 120
            for j, item in enumerate(items):
                sub_angle = angle - 0.3 + 0.6 * j / max(len(items) - 1, 1)
                sx = bx + sub_radius * math.cos(sub_angle)
                sy = by + sub_radius * math.sin(sub_angle)

                scene.add_text(sx - 30, sy - 8, item, font_size=12,
                              roughness=self._roughness)
                scene.add_arrow(bx, by, sx, sy, roughness=self._roughness)

        return scene
