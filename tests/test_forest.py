"""Uji inti algoritme (cocok dengan perhitungan manual BLT) dan fitur studi kasus buatan sendiri."""
import unittest

from cases import BLT, CASES
from custom_case import CaseError, EXAMPLE_CSV, build_case, parse_table
from forest import Tree, build_forest, build_node
from tree_view import layout

# Sampel bootstrap dan kolom acak dari perhitungan manual pada laporan.
REPORT_SAMPLE = (14, 14, 1, 2, 2, 6, 14, 3, 12, 13, 11, 14, 5, 5, 10)
REPORT_ROOTS = [("rumah", "kerja"), ("rumah", "kendaraan"), ("rumah", "lansia"),
                ("kerja", "kendaraan"), ("kerja", "lansia"), ("kendaraan", "lansia")]
REPORT_COLUMNS = {
    (1, "1.3"): ("rumah", "lansia"), (2, "1.1"): ("rumah", "kerja"), (2, "1.2"): ("kerja", "lansia"),
    (3, "1.1"): ("kendaraan", "lansia"), (3, "1.2"): ("kerja", "lansia"), (3, "1.3"): ("kerja", "kendaraan"),
    (4, "1.3"): ("kendaraan", "lansia"), (5, "1.3"): ("rumah", "lansia"),
    (6, "1.1"): ("kerja", "lansia"), (6, "1.2"): ("rumah", "kerja"),
}


def report_tree(number):
    rows = [BLT.row(no) for no in REPORT_SAMPLE]
    pick = lambda node_id, available: REPORT_COLUMNS[(number, node_id)]  # noqa: E731
    root_columns = REPORT_ROOTS[number - 1]
    return Tree(number, rows, root_columns, build_node(BLT, rows, "1", (), pick, root_columns=root_columns))


class ReportRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trees = {n: report_tree(n) for n in range(1, 7)}

    def test_root_splits_match_report(self):
        expected = {1: ("kerja", 0.540512), 2: ("kendaraan", 0.186403), 3: ("rumah", 0.162212),
                    4: ("kerja", 0.540512), 5: ("kerja", 0.540512), 6: ("kendaraan", 0.186403)}
        for number, (attribute, gain_ratio) in expected.items():
            root = self.trees[number].root
            self.assertEqual(root.split, attribute)
            self.assertAlmostEqual(root.best.gain_ratio, gain_ratio, places=6)

    def test_root_entropy(self):
        self.assertAlmostEqual(self.trees[1].root.entropy, 0.970951, places=6)

    def test_inner_nodes_match_report(self):
        node = self.trees[3].by_id["1.3"]
        self.assertEqual(node.split, "kerja")
        self.assertAlmostEqual(node.best.gain_ratio, 0.526589, places=6)

    def test_gain_ratio_tie_prefers_first_candidate(self):
        self.assertEqual(self.trees[4].by_id["1.3"].split, "kendaraan")

    def test_votes_match_report(self):
        labels = [self.trees[n].predict(BLT.default_query).label for n in range(1, 7)]
        self.assertEqual(labels, ["Layak", "Tidak Layak", "Tidak Layak", "Tidak Layak", "Layak", "Tidak Layak"])


class ForestTest(unittest.TestCase):
    def test_same_seed_gives_same_forest(self):
        for case in CASES.values():
            first = build_forest(case, seed=7, n_trees=5)
            second = build_forest(case, seed=7, n_trees=5)
            self.assertEqual([t.root.split for t in first.trees], [t.root.split for t in second.trees])
            self.assertEqual(len(first.trees), 5)

    def test_every_leaf_is_labelled_and_vote_counts_trees(self):
        for case in CASES.values():
            forest = build_forest(case, seed=3, n_trees=8, per_tree_bootstrap=True)
            for tree in forest.trees:
                self.assertTrue(all(leaf.label for leaf in tree.leaves))
            self.assertEqual(sum(forest.vote(case.default_query).tally), 8)

    def test_sibling_edge_labels_never_overlap(self):
        for case in CASES.values():
            for seed in range(1, 15):
                for tree in build_forest(case, seed=seed, n_trees=6, per_tree_bootstrap=True).trees:
                    edges = sorted(layout(tree.root).edges, key=lambda e: (e.ly, e.lx))
                    for a, b in zip(edges, edges[1:]):
                        if a.ly == b.ly:
                            self.assertGreaterEqual(b.lx - a.lx, (a.lw + b.lw) / 2, (case.key, seed))


class ViewBoxTest(unittest.TestCase):
    def test_view_box_contains_every_visible_node_and_label(self):
        for case in CASES.values():
            for tree in build_forest(case, seed=5, n_trees=6, per_tree_bootstrap=True).trees:
                lay = layout(tree.root)
                steps = [None, *range(1, len(tree.split_nodes) + 1)]
                for step in steps:
                    visible = tree.visible_ids(step)
                    box = lay.view_box(visible)
                    for node_id in visible:
                        p = lay.positions[node_id]
                        self.assertGreaterEqual(p.x - lay.node_w / 2, box.x)
                        self.assertLessEqual(p.x + lay.node_w / 2, box.x + box.w)
                        self.assertGreaterEqual(p.y - lay.node_h / 2, box.y)
                        self.assertLessEqual(p.y + lay.node_h / 2, box.y + box.h)


class CustomCaseTest(unittest.TestCase):
    def test_example_builds_and_runs(self):
        case = build_case("k1", "Contoh", EXAMPLE_CSV)
        self.assertEqual(case.target, "Beli")
        self.assertEqual(case.classes, ("Tidak", "Ya"))
        self.assertEqual(len(case.data), 12)
        forest = build_forest(case, seed=1, n_trees=4)
        self.assertEqual(sum(forest.vote(case.default_query).tally), 4)

    def test_positive_class_can_be_chosen(self):
        case = build_case("k1", "Contoh", EXAMPLE_CSV, positive="Tidak")
        self.assertEqual(case.classes, ("Ya", "Tidak"))

    def test_other_delimiters_and_target_column(self):
        text = "a;b;c\nx;p;1\ny;q;2\nx;q;1\ny;p;2\nx;p;1"
        self.assertEqual(parse_table(text)[0], ["a", "b", "c"])
        case = build_case("k1", "T", text.replace(";", "\t"), target="a")
        self.assertEqual(case.target, "a")

    def test_invalid_data_reports_clear_errors(self):
        bad = {
            "kosong": "",
            "sel kosong": "a,b,c\nx,,1\ny,q,2\nx,q,1\ny,p,2",
            "tiga kelas": "a,b,c\nx,p,1\ny,q,2\nx,q,3\ny,p,1",
            "terlalu sedikit baris": "a,b,c\nx,p,1\ny,q,2",
            "kolom kurang": "a,b,c\nx,p\ny,q,2\nx,q,1\ny,p,2",
        }
        for name, text in bad.items():
            with self.assertRaises(CaseError, msg=name):
                build_case("k1", "T", text)


if __name__ == "__main__":
    unittest.main()
