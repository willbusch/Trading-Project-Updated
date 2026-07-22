"""Render reports/results_dashboard.html from reports/dashboard_data.json.

Self-contained: inline CSS/JS, Chart.js loaded via CDN, data embedded
directly in the page (no fetch() calls, no external data reads at view
time — everything needed is baked in at generation time). Re-run this
(after scripts/generate_dashboard_data.py) whenever the backtest changes,
so the dashboard never goes stale relative to the data it shows.
"""
import json

DATA_PATH = "reports/dashboard_data.json"
OUT_PATH = "reports/results_dashboard.html"

CAVEAT_BANNER = (
    "STILL the survivorship-biased proxy universe with current-snapshot "
    "market caps — top-10-by-cap, tiered gates, and reserve modeling all "
    "lean on point-in-time data this project does not truly have. THE "
    "HONEST VERDICT (2026-07-22 “Beat-SPY Package” run): this cell "
    "does NOT beat SPY risk-adjusted — every tested cell runs roughly "
    "DOUBLE SPY's max drawdown despite an enormous headline return, and the "
    "mandatory overfitting guard flags the top-ranked cells as concentrated "
    "in 2–3 large, plausibly lucky LEAP trades, not proven edge. A good "
    "return number here is NECESSARY but NOT SUFFICIENT evidence — full "
    "detail in reports/beat_spy_package.md. Do not let this number end the "
    "skepticism."
)


def fmt_pct(v, digits=1):
    return "—" if v is None else f"{v*100:.{digits}f}%"


def fmt_num(v, digits=1):
    return "—" if v is None else f"{v:.{digits}f}"


