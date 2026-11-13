"""Studi kasus yang tersedia: data latih, atribut, dan teks penjelasnya.

Urutan `classes` penting: indeks 0 = kelas negatif (merah muda), indeks 1 = kelas positif (hijau).
"""
from dataclasses import dataclass, field


@dataclass
class Case:
    key: str
    title: str
    summary: str
    subject: str
    target: str
    classes: tuple
    attributes: dict
    rows: tuple
    default_query: dict
    presets: tuple
    note: str
    custom: bool = False
    data: list = field(init=False)

    def __post_init__(self):
        keys = ("no", *self.attributes, "label")
        self.data = [dict(zip(keys, row)) for row in self.rows]

    def row(self, no):
        return next(row for row in self.data if row["no"] == no)

    def counts(self, rows):
        """Jumlah data per kelas, urutannya mengikuti `classes`."""
        labels = [row["label"] for row in rows]
        return tuple(labels.count(name) for name in self.classes)

    def majority(self, counts):
        """Kelas terbanyak; bila seri dipilih kelas yang lebih dulu."""
        return self.classes[counts.index(max(counts))]


def _attr(label, values, color, shape, hint):
    return {"label": label, "values": values, "color": color, "shape": shape, "hint": hint}


BLT = Case(
    key="blt",
    title="Kelayakan Penerima BLT",
    summary="Menentukan apakah rumah tangga layak menerima Bantuan Langsung Tunai.",
    subject="rumah tangga",
    target="Kelayakan",
    classes=("Tidak Layak", "Layak"),
    attributes={
        "rumah": _attr("Kondisi Rumah", ("Permanen", "Semi Permanen", "Darurat"), "violet", "square",
                       "Kualitas bangunan tempat tinggal. Permanen: dinding tembok dan atap kokoh. "
                       "Semi Permanen: campuran tembok dan kayu. Darurat: bahan seadanya."),
        "kerja": _attr("Status Kerja", ("Tetap", "Tidak Tetap", "Tidak Bekerja"), "pink", "circle",
                       "Pekerjaan kepala keluarga: tetap, tidak tetap, atau tidak bekerja."),
        "kendaraan": _attr("Kendaraan", ("Ada", "Tidak Ada"), "amber", "triangle",
                           "Kepemilikan kendaraan bermotor oleh rumah tangga."),
        "lansia": _attr("Lansia/Disabilitas", ("Ada", "Tidak Ada"), "mint", "diamond",
                        "Ada atau tidaknya anggota rumah tangga lansia atau penyandang disabilitas."),
    },
    rows=(
        (1, "Darurat", "Tidak Bekerja", "Tidak Ada", "Ada", "Layak"),
        (2, "Darurat", "Tidak Tetap", "Tidak Ada", "Tidak Ada", "Layak"),
        (3, "Semi Permanen", "Tidak Bekerja", "Tidak Ada", "Ada", "Layak"),
        (4, "Semi Permanen", "Tidak Tetap", "Ada", "Tidak Ada", "Tidak Layak"),
        (5, "Semi Permanen", "Tetap", "Tidak Ada", "Tidak Ada", "Tidak Layak"),
        (6, "Permanen", "Tetap", "Ada", "Tidak Ada", "Tidak Layak"),
        (7, "Permanen", "Tidak Tetap", "Ada", "Tidak Ada", "Tidak Layak"),
        (8, "Permanen", "Tidak Bekerja", "Tidak Ada", "Ada", "Layak"),
        (9, "Permanen", "Tetap", "Tidak Ada", "Tidak Ada", "Tidak Layak"),
        (10, "Darurat", "Tetap", "Tidak Ada", "Tidak Ada", "Tidak Layak"),
        (11, "Semi Permanen", "Tidak Bekerja", "Ada", "Tidak Ada", "Tidak Layak"),
        (12, "Permanen", "Tidak Tetap", "Tidak Ada", "Ada", "Layak"),
        (13, "Darurat", "Tidak Tetap", "Ada", "Ada", "Layak"),
        (14, "Permanen", "Tetap", "Ada", "Ada", "Tidak Layak"),
        (15, "Semi Permanen", "Tetap", "Ada", "Tidak Ada", "Tidak Layak"),
    ),
    default_query={"rumah": "Permanen", "kerja": "Tidak Bekerja", "kendaraan": "Ada", "lansia": "Ada"},
    presets=(
        ("Kondisi sedang", {"rumah": "Semi Permanen", "kerja": "Tidak Tetap", "kendaraan": "Tidak Ada", "lansia": "Tidak Ada"}),
        ("Sangat rentan", {"rumah": "Darurat", "kerja": "Tidak Bekerja", "kendaraan": "Tidak Ada", "lansia": "Ada"}),
        ("Mapan", {"rumah": "Permanen", "kerja": "Tetap", "kendaraan": "Ada", "lansia": "Tidak Ada"}),
    ),
    note="Data simulasi untuk pembelajaran, bukan data resmi pemerintah.",
)

