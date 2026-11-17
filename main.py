"""Bot trading dip-buy swing untuk kompetisi make.fun "Race a BTC trading bot".

Strategi
--------
Satu posisi long CBBTC/USDC, 100% kas per entry, maksimal 1 trip dalam
jendela 1440 bar (1 menit). Entry hanya saat harga turun (dip) dari
tertinggi 45 bar terakhir lalu memantul kembali:

* dip: close turun >= dip_bps (15 bps) dari max close 45 bar terakhir;
* dip_low dicatat (harga terendah selama fase dip) dan dip_age dihitung;
* entry butuh close memantul >= bounce_bps (5 bps) di atas dip_low,
  close harus berada di atas SMA(trend_n=60) (filter tren),
  dan dip_age tidak boleh melewati dip_max_age (30 bar);
* filter RSI(14) dan ATR(20) tersedia tapi nonaktif di parameter final
  (rsi_max dan min_atr_bps bernilai None).

Exit satu posisi, yang mana dulu tercapai:

* take-profit tp_bps (30 bps) di atas cost (atau trailing bila
  trail_bps diisi), stop-loss sl_bps (40 bps) di bawah cost,
  max_hold (60 bar), atau norecov (bila diisi: masih rugi setelah
  norecov_bars bar).

Satu trip disengaja: varian 4-trip yang sama mencetak +$4,92 di dev
window race ini tapi -$26,21 / -$23,13 di dev window 13/15 Nov yang
turun, sementara varian 1-trip ini positif di dua dari tiga jendela
turun dan kerugian terburuknya hanya -$5,92. Dipilih setelah sweep
~1.100 kombinasi dan konsultasi second brain independen.

Terverifikasi: harness lokal kit --twice pada dev window
btc-race-24h-20261117-0603: net PnL +$1,47 (1 trip), max drawdown
0,21%, deterministik, dev gate lolos.

Protokol
--------
Berbicara agent-fun/bars-replay/v1 lewat shim vendor: shim membaca
NDJSON dari stdin (hello, lalu satu batch per menit, lalu done) dan
memanggil on_batch(state, batch); balasan berupa list order (boleh
kosong). Satu batch membawa bar yang baru tutup, fills dari order
batch sebelumnya, dan akun. Order yang diputuskan pada batch menit t
terisi pada open bar berikutnya.

Determinisme
------------
Penuh: tanpa jam dinding, tanpa random, tanpa environment, tanpa file.
Semua state berasal dari bar, fills, dan state yang dikirim harness.
Dua eksekusi pada data yang sama menghasilkan order yang sama persis.
Hanya standard library yang dipakai.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "vendor"))

import makefun_bars

from params import P

SYMBOL = "CBBTC"
BPS = 10000
WINDOW_BARS = 1440

# Riwayat harga per bar CBBTC (paralel, indeks sama).
closes = []
highs = []
lows = []

# State strategi.
dip_low = None      # close terendah selama fase dip yang sedang berjalan
dip_age = 0         # berapa bar fase dip sudah berjalan
trips_started = 0   # berapa buy fill yang sudah diterima
entry_seq = None    # seq batch saat posisi sekarang mulai dipegang
peak_value = None   # nilai posisi tertinggi sejak entry (untuk trailing)


def sma(n):
    """Rata-rata close n bar terakhir; None bila bar belum cukup."""
    if len(closes) < n:
        return None
    return sum(closes[-n:]) / float(n)


def rsi(period=14):
    """RSI Wilder: 14 perubahan pertama dirata-rata, lalu smoothing
    (prev * (period - 1) + current) / period. None bila bar belum cukup."""
    if len(closes) < period + 1:
        return None
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    if len(changes) < period:
        return None
    avg_gain = sum(c if c > 0 else 0 for c in changes[:period]) / float(period)
    avg_loss = sum(-c if c < 0 else 0 for c in changes[:period]) / float(period)
    for c in changes[period:]:
        avg_gain = (avg_gain * (period - 1) + (c if c > 0 else 0)) / float(period)
        avg_loss = (avg_loss * (period - 1) + (-c if c < 0 else 0)) / float(period)
    total = avg_gain + avg_loss
    if total == 0:
        return 50.0
    return 100.0 * avg_gain / total


def atr_bps(period=20):
    """ATR dalam bps: rata-rata 20 bar terakhir dari
    (high - low) * 10000 / close. None bila bar belum cukup."""
    if len(closes) < period:
        return None
    total = 0.0
    for i in range(len(closes) - period, len(closes)):
        total += (highs[i] - lows[i]) * BPS / closes[i]
    return total / float(period)


def on_batch(state, batch):
    global dip_low, dip_age, trips_started, entry_seq, peak_value

    # 1. Serap semua bar CBBTC dari batch ini (o/h/l/c bisa berupa
    #    angka atau string angka, jadi pakai int()).
    for bar in batch.get("bars", []):
        if bar.get("symbol") != SYMBOL:
            continue
        closes.append(int(bar["c"]))
        highs.append(int(bar["h"]))
        lows.append(int(bar["l"]))

    # 2. Hitung buy fill: tiap buy yang terisi memulai satu trip.
    for fill in batch.get("fills", []):
        if (fill.get("symbol") == SYMBOL
                and fill.get("status") == "filled"
                and fill.get("side") == "buy"):
            trips_started += 1

    # 3. Lacak posisi: catat entry_seq dan peak_value saat posisi baru
    #    muncul; bersihkan saat posisi sudah tidak ada.
    held = state.positions.get(SYMBOL)
    holding = held is not None and held.qty
    if holding:
        # Posisi baru pertama kali terlihat pada batch setelah fill buy
        # dilaporkan, jadi entry_seq menandai batch itu dan bars_held
        # dihitung dari sana (bukan dari batch saat order dikirim).
        if entry_seq is None:
            entry_seq = state.seq
            peak_value = state.value(SYMBOL, held.qty)
    else:
        entry_seq = None
        peak_value = None

    # 4. EXIT: bila sedang memegang posisi.
    if holding:
        value = state.value(SYMBOL, held.qty)
        cost = held.cost
        if peak_value is None or value > peak_value:
            peak_value = value
        bars_held = state.seq - entry_seq

        sell = False
        if P["trail_bps"] is not None:
            armed = peak_value * BPS >= cost * (BPS + P["tp_bps"])
            if armed and value * BPS <= peak_value * (BPS - P["trail_bps"]):
                sell = True
        elif value * BPS >= cost * (BPS + P["tp_bps"]):
            sell = True
        if not sell:
            if P["sl_bps"] is not None and value * BPS <= cost * (BPS - P["sl_bps"]):
                sell = True
            elif bars_held >= P["max_hold"]:
                sell = True
            elif (P["norecov_bars"] is not None
                    and bars_held >= P["norecov_bars"]
                    and value < cost):
                sell = True
        if sell:
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                     "max_slippage_bps": 100}]
        return []

    # 5. ENTRY: bila tidak memegang posisi.
    # Satu trip saja per jendela: membatasi kerugian bila live window
    # ternyata turun (varian 4-trip kehilangan -$26 di jendela turun).
    if trips_started >= P["max_trips"]:
        return []
    if len(closes) < P["high_n"]:
        return []
    if state.seq >= WINDOW_BARS - P["no_entry_last"]:
        return []

    close = closes[-1]
    high_n_val = max(closes[-P["high_n"]:])
    dip = close * BPS <= high_n_val * (BPS - P["dip_bps"])
    if dip:
        if dip_low is None:
            dip_low = close
            dip_age = 0
        else:
            if close < dip_low:
                dip_low = close
            dip_age += 1
    else:
        # Bukan dip: bila harga sudah kembali dekat ke tertinggi,
        # fase dip dianggap selesai dan pelacakan direset.
        if close * BPS > high_n_val * (BPS - P["dip_bps"] // 2):
            dip_low = None
            dip_age = 0
        return []
    if dip_age > P["dip_max_age"]:
        return []

    # Filter tren: close harus di atas SMA(trend_n).
    if P["trend_n"] is not None:
        trend = sma(P["trend_n"])
        if trend is None or close < trend:
            return []

    # Filter RSI: RSI harus di bawah rsi_max (nonaktif bila None).
    if P["rsi_max"] is not None:
        r = rsi(14)
        if r is None or r > P["rsi_max"]:
            return []

    # Filter ATR: ATR harus di atas min_atr_bps (nonaktif bila None).
    if P["min_atr_bps"] is not None:
        a = atr_bps(20)
        if a is None or a < P["min_atr_bps"]:
            return []

    # Konfirmasi pantulan: close harus naik bounce_bps di atas dip_low.
    if P["bounce_bps"] is not None:
        if close * BPS < dip_low * (BPS + P["bounce_bps"]):
            return []

    # Beli 100% kas (dibatasi weight_room), selama di atas notional minimum.
    amount = min(state.cash, state.weight_room(SYMBOL))
    if amount < int(state.hello["fees"]["min_notional_quote_units"]):
        return []
    return [{"side": "buy", "symbol": SYMBOL,
             "notional_quote_units": amount, "max_slippage_bps": 100}]


makefun_bars.run(on_batch)
