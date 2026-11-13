"""Aplikasi Flask: web simulasi Random Forest dengan studi kasus bawaan dan buatan sendiri."""
import os

from flask import Flask, redirect, render_template, request, session, url_for
from jinja2 import pass_context

import config
import custom_case
from cases import CASES, DEFAULT_CASE
from forest import build_forest
from formulas import describe_path, describe_step, describe_tree, explain, num
from tree_view import layout, size_class

app = Flask(__name__)
# Studi kasus buatan sendiri disimpan di cookie session; set SECRET_KEY di server produksi.
app.secret_key = os.environ.get("SECRET_KEY", "ganti-di-produksi")
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
COOKIE_LIMIT = 3800

app.jinja_env.filters["num"] = num
app.jinja_env.globals.update(
    explain=explain, describe_tree=describe_tree, describe_step=describe_step, describe_path=describe_path,
    size_class=size_class,
)


@app.template_filter("slug")
@pass_context
def class_slug(context, label):
    """'pos' untuk kelas positif (indeks 1), 'neg' untuk kelas negatif; dipakai sebagai kelas CSS."""
    return "pos" if label == context["classes"][1] else "neg"


def all_cases():
    return {**CASES, **custom_case.load_saved(session.get("custom", {}))}


def current_case():
    cases = all_cases()
    return cases.get(request.args.get("kasus"), cases[DEFAULT_CASE])


@app.context_processor
def inject_globals():
    case = current_case()

    def link(endpoint, **values):
        """url_for yang mempertahankan pilihan studi kasus."""
        if case.key != DEFAULT_CASE:
            values["kasus"] = case.key
        return url_for(endpoint, **values)

    return {
        "app_title": config.APP_TITLE,
        "case": case,
        "cases": list(all_cases().values()),
        "attributes": case.attributes,
        "classes": case.classes,
        "data": case.data,
        "link": link,
    }


def read_int(raw, default, low, high):
    try:
        return min(max(int(raw), low), high)
    except (TypeError, ValueError):
        return default


def read_settings(args):
    return {
        "seed": read_int(args.get("seed"), config.DEFAULT_SEED, *config.SEED_RANGE),
        "n_trees": read_int(args.get("n_trees"), config.DEFAULT_TREES, *config.TREE_RANGE),
        "per_tree": args.get("per_tree") == "1",
    }


def read_query(args, case):
    """Nilai yang tidak dikenal diganti dengan nilai bawaan agar input selalu valid."""
    return {
        key: args.get(key) if args.get(key) in spec["values"] else case.default_query[key]
        for key, spec in case.attributes.items()
    }


@app.route("/")
def index():
    return render_template("index.html", page="beranda")


@app.route("/dataset")
def dataset():
    case = current_case()
    value_stats = {
        key: [(value, case.counts([r for r in case.data if r[key] == value])) for value in spec["values"]]
        for key, spec in case.attributes.items()
    }
    return render_template("dataset.html", page="dataset", value_stats=value_stats,
                           totals=case.counts(case.data))


@app.route("/simulasi")
def simulasi():
    case = current_case()
    settings = read_settings(request.args)
    query = read_query(request.args, case)
    forest = build_forest(case, settings["seed"], settings["n_trees"], settings["per_tree"])
    return render_template(
        "simulasi.html",
        page="simulasi",
        settings=settings,
        query=query,
        forest=forest,
        vote=forest.vote(query),
        layouts={tree.number: layout(tree.root) for tree in forest.trees},
        tree_range=config.TREE_RANGE,
    )


def fits_in_cookie(saved):
    serializer = app.session_interface.get_signing_serializer(app)
    return len(serializer.dumps({"custom": saved})) <= COOKIE_LIMIT


@app.route("/kasus-baru", methods=["GET", "POST"])
def kasus_baru():
    saved = dict(session.get("custom", {}))
    form = {"title": "", "csv": "", "target": "", "positive": ""}
    preview, headers, class_options, errors = None, [], [], []

    if request.method == "POST":
        form = {name: request.form.get(name, "") for name in form}
        upload = request.files.get("file")
        if upload and upload.filename:
            form["csv"] = upload.read().decode("utf-8-sig", errors="replace")
        try:
            headers, rows = custom_case.parse_table(form["csv"])
            form["target"] = form["target"] if form["target"] in headers else headers[-1]
            class_options = custom_case.distinct(row[headers.index(form["target"])] for row in rows)
            preview = custom_case.build_case("pratinjau", form["title"], form["csv"], form["target"], form["positive"])
            form["positive"] = preview.classes[1]

            if request.form.get("action") == "save":
                if len(saved) >= custom_case.MAX_CASES:
                    raise custom_case.CaseError([f"Maksimal {custom_case.MAX_CASES} studi kasus sendiri, hapus salah satu dulu."])
                key = custom_case.next_key(saved)
                saved[key] = {"title": preview.title, "csv": form["csv"], "target": form["target"],
                              "positive": form["positive"]}
                if not fits_in_cookie(saved):
                    raise custom_case.CaseError(["Data terlalu besar untuk disimpan di browser. Kurangi jumlah baris."])
                session["custom"] = saved
                return redirect(url_for("simulasi", kasus=key))
        except custom_case.CaseError as error:
            errors = error.messages
            preview = None

    return render_template(
        "kasus_baru.html", page="kasus", form=form, preview=preview, headers=headers,
        class_options=class_options, errors=errors, saved=custom_case.load_saved(saved),
        limits=custom_case, example_csv=custom_case.EXAMPLE_CSV, example_title=custom_case.EXAMPLE_TITLE,
    )


@app.post("/kasus-baru/hapus/<key>")
def hapus_kasus(key):
    saved = dict(session.get("custom", {}))
    saved.pop(key, None)
    session["custom"] = saved
    return redirect(url_for("kasus_baru"))


@app.route("/panduan")
def panduan():
    return render_template("panduan.html", page="panduan")


if __name__ == "__main__":
    app.run(debug=True)
