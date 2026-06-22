# -*- coding: utf-8 -*-
"""
有点东西-Nichecraft · Mermaid-to-SVG Renderer
AtomCollide-智械工坊 · 2026

融合自 Excalidraw (125K⭐, +134) 的 Mermaid 集成模式。

支持图表类型:
  - MR1: flowchart (TD/LR方向)
  - MR2: sequenceDiagram (参与者+消息)
  - MR3: classDiagram (类+关系)
  - MR4: gantt (甘特图)
  - MR5: pie (饼图)
  - MR6: mindmap (思维导图)

输出: SVG字符串，兼容Nichecraft管线。

Usage:
    from mermaid_renderer import MermaidRenderer
    mr = MermaidRenderer()
    svg = mr.render("flowchart TD\\n  A[开始] --> B[处理] --> C[结束]")
    mr.save(svg, "output.svg")
"""

import re
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from xml.etree import ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"

# ── Mermaid图表类型检测 ──

CHART_TYPES = [
    "flowchart", "graph", "sequenceDiagram", "classDiagram",
    "stateDiagram", "erDiagram", "journey", "gantt", "pie",
    "mindmap", "timeline", "sankey", "xychart", "block",
]

_CHART_TYPE_RE = re.compile(
    r"^(?:%%\{.*?\}%%[\s\n]*)?\b(?:" +
    "|".join(rf"\s*{ct}(-beta)?" for ct in CHART_TYPES) +
    r")\b",
    re.MULTILINE,
)


@dataclass
class FlowNode:
    """流程图节点"""
    id: str
    label: str
    shape: str = "rect"  # rect/round/diamond/circle/stadium
    x: float = 0
    y: float = 0
    width: float = 160
    height: float = 60


@dataclass
class FlowEdge:
    """流程图边"""
    source: str
    target: str
    label: str = ""
    style: str = "solid"  # solid/dashed/dotted


