"""Render reports/results_dashboard.html — REDESIGNED 2026-07-22, corrected
2026-07-22b after the SPY-history data fix.

Grouped BY STRATEGY, not by chart type. One card per variant (the Part 2
three-way valve test on the champion cell, plus SPY), each with essential
stats (incl. risk-adjusted Sharpe/Calmar and a concentration callout) and a
plain-language Notes & Takeaways block. A plain-language LEGEND explains the
core strategy and what each variant changes. Winner crowned by return/maxDD.
Equity curve + trade log kept (trade log collapsible). Retired-generation
ablations collapsed into an Archive.

Self-contained: inline CSS/JS, Chart.js via CDN, data embedded at build
time. Reads the pickled Part 2 run + analyst_metrics (no re-simulation) so
the dashboard and reports/exit_entry_valve.md always show identical numbers.
"""
import json
import pickle
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

SCRATCH = ("/tmp/claude-0/-home-user-Trading-Project-Updated/"
          "cea16de6-50ec-53c6-8ee4-cf32e7e300aa/scratchpad")
OUT_PATH = "reports/results_dashboard.html"

CAVEAT = (
    "STILL a survivorship-biased proxy universe with current-snapshot market "
    "caps. The headline returns are NOT edge — 87% of the winner's gains come "
    "from just 2 LEAP trades (one TSLA LEAP alone = 60%); strip those and the "
    "strategy returns ~13%/yr (SPY-like) at ~1.5x SPY's drawdown. Beating SPY "
    "here is NECESSARY but NOT SUFFICIENT evidence. Vault numbers are "
    "directional at best. Do not let a good number end the skepticism."
)

# core strategy + per-variant plain-language legend (the owner asked for this)
LEGEND_CORE = [
    "<b>Universe:</b> only large, profitable, liquid US companies — you only ever buy quality.",
    "<b>Entry — drawdown gate:</b> only look once a name is far below its own 2-year high "
    "(25% for the biggest caps, 30% mid, 40% for smaller). Buy fear.",
    "<b>Entry — UT-Bot trigger:</b> don't catch a falling knife — wait for a momentum "
    "indicator to flip to buy, confirming the bottom is turning up. Gate AND trigger both required.",
    "<b>Instrument:</b> a top-10 mega-cap is bought as a ~2-year call option (LEAP) for leverage "
    "(only ONE at a time, ~30% of book); everything else is bought as shares.",
    "<b>Exit — Fibonacci zones:</b> measure the recovery from the dip low back toward the old high. "
    "Below 0.9 = hold no matter what (no stop-losses, ever). 0.9-1.618 = sell on a weekly momentum "
    "sell. Past 1.618 = trail so big winners keep running.",
]
LEGEND_VARIANTS = [
    ("No valve", "Never force anything out — pure patient holding. A stale holding can block a "
     "new entry indefinitely."),
    ("Underwater valve", "If a position is held >12 months AND is below its buy price AND a better "
     "candidate is waiting, kick it out to free the slot. (Targets losers.)"),
    ("Underperformance valve", "Same, but the trigger is 'trailing SPY by >=5%/year' instead of "
     "'below buy price' — so it can also evict a mediocre winner that's lagging the index."),
    ("SPY buy &amp; hold", "Not one of our strategies — the benchmark. Just own the index."),
]

VARIANT_META = {
    "1_no_valve": ("No valve", "Recycling off — patient holding, nothing forced out."),
    "2_underwater": ("Underwater valve", "Recycle a long-held EQUITY that's below its entry price."),
    "3_underperformance": ("Underperformance valve", "Recycle a long-held EQUITY trailing SPY by ≥5%/yr."),
}

