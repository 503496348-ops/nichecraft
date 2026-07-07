from scripts.canvas_state import CanvasState, CanvasElement, ElementType


def test_canvas_state_roundtrip_with_v2_schema():
    state = CanvasState(
        canvas_width=1280,
        canvas_height=720,
        elements=[
            CanvasElement(
                id="n1",
                type=ElementType.RECTANGLE,
                x=10,
                y=20,
                width=200,
                height=100,
                text="hello",
            )
        ],
    )

    json_text = state.to_json()
    restored = CanvasState.from_json(json_text)

    assert restored.schema_version == 2
    assert restored.canvas_width == 1280
    assert restored.canvas_height == 720
    assert len(restored.elements) == 1
    assert restored.elements[0].id == "n1"
    assert restored.elements[0].type == ElementType.RECTANGLE


def test_canvas_state_migrates_legacy_keys_and_defaults():
    legacy = {
        "sceneWidth": 1024,
        "sceneHeight": 768,
        "bg_color": "#111111",
        "elements": [
            {
                "id": "legacy-1",
                "type": "ellipse",
                "x": 1,
                "y": 2,
                "width": 30,
                "height": 40,
                "style": {"fill_color": "#ff0000", "stroke_width": 3},
            }
        ],
    }

    restored = CanvasState.from_dict(legacy)
    assert restored.schema_version == 2
    assert restored.canvas_width == 1024
    assert restored.canvas_height == 768
    assert restored.background_color == "#111111"
    assert restored.page_version == 1
    assert len(restored.elements) == 1
    assert restored.elements[0].style.fill_color == "#ff0000"
    assert restored.elements[0].type == ElementType.ELLIPSE


def test_canvas_state_erase_elements_keeps_history_and_changes_count():
    state = CanvasState(
        elements=[
            CanvasElement(id="a", type=ElementType.TEXT, x=0, y=0),
            CanvasElement(id="b", type=ElementType.TEXT, x=1, y=1),
            CanvasElement(id="c", type=ElementType.TEXT, x=2, y=2),
        ]
    )
    removed = state.erase_elements(["a", "c"])
    assert removed == 2
    assert {e.id for e in state.elements} == {"b"}
    assert state.undo() is True
    assert {e.id for e in state.elements} == {"a", "b", "c"}