def build_html(data: dict) -> str:
    cell = data["cell"]
    variant = data["exit_variant"]
    vault_start = data["vault_start"]
    pv, va = data["stats"]["pre_vault"], data["stats"]["vault"]
    pv_t, pv_d = pv["trade"], pv["dd"]
    va_t, va_d = va["trade"], va["dd"]
    spy_pv = data["spy_benchmark"]["pre_vault"]
    spy_va = data["spy_benchmark"]["vault"]

    beat_spy_vault = (va_d["total_return"] or -9) > (spy_va["total_return"] or 9)
    # RISK-ADJUSTED verdict (2026-07-22): both return AND max drawdown must
    # beat SPY, or it isn't a win — see reports/beat_spy_package.md.
    beat_return_pv = (pv_d["total_return"] or -9) > (spy_pv["total_return"] or 9)
    beat_dd_pv = (pv_d["max_drawdown"] or 9) < (spy_pv["max_drawdown"] or 9)
    beat_return_va = (va_d["total_return"] or -9) > (spy_va["total_return"] or 9)
    beat_dd_va = (va_d["max_drawdown"] or 9) < (spy_va["max_drawdown"] or 9)
    beats_spy_risk_adjusted = beat_return_pv and beat_dd_pv and beat_return_va and beat_dd_va
    ec = data["exit_comparison"]
    # The exit-ablation comparison table (section 3) and Gap section
    # (section 4) document the 2026-07-20 PRE-1.618 exit-shape ablation
    # (simple_05 / simple_09 / latch_v2) — a separate, still-valid question
    # from A7's POST-1.618 trailing-exit change, so they reference that
    # ablation's own winner, not today's champion `variant` (which may be
    # "trail_ut"/"trail_pct20"/"trail_pct15" and isn't a key in `ec`).
    gap_variant = "simple_09"

    def _trade_row(t):
        exit_price_str = f"${t['exit_price']:.2f}" if t['exit_price'] else "—"
        pnl_str = fmt_pct(t['pnl_pct'], 1) if t['pnl_pct'] is not None else "—"
        row_class = "open" if t["is_open"] else ""
        pnl_class = "pos" if (t["pnl_pct"] or 0) >= 0 else "neg"
        return (
            f"<tr class='{row_class}'>"
            f"<td>{t['ticker']}</td><td>{t['kind']}</td>"
            f"<td>{t['entry_date']}</td><td>${t['entry_price']:.2f}</td>"
            f"<td>{t['exit_date'] or '—'}</td>"
            f"<td>{exit_price_str}</td>"
            f"<td>{t['exit_reason']}</td>"
            f"<td>{t['hold_days'] if t['hold_days'] is not None else '—'}</td>"
            f"<td class='{pnl_class}'>{pnl_str}</td>"
            f"</tr>"
        )

    trade_rows = "".join(_trade_row(t) for t in data["trade_log"])

    exit_rows = "".join(
        f"<tr class='{'winner' if k == gap_variant else ''}'>"
        f"<td>{k}{' ⭐' if k == gap_variant else ''}</td>"
        f"<td>{ec[k]['n_closed']}</td>"
        f"<td>{fmt_pct(ec[k]['win_rate'])}</td>"
        f"<td>{fmt_pct(ec[k]['expectancy_pct'])}</td>"
        f"<td>{fmt_pct(ec[k]['total_return'])}</td>"
        f"<td>{ec[k]['gap_trades']}</td>"
        f"<td>${ec[k]['gap_giveback']:,.0f}</td>"
        f"</tr>"
        for k in ["simple_05", "simple_09", "latch_v2"]
    )

    tg = data.get("tiered_gate")
    tiered_html = ""
    if tg:
        min_vault_n = min(r["vault_n"] for r in tg["matrix"])
        min_vault_exp_at_min_n = min(
            (r["vault_exp"] or 9e9) for r in tg["matrix"] if r["vault_n"] == min_vault_n
        )

        def _tiered_row(r):
            weak = (r["vault_n"] == min_vault_n and (r["vault_exp"] or 9e9) == min_vault_exp_at_min_n)
            flag = " ⚠️" if weak else ""
            ys = ", ".join(f"{y}:{n}" for y, n in sorted(r["year_spread"].items()))
            return (
                f"<tr><td>{r['cell']}</td>"
                f"<td>{fmt_pct(r['total_return'])}</td>"
                f"<td>{fmt_pct(r['prevault_exp'])}</td><td>{r['prevault_n']}</td>"
                f"<td>{fmt_pct(r['vault_exp'])}{flag}</td><td>{r['vault_n']}</td>"
                f"<td style='font-size:0.75rem;color:var(--muted)'>{ys}</td></tr>"
            )

        tiered_rows = "".join(_tiered_row(r) for r in tg["matrix"])
        fb, tb = tg["flat_baseline"], tg["tiered_baseline_cell"]

        tiered_html = f"""
  <div class="panel" style="border-color:var(--warn);">
    <h2>7. Tiered Drawdown Gate — ✅ ADOPTED 2026-07-21 (history: reopened research 2026-07-20)</h2>
    <div class="sub">25% ($500B+) / 30% ($150-500B) / 40% (under $150B), by CURRENT market cap (no point-in-time data available — flagged proxy). Now the OFFICIAL gate driving the primary equity curve above. This section's matrix is the 2026-07-20 exploration that led to adoption; full detail: <code>reports/fib_tiered_gate.md</code>, <code>reports/fib_final_run.md</code>.</div>
    <h3 style="margin-top:14px;font-size:0.95rem;">6-cell matrix, sorted by total return (vault columns never hidden)</h3>
    <div class="table-scroll">
    <table>
      <thead><tr><th>Cell</th><th>Total Ret</th><th>Pre-vault Exp</th><th>Pre-vault N</th>
        <th>Vault Exp</th><th>Vault N</th><th>Year spread</th></tr></thead>
      <tbody>{tiered_rows}</tbody>
    </table>
    </div>
    <div class="sub">⚠️ = weakest vault performance among the 6 — check before trusting the total-return sort alone.</div>
    <h3 style="margin-top:14px;font-size:0.95rem;">Tiered vs flat, same cell ({cell}), both re-run fresh this session</h3>
    <table>
      <thead><tr><th></th><th>Pre-vault N</th><th>Pre-vault Exp</th><th>Pre-vault Ret</th>
        <th>Vault N</th><th>Vault Exp</th><th>Vault Ret</th></tr></thead>
      <tbody>
        <tr><td>Flat 40%/25%</td><td>{fb['prevault_n']}</td><td>{fmt_pct(fb['prevault_exp'])}</td>
          <td>{fmt_pct(fb['prevault_ret'])}</td><td>{fb['vault_n']}</td>
          <td>{fmt_pct(fb['vault_exp'])}</td><td>{fmt_pct(fb['vault_ret'])}</td></tr>
        <tr><td>Tiered 25/30/40</td><td>{tb['prevault_n']}</td><td>{fmt_pct(tb['prevault_exp'])}</td>
          <td>{fmt_pct(tb['prevault_ret'])}</td><td>{tb['vault_n']}</td>
          <td>{fmt_pct(tb['vault_exp'])}</td><td>{fmt_pct(tb['vault_ret'])}</td></tr>
      </tbody>
    </table>
    <div class="sub">Net result on this cell: tiering LOWERED trade count and total return; vault performance was essentially unchanged. Not a clean win — see the full report for the honest read across all 6 cells.</div>
  </div>"""

    leap_correction_html = ""
    lc = data.get("leap_correction")
    if lc:
        def _lc_row(r):
            mult = r.get("multiplier_vs_underlying")
            mult_str = f"{mult:.2f}x" if mult is not None else "—"
            exit_label = r["exit_date"] or "OPEN"
            new_pnl = r.get("new_real_pnl_pct")
            return (
                f"<tr><td>{r['ticker']}</td><td>{r['entry_date']}</td><td>{exit_label}</td>"
                f"<td>{fmt_pct(r['underlying_move_pct'])}</td>"
                f"<td>{fmt_pct(r['old_approx_pnl_pct'])}</td>"
                f"<td class='{'pos' if (new_pnl or 0)>=0 else 'neg'}'>{fmt_pct(new_pnl) if new_pnl is not None else '—'}</td>"
                f"<td>{mult_str}</td></tr>"
            )
        lc_rows = "".join(_lc_row(r) for r in lc)
        leap_correction_html = f"""
  <div class="panel" style="border-color:var(--accent);">
    <h2>8. LEAP Pricing Correction — ⭐ the headline fix (2026-07-21)</h2>
    <div class="sub">The old flat 0.55-delta approximation retired. Real Black-Scholes pricing (K and sigma frozen at entry from the underlying's own trailing realized vol; only S and T evolve) now drives every LEAP trade's P&L. Every trade below was mispriced by the old model.</div>
    <div class="table-scroll">
    <table>
      <thead><tr><th>Ticker</th><th>Entry</th><th>Exit</th><th>Underlying move</th>
        <th>OLD approx</th><th>NEW real</th><th>Multiplier</th></tr></thead>
      <tbody>{lc_rows}</tbody>
    </table>
    </div>
    <div class="sub">JPM/ASML/TSLA/MU(2nd): understated 2.5-3.8x by the old model. MU(1st): underlying nearly flat (-1.2%) but the real option, held through 2 years of theta into a flat-to-down move, <b>expired completely worthless (-100%)</b> — a real outcome the old linear model could never represent. MSFT (still open) flips from ~0% under the old model to a real -21.7% loss under real pricing on a barely-negative underlying move — theta decay alone. Multiplier figures on near-zero underlying moves are mathematically noisy; read the absolute percentages.</div>
  </div>"""

    data_json = json.dumps(data)

    return f"""<title>Backtest Results Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1117; --panel: #171a23; --border: #2a2e3a; --text: #e8e9ed;
    --muted: #9198a8; --accent: #5b9dff; --pos: #4ade80; --neg: #f87171;
    --warn: #fbbf24;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{ --bg: #f6f7fb; --panel: #ffffff; --border: #dde1ea; --text: #1a1d29;
             --muted: #5c6270; --accent: #2563eb; --pos: #16a34a; --neg: #dc2626;
             --warn: #b45309; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: var(--bg); color: var(--text); line-height: 1.5; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; padding: 16px; }}
  h1 {{ font-size: 1.4rem; margin: 8px 0 4px; }}
  h2 {{ font-size: 1.1rem; margin: 0 0 12px; }}
  .meta {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 16px; }}
  .banner {{ background: #7f1d1d; color: #fecaca; border: 1px solid #991b1b;
             border-radius: 8px; padding: 12px 16px; font-size: 0.9rem;
             font-weight: 600; margin-bottom: 20px; }}
  @media (prefers-color-scheme: light) {{
    .banner {{ background: #fef2f2; color: #7f1d1d; border-color: #fca5a5; }}
  }}
  .panel {{ background: var(--panel); border: 1px solid var(--border);
            border-radius: 10px; padding: 16px; margin-bottom: 20px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
           gap: 12px; }}
  .stat {{ background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
           padding: 10px 12px; }}
  .stat .label {{ color: var(--muted); font-size: 0.72rem; text-transform: uppercase;
                  letter-spacing: 0.03em; }}
  .stat .value {{ font-size: 1.25rem; font-weight: 700; margin-top: 2px; }}
  .verdict {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }}
  .verdict .pill {{ padding: 8px 14px; border-radius: 20px; font-weight: 600;
                    font-size: 0.85rem; }}
  .pill.yes {{ background: rgba(74,222,128,0.15); color: var(--pos);
              border: 1px solid var(--pos); }}
  .pill.no {{ background: rgba(248,113,113,0.15); color: var(--neg);
             border: 1px solid var(--neg); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; font-size: 0.75rem;
        text-transform: uppercase; cursor: pointer; user-select: none; }}
  th:hover {{ color: var(--accent); }}
  tr.winner {{ background: rgba(91,157,255,0.08); }}
  tr.open td {{ color: var(--warn); }}
  td.pos {{ color: var(--pos); }} td.neg {{ color: var(--neg); }}
  .table-scroll {{ overflow-x: auto; max-height: 420px; overflow-y: auto; }}
  canvas {{ max-width: 100%; }}
  .sub {{ color: var(--muted); font-size: 0.8rem; margin-top: 4px; }}
</style>

<div class="wrap">
  <h1>Latched-Fib Strategy — Backtest Results Dashboard</h1>
  <div class="meta">Generated {data['generated_at']} · #1-ranked cell (return÷maxDD) <b>{cell}</b> ·
    equity sizing <b>{data.get('equity_sizing', '?')}</b> · trailing exit <b>{variant}</b> · vault boundary {vault_start}</div>

  <div class="banner">⚠️ {CAVEAT_BANNER}</div>

  <div class="panel">
    <h2>1. Equity Curves</h2>
    <canvas id="equityChart" height="320"></canvas>
    <div class="sub">Vertical line marks the 12-month vault boundary ({vault_start}) — everything right of it was tested once, held out from strategy selection.</div>
  </div>

  <div class="panel">
    <h2>2. Verdict Panel</h2>
    <div class="verdict">
      <span class="pill {'yes' if beats_spy_risk_adjusted else 'no'}" style="font-size:1.05rem;">
        {'✅ BEATS SPY RISK-ADJUSTED (return AND max DD, both windows)' if beats_spy_risk_adjusted else '❌ DOES NOT BEAT SPY RISK-ADJUSTED'}
      </span>
      <span class="pill {'yes' if beat_return_pv else 'no'}">
        pre-vault return {'beats' if beat_return_pv else 'trails'} SPY
      </span>
      <span class="pill {'yes' if beat_dd_pv else 'no'}">
        pre-vault max DD {'beats' if beat_dd_pv else 'WORSE than'} SPY
      </span>
      <span class="pill {'yes' if beat_return_va else 'no'}">
        vault return {'beats' if beat_return_va else 'trails'} SPY
      </span>
      <span class="pill {'yes' if beat_dd_va else 'no'}">
        vault max DD {'beats' if beat_dd_va else 'WORSE than'} SPY
      </span>
    </div>
    <div class="sub" style="margin-top:8px;">Per the 2026-07-22 "Beat-SPY Package" run's own rule: BOTH return and max drawdown must beat SPY, in both windows, or it isn't a risk-adjusted win. The huge return number below is real; the drawdown number next to it is what actually decides the verdict. Full 7-question answer set, 12-cell ranking, and the mandatory overfitting guard: <code>reports/beat_spy_package.md</code>.</div>
    <h3 style="margin-top:18px;font-size:0.95rem;">Pre-vault</h3>
    <div class="grid">
      <div class="stat"><div class="label">Total Return</div><div class="value">{fmt_pct(pv_d['total_return'])}</div></div>
      <div class="stat"><div class="label">CAGR</div><div class="value">{fmt_pct(pv_d['cagr'])}</div></div>
      <div class="stat"><div class="label">Expectancy/Trade</div><div class="value">{fmt_pct(pv_t['expectancy_pct'])}</div></div>
      <div class="stat"><div class="label">Win Rate</div><div class="value">{fmt_pct(pv_t['win_rate'])}</div></div>
      <div class="stat"><div class="label">Max Drawdown</div><div class="value">{fmt_pct(pv_d['max_drawdown'])}</div></div>
      <div class="stat"><div class="label">Avg Hold (days)</div><div class="value">{fmt_num(pv_t['avg_hold_days'], 0)}</div></div>
      <div class="stat"><div class="label">Trades Closed</div><div class="value">{pv_t['n_closed']}</div></div>
      <div class="stat"><div class="label">SPY Total Return</div><div class="value">{fmt_pct(spy_pv['total_return'])}</div></div>
    </div>
    <h3 style="margin-top:18px;font-size:0.95rem;">Vault (last 12mo, tested once)</h3>
    <div class="grid">
      <div class="stat"><div class="label">Total Return</div><div class="value">{fmt_pct(va_d['total_return'])}</div></div>
      <div class="stat"><div class="label">CAGR</div><div class="value">{fmt_pct(va_d['cagr'])}</div></div>
      <div class="stat"><div class="label">Expectancy/Trade</div><div class="value">{fmt_pct(va_t['expectancy_pct'])}</div></div>
      <div class="stat"><div class="label">Win Rate</div><div class="value">{fmt_pct(va_t['win_rate'])}</div></div>
      <div class="stat"><div class="label">Max Drawdown</div><div class="value">{fmt_pct(va_d['max_drawdown'])}</div></div>
      <div class="stat"><div class="label">Avg Hold (days)</div><div class="value">{fmt_num(va_t['avg_hold_days'], 0)}</div></div>
      <div class="stat"><div class="label">Trades Closed</div><div class="value">{va_t['n_closed']}</div></div>
      <div class="stat"><div class="label">SPY Total Return</div><div class="value">{fmt_pct(spy_va['total_return'])}</div></div>
    </div>
    <div class="sub">Vault trade counts are 1–2 in this backtest — not statistically meaningful on their own. Treat the vault verdict as suggestive, not proof.</div>
  </div>

  <div class="panel">
    <h2>3. Exit-Ablation Comparison (2026-07-20, pre-vault)</h2>
    <div class="table-scroll">
    <table>
      <thead><tr><th>Variant</th><th>Closed</th><th>Win Rate</th><th>Expectancy</th>
        <th>Total Return</th><th>Gap Trades</th><th>Gap Give-back</th></tr></thead>
      <tbody>{exit_rows}</tbody>
    </table>
    </div>
    <div class="sub">⭐ = winner, selected on pre-vault expectancy only. The full-latch design (<code>latch_v2</code>) lost to a plain 0.9 floor despite more complexity, and cost $77k in quantified give-back with no expectancy benefit.</div>
  </div>

  <div class="panel">
    <h2>4. The Gap — Pre-1.618 Exit Shape ({gap_variant})</h2>
    <div class="grid">
      <div class="stat"><div class="label">Gap Trades</div><div class="value">{ec[gap_variant]['gap_trades']}</div></div>
      <div class="stat"><div class="label">Total Give-back</div><div class="value">${ec[gap_variant]['gap_giveback']:,.0f}</div></div>
    </div>
    <div class="sub">The Gap = trades that peaked above entry, never hit the 1.618 target, never triggered a zone exit, and closed at a loss or gave back most of their peak gain — the accepted cost of "no exit below the floor." Zero for the winning variant in this sample; it will not stay zero on a larger or less curated universe.</div>
  </div>

  <div class="panel">
    <h2>5. Trade Log ({len(data['trade_log'])} trades)</h2>
    <div class="table-scroll">
    <table id="tradeTable">
      <thead><tr>
        <th onclick="sortTable(0)">Ticker</th><th onclick="sortTable(1)">Kind</th>
        <th onclick="sortTable(2)">Entry Date</th><th onclick="sortTable(3)">Entry $</th>
        <th onclick="sortTable(4)">Exit Date</th><th onclick="sortTable(5)">Exit $</th>
        <th onclick="sortTable(6)">Exit Zone</th><th onclick="sortTable(7)">Hold (d)</th>
        <th onclick="sortTable(8)">P&amp;L %</th>
      </tr></thead>
      <tbody>{trade_rows}</tbody>
    </table>
    </div>
    <div class="sub">Click a column header to sort. "Kind" (equity/LEAP) shown in place of a live-account label — these are simulated backtest trades, not tied to a real brokerage account.</div>
  </div>
  {tiered_html}
  {leap_correction_html}
</div>

<script>
const DATA = {data_json};

const ctx = document.getElementById('equityChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: DATA.curves.strategy.dates,
    datasets: [
      {{ label: 'Strategy ({variant})', data: DATA.curves.strategy.values,
        borderColor: '#5b9dff', borderWidth: 1.5, pointRadius: 0, tension: 0 }},
      {{ label: 'Strategy (idle cash in SPY)', data: DATA.curves.strategy_spy_idle_cash.values,
        borderColor: '#4ade80', borderWidth: 1.5, pointRadius: 0, tension: 0 }},
      {{ label: 'SPY buy-and-hold', data: DATA.curves.spy_buy_hold.values,
        borderColor: '#fbbf24', borderWidth: 1.5, pointRadius: 0, tension: 0 }},
    ]
  }},
  options: {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    scales: {{
      x: {{ ticks: {{ maxTicksLimit: 10 }}, grid: {{ display: false }} }},
      y: {{ ticks: {{ callback: v => '$' + v.toLocaleString() }} }}
    }},
    plugins: {{
      legend: {{ position: 'top' }},
      annotation: {{}}
    }}
  }}
}});

function sortTable(col) {{
  const table = document.getElementById('tradeTable');
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);
  const asc = table.dataset.sortCol == col && table.dataset.sortDir !== 'asc';
  rows.sort((a, b) => {{
    let x = a.cells[col].innerText, y = b.cells[col].innerText;
    const nx = parseFloat(x.replace(/[^0-9.-]/g,'')), ny = parseFloat(y.replace(/[^0-9.-]/g,''));
    if (!isNaN(nx) && !isNaN(ny)) return asc ? nx - ny : ny - nx;
    return asc ? x.localeCompare(y) : y.localeCompare(x);
  }});
  rows.forEach(r => tbody.appendChild(r));
  table.dataset.sortCol = col;
  table.dataset.sortDir = asc ? 'asc' : 'desc';
}}
</script>
"""


def main():
    data = json.load(open(DATA_PATH))
    html = build_html(data)
    open(OUT_PATH, "w").write(html)
    print("wrote", OUT_PATH, len(html), "chars")


if __name__ == "__main__":
    main()
