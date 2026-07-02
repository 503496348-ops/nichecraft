from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.editable_pptx_layers import LayerAsset, SlideLayout, make_text_box, make_icon_box, write_manifest, write_layout, qa_summary, validate_layout_file

def test_layer_manifest_and_layout_contract():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        for name in ['bg.png','frame.png','icons.png','bg.md','frame.md','icons.md']:
            (root/name).write_text('x')
        assets=[LayerAsset('background','gen://bg',str(root/'bg.png'),str(root/'bg.md')), LayerAsset('frame','gen://frame',str(root/'frame.png'),str(root/'frame.md')), LayerAsset('icons','gen://icons',str(root/'icons.png'),str(root/'icons.md'))]
        manifest=write_manifest(root/'manifest.json',assets)
        layout=SlideLayout(1600,900,'bg.png','frame.png',[make_icon_box('icons/i1.png',[100,200,80,80],1600,900)],[make_text_box('核心结论',[320,120,300,60],1600,900,bold=True)])
        result=qa_summary(manifest, write_layout(root/'layout.json',layout), root)
        assert result['ok'], result

def test_layout_rejects_placeholder_text():
    layout=SlideLayout(1000,600,'bg.png',texts=[make_text_box('Lorem ipsum placeholder',[10,20,100,30],1000,600)])
    with tempfile.TemporaryDirectory() as td:
        errors=validate_layout_file(write_layout(Path(td)/'layout.json',layout))
    assert any('placeholder' in e.lower() for e in errors)