NOTES = {
    "1_no_valve": [
        ("good", "Best return-per-drawdown of the three (barely) AND the lowest max drawdown — recycling adds nothing here."),
        ("good", "Simplest to reason about: pure patient holding, 9 trades, zero forced turnover."),
        ("warn", "87% of gains come from 2 LEAP trades (one TSLA LEAP alone = 60%). Ex-those-2, return drops to ~161% total (~13%/yr) — SPY-like, at ~1.5× the drawdown."),
        ("warn", "100% pre-vault win rate on 9 trades is a survivorship + tiny-sample artifact, not skill."),
    ],
    "2_underwater": [
        ("good", "Statistically TIED with no-valve on return/DD (30.00 vs 30.01); marginally best Sharpe."),
        ("good", "Slightly less concentrated (top-2 = 71% of gains vs 87%)."),
        ("bad", "Slightly WORSE max drawdown than no-valve for no return benefit — churn without a clear payoff."),
        ("warn", "Recycles losers (MUFG, MMM) that were never the real slot-blockers."),
    ],
    "3_underperformance": [
        ("bad", "WORST of the three once judged on CORRECTED SPY data (return/DD 25.60 vs ~30). Its earlier 'win' was an artifact of SPY history starting only 2021-07."),
        ("bad", "Churns fine winners (UBS +23%, MMM +21%) into names that did worse (WDC −32%, RCL −55%). 'Lagging SPY for a year' is a bad eviction signal — quality lags then recovers."),
        ("warn", "Still does NOT capture the Oct-Dec 2022 mega-caps it was built for — those are LEAP-slot contention, which this equity-only valve never touches."),
        ("warn", "Most turnover of the three (8 recycles)."),
    ],
    "SPY": [
        ("good", "The honest bar over the FULL window (2018-2025, now that SPY data is fixed): 11.9%/yr at 34.1% max drawdown, Sharpe 0.47."),
        ("bad", "Every strategy variant beats it on return and on Sharpe/Calmar — but at ~1.4× its drawdown."),
        ("warn", "The strategy's entire edge over SPY is ~2 LEAP trades. Strip those and it is SPY-like. That is the whole story."),
    ],
}

WINNER_ID = "1_no_valve"
WINNER_REASON = ("Best return-per-drawdown of the three (barely) with the lowest max drawdown — "
                "but the real finding is that RECYCLING DOESN'T EARN ITS KEEP: no-valve ties the "
                "underwater valve, and the underperformance valve actively HURT once the SPY data "
                "was corrected. Recommendation: run NO valve.")


def _align(curves: dict) -> dict:
    union = pd.DatetimeIndex(sorted(set().union(*[set(c.index) for c in curves.values()])))
    out = {}
    for name, curve in curves.items():
        a = curve.reindex(union).ffill()
        out[name] = [None if v != v else round(float(v), 2) for v in a.values]
    out["_dates"] = [d.strftime("%Y-%m-%d") for d in union]
    return out