TENIS = Case(
    key="tenis",
    title="Bermain Tenis",
    summary="Kasus klasik: apakah cuaca hari ini cocok untuk bermain tenis?",
    subject="hari",
    target="Keputusan",
    classes=("Tidak Main", "Main"),
    attributes={
        "cuaca": _attr("Cuaca", ("Cerah", "Mendung", "Hujan"), "amber", "circle",
                       "Kondisi langit pada hari tersebut."),
        "suhu": _attr("Suhu", ("Panas", "Sedang", "Dingin"), "pink", "triangle",
                      "Tingkat suhu udara."),
        "lembap": _attr("Kelembapan", ("Tinggi", "Normal"), "violet", "square",
                        "Tingkat kelembapan udara."),
        "angin": _attr("Angin", ("Lemah", "Kuat"), "mint", "diamond",
                       "Kekuatan angin di lapangan."),
    },
    rows=(
        (1, "Cerah", "Panas", "Tinggi", "Lemah", "Tidak Main"),
        (2, "Cerah", "Panas", "Tinggi", "Kuat", "Tidak Main"),
        (3, "Mendung", "Panas", "Tinggi", "Lemah", "Main"),
        (4, "Hujan", "Sedang", "Tinggi", "Lemah", "Main"),
        (5, "Hujan", "Dingin", "Normal", "Lemah", "Main"),
        (6, "Hujan", "Dingin", "Normal", "Kuat", "Tidak Main"),
        (7, "Mendung", "Dingin", "Normal", "Kuat", "Main"),
        (8, "Cerah", "Sedang", "Tinggi", "Lemah", "Tidak Main"),
        (9, "Cerah", "Dingin", "Normal", "Lemah", "Main"),
        (10, "Hujan", "Sedang", "Normal", "Lemah", "Main"),
        (11, "Cerah", "Sedang", "Normal", "Kuat", "Main"),
        (12, "Mendung", "Sedang", "Tinggi", "Kuat", "Main"),
        (13, "Mendung", "Panas", "Normal", "Lemah", "Main"),
        (14, "Hujan", "Sedang", "Tinggi", "Kuat", "Tidak Main"),
    ),
    default_query={"cuaca": "Cerah", "suhu": "Dingin", "lembap": "Tinggi", "angin": "Kuat"},
    presets=(
        ("Cerah terik", {"cuaca": "Cerah", "suhu": "Panas", "lembap": "Tinggi", "angin": "Lemah"}),
        ("Mendung sejuk", {"cuaca": "Mendung", "suhu": "Sedang", "lembap": "Normal", "angin": "Lemah"}),
        ("Hujan berangin", {"cuaca": "Hujan", "suhu": "Dingin", "lembap": "Tinggi", "angin": "Kuat"}),
    ),
    note="Dataset klasik 14 hari yang sering dipakai untuk belajar pohon keputusan.",
)

LULUS = Case(
    key="lulus",
    title="Kelulusan Tepat Waktu",
    summary="Memprediksi apakah mahasiswa akan lulus tepat waktu.",
    subject="mahasiswa",
    target="Kelulusan",
    classes=("Terlambat", "Tepat Waktu"),
    attributes={
        "ipk": _attr("IPK", ("Tinggi", "Sedang", "Rendah"), "violet", "square",
                     "Kategori indeks prestasi kumulatif mahasiswa."),
        "hadir": _attr("Kehadiran", ("Tinggi", "Rendah"), "mint", "diamond",
                       "Tingkat kehadiran di perkuliahan."),
        "kerja": _attr("Kerja Paruh Waktu", ("Ya", "Tidak"), "amber", "triangle",
                       "Apakah mahasiswa bekerja paruh waktu selama kuliah."),
        "org": _attr("Organisasi", ("Aktif", "Tidak Aktif"), "pink", "circle",
                     "Keaktifan mahasiswa dalam organisasi kampus."),
    },
    rows=(
        (1, "Tinggi", "Tinggi", "Tidak", "Aktif", "Tepat Waktu"),
        (2, "Tinggi", "Tinggi", "Ya", "Aktif", "Tepat Waktu"),
        (3, "Tinggi", "Rendah", "Tidak", "Tidak Aktif", "Tepat Waktu"),
        (4, "Tinggi", "Rendah", "Ya", "Tidak Aktif", "Terlambat"),
        (5, "Sedang", "Tinggi", "Tidak", "Aktif", "Tepat Waktu"),
        (6, "Sedang", "Tinggi", "Ya", "Tidak Aktif", "Tepat Waktu"),
        (7, "Sedang", "Rendah", "Tidak", "Aktif", "Terlambat"),
        (8, "Sedang", "Rendah", "Ya", "Tidak Aktif", "Terlambat"),
        (9, "Rendah", "Tinggi", "Tidak", "Tidak Aktif", "Terlambat"),
        (10, "Rendah", "Tinggi", "Ya", "Aktif", "Terlambat"),
        (11, "Rendah", "Rendah", "Tidak", "Tidak Aktif", "Terlambat"),
        (12, "Rendah", "Rendah", "Ya", "Aktif", "Terlambat"),
        (13, "Sedang", "Tinggi", "Tidak", "Tidak Aktif", "Tepat Waktu"),
        (14, "Tinggi", "Tinggi", "Ya", "Tidak Aktif", "Tepat Waktu"),
        (15, "Sedang", "Rendah", "Tidak", "Tidak Aktif", "Terlambat"),
    ),
    default_query={"ipk": "Sedang", "hadir": "Tinggi", "kerja": "Ya", "org": "Aktif"},
    presets=(
        ("Berprestasi", {"ipk": "Tinggi", "hadir": "Tinggi", "kerja": "Tidak", "org": "Aktif"}),
        ("Sibuk bekerja", {"ipk": "Sedang", "hadir": "Rendah", "kerja": "Ya", "org": "Tidak Aktif"}),
        ("Perlu bimbingan", {"ipk": "Rendah", "hadir": "Rendah", "kerja": "Ya", "org": "Tidak Aktif"}),
    ),
    note="Data simulasi buatan sendiri untuk pembelajaran, bukan data akademik sebenarnya.",
)

CASES = {case.key: case for case in (BLT, TENIS, LULUS)}
DEFAULT_CASE = BLT.key