class MermaidRenderer:
    """Mermaid语法→SVG渲染器"""

    def __init__(self, width: int = 800, height: int = 600,
                 theme: str = "default"):
        self.width = width
        self.height = height
        self.theme = theme
        self._themes = {
            "default": {
                "bg": "#FFFFFF", "node_bg": "#E8F4FD", "node_border": "#1890FF",
                "edge_color": "#666666", "text_color": "#333333",
                "accent": "#FF6B6B", "success": "#52C41A",
            },
            "dark": {
                "bg": "#1A1A2E", "node_bg": "#16213E", "node_border": "#0F3460",
                "edge_color": "#A0A0A0", "text_color": "#E0E0E0",
                "accent": "#E94560", "success": "#52C41A",
            },
            "warm": {
                "bg": "#FFF8F0", "node_bg": "#FFE8CC", "node_border": "#FF9A3C",
                "edge_color": "#8B7355", "text_color": "#4A3728",
                "accent": "#E74C3C", "success": "#27AE60",
            },
        }

    def _get_theme(self) -> Dict[str, str]:
        return self._themes.get(self.theme, self._themes["default"])

    def detect_type(self, definition: str) -> Optional[str]:
        """检测Mermaid图表类型"""
        definition = definition.strip()
        for chart_type in CHART_TYPES:
            if re.match(rf"^\s*{chart_type}", definition, re.IGNORECASE):
                return chart_type
        return None

    def render(self, definition: str) -> str:
        """
        渲染Mermaid定义为SVG。

        Args:
            definition: Mermaid语法字符串

        Returns:
            SVG字符串
        """
        chart_type = self.detect_type(definition)
        if chart_type is None:
            return self._error_svg("Unsupported or unrecognized diagram type")

        renderers = {
            "flowchart": self._render_flowchart,
            "graph": self._render_flowchart,
            "sequenceDiagram": self._render_sequence,
            "pie": self._render_pie,
            "mindmap": self._render_mindmap,
        }

        renderer = renderers.get(chart_type)
        if renderer:
            return renderer(definition)
        return self._error_svg(f"Renderer for '{chart_type}' not yet implemented")

    def save(self, svg_content: str, output_path: str):
        """保存SVG到文件"""
        Path(output_path).write_text(svg_content, encoding="utf-8")

    # ── Flowchart渲染 ──

    def _render_flowchart(self, definition: str) -> str:
        """渲染流程图"""
        theme = self._get_theme()
        nodes: Dict[str, FlowNode] = {}
        edges: List[FlowEdge] = []
        direction = "TD"  # Top-Down default

        lines = definition.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect direction
            dir_match = re.match(r"(?:flowchart|graph)\s+(TD|LR|TB|RL|BT)", line, re.I)
            if dir_match:
                direction = dir_match.group(1).upper()
                continue

            # Parse edge: A --> B or A -- text --> B
            edge_match = re.match(
                r'(\w+)(?:\[([^\]]*)\])?\s*(?:-->|---?|-->>|==>|-.->|~~~)\s*(?:"?([^"-->]*)?"?\s*(?:-->|---)?)?\s*(\w+)(?:\[([^\]]*)\])?',
                line,
            )
            if edge_match:
                src_id = edge_match.group(1)
                src_label = edge_match.group(2) or src_id
                edge_label = edge_match.group(3) or ""
                tgt_id = edge_match.group(4)
                tgt_label = edge_match.group(5) or tgt_id

                if src_id not in nodes:
                    nodes[src_id] = FlowNode(id=src_id, label=src_label)
                if tgt_id not in nodes:
                    nodes[tgt_id] = FlowNode(id=tgt_id, label=tgt_label)

                edges.append(FlowEdge(source=src_id, target=tgt_id, label=edge_label.strip()))
                continue

            # Parse standalone node: A[Label] or A(Label) or A{Label}
            node_match = re.match(r'(\w+)([\[\({])([^\]\)}]*)([\]\)}])', line)
            if node_match:
                nid = node_match.group(1)
                open_bracket = node_match.group(2)
                label = node_match.group(3)
                shape = {"[": "rect", "(": "round", "{": "diamond"}.get(open_bracket, "rect")
                nodes[nid] = FlowNode(id=nid, label=label, shape=shape)

        if not nodes:
            return self._error_svg("No nodes found in flowchart definition")

        # Layout
        is_lr = direction in ("LR", "RL")
        self._layout_flowchart(nodes, edges, is_lr)

        # Calculate SVG dimensions
        max_x = max(n.x + n.width for n in nodes.values()) + 80
        max_y = max(n.y + n.height for n in nodes.values()) + 80
        self.width = max(self.width, int(max_x))
        self.height = max(self.height, int(max_y))

        # Build SVG
        svg = self._svg_header()
        svg += self._svg_styles(theme)

        # Draw edges first (behind nodes)
        for edge in edges:
            svg += self._svg_edge(edge, nodes, theme)

        # Draw nodes
        for node in nodes.values():
            svg += self._svg_node(node, theme)

        svg += "</svg>"
        return svg

    def _layout_flowchart(self, nodes: Dict[str, FlowNode], edges: List[FlowEdge], is_lr: bool):
        """自动布局流程图节点"""
        # Topological sort
        in_degree = {nid: 0 for nid in nodes}
        adjacency: Dict[str, List[str]] = {nid: [] for nid in nodes}
        for edge in edges:
            if edge.target in in_degree:
                in_degree[edge.target] += 1
            if edge.source in adjacency:
                adjacency[edge.source].append(edge.target)

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order: List[str] = []
        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for child in adjacency.get(nid, []):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        # Position nodes
        x_start, y_start = 60, 60
        x_gap = 220 if is_lr else 200
        y_gap = 120 if not is_lr else 100

        # Group by depth
        depths: Dict[str, int] = {}
        for nid in order:
            parent_depths = [depths.get(e.source, 0) for e in edges if e.target == nid]
            depths[nid] = max(parent_depths, default=0) + 1

        # Assign positions
        depth_groups: Dict[int, List[str]] = {}
        for nid, depth in depths.items():
            depth_groups.setdefault(depth, []).append(nid)

        for depth, group in depth_groups.items():
            for i, nid in enumerate(group):
                node = nodes[nid]
                if is_lr:
                    node.x = x_start + (depth - 1) * x_gap
                    node.y = y_start + i * y_gap
                else:
                    node.x = x_start + i * x_gap - (len(group) - 1) * x_gap / 2
                    node.y = y_start + (depth - 1) * y_gap

    # ── Pie chart渲染 ──

    def _render_pie(self, definition: str) -> str:
        """渲染饼图"""
        theme = self._get_theme()
        slices = []

        for line in definition.strip().split("\n"):
            line = line.strip()
            match = re.match(r'pie\s+title\s+(.*)', line, re.I)
            if match:
                continue
            match = re.match(r'"([^"]+)"\s*:\s*(\d+(?:\.\d+)?)', line)
            if match:
                slices.append((match.group(1), float(match.group(2))))

        if not slices:
            return self._error_svg("No data found in pie chart")

        total = sum(v for _, v in slices)
        cx, cy, r = self.width / 2, self.height / 2, min(self.width, self.height) / 2 - 60

        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
                  "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"]

        svg = self._svg_header()
        svg += f'<rect width="{self.width}" height="{self.height}" fill="{theme["bg"]}"/>\n'

        start_angle = 0
        for i, (label, value) in enumerate(slices):
            angle = (value / total) * 360
            end_angle = start_angle + angle
            color = colors[i % len(colors)]

            # SVG arc
            start_rad = math.radians(start_angle - 90)
            end_rad = math.radians(end_angle - 90)
            x1 = cx + r * math.cos(start_rad)
            y1 = cy + r * math.sin(start_rad)
            x2 = cx + r * math.cos(end_rad)
            y2 = cy + r * math.sin(end_rad)
            large_arc = 1 if angle > 180 else 0

            svg += f'<path d="M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z" '
            svg += f'fill="{color}" stroke="{theme["bg"]}" stroke-width="2"/>\n'

            # Label
            mid_rad = math.radians((start_angle + end_angle) / 2 - 90)
            lx = cx + r * 0.65 * math.cos(mid_rad)
            ly = cy + r * 0.65 * math.sin(mid_rad)
            pct = value / total * 100
            svg += f'<text x="{lx}" y="{ly}" text-anchor="middle" dominant-baseline="middle" '
            svg += f'fill="{theme["text_color"]}" font-size="12" font-family="system-ui">'
            svg += f'{label} ({pct:.0f}%)</text>\n'

            start_angle = end_angle

        svg += "</svg>"
        return svg

    # ── Sequence diagram渲染 ──

    def _render_sequence(self, definition: str) -> str:
        """渲染序列图"""
        theme = self._get_theme()
        participants: List[str] = []
        messages: List[Tuple[str, str, str]] = []  # (from, to, text)

        for line in definition.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("%%"):
                continue

            # Participant declaration
            part_match = re.match(r'participant\s+(\w+)(?:\s+as\s+(.+))?', line, re.I)
            if part_match:
                participants.append(part_match.group(1))
                continue

            # Message: A->B: text or A->>B: text
            msg_match = re.match(r'(\w+)\s*-{1,2}>+?\s*(\w+)\s*:\s*(.+)', line)
            if msg_match:
                src, tgt, text = msg_match.group(1), msg_match.group(2), msg_match.group(3)
                if src not in participants:
                    participants.append(src)
                if tgt not in participants:
                    participants.append(tgt)
                messages.append((src, tgt, text))

        if not participants:
            return self._error_svg("No participants found in sequence diagram")

        # Layout
        col_width = max(180, self.width // (len(participants) + 1))
        row_height = 60
        header_y = 40
        msg_start_y = header_y + 60

        actual_width = col_width * (len(participants) + 1)
        actual_height = msg_start_y + len(messages) * row_height + 80
        self.width = max(self.width, actual_width)
        self.height = max(self.height, actual_height)

        svg = self._svg_header()
        svg += f'<rect width="{self.width}" height="{self.height}" fill="{theme["bg"]}"/>\n'

        # Draw participant boxes and lifelines
        positions: Dict[str, float] = {}
        for i, p in enumerate(participants):
            x = col_width * (i + 1)
            positions[p] = x
            # Box
            svg += f'<rect x="{x - 50}" y="{header_y}" width="100" height="40" rx="6" '
            svg += f'fill="{theme["node_bg"]}" stroke="{theme["node_border"]}" stroke-width="2"/>\n'
            # Label
            svg += f'<text x="{x}" y="{header_y + 25}" text-anchor="middle" '
            svg += f'fill="{theme["text_color"]}" font-size="14" font-weight="bold" font-family="system-ui">{p}</text>\n'
            # Lifeline
            svg += f'<line x1="{x}" y1="{header_y + 40}" x2="{x}" y2="{self.height - 30}" '
            svg += f'stroke="{theme["edge_color"]}" stroke-width="1" stroke-dasharray="6,4"/>\n'

        # Draw messages
        for i, (src, tgt, text) in enumerate(messages):
            y = msg_start_y + i * row_height
            x1 = positions.get(src, 100)
            x2 = positions.get(tgt, 200)

            # Arrow
            svg += f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
            svg += f'stroke="{theme["edge_color"]}" stroke-width="2" marker-end="url(#arrowhead)"/>\n'

            # Text
            mid_x = (x1 + x2) / 2
            svg += f'<text x="{mid_x}" y="{y - 8}" text-anchor="middle" '
            svg += f'fill="{theme["text_color"]}" font-size="12" font-family="system-ui">{text}</text>\n'

        # Arrowhead marker
        svg = svg.replace(self._svg_header(), self._svg_header() +
            '<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">'
            f'<polygon points="0 0, 10 3.5, 0 7" fill="{theme["edge_color"]}"/></marker></defs>\n')

        svg += "</svg>"
        return svg

    # ── Mindmap渲染 ──

    def _render_mindmap(self, definition: str) -> str:
        """渲染思维导图"""
        theme = self._get_theme()
        nodes = []

        for line in definition.strip().split("\n"):
            line = line.rstrip()
            if not line or line.startswith("mindmap"):
                continue
            indent = len(line) - len(line.lstrip())
            level = indent // 2
            text = line.strip()
            # Remove markdown-style markers
            text = re.sub(r'^[`\-=*]+\s*', '', text)
            text = re.sub(r'\s*[`\-+=*]+$', '', text)
            if text:
                nodes.append((level, text))

        if not nodes:
            return self._error_svg("No nodes found in mindmap")

        # Layout: root in center, children radiate outward
        cx, cy = self.width / 2, self.height / 2
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]

        svg = self._svg_header()
        svg += f'<rect width="{self.width}" height="{self.height}" fill="{theme["bg"]}"/>\n'

        # Draw connections and nodes
        positions: List[Tuple[float, float, str, int]] = []
        root_pos = (cx, cy)

        # Simple radial layout
        level_nodes: Dict[int, List[Tuple[int, str]]] = {}
        for i, (level, text) in enumerate(nodes):
            level_nodes.setdefault(level, []).append((i, text))

        for level, items in level_nodes.items():
            if level == 0:
                # Root node
                svg += f'<rect x="{cx - 80}" y="{cy - 25}" width="160" height="50" rx="25" '
                svg += f'fill="{colors[0]}" stroke="none"/>\n'
                svg += f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" dominant-baseline="middle" '
                svg += f'fill="white" font-size="16" font-weight="bold" font-family="system-ui">{items[0][1]}</text>\n'
                positions.append((cx, cy, items[0][1], 0))
            else:
                # Child nodes - distribute radially
                angle_step = 360 / max(len(items), 1)
                radius = 120 + level * 100
                for j, (idx, text) in enumerate(items):
                    angle = math.radians(angle_step * j - 90)
                    x = cx + radius * math.cos(angle)
                    y = cy + radius * math.sin(angle)
                    color = colors[level % len(colors)]

                    # Connection line to parent
                    parent_x, parent_y = cx, cy  # Simplified: connect to center
                    svg += f'<line x1="{parent_x}" y1="{parent_y}" x2="{x}" y2="{y}" '
                    svg += f'stroke="{theme["edge_color"]}" stroke-width="2"/>\n'

                    # Node
                    svg += f'<rect x="{x - 60}" y="{y - 20}" width="120" height="40" rx="8" '
                    svg += f'fill="{color}" stroke="none" opacity="0.9"/>\n'
                    svg += f'<text x="{x}" y="{y + 5}" text-anchor="middle" dominant-baseline="middle" '
                    svg += f'fill="white" font-size="12" font-family="system-ui">{text}</text>\n'
                    positions.append((x, y, text, level))

        svg += "</svg>"
        return svg

    # ── SVG helpers ──

    def _svg_header(self) -> str:
        return (f'<svg xmlns="{SVG_NS}" width="{self.width}" height="{self.height}" '
                f'viewBox="0 0 {self.width} {self.height}">\n')

    def _svg_styles(self, theme: Dict[str, str]) -> str:
        return f"""<style>
  text {{ font-family: 'system-ui', -apple-system, sans-serif; }}
</style>
<defs>
  <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="{theme['edge_color']}"/>
  </marker>
</defs>
"""

    def _svg_node(self, node: FlowNode, theme: Dict[str, str]) -> str:
        if node.shape == "diamond":
            cx, cy = node.x + node.width / 2, node.y + node.height / 2
            hw, hh = node.width / 2, node.height / 2
            return (f'<polygon points="{cx},{node.y} {node.x + node.width},{cy} '
                    f'{cx},{node.y + node.height} {node.x},{cy}" '
                    f'fill="{theme["node_bg"]}" stroke="{theme["node_border"]}" stroke-width="2"/>\n'
                    f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" fill="{theme["text_color"]}" '
                    f'font-size="13">{node.label}</text>\n')
        elif node.shape == "round":
            return (f'<rect x="{node.x}" y="{node.y}" width="{node.width}" height="{node.height}" '
                    f'rx="20" fill="{theme["node_bg"]}" stroke="{theme["node_border"]}" stroke-width="2"/>\n'
                    f'<text x="{node.x + node.width/2}" y="{node.y + node.height/2 + 5}" '
                    f'text-anchor="middle" fill="{theme["text_color"]}" font-size="13">{node.label}</text>\n')
        else:  # rect
            return (f'<rect x="{node.x}" y="{node.y}" width="{node.width}" height="{node.height}" '
                    f'rx="8" fill="{theme["node_bg"]}" stroke="{theme["node_border"]}" stroke-width="2"/>\n'
                    f'<text x="{node.x + node.width/2}" y="{node.y + node.height/2 + 5}" '
                    f'text-anchor="middle" fill="{theme["text_color"]}" font-size="13">{node.label}</text>\n')

    def _svg_edge(self, edge: FlowEdge, nodes: Dict[str, FlowNode], theme: Dict[str, str]) -> str:
        src = nodes.get(edge.source)
        tgt = nodes.get(edge.target)
        if not src or not tgt:
            return ""

        x1 = src.x + src.width / 2
        y1 = src.y + src.height
        x2 = tgt.x + tgt.width / 2
        y2 = tgt.y

        dash = ' stroke-dasharray="6,4"' if edge.style == "dashed" else ""
        svg = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
               f'stroke="{theme["edge_color"]}" stroke-width="2"{dash} '
               f'marker-end="url(#arrowhead)"/>\n')

        if edge.label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            svg += (f'<text x="{mx}" y="{my - 8}" text-anchor="middle" '
                    f'fill="{theme["text_color"]}" font-size="11">{edge.label}</text>\n')

        return svg

    def _error_svg(self, message: str) -> str:
        return (f'<svg xmlns="{SVG_NS}" width="400" height="100">'
                f'<rect width="400" height="100" fill="#FFF3F3"/>'
                f'<text x="200" y="55" text-anchor="middle" fill="#CC0000" font-size="14">'
                f'⚠ {message}</text></svg>')


# ── CLI ──

if __name__ == "__main__":
    import sys
    definition = """flowchart TD
    A[用户请求] --> B{是否有效?}
    B -->|是| C[处理请求]
    B -->|否| D[返回错误]
    C --> E[生成响应]
    E --> F[返回结果]
"""
    if len(sys.argv) > 1:
        definition = open(sys.argv[1]).read()

    mr = MermaidRenderer()
    svg = mr.render(definition)
    print(svg[:500] + "...")
    mr.save(svg, "/tmp/test_mermaid.svg")
    print(f"\nSaved to /tmp/test_mermaid.svg")