def main():
    from backtest.fib_reporting import compute_trade_stats
    from screener.data import fetch_daily_bars

    full = pickle.load(open(f"{SCRATCH}/part2_valve_full.pkl", "rb"))
    am = pickle.load(open(f"{SCRATCH}/analyst_metrics.pkl", "rb"))
    conc, spy_stats = am["conc"], am["spy"]

    any_res = full["1_no_valve"]["result"]
    start, end = any_res.equity_curve.index.min(), any_res.equity_curve.index.max()
    seed = float(any_res.equity_curve.iloc[0])

    spy = fetch_daily_bars("SPY")["Close"].loc[start:end]
    spy_curve = (spy / spy.iloc[0]) * seed

    curves = {vid: full[vid]["result"].equity_curve for vid in VARIANT_META}
    curves["SPY"] = spy_curve
    aligned = _align(curves)

    cards = []
    for vid, d in full.items():
        res = d["result"]; ts = compute_trade_stats(res); c = conc[vid]
        cards.append({
            "id": vid, "label": VARIANT_META[vid][0], "subtitle": VARIANT_META[vid][1],
            "is_winner": vid == WINNER_ID,
            "stats": {"total_return": d["total_return"], "cagr": c["cagr"],
                     "max_drawdown": d["max_drawdown"], "ret_dd": d["ret_dd"],
                     "sharpe": c["sharpe"], "calmar": c["calmar"],
                     "win_rate": d["win_rate"], "n_closed": d["n_closed"],
                     "avg_hold": ts["avg_hold_days"], "deployment": d["deployment"]},
            "conc": {"top1": c["top1_pct"], "top2": c["top2_pct"],
                    "ex2": c["ex2_return"], "leap": c["leap_pct"], "n_leap": c["n_leap"]},
            "notes": NOTES[vid],
        })
    cards.append({
        "id": "SPY", "label": "SPY buy & hold", "subtitle": "The benchmark (full window, 2018-2025).",
        "is_winner": False,
        "stats": {"total_return": spy_stats["total_return"], "cagr": spy_stats["cagr"],
                 "max_drawdown": spy_stats["maxdd"],
                 "ret_dd": spy_stats["total_return"] / spy_stats["maxdd"],
                 "sharpe": spy_stats["sharpe"], "calmar": spy_stats["calmar"],
                 "win_rate": None, "n_closed": None, "avg_hold": None, "deployment": 1.0},
        "conc": None, "notes": NOTES["SPY"],
    })

    win_res = full[WINNER_ID]["result"]
    trade_log = sorted(
        [{"ticker": t.ticker, "kind": t.kind, "entry": t.entry_date.strftime("%Y-%m-%d"),
          "exit": t.exit_date.strftime("%Y-%m-%d") if t.exit_date else None,
          "reason": t.exit_reason or "OPEN",
          "pnl_pct": round(t.pnl_pct, 4) if t.pnl_pct is not None else None}
         for t in win_res.trades], key=lambda x: x["entry"])

    part1 = pickle.load(open(f"{SCRATCH}/part1_results.pkl", "rb"))
    part1_answers = {
        "trail": "ut_trail vs pct_trail: essentially a wash (ut won only 2/6 pairs; biggest "
                "runners identical). The champion's ut_trail win is cell-specific luck.",
        "tf": "daily vs 3-day: an INTERACTION with sizing, not a standalone edge (3-day wins with "
             "deepen/both, daily with diversify; trade counts and win rates near-equal).",
        "deadzone": f"0.5-0.9 dead zone: zero stalls in the champion cell; only "
                   f"{part1['pooled'][0]}/{part1['pooled'][1]} equity trades "
                   f"({part1['pooled'][0]/part1['pooled'][1]:.0%}) pooled. Rare, non-binding.",
    }

    data = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "window": {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")},
        "cards": cards, "curves": aligned, "trade_log": trade_log,
        "winner_id": WINNER_ID, "winner_reason": WINNER_REASON,
        "part1": part1_answers, "caveat": CAVEAT,
    }
    open(OUT_PATH, "w").write(_render(data))
    print(f"wrote {OUT_PATH}; winner {WINNER_ID}; {len(cards)} cards; {len(trade_log)} trades")


# ------------------------------------------------------------------ render
def _pct(v, d=1): return "—" if v is None else f"{v*100:.{d}f}%"
def _num(v, d=0): return "—" if v is None else f"{v:.{d}f}"
def _stat(label, value): return f'<div class="stat"><div class="lbl">{label}</div><div class="val">{value}</div></div>'


def _card(c):
    s = c["stats"]
    crown = '<span class="crown">⭐ WINNER</span>' if c["is_winner"] else ""
    stat_html = "".join([
        _stat("Total return", _pct(s["total_return"])), _stat("CAGR", _pct(s["cagr"])),
        _stat("Max drawdown", _pct(s["max_drawdown"])), _stat("Return ÷ DD", _num(s["ret_dd"], 2)),
        _stat("Sharpe", _num(s["sharpe"], 2)), _stat("Calmar", _num(s["calmar"], 2)),
        _stat("Win rate", _pct(s["win_rate"])), _stat("Trades", _num(s["n_closed"])),
        _stat("Avg hold (d)", _num(s["avg_hold"])), _stat("Deployment", _pct(s["deployment"])),
    ])
    conc_html = ""
    if c["conc"]:
        k = c["conc"]
        conc_html = (f'<div class="conc">⚠️ <b>Concentration:</b> top-2 trades = {_pct(k["top2"],0)} '
                    f'of gains · {k["n_leap"]} LEAP trades = {_pct(k["leap"],0)} of net P&amp;L · '
                    f'ex-top-2 return {_pct(k["ex2"],0)}</div>')
    icon = {"good": "✅", "bad": "⚠️", "warn": "🔍"}
    notes = "".join(f'<li><span>{icon[k]}</span> {t}</li>' for k, t in c["notes"])
    cls = "card winner" if c["is_winner"] else "card"
    return (f'<div class="{cls}"><div class="card-head"><h3>{c["label"]}{crown}</h3>'
           f'<div class="sub">{c["subtitle"]}</div></div>'
           f'<div class="stats">{stat_html}</div>{conc_html}'
           f'<div class="notes-title">Notes &amp; Takeaways</div><ul class="notes">{notes}</ul></div>')


