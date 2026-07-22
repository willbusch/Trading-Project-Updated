"""Render reports/results_dashboard.html — REDESIGNED 2026-07-22.

Grouped BY STRATEGY, not by chart type. One card per variant (the Part 2
three-way valve test on the champion cell, plus SPY), each with only the
essential stats and a plain-language Notes & Takeaways block. Winner
crowned by return/maxDD. Equity curve + trade log kept (trade log
collapsible). Retired-generation ablations collapsed into an Archive.

Self-contained: inline CSS/JS, Chart.js via CDN, data embedded at build
time. Reads the pickled Part 1 + Part 2 runs (no re-simulation) so the
dashboard and reports/exit_entry_valve.md always show identical numbers.
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
    "caps, and SPY price history only reaches back to 2021-07. Beating SPY "
    "here is NECESSARY but NOT SUFFICIENT evidence of edge — the headline "
    "returns rest on 2-3 large LEAP trades, and vault numbers are directional "
    "at best. This dashboard shows the CURRENT strategy picture, not proof. "
    "Do not let a good number end the skepticism."
)

VARIANT_META = {
    "1_no_valve": ("No valve", "Recycling off — patient holding, nothing forced out."),
    "2_underwater": ("Underwater valve", "Recycle a long-held EQUITY that's below its entry price."),
    "3_underperformance": ("Underperformance valve", "Recycle a long-held EQUITY trailing SPY by ≥5%/yr."),
}

NOTES = {
    "1_no_valve": [
        ("good", "Simplest to reason about — 9 trades, no forced turnover."),
        ("bad", "Leaves mediocre holds in place; a stale winner can block a generational entry indefinitely."),
        ("warn", "100% pre-vault win rate is a survivorship + tiny-sample artifact, not skill."),
        ("warn", "Return rests almost entirely on 2-3 LEAP trades (META +449%, TSLA ×2)."),
    ],
    "2_underwater": [
        ("good", "Adds entries (17 vs 9) by clearing dead losers like MUFG (-4.6%), MMM (-3.8%)."),
        ("bad", "Wrong target: it only frees LOSERS, but the real slot-blockers were mediocre WINNERS lagging the index."),
        ("bad", "Higher return than no-valve but WORSE max drawdown (48.2%) — churn without a clear risk payoff."),
        ("warn", "Most turnover of the three (6 recycles)."),
    ],
    "3_underperformance": [
        ("good", "Best return AND lowest drawdown of the three → best return/DD (25.89)."),
        ("good", "Recycles the RIGHT targets: caught VZ (+2.5% but trailing SPY +12%) plus deep laggards RCL/NEM."),
        ("warn", "Does NOT capture the Oct-Dec 2022 mega-caps it was built for — those are LEAP-slot contention (single LEAP slot held by the 2022 META LEAP), and this valve never touches the LEAP."),
        ("warn", "SPY data starts 2021-07, so the valve is BLIND to pre-2021 (2020-vintage) holds — its win is on partial coverage. Directional, not proven."),
    ],
    "SPY": [
        ("good", "The honest bar: +45.9% pre-vault (~9.8% CAGR) at 25.4% max drawdown."),
        ("bad", "Every strategy variant beats it on return but at roughly DOUBLE its drawdown."),
        ("warn", "Cached SPY history begins 2021-07, so this benchmark covers 2021-07 onward, not the full span."),
    ],
}

WINNER_ID = "3_underperformance"
WINNER_REASON = ("Highest return (1221%) with the LOWEST max drawdown (47.2%) of the three, "
                "so the best return-per-unit-drawdown — and it recycles the right targets "
                "(lagging winners, not just losers). Adopt only with its two caveats in view.")


def _align(curves: dict) -> dict:
    """Reindex every curve onto one shared date union (A8 fix). Forward-fill
    WITHIN each series' own coverage only; leave leading gaps as null so a
    shorter series (SPY starts 2021-07) simply begins mid-chart instead of
    being back-filled into a misleading flat line."""
    union = pd.DatetimeIndex(sorted(set().union(*[set(c.index) for c in curves.values()])))
    out = {}
    for name, curve in curves.items():
        a = curve.reindex(union).ffill()
        out[name] = [None if v != v else round(float(v), 2) for v in a.values]
    out["_dates"] = [d.strftime("%Y-%m-%d") for d in union]
    return out


def main():
    from backtest.fib_reporting import compute_trade_stats
    from backtest.fib_universe import deployment_pct
    from screener.data import fetch_daily_bars

    full = pickle.load(open(f"{SCRATCH}/part2_valve_full.pkl", "rb"))
    part1 = pickle.load(open(f"{SCRATCH}/part1_results.pkl", "rb"))

    # window from the champion curves
    any_res = full["1_no_valve"]["result"]
    start = any_res.equity_curve.index.min()
    end = any_res.equity_curve.index.max()
    seed = float(any_res.equity_curve.iloc[0])

    spy = fetch_daily_bars("SPY")["Close"].loc[start:end]
    spy_curve = (spy / spy.iloc[0]) * seed

    curves = {vid: full[vid]["result"].equity_curve for vid in VARIANT_META}
    curves["SPY"] = spy_curve
    aligned = _align(curves)

    cards = []
    for vid, d in full.items():
        res = d["result"]
        ts = compute_trade_stats(res)
        cards.append({
            "id": vid, "label": VARIANT_META[vid][0], "subtitle": VARIANT_META[vid][1],
            "is_winner": vid == WINNER_ID,
            "stats": {
                "total_return": d["total_return"], "cagr": d["cagr"],
                "max_drawdown": d["max_drawdown"], "ret_dd": d["ret_dd"],
                "win_rate": d["win_rate"], "n_closed": d["n_closed"],
                "avg_hold": ts["avg_hold_days"], "deployment": d["deployment"],
                "n_recycle": d["n_recycle"],
            },
            "notes": NOTES[vid],
        })
    # SPY pseudo-card
    from backtest.reporting import compute_drawdown_stats
    spy_dd = compute_drawdown_stats(spy.rename("SPY"))
    cards.append({
        "id": "SPY", "label": "SPY buy & hold", "subtitle": "The benchmark (2021-07 onward).",
        "is_winner": False,
        "stats": {"total_return": spy_dd["total_return"], "cagr": spy_dd["cagr"],
                 "max_drawdown": spy_dd["max_drawdown"],
                 "ret_dd": spy_dd["total_return"] / spy_dd["max_drawdown"] if spy_dd["max_drawdown"] else None,
                 "win_rate": None, "n_closed": None, "avg_hold": None, "deployment": 1.0,
                 "n_recycle": None},
        "notes": NOTES["SPY"],
    })

    # winner's trade log
    win_res = full[WINNER_ID]["result"]
    trade_log = sorted(
        [{"ticker": t.ticker, "kind": t.kind,
          "entry": t.entry_date.strftime("%Y-%m-%d"),
          "exit": t.exit_date.strftime("%Y-%m-%d") if t.exit_date else None,
          "reason": t.exit_reason or "OPEN",
          "pnl_pct": round(t.pnl_pct, 4) if t.pnl_pct is not None else None}
         for t in win_res.trades],
        key=lambda x: x["entry"])

    part1_answers = {
        "trail": f"ut_trail vs pct_trail: essentially a wash (avg return 507.6% vs 517.4%, "
                f"ret/DD 10.70 vs 10.93). ut_trail won only 2 of 6 pairs; biggest runners "
                f"identical. The champion's ut_trail win is cell-specific luck, not a mechanic edge.",
        "tf": f"daily vs 3-day: 3-day's higher average is an INTERACTION with sizing, not a "
             f"standalone edge — 3-day wins big with deepen/both, daily wins big with "
             f"diversify. Trade counts (17 vs 15) and win rates (63% vs 61%) are near-equal. "
             f"Low confidence 3-day is genuinely better.",
        "deadzone": f"0.5-0.9 dead zone: the champion cell had ZERO trades stall 6mo+ in the "
                   f"zone; pooled across all 12 cells only {part1['pooled'][0]} of "
                   f"{part1['pooled'][1]} equity trades ({part1['pooled'][0]/part1['pooled'][1]:.0%}) "
                   f"did. Real risk in theory, but empirically rare and not binding in the winner.",
    }

    data = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "window": {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")},
        "cards": cards, "curves": aligned, "trade_log": trade_log,
        "winner_id": WINNER_ID, "winner_reason": WINNER_REASON,
        "part1": part1_answers, "caveat": CAVEAT, "seed": seed,
    }
    html = _render(data)
    open(OUT_PATH, "w").write(html)
    print(f"wrote {OUT_PATH} ({len(html)} chars)")
    print(f"winner: {WINNER_ID}; cards: {len(cards)}; trade log: {len(trade_log)}")


# ------------------------------------------------------------------ render

def _pct(v, d=1):
    return "—" if v is None else f"{v*100:.{d}f}%"


def _num(v, d=0):
    return "—" if v is None else f"{v:.{d}f}"


def _stat(label, value):
    return f'<div class="stat"><div class="lbl">{label}</div><div class="val">{value}</div></div>'


def _card(c):
    s = c["stats"]
    crown = '<span class="crown">⭐ WINNER</span>' if c["is_winner"] else ""
    stat_html = "".join([
        _stat("Total return", _pct(s["total_return"])),
        _stat("Max drawdown", _pct(s["max_drawdown"])),
        _stat("Return ÷ DD", _num(s["ret_dd"], 2)),
        _stat("CAGR", _pct(s["cagr"])),
        _stat("Win rate", _pct(s["win_rate"])),
        _stat("Trades", _num(s["n_closed"])),
        _stat("Avg hold (d)", _num(s["avg_hold"])),
        _stat("Deployment", _pct(s["deployment"])),
    ])
    icon = {"good": "✅", "bad": "⚠️", "warn": "🔍"}
    notes = "".join(
        f'<li class="note-{kind}"><span>{icon[kind]}</span> {text}</li>'
        for kind, text in c["notes"])
    cls = "card winner" if c["is_winner"] else "card"
    return (f'<div class="{cls}"><div class="card-head"><div><h3>{c["label"]}{crown}</h3>'
           f'<div class="sub">{c["subtitle"]}</div></div></div>'
           f'<div class="stats">{stat_html}</div>'
           f'<div class="notes-title">Notes &amp; Takeaways</div>'
           f'<ul class="notes">{notes}</ul></div>')


def _trade_rows(log):
    out = []
    for t in log:
        pnl = _pct(t["pnl_pct"]) if t["pnl_pct"] is not None else "open"
        cls = "pos" if (t["pnl_pct"] or 0) >= 0 else "neg"
        out.append(f'<tr><td>{t["ticker"]}</td><td>{t["kind"]}</td><td>{t["entry"]}</td>'
                  f'<td>{t["exit"] or "—"}</td><td>{t["reason"]}</td>'
                  f'<td class="{cls}">{pnl}</td></tr>')
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
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px;margin-bottom:24px;}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;}
.card.winner{border-color:var(--win);box-shadow:0 0 0 1px var(--win) inset;}
.card-head h3{margin:0;font-size:1.05rem;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.crown{font-size:.68rem;background:var(--win);color:#1a1d29;padding:2px 7px;border-radius:20px;font-weight:700;}
.card .sub{color:var(--sub);font-size:.8rem;margin-top:2px;}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:14px 0;}
.stat{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px 10px;}
.stat .lbl{color:var(--sub);font-size:.7rem;text-transform:uppercase;letter-spacing:.03em;}
.stat .val{font-size:1.15rem;font-weight:600;margin-top:2px;}
.notes-title{font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:var(--sub);
margin:6px 0 6px;font-weight:600;}
.notes{list-style:none;padding:0;margin:0;}
.notes li{display:flex;gap:8px;font-size:.85rem;margin-bottom:7px;align-items:flex-start;}
.notes li span{flex:none;}
.note-bad{color:var(--text);}.note-warn{color:var(--text);}
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
const cvs=document.getElementById('eq');
const series=[
 {k:'3_underperformance',label:'Underperformance valve (winner)',c:'#facc15'},
 {k:'2_underwater',label:'Underwater valve',c:'#5b9dff'},
 {k:'1_no_valve',label:'No valve',c:'#4ade80'},
 {k:'SPY',label:'SPY buy & hold',c:'#f87171'},
];
new Chart(cvs,{type:'line',data:{labels:D.curves._dates,datasets:series.map(s=>({
 label:s.label,data:D.curves[s.k],borderColor:s.c,borderWidth:1.6,pointRadius:0,
 tension:0,spanGaps:false}))},
 options:{responsive:true,interaction:{mode:'index',intersect:false},
  scales:{x:{ticks:{maxTicksLimit:9},grid:{display:false}},
   y:{ticks:{callback:v=>'$'+(v/1000).toFixed(0)+'k'}}},
  plugins:{legend:{position:'top',labels:{boxWidth:12}}}}});
"""


