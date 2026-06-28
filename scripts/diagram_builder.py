"""Diagram Builder - 图表构建器

提供高级 API 创建常见图表类型：

- 流程图 (Flowchart)
- 序列图 (Sequence Diagram)
- 思维导图 (Mind Map)
- 架构图 (Architecture Diagram)
- 数据流图 (Data Flow Diagram)

"""

from dataclasses import dataclass
from typing import Optional
from .excalidraw_svg import (
    ExcalidrawElement, ElementType, FillStyle, StrokeStyle,
    rect, ellipse, arrow, line, text, render_scene_to_svg,
)


@dataclass
class DiagramNode:
    """图表节点"""
    id: str
    label: str
    shape: str = "rectangle"  # rectangle, ellipse, diamond
    x: float = 0
    y: float = 0
    width: float = 150
    height: float = 60
    color: str = "#a5d8ff"
    stroke: str = "#1e1e1e"


@dataclass
class DiagramEdge:
    """图表边"""
    source: str
    target: str
    label: str = ""
    style: str = "solid"  # solid, dashed, dotted


class DiagramBuilder:
    """图表构建器
    
    提供声明式 API 创建常见图表：
    
    ```python
    builder = DiagramBuilder()
    builder.add_node("start", "开始", shape="ellipse")
    builder.add_node("process", "处理数据")
    builder.add_edge("start", "process")
    svg = builder.render()
    ```
    """
    
    def __init__(self, width: float = 800, height: float = 600,
                 background: str = "white"):
        self.width = width
        self.height = height
        self.background = background
        self.nodes: dict[str, DiagramNode] = {}
        self.edges: list[DiagramEdge] = []
        self._auto_layout = True
    
    def add_node(self, node_id: str, label: str, **kwargs) -> "DiagramBuilder":
        """添加节点"""
        self.nodes[node_id] = DiagramNode(id=node_id, label=label, **kwargs)
        return self
    
    def add_edge(self, source: str, target: str, label: str = "",
                 style: str = "solid") -> "DiagramBuilder":
        """添加边"""
        self.edges.append(DiagramEdge(source=source, target=target,
                                     label=label, style=style))
        return self
    
    def set_layout(self, positions: dict[str, tuple[float, float]]) -> "DiagramBuilder":
        """手动设置节点位置"""
        for node_id, (x, y) in positions.items():
            if node_id in self.nodes:
                self.nodes[node_id].x = x
                self.nodes[node_id].y = y
        self._auto_layout = False
        return self
    
    def _auto_layout_nodes(self):
        """自动布局节点（简化版层次布局）"""
        if not self._auto_layout:
            return
        
        # 找到根节点（没有入边的节点）
        targets = {e.target for e in self.edges}
        roots = [n for n in self.nodes if n not in targets]
        
        if not roots:
            # 如果没有根节点，使用第一个节点
            roots = [list(self.nodes.keys())[0]]
        
        # BFS 层次布局
        visited = set()
        levels: list[list[str]] = []
        
        queue = roots[:]
        while queue:
            level = []
            next_queue = []
            
            for node_id in queue:
                if node_id in visited:
                    continue
                visited.add(node_id)
                level.append(node_id)
                
                # 找到子节点
                for edge in self.edges:
                    if edge.source == node_id and edge.target not in visited:
                        next_queue.append(edge.target)
            
            if level:
                levels.append(level)
            queue = next_queue
        
        # 处理未访问的节点
        remaining = [n for n in self.nodes if n not in visited]
        if remaining:
            levels.append(remaining)
        
        # 计算位置
        margin_x = 100
        margin_y = 80
        level_height = 100
        
        for level_idx, level in enumerate(levels):
            level_width = len(level) * 200
            start_x = (self.width - level_width) / 2
            
            for node_idx, node_id in enumerate(level):
                node = self.nodes[node_id]
                node.x = start_x + node_idx * 200 + (200 - node.width) / 2
                node.y = margin_y + level_idx * level_height
    
    def _build_elements(self) -> tuple[list[ExcalidrawElement], dict[str, str]]:
        """构建元素列表"""
        self._auto_layout_nodes()
        
        elements = []
        texts = {}
        
        # 渲染节点
        for node in self.nodes.values():
            if node.shape == "ellipse":
                elem = ellipse(node.x, node.y, node.width, node.height,
                             stroke=node.stroke, fill=node.color, roughness=1.0)
            elif node.shape == "diamond":
                # 菱形用旋转的正方形模拟
                elem = rect(node.x, node.y, node.width, node.height,
                          stroke=node.stroke, fill=node.color, roughness=1.0)
            else:
                elem = rect(node.x, node.y, node.width, node.height,
                          stroke=node.stroke, fill=node.color, roughness=1.0)
            
            elements.append(elem)
            
            # 文本
            t = text(node.x, node.y, node.width, node.height, stroke=node.stroke)
            elements.append(t)
            texts[t.id] = node.label
        
        # 渲染边
        for edge in self.edges:
            source = self.nodes[edge.source]
            target = self.nodes[edge.target]
            
            # 计算连接点（简化版：使用节点中心）
            x1 = source.x + source.width / 2
            y1 = source.y + source.height
            x2 = target.x + target.width / 2
            y2 = target.y
            
            elem = arrow(x1, y1, x2, y2, roughness=1.0)
            elements.append(elem)
            
            # 边标签
            if edge.label:
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                t = text(mid_x - 40, mid_y - 15, 80, 30)
                elements.append(t)
                texts[t.id] = edge.label
        
        return elements, texts
    
    def render(self) -> str:
        """渲染为 SVG"""
        elements, texts = self._build_elements()
        return render_scene_to_svg(
            elements, self.width, self.height,
            self.background, texts
        )
    
    def save(self, path: str):
        """保存到文件"""
        svg = self.render()
        with open(path, "w") as f:
            f.write(svg)


