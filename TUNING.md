# Catatan tuning — btc-race-24h-20261117-0603

Seluruh penalaan dilakukan dalam satu sesi agen pada 17 Nov 2026,
memakai harness lokal kit (`harness.py`, replika setia engine kit).
Semua angka di bawah adalah hasil harness, bukan klaim.

## Dev window baru

- Jendela: 16 Nov 06:03 UTC – 17 Nov 06:03 UTC, 1.440 bar.
- BTC naik pelan: +49 bps dari buka ke tutup, drawdown terbesar 212 bps.
- Baseline parameter lama (dip 40, TP 70, SL 50, hold 180, 4 trip):
  rugi $8,13 dalam satu trip. Bot-v2 (capitulation-reversal, ambang
  700 bps) tidak pernah entry sama sekali: nol trade.

## Putaran sweep

- Putaran pertama, 240 kombinasi (dip 15–40, TP 30–70, hold 60–180,
  tren ada/tidak, pantulan 5/10): hanya 4 yang positif. Terbaik
  dip 15, TP 30, hold 60: +$3,77.
- Putaran kedua, 720 kombinasi (dip 12–25, TP 25–40, SL 25–50,
  hold 45–90, tanpa-pulih 20/30): 111 positif. Puncak dip 12,
  TP 35, SL 50, hold 60: +$4,92. Tetangganya (dip 12–18, TP 30–35)
  semua di +$3,77 sampai +$4,92 — sebuah plateau, bukan titik rapuh.
- Bot-v2, 120 kombinasi (ambang 100–300, TP 100–300): nol trade di
  semua kombinasi. Ambangnya diukur dari close pertama window,
  dan window ini tidak pernah jatuh 100 bps dari bukaannya.
- Filter rezim (SMA 60 harus di atas SMA 120/240) dicoba dan
  dibuang: ia memblokir justru entry yang menang di window baru
  (hasil jatuh ke -$4,07 / -$5,79) dan tidak menyelamatkan
  jendela turun.

## Jebakan cache yang ketemu di tengah jalan

Di tengah sweep, satu hasil tampak tidak konsisten dengan ulangan
langsungnya. Penyebabnya: Python memakai file `.pyc` bila detik
mtime dan ukuran file sumber sama — penulisan `params.py` yang
cepat dalam loop kadang terbaca basi. Sejak itu semua sweep
dijalankan tanpa cache bytecode, dan semua kandidat teratas
diverifikasi ulang dengan cara bersih itu. Angka-angka di dokumen
ini adalah angka hasil verifikasi bersih, bukan angka sweep awal.

## Membatasi jumlah trip

Varian 4-trip terbaik (+$4,92) runtuh di jendela turun: -$26,21
(13 Nov) dan -$23,13 (15 Nov). Membatasi ke 1 trip mengubah
profilnya total:

| Kandidat | Dev baru | 12 Nov | 13 Nov | 15 Nov |
| --- | --- | --- | --- | --- |
| 4 trip, dip 12, TP 35 | +4,92 | -0,53 | -26,21 | -23,13 |
| 4 trip, dip 12, TP 30 | +4,43 | +0,42 | -26,21 | -19,53 |
| 1 trip, dip 12, TP 30, SL 40 | +1,47 | +1,60 | -5,92 | +1,06 |
| 1 trip, dip 15, TP 30, SL 40 | +1,47 | +1,60 | -5,92 | +1,06 |

SL 40 adalah titik terbaik out-of-sample untuk varian 1-trip
(SL 25/30/50 masing-masing lebih buruk di satu window).
Dip 12 dan dip 15 memberi hasil identik di keempat window;
dip 15 diambil sebagai tengah plateau.

## Rezim jendela lama

Ketiga jendela lama semuanya turun: 12 Nov -230 bps, 13 Nov
-491 bps, 15 Nov -400 bps (drawdown terbesar 792 bps). Bahkan
parameter lama yang dulu menang pun rugi -$30,63 di 15 Nov.
Tidak ada parameter long-only yang ditemukan positif di keempat
window sekaligus; varian 1-trip adalah yang paling dekat —
positif di tiga dari empat, dengan kerugian terburuk -$5,92.

## Pendapat second brain

DeepSeek (via 100milionseek, 1.356 token) diminta menilai dua
kandidat tanpa diberi tahu pilihan penulis. Ia memilih varian
1-trip secara independen, dengan alasan: ketahanan rezim,
downside yang dibatasi satu trip, dan trade-off terburuk vs
terbaik yang lebih baik. Risiko yang ia catat: upside terbatas
bila live window mengulang grind naik yang pelan.

## Parameter final dan verifikasi

- dip 15, high_n 45, TP 30, SL 40, hold 60, tren SMA 60,
  pantulan 5, maks 1 trip.
- Harness `--twice` pada dev window baru: +$1,47 (1 trip,
  2 trade), fee $0,80, drawdown maks 0,21%, deterministik,
  dev gate lolos. Hasil yang sama persis pada repo ini
  maupun pada direktori kerja penalaan.
- Keterbatasan yang diakui: bila live window jatuh seperti
  13 Nov, entri tunggal ini bisa rugi sekitar $6. Tidak ada
  proteksi yang ditemukan yang menghindari itu tanpa ikut
  membunuh entry yang menang di window baru.
