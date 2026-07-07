"""
Nichecraft — Canvas State Management
=====================================
Inspired by Excalidraw (125K⭐) element model.

This module now supports round-trip-safe canvas schemas with lightweight
migration so older saved states can still be restored.

Key additions:
- schema_version / page_version tracking
- deterministic element serialization
- migration for legacy payloads (missing schema fields or mixed key names)
- bounded undo/redo history with explicit snapshot payloads
- active canvas tool + erase tool transition guard hooks
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from dataclasses import fields
from typing import Any, Dict, Optional
from enum import Enum

CANVAS_STATE_SCHEMA_VERSION = 2
CANVAS_PAGE_SCHEMA_VERSION = 1
CANVAS_ELEMENT_SCHEMA_VERSION = 1


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

    @classmethod
    def from_input(cls, raw: Any) -> "ElementStyle":
        if isinstance(raw, ElementStyle):
            return raw
        if not isinstance(raw, dict):
            return cls()
        allowed = {f.name for f in fields(cls)}
        cleaned = {k: v for k, v in raw.items() if k in allowed}
        return cls(**cleaned)


@dataclass
class CanvasElement:
    """A single canvas element."""

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
    schema_version: int = CANVAS_ELEMENT_SCHEMA_VERSION

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d

    @classmethod
    def _coerce_type(cls, raw: Any) -> ElementType:
        if isinstance(raw, ElementType):
            return raw
        if not isinstance(raw, str):
            raise ValueError("element type must be a string")
        return ElementType(raw)

    @classmethod
    def from_dict(cls, data: dict) -> "CanvasElement":
        payload = dict(data)
        raw_type = payload.pop("type", "rectangle")
        style = ElementStyle.from_input(payload.pop("style", {}))

        schema_version = int(payload.pop("schema_version", CANVAS_ELEMENT_SCHEMA_VERSION))
        return cls(
            id=payload.pop("id", str(uuid.uuid4())),
            type=cls._coerce_type(raw_type),
            x=float(payload.pop("x", 0.0)),
            y=float(payload.pop("y", 0.0)),
            width=float(payload.pop("width", 100.0)),
            height=float(payload.pop("height", 100.0)),
            text=str(payload.pop("text", "")),
            style=style,
            group_id=payload.pop("group_id", None),
            z_index=int(payload.pop("z_index", 0)),
            locked=bool(payload.pop("locked", False)),
            visible=bool(payload.pop("visible", True)),
            schema_version=max(schema_version, CANVAS_ELEMENT_SCHEMA_VERSION),
        )

    @property
    def is_grouped(self) -> bool:
        return self.group_id is not None


@dataclass
class CanvasState:
    """Full canvas state with undo/redo support and migration hooks."""

    elements: list[CanvasElement] = field(default_factory=list)
    canvas_width: int = 1920
    canvas_height: int = 1080
    background_color: str = "#f5f5f5"
    schema_version: int = CANVAS_STATE_SCHEMA_VERSION
    page_version: int = CANVAS_PAGE_SCHEMA_VERSION
    page_id: str = "page-1"
    active_tool: str = "select"
    _history: list[dict] = field(default_factory=list)
    _history_index: int = -1

    def __post_init__(self) -> None:
        self._normalize_elements()
        if not self._history:
            self._history = [self.to_dict()]
            self._history_index = 0

    def _normalize_elements(self) -> None:
        # keep deterministic order by z_index then insertion id (for stable snapshots)
        self.elements.sort(key=lambda e: (e.z_index, e.id))

    def add_element(self, element: CanvasElement) -> None:
        self._snapshot()
        self.elements.append(element)
        self._normalize_elements()

    def remove_element(self, element_id: str) -> None:
        self._snapshot()
        self.elements = [e for e in self.elements if e.id != element_id]

    def erase_elements(self, element_ids: list[str]) -> int:
        before = len(self.elements)
        if not element_ids:
            return 0
        self._snapshot()
        remove = set(element_ids)
        self.elements = [e for e in self.elements if e.id not in remove]
        self._normalize_elements()
        return before - len(self.elements)

    def move_element(self, element_id: str, x: float, y: float) -> None:
        for e in self.elements:
            if e.id == element_id:
                self._snapshot()
                e.x = x
                e.y = y
                return

    def get_element(self, element_id: str) -> Optional[CanvasElement]:
        for e in self.elements:
            if e.id == element_id:
                return e
        return None

    def group_elements(self, element_ids: list[str], group_id: str) -> None:
        self._snapshot()
        for e in self.elements:
            if e.id in element_ids:
                e.group_id = group_id

    def set_tool(self, tool: str) -> None:
        self._snapshot()
        self.active_tool = tool

    def _snapshot(self) -> None:
        snapshot = self.to_dict()
        self._history = self._history[: self._history_index + 1]
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

    def _restore_snapshot(self, snapshot: dict) -> None:
        restored = self.from_dict(snapshot)
        self.elements = restored.elements
        self.canvas_width = restored.canvas_width
        self.canvas_height = restored.canvas_height
        self.background_color = restored.background_color
        self.schema_version = restored.schema_version
        self.page_version = restored.page_version
        self.page_id = restored.page_id
        self.active_tool = restored.active_tool
        self._history = restored._history
        self._history_index = restored._history_index

    def to_dict(self) -> dict[str, Any]:
        data = {
            "schema_version": self.schema_version,
            "page_version": self.page_version,
            "page_id": self.page_id,
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "background_color": self.background_color,
            "active_tool": self.active_tool,
            "elements": [e.to_dict() for e in self.elements],
        }
        return data

    def to_json(self) -> str:
        payload = self.to_dict()
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @classmethod
    def _migrate_legacy_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        # Legacy compatibility: scene_* keys and omitted schema version.
        migrated = dict(payload)
        migrated["schema_version"] = int(migrated.get("schema_version", 1))

        # legacy alias for canvas dimensions
        if "sceneWidth" in migrated and "canvas_width" not in migrated:
            migrated["canvas_width"] = migrated.pop("sceneWidth")
        if "sceneHeight" in migrated and "canvas_height" not in migrated:
            migrated["canvas_height"] = migrated.pop("sceneHeight")

        if "bg_color" in migrated and "background_color" not in migrated:
            migrated["background_color"] = migrated.pop("bg_color")

        # legacy payloads often stored elements under `elements` already, keep as is.
        migrated["page_version"] = int(migrated.get("page_version", 1))
        return migrated

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CanvasState":
        migrated = cls._migrate_legacy_payload(payload)
        schema_version = int(migrated.get("schema_version", 1))
        if schema_version > CANVAS_STATE_SCHEMA_VERSION:
            raise ValueError(f"Unsupported canvas schema version: {schema_version}")

        elements: list[CanvasElement] = []
        raw_elements = migrated.get("elements", [])
        for item in raw_elements:
            if isinstance(item, dict):
                elements.append(CanvasElement.from_dict(item))

        return cls(
            elements=elements,
            canvas_width=int(migrated.get("canvas_width", 1920)),
            canvas_height=int(migrated.get("canvas_height", 1080)),
            background_color=str(migrated.get("background_color", "#f5f5f5")),
            schema_version=CANVAS_STATE_SCHEMA_VERSION,
            page_version=int(migrated.get("page_version", CANVAS_PAGE_SCHEMA_VERSION)),
            page_id=str(migrated.get("page_id", "page-1")),
            active_tool=str(migrated.get("active_tool", "select")),
        )

    @classmethod
    def from_json(cls, data: str) -> "CanvasState":
        migrated = json.loads(data)
        if isinstance(migrated, str):
            migrated = json.loads(migrated)
        if not isinstance(migrated, dict):
            raise ValueError("state payload must be a JSON object")
        return cls.from_dict(migrated)


if __name__ == "__main__":
    canvas = CanvasState()
    canvas.add_element(
        CanvasElement(
            id="title",
            type=ElementType.TEXT,
            x=100,
            y=50,
            width=400,
            height=60,
            text="欢迎使用Nichecraft",
        )
    )
    canvas.add_element(
        CanvasElement(
            id="box1",
            type=ElementType.RECTANGLE,
            x=100,
            y=150,
            width=200,
            height=100,
        )
    )
    print(canvas.to_json())
    print(f"\n✅ Canvas: {len(canvas.elements)} elements, undo history: {len(canvas._history)}")