# === 预设图表模板 ===

def flowchart(steps: list[tuple[str, str]], width: float = 800,
              height: float = None) -> DiagramBuilder:
    """创建流程图
    
    Args:
        steps: [(id, label), ...] 步骤列表
        width: 画布宽度
        height: 画布高度（自动计算）
    
    Returns:
        DiagramBuilder 实例
    """
    if height is None:
        height = len(steps) * 100 + 100
    
    builder = DiagramBuilder(width, height)
    
    for i, (step_id, label) in enumerate(steps):
        # 第一个和最后一个用椭圆
        if i == 0 or i == len(steps) - 1:
            builder.add_node(step_id, label, shape="ellipse", color="#b2f2bb")
        else:
            builder.add_node(step_id, label, shape="rectangle", color="#a5d8ff")
        
        # 连接到前一个
        if i > 0:
            builder.add_edge(steps[i-1][0], step_id)
    
    return builder


def sequence_diagram(participants: list[str],
                     messages: list[tuple[str, str, str]],
                     width: float = 800, height: float = None) -> DiagramBuilder:
    """创建序列图
    
    Args:
        participants: 参与者列表
        messages: [(from, to, message), ...] 消息列表
        width: 画布宽度
        height: 画布高度（自动计算）
    
    Returns:
        DiagramBuilder 实例
    """
    if height is None:
        height = len(messages) * 60 + 200
    
    builder = DiagramBuilder(width, height)
    
    # 添加参与者
    participant_width = 100
    spacing = (width - participant_width * len(participants)) / (len(participants) + 1)
    
    for i, name in enumerate(participants):
        x = spacing + i * (participant_width + spacing)
        builder.add_node(name, name, shape="rectangle", color="#d0bfff",
                        x=x, y=50, width=participant_width, height=40)
    
    # 添加消息
    for i, (from_p, to_p, msg) in enumerate(messages):
        from_node = builder.nodes[from_p]
        to_node = builder.nodes[to_p]
        
        y = 100 + i * 60
        builder.add_edge(from_p, to_p, label=msg)
    
    return builder


