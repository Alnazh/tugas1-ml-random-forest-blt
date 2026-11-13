"""Membuat studi kasus dari data CSV yang ditempel atau diunggah pengguna."""
import csv
import io
from collections import Counter

from cases import Case

MAX_CASES = 3
ROW_LIMITS = (4, 40)
ATTRIBUTE_LIMITS = (2, 6)
MAX_VALUES = 6
MAX_TITLE = 40

COLORS = ("violet", "pink", "amber", "mint")
SHAPES = ("square", "circle", "triangle", "diamond")

EXAMPLE_TITLE = "Pembelian Gadget"
EXAMPLE_CSV = """Umur,Penghasilan,Status,Ulasan,Beli
Muda,Tinggi,Lajang,Baik,Ya
Muda,Tinggi,Lajang,Buruk,Tidak
Dewasa,Tinggi,Lajang,Baik,Ya
Dewasa,Sedang,Menikah,Baik,Ya
Muda,Rendah,Menikah,Baik,Tidak
Muda,Rendah,Lajang,Buruk,Tidak
Dewasa,Rendah,Menikah,Buruk,Tidak
Dewasa,Sedang,Lajang,Buruk,Tidak
Muda,Sedang,Menikah,Baik,Ya
Dewasa,Tinggi,Menikah,Baik,Ya
Muda,Sedang,Lajang,Buruk,Tidak
Dewasa,Rendah,Lajang,Baik,Ya"""


class CaseError(ValueError):
    """Data tidak memenuhi syarat; `messages` berisi semua masalah yang ditemukan."""

    def __init__(self, messages):
        super().__init__("; ".join(messages))
        self.messages = messages


def parse_table(text):
    """Baca teks CSV (pemisah koma, titik koma, atau tab) menjadi (header, baris)."""
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not lines:
        raise CaseError(["Data masih kosong."])

    delimiter = max(",;\t", key=lines[0].count)
    reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=delimiter)
    table = [[cell.strip() for cell in row] for row in reader]
    headers, rows = table[0], table[1:]

    errors = []
    if len(set(headers)) != len(headers) or "" in headers:
        errors.append("Nama kolom pada baris pertama harus unik dan tidak boleh kosong.")
    for number, row in enumerate(rows, start=1):
        if len(row) != len(headers):
            errors.append(f"Baris data ke-{number} punya {len(row)} kolom, seharusnya {len(headers)}.")
        elif "" in row:
            errors.append(f"Baris data ke-{number} memiliki sel kosong.")
    if errors:
        raise CaseError(errors[:6])
    return headers, rows


def distinct(values):
    """Nilai unik dengan urutan kemunculan pertama."""
    return list(dict.fromkeys(values))


def build_case(key, title, text, target="", positive=""):
    """Validasi data lalu bangun `Case`. Kolom target bawaan adalah kolom terakhir."""
    headers, rows = parse_table(text)
    target = target if target in headers else headers[-1]
    target_index = headers.index(target)
    attribute_names = [h for h in headers if h != target]

    errors = []
    if not ROW_LIMITS[0] <= len(rows) <= ROW_LIMITS[1]:
        errors.append(f"Jumlah baris data harus {ROW_LIMITS[0]} sampai {ROW_LIMITS[1]}, ditemukan {len(rows)}.")
    if not ATTRIBUTE_LIMITS[0] <= len(attribute_names) <= ATTRIBUTE_LIMITS[1]:
        errors.append(
            f"Jumlah atribut (di luar kolom target) harus {ATTRIBUTE_LIMITS[0]} sampai "
            f"{ATTRIBUTE_LIMITS[1]}, ditemukan {len(attribute_names)}."
        )
    classes = distinct(row[target_index] for row in rows)
    if len(classes) != 2:
        errors.append(f"Kolom target '{target}' harus berisi tepat 2 kelas, ditemukan {len(classes)}: "
                      f"{', '.join(classes[:5])}.")
    for index, name in enumerate(headers):
        if index != target_index and len(distinct(row[index] for row in rows)) > MAX_VALUES:
            errors.append(f"Kolom '{name}' punya lebih dari {MAX_VALUES} nilai berbeda.")
    if errors:
        raise CaseError(errors)

    if positive not in classes:
        positive = classes[0]
    classes = tuple(sorted(classes, key=lambda name: name == positive))  # kelas positif di indeks 1

    attributes, columns = {}, []
    for number, name in enumerate(attribute_names):
        index = headers.index(name)
        attr_key = f"a{number + 1}"
        values = tuple(distinct(row[index] for row in rows))
        attributes[attr_key] = {
            "label": name, "values": values, "color": COLORS[number % 4], "shape": SHAPES[number % 4],
            "hint": f"Kolom '{name}' dari data yang kamu masukkan.",
        }
        columns.append(index)

    data_rows = tuple((no, *(row[i] for i in columns), row[target_index]) for no, row in enumerate(rows, start=1))
    default_query = {
        attr_key: Counter(r[1 + n] for r in data_rows).most_common(1)[0][0]
        for n, attr_key in enumerate(attributes)
    }
    title = (title.strip() or "Studi Kasus Saya")[:MAX_TITLE]
    return Case(
        key=key,
        title=title,
        summary=f"Data buatan sendiri: {len(rows)} baris, {len(attributes)} atribut, target {target}.",
        subject="data",
        target=target,
        classes=classes,
        attributes=attributes,
        rows=data_rows,
        default_query=default_query,
        presets=(),
        note="Data ini dimasukkan sendiri oleh pengguna dan hanya tersimpan di browser ini.",
        custom=True,
    )


def load_saved(saved):
    """Bangun ulang kasus dari isi session; entri yang rusak dilewati."""
    cases = {}
    for key, item in saved.items():
        try:
            cases[key] = build_case(key, item["title"], item["csv"], item["target"], item["positive"])
        except (CaseError, KeyError):
            continue
    return cases


def next_key(saved):
    return next(f"k{n}" for n in range(1, MAX_CASES + 2) if f"k{n}" not in saved)
