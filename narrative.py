"""Penjelasan teks yang berubah mengikuti hasil simulasi pohon."""
from formulas import num


def _label(case, key):
    return case.attributes[key]["label"]


def join_and(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " dan " + items[-1]


def tree_story(tree, case):
    """Ringkasan satu pohon: kolom akar, kolom yang dipakai, dan jumlah daun per kelas."""
    root = tree.root
    others = [ev for ev in root.evaluations if ev is not root.best]
    text = (f"Pohon {tree.number} dimulai dari {_label(case, root.split)} karena Gain Ratio-nya tertinggi "
            f"({num(root.best.gain_ratio)})")
    if others:
        rivals = join_and(f"{_label(case, ev.attribute)} ({num(ev.gain_ratio)})" for ev in others)
        tie = any(round(ev.gain_ratio, 9) == round(root.best.gain_ratio, 9) for ev in others)
        text += f", dibanding {rivals}" + ("; nilainya seri sehingga dipilih kolom yang lebih dulu" if tie else "")
    text += "."

    used = list(dict.fromkeys(node.split for node in tree.split_nodes))
    leaves = tree.leaves
    per_class = join_and(
        f"{sum(1 for leaf in leaves if leaf.label == name)} daun {name}" for name in case.classes
    )
    return [
        text,
        f"Pohon ini memakai kolom {join_and(_label(case, key) for key in used)}, terdiri dari "
        f"{len(tree.nodes())} node dengan kedalaman {tree.depth}, dan menghasilkan {per_class}.",
    ]


def leaf_rules(tree, case):
    """Aturan jika-maka untuk setiap daun, urut dari kiri ke kanan pada gambar."""
    nodes, rules = tree.by_id, []
    for leaf in tree.leaves:
        conditions, node = [], leaf
        while node.parent_id:
            parent = nodes[node.parent_id]
            conditions.append((_label(case, parent.split), node.branch_value))
            node = parent
        rules.append({"id": leaf.id, "conditions": conditions[::-1], "label": leaf.label,
                      "size": leaf.size, "pure": leaf.is_pure})
    return rules


def step_story(tree, node, case):
    """Penjelasan gambar pohon setelah satu node dipecah."""
    leaves = [c for c in node.children if c.is_leaf]
    pending = [c for c in node.children if not c.is_leaf]
    text = (f"Node {node.id} dipecah berdasarkan {_label(case, node.split)} "
            f"(Gain Ratio {num(node.best.gain_ratio)}), menghasilkan {len(node.children)} cabang.")
    if leaves:
        text += " Daun terbentuk: " + join_and(f"{c.branch_value} menjadi {c.label}" for c in leaves) + "."
    if pending:
        text += " Masih harus dihitung: " + join_and(f"Node {c.id}" for c in pending) + "."
    else:
        remaining = len(tree.split_nodes) - (tree.split_nodes.index(node) + 1)
        if remaining == 0:
            text += " Semua cabang sudah homogen, pohon selesai."
    return text


def path_story(tree, prediction, case):
    """Penjelasan jalur penelusuran data baru pada satu pohon."""
    leaf = tree.by_id[prediction.path[-1]]
    route = " → ".join(f"{_label(case, attr)} = {value}" for attr, value in prediction.decisions)
    if prediction.unseen:
        tail = (f"nilai tersebut tidak pernah muncul pada cabang ini, sehingga dipakai kelas mayoritas "
                f"Node {leaf.id} ({leaf.majority})")
    else:
        kind = "semuanya" if leaf.is_pure else "mayoritas"
        tail = f"berhenti di daun Node {leaf.id} ({leaf.size} data, {kind} {leaf.label})"
    return f"{route}, {tail}."


def vote_story(vote, case):
    parts = []
    for name in case.classes:
        voters = vote.voters(name)
        parts.append(f"{name}: " + (f"pohon {', '.join(map(str, voters))}" if voters else "tidak ada"))
    top, total = max(vote.tally), sum(vote.tally)
    return f"Perolehan suara: {'; '.join(parts)}. Pemenang meraih {top} dari {total} suara."
