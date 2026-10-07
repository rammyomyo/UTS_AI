# -*- coding: utf-8 -*-
"""
==============================================================================
 PEMBUAT DATASET SIMULASI: PREDIKSI KELULUSAN TEPAT WAKTU MAHASISWA
==============================================================================
 Menghasilkan file  dataset_kelulusan.csv  (300 baris, 10 kolom).

 Cara pakai:
   1. Pasang library satu kali:   python -m pip install pandas numpy
   2. Jalankan skrip ini:         python buat_dataset.py
   3. File dataset_kelulusan.csv muncul di folder yang sama.

 Catatan:
   - Seed acak dikunci (42) sehingga hasil dapat direproduksi.
   - Urutan pemanggilan angka acak TIDAK BOLEH diubah, karena akan mengubah
     isi dataset. Di akhir skrip ada pemeriksaan otomatis yang memastikan
     hasilnya sama dengan dataset yang dipakai pada laporan.
==============================================================================
"""
import numpy as np
import pandas as pd

# ------------------------------------------------------------------ PENGATURAN
JUMLAH_DATA = 300          # jumlah mahasiswa (baris)
SEED = 42                  # kunci angka acak agar hasil selalu sama
rng = np.random.default_rng(SEED)

# ------------------------------------------- TAHAP 1: KEMAMPUAN AKADEMIK (LATEN)
# Setiap mahasiswa diberi "kemampuan akademik" berdistribusi normal
# (rata-rata 0, simpangan baku 1). Variabel ini TIDAK masuk dataset; ia hanya
# dipakai untuk membuat variabel lain saling berhubungan secara wajar.
kemampuan = rng.normal(0, 1, JUMLAH_DATA)

# ---------------------------------------------------- TAHAP 2: IPK SEMESTER 1-4
# IPK = 3,05 + 0,40 x kemampuan + pergeseran per semester + noise acak,
# lalu dibatasi pada rentang 1,5 - 4,0 dan dibulatkan 2 desimal.
def buat_ipk(pergeseran):
    nilai = 3.05 + 0.40 * kemampuan + pergeseran + rng.normal(0, 0.18, JUMLAH_DATA)
    return np.clip(nilai, 1.5, 4.0).round(2)

ipk_sem1 = buat_ipk(-0.05)
ipk_sem2 = buat_ipk(0.00)
ipk_sem3 = buat_ipk(0.03)
ipk_sem4 = buat_ipk(0.05)

# ------------------------------------------------------------ TAHAP 3: KEHADIRAN
# Kehadiran (%) naik bila kemampuan tinggi; dibatasi 40 - 100.
kehadiran = np.clip(85 + 7 * kemampuan + rng.normal(0, 6, JUMLAH_DATA), 40, 100).round(1)

# --------------------------------------------------- TAHAP 4: MATA KULIAH MENGULANG
# Semakin rendah kemampuan, semakin banyak mata kuliah yang diulang
# (distribusi Poisson, maksimum 8).
rata_ulang = np.clip(1.0 - 0.8 * kemampuan, 0.05, 5)
mk_mengulang = np.minimum(rng.poisson(rata_ulang), 8)

# ------------------------------------------------------------------ TAHAP 5: SKS
# SKS lulus sampai semester 4: dasar 80, berkurang 3 SKS untuk tiap mata kuliah
# yang diulang, ditambah variasi acak -4 s.d. +4; dibatasi 40 - 84.
sks_lulus = np.clip(80 - 3 * mk_mengulang + rng.integers(-4, 5, JUMLAH_DATA), 40, 84)

# ------------------------------------------------------- TAHAP 6: AKTIF ORGANISASI
# Dibangkitkan acak: peluang "Ya" sekitar 35 persen.
aktif_organisasi = np.where(rng.random(JUMLAH_DATA) < 0.35, "Ya", "Tidak")

# ------------------------------------------------- TAHAP 7: LABEL (TARGET) KELULUSAN
# Skor kelulusan memakai rata-rata IPK, kehadiran, mata kuliah mengulang, SKS,
# dan keaktifan organisasi, ditambah noise acak (simpangan baku 0,6) agar label
# tidak sepenuhnya pasti. Skor diubah menjadi peluang dengan fungsi logistik,
# lalu label ditentukan secara acak menurut peluang tersebut.
rata_ipk = (ipk_sem1 + ipk_sem2 + ipk_sem3 + ipk_sem4) / 4
skor = (2.8 * (rata_ipk - 2.9)
        + 0.06 * (kehadiran - 82)
        - 0.55 * mk_mengulang
        + 0.08 * (sks_lulus - 70)
        - 0.4 * (aktif_organisasi == "Ya")
        + rng.normal(0, 0.6, JUMLAH_DATA))
peluang = 1 / (1 + np.exp(-skor))
lulus_tepat_waktu = np.where(rng.random(JUMLAH_DATA) < peluang, "Ya", "Tidak")

# ------------------------------------------------------ TAHAP 8: SUSUN DATAFRAME
df = pd.DataFrame({
    "ID": [f"M{str(i + 1).zfill(3)}" for i in range(JUMLAH_DATA)],
    "IPK_Sem1": ipk_sem1,
    "IPK_Sem2": ipk_sem2,
    "IPK_Sem3": ipk_sem3,
    "IPK_Sem4": ipk_sem4,
    "SKS_Lulus": sks_lulus,
    "Kehadiran": kehadiran,
    "MK_Mengulang": mk_mengulang,
    "Aktif_Organisasi": aktif_organisasi,
    "Lulus_Tepat_Waktu": lulus_tepat_waktu,
})

# ------------------------------------------------ TAHAP 9: SISIPKAN NILAI KOSONG
# 6 baris pada Kehadiran dan 6 baris pada IPK_Sem3 (sekitar 2 persen) dikosongkan
# agar tahap pembersihan data (Missing Value di KNIME) bermakna.
for kolom in ["Kehadiran", "IPK_Sem3"]:
    baris_kosong = rng.choice(JUMLAH_DATA, size=6, replace=False)
    df.loc[baris_kosong, kolom] = np.nan

# --------------------------------------------------------------- TAHAP 10: SIMPAN
df.to_csv("dataset_kelulusan.csv", index=False)

# --------------------------------------------------------- RINGKASAN DAN PEMERIKSAAN
jumlah_ya = int((df["Lulus_Tepat_Waktu"] == "Ya").sum())
jumlah_tidak = int((df["Lulus_Tepat_Waktu"] == "Tidak").sum())
print("Ukuran dataset (baris, kolom):", df.shape)
print("Lulus_Tepat_Waktu = Ya    :", jumlah_ya)
print("Lulus_Tepat_Waktu = Tidak :", jumlah_tidak)
print("Nilai kosong per kolom    :", df.isna().sum()[df.isna().sum() > 0].to_dict())

# Nilai acuan dari dataset yang dipakai pada laporan dan workflow KNIME.
cocok = (jumlah_ya == 181 and jumlah_tidak == 119
         and int(df["SKS_Lulus"].sum()) == 23113
         and int(df["MK_Mengulang"].sum()) == 310
         and int((df["Aktif_Organisasi"] == "Ya").sum()) == 97)
if cocok:
    print("PEMERIKSAAN: SESUAI. Dataset sama dengan yang dipakai pada laporan.")
else:
    print("PEMERIKSAAN: BERBEDA. Dataset ini TIDAK sama dengan dataset laporan.")
    print("Pakai dataset_kelulusan.csv asli untuk KNIME agar angka laporan tetap cocok.")