def _trade_rows(log):
    out = []
    for t in log:
        pnl = _pct(t["pnl_pct"]) if t["pnl_pct"] is not None else "open"
        cls = "pos" if (t["pnl_pct"] or 0) >= 0 else "neg"
        out.append(f'<tr><td>{t["ticker"]}</td><td>{t["kind"]}</td><td>{t["entry"]}</td>'
                  f'<td>{t["exit"] or "—"}</td><td>{t["reason"]}</td><td class="{cls}">{pnl}</td></tr>')
    return "".join(out)


CSS = """
:root{--bg:#0f1117;--panel:#171a23;--border:#262b38;--text:#e8e9ed;--sub:#9aa0ad;
--accent:#5b9dff;--good:#4ade80;--bad:#fbbf24;--warn:#f87171;--win:#facc15;}
@media (prefers-color-scheme:light){:root{--bg:#f6f7fb;--panel:#fff;--border:#e2e6ef;
--text:#1a1d29;--sub:#5a6272;--accent:#2563eb;}}
:root[data-theme=dark]{--bg:#0f1117;--panel:#171a23;--border:#262b38;--text:#e8e9ed;--sub:#9aa0ad;}
:root[data-theme=light]{--bg:#f6f7fb;--panel:#fff;--border:#e2e6ef;--text:#1a1d29;--sub:#5a6272;--accent:#2563eb;}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}
.wrap{max-width:1180px;margin:0 auto;padding:20px 16px 60px;}
h1{font-size:1.5rem;margin:0 0 4px;}
.meta{color:var(--sub);font-size:.85rem;margin-bottom:16px;}
.banner{background:rgba(248,113,113,.12);border:1px solid var(--warn);border-radius:10px;
padding:12px 16px;font-size:.9rem;margin-bottom:20px;}
.winner-strip{background:linear-gradient(90deg,rgba(250,204,21,.15),transparent);
border:1px solid var(--win);border-radius:10px;padding:12px 16px;margin-bottom:22px;}
.winner-strip b{color:var(--win);}
.legend{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:22px;}
.legend h2{margin:0 0 10px;font-size:1.1rem;}
.legend ul{margin:0 0 10px;padding-left:18px;}
.legend li{font-size:.88rem;margin-bottom:5px;}
.legend .vk{font-size:.88rem;margin-bottom:6px;}
.legend .vk b{color:var(--accent);}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(285px,1fr));gap:14px;margin-bottom:24px;}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;}
.card.winner{border-color:var(--win);box-shadow:0 0 0 1px var(--win) inset;}
.card-head h3{margin:0;font-size:1.05rem;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.crown{font-size:.68rem;background:var(--win);color:#1a1d29;padding:2px 7px;border-radius:20px;font-weight:700;}
.card .sub{color:var(--sub);font-size:.8rem;margin-top:2px;}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:14px 0 10px;}
.stat{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px 10px;}
.stat .lbl{color:var(--sub);font-size:.7rem;text-transform:uppercase;letter-spacing:.03em;}
.stat .val{font-size:1.12rem;font-weight:600;margin-top:2px;}
.conc{background:rgba(248,113,113,.1);border:1px solid var(--warn);border-radius:8px;
padding:8px 10px;font-size:.78rem;margin-bottom:10px;}
.notes-title{font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:var(--sub);
margin:6px 0;font-weight:600;}
.notes{list-style:none;padding:0;margin:0;}
.notes li{display:flex;gap:8px;font-size:.85rem;margin-bottom:7px;align-items:flex-start;}
.notes li span{flex:none;}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:18px;}
.panel h2{margin:0 0 12px;font-size:1.1rem;}
canvas{max-width:100%;}
.analysis li{margin-bottom:10px;font-size:.9rem;}
.analysis b{color:var(--accent);}
details{background:var(--panel);border:1px solid var(--border);border-radius:12px;margin-bottom:14px;}
details summary{padding:14px 16px;cursor:pointer;font-weight:600;}
details .body{padding:0 16px 16px;}
table{width:100%;border-collapse:collapse;font-size:.85rem;}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--border);}
th{color:var(--sub);font-weight:600;}
.pos{color:var(--good);}.neg{color:var(--warn);}
.table-scroll{overflow-x:auto;}
a{color:var(--accent);}
"""

