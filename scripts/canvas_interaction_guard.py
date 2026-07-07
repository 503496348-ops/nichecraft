"""Canvas interaction guardrails for whiteboard and presentation editing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

MUTATING_ACTIONS = {"create", "delete", "move", "resize", "style", "drag_tool", "ungroup", "erase"}
ALLOWED_TOOLS = {"select", "rectangle", "ellipse", "line", "arrow", "text", "erase", "hand"}


@dataclass(frozen=True)
class ViewportLock:
    locked: bool = False
    reason: str = ""
    allowed_zoom_min: float = 0.25
    allowed_zoom_max: float = 4.0

    def clamp_zoom(self, requested: float) -> float:
        return min(max(requested, self.allowed_zoom_min), self.allowed_zoom_max)


@dataclass
class CanvasInteractionState:
    read_only: bool = False
    viewport: ViewportLock = field(default_factory=ViewportLock)
    active_group_id: str | None = None
    selected_tool: str = "select"
    is_erasing: bool = False


def authorize_canvas_action(state: CanvasInteractionState, action: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if state.read_only and action in MUTATING_ACTIONS:
        return {"allowed": False, "reason": "read_only_blocks_mutation", "action": action}
    if state.viewport.locked and action in {"pan", "zoom", "fit_to_content"}:
        return {
            "allowed": False,
            "reason": "viewport_locked",
            "action": action,
            "lock_reason": state.viewport.reason,
        }
    if action == "zoom":
        requested = float(payload.get("zoom", 1.0))
        clamped = state.viewport.clamp_zoom(requested)
        return {
            "allowed": True,
            "action": action,
            "zoom": clamped,
            "clamped": clamped != requested,
        }
    if action == "drag_tool" and payload.get("source") == "toolbar" and state.read_only:
        return {"allowed": False, "reason": "toolbar_drag_disabled_in_read_only", "action": action}
    if action == "select_tool":
        tool = str(payload.get("tool", "select"))
        if tool not in ALLOWED_TOOLS:
            return {"allowed": False, "reason": "unsupported_tool", "action": action, "tool": tool}
    if action == "erase":
        if state.selected_tool != "erase" and not payload.get("is_erasing", False):
            return {"allowed": False, "reason": "erase_requires_erase_tool", "action": action}
        removed = payload.get("target_ids", [])
        if removed and not isinstance(removed, list):
            return {"allowed": False, "reason": "target_ids_must_be_list", "action": action}
    return {"allowed": True, "action": action}


def enter_group_drilldown(state: CanvasInteractionState, group_id: str, groups: Mapping[str, list[str]]) -> CanvasInteractionState:
    if group_id not in groups:
        raise KeyError(group_id)
    return CanvasInteractionState(read_only=state.read_only, viewport=state.viewport, active_group_id=group_id, selected_tool="select")


def visible_element_ids(state: CanvasInteractionState, groups: Mapping[str, list[str]], all_ids: list[str]) -> list[str]:
    if not state.active_group_id:
        return list(all_ids)
    return list(groups.get(state.active_group_id, []))


def apply_interaction(state: CanvasInteractionState, action: str, payload: Mapping[str, Any] | None = None) -> tuple[CanvasInteractionState, dict[str, Any]]:
    decision = authorize_canvas_action(state, action, payload)
    if not decision["allowed"]:
        return state, decision

    payload = payload or {}
    next_state = state

    if action == "select_tool":
        tool = str(payload.get("tool", "select"))
        next_state = CanvasInteractionState(
            read_only=state.read_only,
            viewport=state.viewport,
            active_group_id=state.active_group_id,
            selected_tool=tool,
            is_erasing=tool == "erase",
        )

    if action == "erase_begin":
        next_state = CanvasInteractionState(
            read_only=state.read_only,
            viewport=state.viewport,
            active_group_id=state.active_group_id,
            selected_tool="erase",
            is_erasing=True,
        )
        decision = {"allowed": True, "action": action, "mode": "erasing"}

    if action == "erase_end":
        next_state = CanvasInteractionState(
            read_only=state.read_only,
            viewport=state.viewport,
            active_group_id=state.active_group_id,
            selected_tool=state.selected_tool,
            is_erasing=False,
        )
        decision = {"allowed": True, "action": action}

    return next_state, decision