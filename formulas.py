"""Teks rumus dan penjelasan otomatis; semua kalimat disusun dari hasil simulasi yang sedang tampil."""
from collections import Counter


def num(value, digits=6):
    """Angka dengan koma desimal, contoh 0,970951."""
    return f"{value:.{digits}f}".replace(".", ",")


def entropy_expression(counts):
    total = sum(counts)
    return " + ".join(f"(−{c}/{total} · log₂({c}/{total}))" for c in counts)


def explain(node, evaluation):
    """Rumus Entropy, Gain, Split Info, dan Gain Ratio untuk satu kolom pada satu node."""
    total = node.size
    branches = evaluation.branches
    weighted = " + ".join(f"({b.size}/{total} · {num(b.entropy)})" for b in branches)
    split_terms = " + ".join(f"(−{b.size}/{total} · log₂({b.size}/{total}))" for b in branches)
    return {
        "entropy": [(b.value, f"{entropy_expression(b.counts)} = {num(b.entropy)}") for b in branches],
        "gain": f"{num(node.entropy)} − ({weighted}) = {num(evaluation.gain)}",
        "split_info": f"{split_terms} = {num(evaluation.split_info)}",
        "gain_ratio": f"{num(evaluation.gain)} / {num(evaluation.split_info)} = {num(evaluation.gain_ratio)}",
    }


def _conditions(case, tree, node):
    """Syarat dari root sampai node, contoh ['Status Kerja = Tidak Bekerja']."""
    chain, by_id = [], tree.by_id
    while node.parent_id:
        parent = by_id[node.parent_id]
        chain.append(f"{case.attributes[parent.split]['label']} = {node.branch_value}")
        node = parent
    return chain[::-1]


def describe_tree(case, tree):
    """Ringkasan pohon utuh."""
    label = lambda key: case.attributes[key]["label"]  # noqa: E731
    root, leaves = tree.root, tree.leaves
    rivals = [ev for ev in root.evaluations if ev.attribute != root.split]
    versus = ", ".join(f"{label(ev.attribute)} ({num(ev.gain_ratio)})" for ev in rivals)
    used = list(dict.fromkeys(node.split for node in tree.split_nodes))
    per_class = Counter(leaf.label for leaf in leaves)
    biggest = max(leaves, key=lambda leaf: leaf.size)
    rule = " dan ".join(_conditions(case, tree, biggest))

    lines = [
        f"Root dipecah menurut {label(root.split)} dengan Gain Ratio {num(root.best.gain_ratio)}"
        + (f", mengalahkan {versus}." if versus else "."),
        f"Pohon ini punya {len(tree.nodes())} node dan {len(leaves)} daun dengan kedalaman {tree.depth}: "
        + ", ".join(f"{per_class[name]} daun {name}" for name in case.classes if per_class[name]) + ".",
        f"Kolom yang dipakai: {', '.join(label(key) for key in used)}.",
        f"Daun dengan data terbanyak: jika {rule}, maka {biggest.label} ({biggest.size} data).",
    ]
    return lines


def describe_step(case, tree, node):
    """Penjelasan satu langkah pemecahan node, mengikuti gambar pohon pada langkah itu."""
    label = lambda key: case.attributes[key]["label"]  # noqa: E731
    best = node.best
    rivals = [ev for ev in node.evaluations if ev.attribute != node.split]
    if rivals:
        versus = ", ".join(f"{label(ev.attribute)} ({num(ev.gain_ratio)})" for ev in rivals)
        reason = f"karena Gain Ratio-nya ({num(best.gain_ratio)}) tertinggi dibanding {versus}"
    else:
        reason = f"karena hanya itu kolom yang tersisa (Gain Ratio {num(best.gain_ratio)})"

    lines = [f"Node {node.id} dipecah menurut {label(node.split)} {reason}. Terbentuk {len(node.children)} cabang."]
    leaves = [c for c in node.children if c.is_leaf]
    pending = [c for c in node.children if not c.is_leaf]
    if leaves:
        lines.append("Langsung menjadi daun: " + "; ".join(
            f"{c.branch_value} → {c.label} ({c.size} data)" for c in leaves) + ".")
    if pending:
        lines.append("Masih campuran dan dihitung berikutnya: " + "; ".join(
            f"{c.branch_value} (Node {c.id}, {c.size} data)" for c in pending) + ".")
    else:
        lines.append("Semua cabang sudah satu kelas, jadi tidak ada node yang perlu dipecah lagi dari sini.")
    return lines


def describe_path(case, tree, prediction):
    """Penjelasan jalur penelusuran data baru pada satu pohon."""
    label = lambda key: case.attributes[key]["label"]  # noqa: E731
    by_id = tree.by_id
    lines = [f"Data baru masuk di Node {prediction.path[0]}."]
    for index, (attribute, value) in enumerate(prediction.decisions):
        node_id = prediction.path[index]
        if index + 1 < len(prediction.path):
            target = by_id[prediction.path[index + 1]]
            where = f"daun Node {target.id} ({target.size} data)" if target.is_leaf else f"Node {target.id}"
            lines.append(f"Di Node {node_id}, {label(attribute)} = {value}, sehingga lanjut ke {where}.")
        else:
            lines.append(
                f"Di Node {node_id}, {label(attribute)} = {value} belum pernah muncul pada cabang ini, "
                f"sehingga dipakai kelas mayoritas node tersebut."
            )
    lines.append(f"Hasil pohon {tree.number}: {prediction.label}.")
    return lines
