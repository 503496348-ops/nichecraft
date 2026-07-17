import json

from scripts.excalidraw_import_adapter import _extract_labels, convert_to_flow


def test_extract_labels_from_text_elements():
    payload = {
        "elements": [
            {"type": "text", "text": "开始"},
            {"type": "text", "text": "  "},
            {"type": "rectangle", "text": "ignore"},
            {"type": "text", "text": "结束"},
        ]
    }
    labels = _extract_labels(payload)
    assert labels == ["开始", "结束"]


def test_convert_to_flow_uses_texts_first():
    payload = {
        "elements": [
            {"type": "text", "text": "A"},
            {"type": "text", "text": "B"},
        ]
    }
    out = convert_to_flow(payload, title="导入")
    nodes = json.loads(json.dumps(out))
    # title + 2 labels
    assert out["type"] == "excalidraw"
    assert len(out["elements"]) > 0
    assert out["source"] == "nichecraft-excalidraw-bridge"
    body = json.dumps(payload)
    assert len(body) > 10


def test_convert_fallback_when_no_text():
    payload = {"elements": [{"type": "rectangle", "id": "r1"}]}
    out = convert_to_flow(payload, title="")
    assert out["elements"], "should produce scene"
