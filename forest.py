"""Inti algoritme Random Forest dengan Gain Ratio, ditulis agar tiap langkah bisa ditampilkan."""
from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations

from config import M_FEATURES


def entropy(counts):
    total = sum(counts)
    return max(0.0, -sum(c / total * math.log2(c / total) for c in counts if c))


@dataclass
class Branch:
    value: str
    rows: list
    counts: tuple
    entropy: float
    split_term: float

    @property
    def size(self):
        return len(self.rows)


@dataclass
class Evaluation:
    attribute: str
    branches: list
    gain: float
    split_info: float
    gain_ratio: float


def evaluate_split(case, rows, attribute, parent_entropy):
    """Hitung Entropy, Gain, Split Info, dan Gain Ratio untuk satu kolom."""
    total = len(rows)
    branches = []
    for value in case.attributes[attribute]["values"]:
        subset = [row for row in rows if row[attribute] == value]
        if not subset:
            continue
        share = len(subset) / total
        counts = case.counts(subset)
        branches.append(Branch(value, subset, counts, entropy(counts), -share * math.log2(share)))

    gain = parent_entropy - sum(b.size / total * b.entropy for b in branches)
    split_info = sum(b.split_term for b in branches)
    gain_ratio = gain / split_info if split_info else 0.0
    return Evaluation(attribute, branches, gain, split_info, gain_ratio)


@dataclass
class Node:
    id: str
    rows: list
    counts: tuple
    entropy: float
    majority: str
    branch_value: str | None = None
    parent_id: str | None = None
    candidates: tuple = ()
    evaluations: list = field(default_factory=list)
    split: str | None = None
    label: str | None = None
    children: list = field(default_factory=list)

    @property
    def is_leaf(self):
        return self.split is None

    @property
    def is_pure(self):
        return sum(1 for c in self.counts if c) == 1

    @property
    def size(self):
        return len(self.rows)

    @property
    def best(self):
        return next(ev for ev in self.evaluations if ev.attribute == self.split)

    def walk(self):
        """Telusuri node ini dan seluruh turunannya (pre-order)."""
        yield self
        for child in self.children:
            yield from child.walk()


def make_picker(rng):
    """Pemilih m kolom acak dari kolom yang belum dipakai pada jalur node."""

    def pick(node_id, available):
        chosen = set(rng.sample(available, min(M_FEATURES, len(available))))
        return tuple(attr for attr in available if attr in chosen)

    return pick


def build_node(case, rows, node_id, used, pick, root_columns=None, branch_value=None, parent_id=None):
    counts = case.counts(rows)
    node = Node(node_id, rows, counts, entropy(counts), case.majority(counts), branch_value, parent_id)
    available = [attr for attr in case.attributes if attr not in used]

    if node.is_pure or not available:
        node.label = node.majority
        return node

    node.candidates = root_columns or pick(node_id, available)
    node.evaluations = [evaluate_split(case, rows, attr, node.entropy) for attr in node.candidates]
    # max() mengembalikan kandidat pertama bila Gain Ratio seri (dibulatkan agar aman dari galat float).
    best = max(node.evaluations, key=lambda ev: round(ev.gain_ratio, 9))
    node.split = best.attribute

    for index, branch in enumerate(best.branches, start=1):
        node.children.append(
            build_node(case, branch.rows, f"{node_id}.{index}", (*used, best.attribute), pick,
                       branch_value=branch.value, parent_id=node_id)
        )
    return node


@dataclass
class Prediction:
    tree_number: int
    path: list
    decisions: list
    label: str
    unseen: bool


@dataclass
class Tree:
    number: int
    sample: list
    root_columns: tuple
    root: Node

    def nodes(self):
        """Seluruh node, berurutan per level (urutan pengerjaan pada laporan)."""
        queue, ordered = [self.root], []
        while queue:
            node = queue.pop(0)
            ordered.append(node)
            queue.extend(node.children)
        return ordered

    @property
    def split_nodes(self):
        return [node for node in self.nodes() if not node.is_leaf]

    @property
    def leaves(self):
        return [node for node in self.nodes() if node.is_leaf]

    @property
    def depth(self):
        return max(len(node.id.split(".")) for node in self.nodes()) - 1

    @property
    def by_id(self):
        return {node.id: node for node in self.nodes()}

    def done_ids(self, step=None):
        """ID node yang sudah dipecah setelah `step` langkah (None = semua)."""
        nodes = self.split_nodes if step is None else self.split_nodes[:step]
        return {node.id for node in nodes}

    def visible_ids(self, step=None):
        """ID node yang sudah tampak pada gambar setelah `step` langkah."""
        if step is None:
            return {node.id for node in self.nodes()}
        done = self.done_ids(step)
        return {node.id for node in self.nodes() if node.parent_id is None or node.parent_id in done}

    def predict(self, query):
        node, path, decisions = self.root, [self.root.id], []
        while not node.is_leaf:
            value = query[node.split]
            decisions.append((node.split, value))
            child = next((c for c in node.children if c.branch_value == value), None)
            if child is None:  # nilai belum pernah muncul pada cabang ini
                return Prediction(self.number, path, decisions, node.majority, True)
            node = child
            path.append(node.id)
        return Prediction(self.number, path, decisions, node.label, False)


@dataclass
class SampleGroup:
    case: object
    trees: list
    sample: list

    @property
    def times(self):
        return Counter(row["no"] for row in self.sample)

    @property
    def counts(self):
        return self.case.counts(self.sample)

    @property
    def repeated(self):
        return sorted(no for no, times in self.times.items() if times > 1)

    @property
    def missing(self):
        return sorted(row["no"] for row in self.case.data if row["no"] not in self.times)


@dataclass
class Vote:
    classes: tuple
    predictions: list
    tally: tuple

    @property
    def winner(self):
        return self.classes[self.tally.index(max(self.tally))]

    @property
    def is_tie(self):
        return self.tally.count(max(self.tally)) > 1


@dataclass
class Forest:
    case: object
    trees: list
    per_tree_bootstrap: bool

    def sample_groups(self):
        if self.per_tree_bootstrap:
            return [SampleGroup(self.case, [tree.number], tree.sample) for tree in self.trees]
        return [SampleGroup(self.case, [tree.number for tree in self.trees], self.trees[0].sample)]

    def vote(self, query):
        predictions = [tree.predict(query) for tree in self.trees]
        counter = Counter(p.label for p in predictions)
        return Vote(self.case.classes, predictions, tuple(counter.get(name, 0) for name in self.case.classes))


def build_forest(case, seed=42, n_trees=6, per_tree_bootstrap=False):
    """Bangun hutan; seed yang sama selalu menghasilkan hutan yang sama."""
    rng = random.Random(seed)
    combos = list(combinations(case.attributes, M_FEATURES))
    roots = rng.sample(combos, n_trees) if n_trees <= len(combos) else [
        *combos, *rng.choices(combos, k=n_trees - len(combos))
    ]
    draw = lambda: [rng.choice(case.data) for _ in case.data]  # noqa: E731
    shared = draw()
    samples = [draw() if per_tree_bootstrap else shared for _ in roots]

    pick = make_picker(rng)
    trees = []
    for number, (sample, root_columns) in enumerate(zip(samples, roots), start=1):
        root = build_node(case, sample, "1", (), pick, root_columns=root_columns)
        trees.append(Tree(number, sample, root_columns, root))
    return Forest(case, trees, per_tree_bootstrap)
