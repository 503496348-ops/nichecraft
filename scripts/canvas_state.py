"""
Nichecraft — Canvas State Management
=====================================
Inspired by Excalidraw (125K⭐) element model.

Key patterns adopted:
- Element-based canvas model (type, x, y, width, height, style)
- State serialization/deserialization (JSON)
- Undo/redo with state snapshots
- Element grouping and z-ordering
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


class ElementType(str, Enum):
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    TEXT = "text"
    LINE = "line"
    IMAGE = "image"
    GROUP = "group"


@dataclass
class ElementStyle:
    """Visual style for a canvas element."""
    fill_color: str = "#ffffff"
    stroke_color: str = "#000000"
    stroke_width: int = 2
    opacity: float = 1.0
    font_size: int = 16
    font_family: str = "Noto Sans SC"
    border_radius: int = 0


@dataclass
class CanvasElement:
    """A single canvas element — Excalidraw-inspired model."""
    id: str
    type: ElementType
    x: float
    y: float
    width: float = 100
    height: float = 100
    text: str = ""
    style: ElementStyle = field(default_factory=ElementStyle)
    group_id: Optional[str] = None
    z_index: int = 0
    locked: bool = False
    visible: bool = True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "CanvasElement":
        style_data = data.pop("style", {})
        style = ElementStyle(**style_data) if isinstance(style_data, dict) else ElementStyle()
        data["type"] = ElementType(data["type"])
        return cls(style=style, **data)


@dataclass
class CanvasState:
    """Full canvas state with undo/redo support."""
    elements: list[CanvasElement] = field(default_factory=list)
    canvas_width: int = 1920
    canvas_height: int = 1080
    background_color: str = "#f5f5f5"
    _history: list[list[dict]] = field(default_factory=list)
    _history_index: int = -1

    def add_element(self, element: CanvasElement):
        self._save_snapshot()
        self.elements.append(element)

    def remove_element(self, element_id: str):
        self._save_snapshot()
        self.elements = [e for e in self.elements if e.id != element_id]

    def move_element(self, element_id: str, x: float, y: float):
        for e in self.elements:
            if e.id == element_id:
                self._save_snapshot()
                e.x = x
                e.y = y
                return

    def get_element(self, element_id: str) -> Optional[CanvasElement]:
        for e in self.elements:
            if e.id == element_id:
                return e
        return None

    def group_elements(self, element_ids: list[str], group_id: str):
        self._save_snapshot()
        for e in self.elements:
            if e.id in element_ids:
                e.group_id = group_id

    def _save_snapshot(self):
        snapshot = [e.to_dict() for e in self.elements]
        self._history = self._history[:self._history_index + 1]
        self._history.append(snapshot)
        self._history_index = len(self._history) - 1

    def undo(self) -> bool:
        if self._history_index > 0:
            self._history_index -= 1
            self._restore_snapshot(self._history[self._history_index])
            return True
        return False

    def redo(self) -> bool:
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._restore_snapshot(self._history[self._history_index])
            return True
        return False

    def _restore_snapshot(self, snapshot: list[dict]):
        self.elements = [CanvasElement.from_dict(d) for d in snapshot]

    def to_json(self) -> str:
        return json.dumps({
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "background_color": self.background_color,
            "elements": [e.to_dict() for e in self.elements],
        }, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, data: str) -> "CanvasState":
        d = json.loads(data)
        elements = [CanvasElement.from_dict(e) for e in d.get("elements", [])]
        return cls(
            elements=elements,
            canvas_width=d.get("canvas_width", 1920),
            canvas_height=d.get("canvas_height", 1080),
            background_color=d.get("background_color", "#f5f5f5"),
        )


if __name__ == "__main__":
    canvas = CanvasState()
    canvas.add_element(CanvasElement(id="title", type=ElementType.TEXT, x=100, y=50, width=400, height=60, text="欢迎使用Nichecraft"))
    canvas.add_element(CanvasElement(id="box1", type=ElementType.RECTANGLE, x=100, y=150, width=200, height=100))
    canvas.add_element(CanvasElement(id="box2", type=ElementType.ELLIPSE, x=400, y=150, width=150, height=150))
    print(canvas.to_json())
    print(f"\n✅ Canvas: {len(canvas.elements)} elements, undo history: {len(canvas._history)}")