def _render(data):
    cards = "".join(_card(c) for c in data["cards"])
    p1 = data["part1"]
    analysis = (
        f'<li><b>Trailing mechanic (ut_trail vs pct_trail):</b> {p1["trail"]}</li>'
        f'<li><b>Entry timeframe (daily vs 3-day):</b> {p1["tf"]}</li>'
        f'<li><b>0.5-0.9 dead zone:</b> {p1["deadzone"]}</li>')
    trade_rows = _trade_rows(data["trade_log"])
    data_json = json.dumps({"curves": data["curves"]})
    script = SCRIPT.replace("__DATA__", data_json)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trader-Resp — Strategy Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Trader-Resp — Strategy Dashboard</h1>
<div class="meta">Generated {data['generated_at']} · champion cell 3day/both/ut_trail ·
valve three-way test · window {data['window']['start']} → {data['window']['end']} (pre-vault)</div>
<div class="banner"><b>⚠️ Read first:</b> {data['caveat']}</div>
<div class="winner-strip"><b>⭐ Winner: {[c['label'] for c in data['cards'] if c['id']==data['winner_id']][0]}</b>
&nbsp;— {data['winner_reason']}</div>
<div class="cards">{cards}</div>
<div class="panel"><h2>Equity curves (all variants + SPY, shared axis)</h2>
<canvas id="eq" height="300"></canvas>
<div class="meta" style="margin-top:8px;">SPY line begins 2021-07 (cached history limit) —
shown honestly rather than back-filled. Curves are the pre-vault selection window; the vault
is held out and not re-peeked here.</div></div>
<div class="panel analysis"><h2>Mechanic analysis — answers from the existing 12-cell run</h2>
<ul>{analysis}</ul></div>
<details><summary>Trade log — winner (underperformance valve), {len(data['trade_log'])} trades</summary>
<div class="body"><div class="table-scroll"><table>
<thead><tr><th>Ticker</th><th>Kind</th><th>Entry</th><th>Exit</th><th>Exit reason</th><th>P&amp;L %</th></tr></thead>
<tbody>{trade_rows}</tbody></table></div></div></details>
<details><summary>Archive — retired-generation research (collapsed)</summary>
<div class="body"><p class="meta">Prior research generations, kept for history, no longer the
current picture:</p><ul>
<li><b>Real LEAP pricing correction</b> (2026-07-21) — flat 0.55-delta → Black-Scholes; see
<code>reports/fib_final_run.md</code>.</li>
<li><b>Tiered drawdown gate</b> exploration (2026-07-20) — 25/30/40 by cap; see
<code>reports/fib_tiered_gate.md</code>.</li>
<li><b>Three-way exit-shape ablation</b> (2026-07-20) — simple_05 / simple_09 / latch_v2;
see <code>reports/fib_final_ablation.md</code>.</li>
<li><b>Beat-SPY Package</b> (2026-07-22) full 12-cell grid + attribution — see
<code>reports/beat_spy_package.md</code>.</li>
</ul></div></details>
</div><script>{script}</script></body></html>"""


if __name__ == "__main__":
    main()
