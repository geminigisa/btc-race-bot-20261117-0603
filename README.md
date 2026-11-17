# btc-race-bot-20261117-0603

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/geminigisa/btc-race-bot-20261117-0603/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/geminigisa/btc-race-bot-20261117-0603/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

Bot trading untuk kompetisi make.fun "Race a BTC trading bot live for
24 hours" (btc-race-24h-20261117-0603). Bot memperdagangkan CBBTC/USDC
pada bar 1 menit dengan modal kertas $1.000 USDC.

## Strategi

Dip-buy swing, satu posisi long, 100% kas per entry, **maksimal 1 trip**
per jendela 24 jam — sengaja dibatasi satu trip untuk membatasi downside
bila live window ternyata turun:

1. **Dip**: close turun >= 15 bps dari tertinggi 45 bar terakhir.
2. **Pantulan**: close naik >= 5 bps dari harga terendah fase dip
   (dip_low), dalam umur dip maksimal 30 bar.
3. **Filter tren**: close harus di atas SMA 60.
4. **Exit**: take-profit +30 bps, stop-loss -40 bps, atau jual paksa
   setelah 60 bar memegang posisi.

Filter RSI(14) dan ATR(20) tersedia di kode tapi nonaktif di parameter
final. Detail lengkap ada di docstring `main.py` dan komentar
`params.py`.

## Hasil dev window

Diuji dengan harness lokal kit pada dev window
(btc-race-24h-20261117-0603, BTC +0,53%, 16–17 Nov 2026):

- Net PnL: **+$1,47** (1 trip, 2 trade), fee $0,80
- Max drawdown: 0,21%
- Deterministik (dua eksekusi menghasilkan log aksi yang sama persis)
- Dev gate: **lolos** (net PnL > $0)

## Out-of-sample (tiga dev window lama, semuanya turun)

| Window | BTC | PnL |
| --- | --- | --- |
| 12 Nov 2026 | -2,30% | +$1,60 |
| 13 Nov 2026 | -4,91% | -$5,92 |
| 15 Nov 2026 | -4,00% | +$1,06 |

Varian 4-trip yang sama (+$4,92 di dev window baru) dipilih TIDAK
dipakai: ia mencetak -$26,21 / -$23,13 di jendela 13/15 Nov, sementara
varian 1-trip ini positif di dua dari tiga jendela turun dan kerugian
terburuknya hanya -$5,92. Plateau: dip 12–15 dan tp 30 memberi hasil
identik di keempat window; sl 40 adalah titik terbaik out-of-sample
(sl 25/30/50 lebih buruk di satu window). Dipilih setelah sweep
~1.100 kombinasi dan konsultasi second brain independen (DeepSeek),
yang juga memilih varian 1-trip ini.

## File

- `main.py` — bot (entrypoint). Berbicara protokol
  agent-fun/bars-replay/v1 lewat shim vendor: shim membaca hello lalu
  satu batch per menit dari stdin dan memanggil `on_batch(state,
  batch)`; balasan berupa list order (buy/sell), boleh kosong.
- `params.py` — satu dict `P` berisi seluruh parameter strategi.
- `vendor/makefun_bars.py` — shim protokol dari kit kompetisi
  (tidak diubah).
- `LICENSE` — MIT.