def mind_map(center: str, branches: list[tuple[str, list[str]]],
             width: float = 800, height: float = 600) -> DiagramBuilder:
    """创建思维导图
    
    Args:
        center: 中心主题
        branches: [(branch_name, [sub_items]), ...] 分支列表
        width: 画布宽度
        height: 画布高度
    
    Returns:
        DiagramBuilder 实例
    """
    builder = DiagramBuilder(width, height)
    
    # 中心节点
    center_x = width / 2 - 75
    center_y = height / 2 - 30
    builder.add_node("center", center, shape="ellipse", color="#ffd8a8",
                    x=center_x, y=center_y, width=150, height=60)
    
    # 分支
    branch_spacing = width / (len(branches) + 1)
    
    for i, (branch_name, sub_items) in enumerate(branches):
        branch_x = branch_spacing * (i + 1) - 60
        branch_y = height / 2 - 150
        
        builder.add_node(f"branch_{i}", branch_name, shape="rectangle",
                        color="#a5d8ff", x=branch_x, y=branch_y)
        builder.add_edge("center", f"branch_{i}")
        
        # 子项
        item_spacing = 100
        start_y = branch_y - item_spacing * len(sub_items) / 2
        
        for j, item in enumerate(sub_items):
            item_y = start_y + j * item_spacing
            builder.add_node(f"item_{i}_{j}", item, shape="rectangle",
                           color="#b2f2bb", x=branch_x, y=item_y, width=120, height=40)
            builder.add_edge(f"branch_{i}", f"item_{i}_{j}")
    
    return builder


def architecture(layers: list[tuple[str, list[str]]],
                 width: float = 800, height: float = 600) -> DiagramBuilder:
    """创建架构图
    
    Args:
        layers: [(layer_name, [components]), ...] 层级列表
        width: 画布宽度
        height: 画布高度
    
    Returns:
        DiagramBuilder 实例
    """
    builder = DiagramBuilder(width, height)
    
    layer_height = height / (len(layers) + 1)
    
    for i, (layer_name, components) in enumerate(layers):
        y = layer_height * (i + 0.5)
        
        # 层背景（用大矩形表示）
        layer_bg = rect(20, y - 10, width - 40, layer_height - 20,
                       fill="#f8f9fa", stroke="#868e96", roughness=0.5)
        builder.nodes[f"layer_{i}"] = DiagramNode(
            id=f"layer_{i}", label=layer_name,
            x=20, y=y - 10, width=width - 40, height=layer_height - 20,
            color="#f8f9fa", stroke="#868e96"
        )
        
        # 组件
        component_width = (width - 60) / len(components) - 10
        
        for j, comp in enumerate(components):
            x = 30 + j * (component_width + 10) + (component_width - 100) / 2
            builder.add_node(f"comp_{i}_{j}", comp, shape="rectangle",
                           color="#a5d8ff", x=x, y=y + 20, width=100, height=40)
            
            # 连接到上一层
            if i > 0:
                # 简化：连接到上一层的第一个组件
                prev_comp = f"comp_{i-1}_{0}"
                if prev_comp in builder.nodes:
                    builder.add_edge(prev_comp, f"comp_{i}_{j}")
    
    return builder


# === 使用示例 ===

if __name__ == "__main__":
    # 流程图
    fc = flowchart([
        ("start", "开始"),
        ("input", "输入数据"),
        ("process", "处理数据"),
        ("output", "输出结果"),
        ("end", "结束"),
    ])
    fc.save("/tmp/flowchart.svg")
    print("流程图已保存: /tmp/flowchart.svg")
    
    # 思维导图
    mm = mind_map("AI Agent", [
        ("感知", ["视觉", "听觉", "触觉"]),
        ("决策", ["规划", "推理", "学习"]),
        ("行动", ["移动", "操作", "交流"]),
    ])
    mm.save("/tmp/mindmap.svg")
    print("思维导图已保存: /tmp/mindmap.svg")
