from scripts.canvas_interaction_guard import (
    CanvasInteractionState,
    ViewportLock,
    apply_interaction,
    authorize_canvas_action,
    enter_group_drilldown,
    visible_element_ids,
)


def test_read_only_blocks_mutating_actions():
    decision = authorize_canvas_action(CanvasInteractionState(read_only=True), "move", {"id": "a"})
    assert decision == {"allowed": False, "reason": "read_only_blocks_mutation", "action": "move"}


def test_viewport_lock_blocks_pan_and_clamps_zoom_when_unlocked():
    locked = CanvasInteractionState(viewport=ViewportLock(True, "review mode"))
    assert authorize_canvas_action(locked, "pan")["reason"] == "viewport_locked"
    unlocked = CanvasInteractionState(viewport=ViewportLock(False, allowed_zoom_min=0.5, allowed_zoom_max=2.0))
    zoom = authorize_canvas_action(unlocked, "zoom", {"zoom": 9})
    assert zoom["zoom"] == 2.0
    assert zoom["clamped"] is True


def test_group_drilldown_limits_visible_elements():
    state = enter_group_drilldown(CanvasInteractionState(), "g1", {"g1": ["a", "b"]})
    assert state.active_group_id == "g1"
    assert visible_element_ids(state, {"g1": ["a", "b"]}, ["a", "b", "c"]) == ["a", "b"]


def test_tool_selection_keeps_state_immutable_style():
    state = CanvasInteractionState()
    next_state, decision = apply_interaction(state, "select_tool", {"tool": "rectangle"})
    assert decision["allowed"] is True
    assert state.selected_tool == "select"
    assert next_state.selected_tool == "rectangle"
    assert state.is_erasing is False
    assert next_state.is_erasing is False


def test_erase_requires_erase_tool_when_not_gestured():
    state = CanvasInteractionState(selected_tool="select")
    decision = authorize_canvas_action(state, "erase", {"target_ids": ["a"]})
    assert decision["allowed"] is False
    assert decision["reason"] == "erase_requires_erase_tool"

    state_with_tool, decision = apply_interaction(state, "select_tool", {"tool": "erase"})
    assert decision["allowed"] is True
    assert state_with_tool.selected_tool == "erase"
    assert state_with_tool.is_erasing is True
    assert authorize_canvas_action(state_with_tool, "erase", {"target_ids": ["a"]})["allowed"] is True
