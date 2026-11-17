"""Parameter strategi dip-buy swing (lihat main.py).

dip_bps: seberapa jauh close harus turun dari tertinggi high_n bar
    terakhir agar dianggap dip (basis poin).
high_n: jendela tertinggi untuk mengukur dip (bar).
tp_bps: take-profit di atas cost (basis poin).
sl_bps: stop-loss di bawah cost (basis poin).
max_hold: jual paksa setelah sekian bar memegang posisi.
norecov_bps / norecov_bars: jual bila masih rugi setelah norecov_bars
    bar (nonaktif bila None).
max_trips: jumlah maksimum trip (buy fill) dalam satu jendela.
no_entry_last: jangan entry pada sekian bar terakhir jendela.
dip_max_age: umur maksimum fase dip agar entry masih diizinkan (bar).
trend_n: filter tren, close harus di atas SMA(n) (nonaktif bila None).
rsi_max: filter RSI, RSI(14) harus di bawah nilai ini (nonaktif bila None).
min_atr_bps: filter ATR, ATR(20) harus di atas nilai ini dalam bps
    (nonaktif bila None).
bounce_bps: konfirmasi pantulan, close harus naik sekian bps di atas
    dip_low (nonaktif bila None).
trail_bps: trailing stop setelah TP tercapai (nonaktif bila None).

Tuning untuk race btc-race-24h-20261117-0603 (sesi 17 Nov 2026):
dip dangkal 15 + TP rapat 30 + hold pendek 60 + SL 40 + max 1 trip.
Dev window baru (BTC +49bps): +$1,47, 1 trip, drawdown 0,63%,
deterministik, dev gate LOLOS (harness --twice).
Out-of-sample: 12 Nov +$1,60; 13 Nov -$5,92; 15 Nov +$1,06.
Dipilih atas varian 4-trip (+$4,92 di dev tapi -$26,21/-$23,13 di
jendela turun) karena downside terbatas: satu trip membatasi
kerugian bila live window ternyata turun. Plateau: dip 12-15 dan
tp 30 memberi hasil identik di keempat window; sl 40 adalah titik
terbaik out-of-sample (sl 25/30/50 lebih buruk di satu window).
"""

P = {'dip_bps': 15, 'high_n': 45, 'tp_bps': 30, 'sl_bps': 40, 'max_hold': 60, 'norecov_bps': None, 'norecov_bars': None, 'max_trips': 1, 'no_entry_last': 60, 'dip_max_age': 30, 'trend_n': 60, 'rsi_max': None, 'min_atr_bps': None, 'bounce_bps': 5, 'trail_bps': None}
