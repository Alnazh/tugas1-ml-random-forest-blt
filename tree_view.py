"""Tata letak pohon keputusan; template menggambar hasilnya sebagai SVG."""
from dataclasses import dataclass
from typing import NamedTuple

NODE_W, NODE_H = 156, 52
MIN_H_GAP, V_GAP = 164, 120
MARGIN = 16
SHADOW, LABEL_H = 4, 24
LABEL_CHAR_W, LABEL_PAD = 7, 22


class Point(NamedTuple):
    x: int
    y: int


class ViewBox(NamedTuple):
    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class Edge:
    parent: str
    child: str
    text: str
    d: str
    lx: int
    ly: int
    lw: int


@dataclass(frozen=True)
class Layout:
    positions: dict
    edges: list
    node_w: int = NODE_W
    node_h: int = NODE_H

    def view_box(self, visible_ids):
        """Kotak gambar yang pas untuk node yang sudah tampak: tidak ada ruang kosong di sisi mana pun."""
        half_w, half_h = self.node_w / 2, self.node_h / 2
        points = []
        for node_id in visible_ids:
            p = self.positions[node_id]
            points += [(p.x - half_w, p.y - half_h), (p.x + half_w + SHADOW, p.y + half_h + SHADOW)]
        for edge in self.edges:
            if edge.child in visible_ids:
                points += [(edge.lx - edge.lw / 2, edge.ly - LABEL_H / 2), (edge.lx + edge.lw / 2, edge.ly + LABEL_H / 2)]
        left, top = min(x for x, _ in points) - MARGIN, min(y for _, y in points) - MARGIN
        right, bottom = max(x for x, _ in points) + MARGIN, max(y for _, y in points) + MARGIN
        return ViewBox(round(left), round(top), round(right - left), round(bottom - top))


def size_class(width):
    """Dipakai CSS untuk batas lebar minimum agar teks pohon besar tetap terbaca."""
    for limit, name in ((520, "sm"), (1000, "md"), (1500, "lg")):
        if width < limit:
            return name
    return "xl"


def label_width(text):
    return len(text) * LABEL_CHAR_W + LABEL_PAD


def make_edge(parent, child, positions):
    """Label cabang diletakkan tepat di atas node anak agar label saudara tidak saling menimpa."""
    start, end = positions[parent.id], positions[child.id]
    y1, y2 = start.y + NODE_H // 2, end.y - NODE_H // 2
    mid = (y1 + y2) // 2
    return Edge(
        parent.id,
        child.id,
        child.branch_value,
        f"M{start.x} {y1} C{start.x} {mid} {end.x} {mid} {end.x} {y2}",
        end.x,
        y2 - 22,
        label_width(child.branch_value),
    )


def layout(root):
    """Daun dibagi rata secara horizontal, node induk berada di tengah anak-anaknya."""
    nodes = list(root.walk())
    # Jarak antar daun selalu lebih lebar dari label terpanjang, sehingga label tidak bertumpuk.
    widest = max((label_width(n.branch_value) for n in nodes if n.branch_value), default=0)
    h_gap = max(MIN_H_GAP, widest + 28, NODE_W + 8)

    raw_x, depth_of = {}, {}
    next_slot = 0

    def place(node, depth):
        nonlocal next_slot
        if node.children:
            xs = [place(child, depth + 1) for child in node.children]
            x = sum(xs) / len(xs)
        else:
            x = next_slot * h_gap
            next_slot += 1
        raw_x[node.id], depth_of[node.id] = x, depth
        return x

    place(root, 0)
    offset_x, offset_y = NODE_W / 2, NODE_H / 2
    positions = {
        node_id: Point(round(x + offset_x), round(offset_y + depth_of[node_id] * V_GAP))
        for node_id, x in raw_x.items()
    }
    edges = [make_edge(node, child, positions) for node in nodes for child in node.children]
    return Layout(positions, edges)