SCRIPT = """
const D=__DATA__;
const series=[
 {k:'1_no_valve',label:'No valve (winner)',c:'#facc15'},
 {k:'2_underwater',label:'Underwater valve',c:'#5b9dff'},
 {k:'3_underperformance',label:'Underperformance valve',c:'#4ade80'},
 {k:'SPY',label:'SPY buy & hold',c:'#f87171'},
];
new Chart(document.getElementById('eq'),{type:'line',data:{labels:D.curves._dates,
 datasets:series.map(s=>({label:s.label,data:D.curves[s.k],borderColor:s.c,
  borderWidth:1.6,pointRadius:0,tension:0,spanGaps:false}))},
 options:{responsive:true,interaction:{mode:'index',intersect:false},
  scales:{x:{ticks:{maxTicksLimit:9},grid:{display:false}},
   y:{ticks:{callback:v=>'$'+(v/1000).toFixed(0)+'k'}}},
  plugins:{legend:{position:'top',labels:{boxWidth:12}}}}});
"""


def _render(data):
    cards = "".join(_card(c) for c in data["cards"])
    p1 = data["part1"]
    analysis = (f'<li><b>Trailing mechanic:</b> {p1["trail"]}</li>'
               f'<li><b>Entry timeframe:</b> {p1["tf"]}</li>'
               f'<li><b>0.5-0.9 dead zone:</b> {p1["deadzone"]}</li>')
    core = "".join(f"<li>{x}</li>" for x in LEGEND_CORE)
    vk = "".join(f'<div class="vk"><b>{n}:</b> {d}</div>' for n, d in LEGEND_VARIANTS)
    script = SCRIPT.replace("__DATA__", json.dumps({"curves": data["curves"]}))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trader-Resp — Strategy Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Trader-Resp — Strategy Dashboard</h1>
<div class="meta">Generated {data['generated_at']} · champion cell 3day/both/ut_trail ·
recycling-valve three-way test · window {data['window']['start']} → {data['window']['end']} (pre-vault)</div>
<div class="banner"><b>⚠️ Read first:</b> {data['caveat']}</div>
<div class="winner-strip"><b>⭐ Winner: {[c['label'] for c in data['cards'] if c['id']==data['winner_id']][0]}</b>
&nbsp;— {data['winner_reason']}</div>
<div class="legend"><h2>How to read this — the strategy in plain terms</h2>
<ul>{core}</ul>
<div class="notes-title">What each card below changes (only the recycling valve differs):</div>
{vk}</div>
<div class="cards">{cards}</div>
<div class="panel"><h2>Equity curves (all variants + SPY, shared axis)</h2>
<canvas id="eq" height="300"></canvas>
<div class="meta" style="margin-top:8px;">Curves are the pre-vault selection window; the vault is
held out and not re-peeked here. SPY history was extended back to 2018 (data fix, 2026-07-22) so
this comparison is now apples-to-apples over the full window.</div></div>
<div class="panel analysis"><h2>Mechanic analysis — answers from the existing 12-cell run</h2>
<ul>{analysis}</ul></div>
<details><summary>Trade log — winner (no valve), {len(data['trade_log'])} trades</summary>
<div class="body"><div class="table-scroll"><table>
<thead><tr><th>Ticker</th><th>Kind</th><th>Entry</th><th>Exit</th><th>Exit reason</th><th>P&amp;L %</th></tr></thead>
<tbody>{_trade_rows(data['trade_log'])}</tbody></table></div></div></details>
<details><summary>Archive — retired-generation research (collapsed)</summary>
<div class="body"><p class="meta">Prior research generations, kept for history:</p><ul>
<li><b>Real LEAP pricing correction</b> (2026-07-21) — see <code>reports/fib_final_run.md</code>.</li>
<li><b>Tiered drawdown gate</b> exploration (2026-07-20) — see <code>reports/fib_tiered_gate.md</code>.</li>
<li><b>Three-way exit-shape ablation</b> (2026-07-20) — see <code>reports/fib_final_ablation.md</code>.</li>
<li><b>Beat-SPY Package</b> 12-cell grid + attribution (2026-07-22) — see <code>reports/beat_spy_package.md</code>.</li>
<li><b>Exit/entry + valve analysis</b> (2026-07-22) — see <code>reports/exit_entry_valve.md</code>.</li>
</ul></div></details>
</div><script>{script}</script></body></html>"""


if __name__ == "__main__":
    main()
