from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable
import json, time

REQUIRED_ASSET_KINDS = {'background', 'frame', 'icons'}
FORBIDDEN_BACKENDS = {'programmatic', 'local', 'pil', 'svg', 'html', 'canvas', 'matplotlib', 'ppt-shapes'}
PLACEHOLDER_MARKERS = ('lorem', 'ipsum', 'placeholder', '占位', '示例文字', '待填写', 'TODO')

@dataclass
class LayerAsset:
    kind: str
    generated_source: str
    copied_to: str
    prompt_file: str
    backend: str = 'imagegen'
    created_at: float = field(default_factory=time.time)
    def validate(self, run_root: Path | None = None) -> list[str]:
        errors=[]
        if self.kind not in REQUIRED_ASSET_KINDS: errors.append(f'unknown asset kind: {self.kind}')
        if not self.generated_source: errors.append(f'{self.kind}: missing generated_source')
        if not self.copied_to: errors.append(f'{self.kind}: missing copied_to')
        if not self.prompt_file: errors.append(f'{self.kind}: missing prompt_file')
        if self.backend.lower() in FORBIDDEN_BACKENDS: errors.append(f'{self.kind}: forbidden backend {self.backend}')
        if run_root is not None:
            root=run_root.resolve()
            for label, raw in [('copied_to', self.copied_to), ('prompt_file', self.prompt_file)]:
                p=Path(raw)
                if p.is_absolute():
                    try: p.resolve().relative_to(root)
                    except Exception: errors.append(f'{self.kind}: {label} escapes run_root: {p}')
        return errors

@dataclass
class TextBox:
    text: str
    source_bbox: list[float]
    x: float; y: float; w: float; h: float
    size_ratio: float | None = None
    bold: bool = False
    color: str = '#111111'
    align: str = 'left'
    def validate(self, ref_width: float, ref_height: float, tolerance: float = 0.004) -> list[str]:
        errors=[]
        if any(m.lower() in self.text.lower() for m in PLACEHOLDER_MARKERS): errors.append(f'placeholder text found: {self.text[:30]}')
        if len(self.source_bbox)!=4: return errors+[f'source_bbox must have 4 numbers for {self.text[:30]}']
        bx,by,bw,bh=self.source_bbox; exp=[bx/ref_width,by/ref_height,bw/ref_width,bh/ref_height]
        for name,a,e in zip('xywh',[self.x,self.y,self.w,self.h],exp):
            if abs(a-e)>tolerance: errors.append(f'{self.text[:30]}: {name}={a:.5f} does not match source_bbox {e:.5f}')
        if self.size_ratio is not None and not (0.004 <= self.size_ratio <= 0.20): errors.append(f'{self.text[:30]}: suspicious size_ratio {self.size_ratio}')
        return errors

@dataclass
class IconBox:
    file: str
    source_bbox: list[float]
    x: float; y: float; w: float; h: float
    role: str = 'icon'
    def validate(self, ref_width: float, ref_height: float, tolerance: float = 0.006) -> list[str]:
        if len(self.source_bbox)!=4: return [f'{self.file}: source_bbox must have 4 numbers']
        bx,by,bw,bh=self.source_bbox; exp=[bx/ref_width,by/ref_height,bw/ref_width,bh/ref_height]
        return [f'{self.file}: {n}={a:.5f} != bbox {e:.5f}' for n,a,e in zip('xywh',[self.x,self.y,self.w,self.h],exp) if abs(a-e)>tolerance]

@dataclass
class SlideLayout:
    ref_width: int
    ref_height: int
    background: str
    frame: str | None = None
    icons: list[IconBox] = field(default_factory=list)
    texts: list[TextBox] = field(default_factory=list)
    units: str = 'fraction'
    def validate(self) -> list[str]:
        errors=[]
        if self.ref_width<=0 or self.ref_height<=0: errors.append('ref_width/ref_height must be positive')
        if self.units!='fraction': errors.append('units must be fraction')
        for item in self.icons: errors.extend(item.validate(self.ref_width,self.ref_height))
        for item in self.texts: errors.extend(item.validate(self.ref_width,self.ref_height))
        ordinary=[t for t in self.texts if len(t.text)>12]
        if len(ordinary)>=4 and sum(1 for t in ordinary if t.bold)/len(ordinary)>0.8: errors.append('too many ordinary text boxes are bold')
        return errors

def bbox_to_fraction(bbox: Iterable[float], ref_width: float, ref_height: float) -> list[float]:
    x,y,w,h=[float(v) for v in bbox]
    if ref_width<=0 or ref_height<=0: raise ValueError('reference size must be positive')
    return [x/ref_width,y/ref_height,w/ref_width,h/ref_height]

def make_text_box(text: str, bbox: Iterable[float], ref_width: int, ref_height: int, **style: Any) -> TextBox:
    vals=[float(v) for v in bbox]; x,y,w,h=bbox_to_fraction(vals,ref_width,ref_height)
    return TextBox(text=text, source_bbox=vals, x=x, y=y, w=w, h=h, size_ratio=style.pop('size_ratio', vals[3]/ref_height), **style)

def make_icon_box(file: str, bbox: Iterable[float], ref_width: int, ref_height: int, **style: Any) -> IconBox:
    vals=[float(v) for v in bbox]; x,y,w,h=bbox_to_fraction(vals,ref_width,ref_height)
    return IconBox(file=file, source_bbox=vals, x=x, y=y, w=w, h=h, **style)

def write_manifest(path: str|Path, assets: list[LayerAsset]) -> Path:
    out=Path(path); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'assets':[asdict(a) for a in assets]}, ensure_ascii=False, indent=2), encoding='utf-8'); return out

def validate_manifest(path: str|Path, run_root: str|Path|None=None) -> list[str]:
    raw=json.loads(Path(path).read_text(encoding='utf-8')); root=Path(run_root) if run_root else None
    assets=[LayerAsset(**x) for x in raw.get('assets', [])]; errors=[]; kinds={a.kind for a in assets}
    if REQUIRED_ASSET_KINDS-kinds: errors.append(f'missing required asset kinds: {sorted(REQUIRED_ASSET_KINDS-kinds)}')
    for a in assets: errors.extend(a.validate(root))
    return errors

def write_layout(path: str|Path, layout: SlideLayout) -> Path:
    out=Path(path); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(asdict(layout), ensure_ascii=False, indent=2), encoding='utf-8'); return out

def load_layout(path: str|Path) -> SlideLayout:
    data=json.loads(Path(path).read_text(encoding='utf-8')); data['icons']=[IconBox(**x) for x in data.get('icons', [])]; data['texts']=[TextBox(**x) for x in data.get('texts', [])]; return SlideLayout(**data)

def validate_layout_file(path: str|Path) -> list[str]: return load_layout(path).validate()
def qa_summary(manifest_path: str|Path, layout_path: str|Path, run_root: str|Path|None=None) -> dict[str,Any]:
    me=validate_manifest(manifest_path,run_root); le=validate_layout_file(layout_path); return {'ok': not me and not le, 'manifest_errors':me, 'layout_errors':le}
def build_deck_spec(slide_layout_paths: list[str|Path], title: str='Nichecraft editable deck') -> dict[str,Any]:
    slides=[]
    for p in slide_layout_paths: slides.append(asdict(load_layout(p)) | {'layout_file': str(p)})
    return {'title':title,'slides':slides,'slide_count':len(slides)}
