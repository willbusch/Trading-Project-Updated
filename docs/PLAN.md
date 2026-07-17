# PLAN.md

**Project:** Trader-Resp — RSI Mean-Reversion Screener + Backtest
**Owner:** Will Busch
**Last updated:** July 15, 2026
**Read alongside:** `STRATEGY.md`, `GOAL.md`, `CLAUDE-CODE-PROMPT.md`

---

## STATUS SNAPSHOT

| Phase | What | Status |
|---|---|---|
| **0** | Fix the book | 🔴 NOT STARTED |
| **1** | Dashboard (screener → BUY/SELL) | 🔴 NOT STARTED |
| **2** | Pinescript port | 🔴 NOT STARTED |
| **3** | **Backtest — THE GATE** | 🔴 NOT STARTED |
| **4** | Live, small | 🔴 BLOCKED on Phase 3 |
| **5** | Scale to full size | 🔴 BLOCKED on Phases 3 + 4 |

**Currently in progress:** Phase 0 — nothing has been fixed in the live book yet.

---

## STAGE 0 UPDATE — 2026-07-15: RSI(14) switch, Robinhood-only data

Three decisions made and implemented this session, ahead of `STRATEGY.md`
being formally updated to match (that update is still pending — see below):

- **Signal switched from RSI(3) to RSI(14) on 3-day bars.** `config.yaml`'s
  `indicators.rsi_period` is now `14`. `screener/indicators.py` itself
  didn't need to change — `rsi(close, period=...)` was already
  period-agnostic; only the config value and the entry/exit threshold
  numbers built around it change.
- **Robinhood (MCP) is now the sole data source.** `yfinance` has been
  removed from `screener/data.py` and `requirements.txt` entirely — there is
  no automatic fallback to any other provider. The module only ever reads
  from the parquet cache (`fetch_daily_bars()`); new data enters the cache
  exclusively via `ingest_robinhood_bars()`, called by the agent after
  pulling from the Robinhood `get_equity_historicals` MCP tool. This is a
  real architectural constraint, not a preference: MCP tools are only
  callable by the agent, not from a standalone Python script, so "fetch" is
  now necessarily an agent-orchestrated step rather than something
  `data.py` does on its own.
- **Two `config.yaml` keys resolved:** `avg_volume_lookback_days` was
  removed entirely (no longer a named threshold — Stage 1's volume filter
  will need to define how it computes average volume when that stage is
  built). `weekly_lower_low_lookback_weeks` is now `8`.

**RSI(14) validation gate — MSFT & HIMS, 3-day bars, Robinhood data,
5-year history (2021-07-15 to 2026-07-15):**

| | MSFT | HIMS |
|---|---|---|
| Close (latest) | $395.63 | $37.17 |
| RSI(14), 3-day (latest, partial bar) | 48.22 | 64.95 |
| RSI(14) range (5yr) | 26.72 – 80.28 | 19.74 – 84.56 |
| RSI(14) median (5yr) | 52.19 | 50.81 |

Values computed and presented for TradingView cross-check — **not yet
confirmed by the owner.** Same open loop as the original RSI(3) gate: the
numbers are ready to compare, the actual match/mismatch determination still
needs a human eyeballing TradingView's RSI(14)/3-day chart for both names.

**Threshold re-tune — proposed, NOT yet written into `config.yaml`.**
The old RSI(3)-era thresholds produce broken signal frequency under RSI(14)
— most notably, `RSI(14) >= 80` (the old euphoria exit) fired **once in 5
years** for MSFT (0.2 signals/year), because RSI(14) is a smoother
oscillator that rarely reaches RSI(3)'s extremes. Measured crossing
frequency across the same 5-year window (MSFT / HIMS, per year):

| Threshold | Old value | Old freq (MSFT/HIMS) | Proposed | New freq (MSFT/HIMS) |
|---|---|---|---|---|
| Entry (RSI < X) | 35 | 1.8 / 2.6 | **35 (unchanged)** | 1.8 / 2.6 |
| Euphoria exit (RSI ≥ X) | 80 | 0.2 / 0.6 | **70** | 1.6 / 2.4 |
| Momentum-break arm (touch ≥ X) | 70 | 1.0 / 1.6 (at 70→60) | **65** | 1.4 / 1.8 (at 65→55) |
| Momentum-break fire (cross < X) | 60 | ″ | **55** | ″ |

Rationale: entry at 35 already fires at a comparable rate to the old
system, no evidence it needs to move. Euphoria and momentum-break levels
needed to come down because RSI(14) simply doesn't reach the old extremes
often enough for those exits to function. **Awaiting owner confirmation
before these four numbers get written into `config.yaml`.**

**Doc drift flagged, not yet resolved:** `STRATEGY.md` (Parts 2 and 5)
still documents RSI(3) with the original 35/70/80/60 thresholds and the
reasoning specific to that period ("why 3-day, not daily," the 25-30% full-
cycle-capture math in `GOAL.md`). This handoff intentionally scoped the
`STRATEGY.md`/`GOAL.md` rewrite out — those documents carry `STRATEGY.md`'s
own quarterly-review / 7-day-cooldown governance and shouldn't be rewritten
as a side effect of a data-pipeline task. They need a deliberate update once
the RSI(14) thresholds above are confirmed, or this project has two
documents actively disagreeing about its own core signal.

---

## PHASE 0 — FIX THE BOOK
*Before any code enforces the strategy, the book has to obey it.*

| Step | Task | Status |
|---|---|---|
| 0.1 | **Close the NFLX LEAP.** Fails 3 rules: sub-$500B underlying, 34% OTM, no RSI trigger. Cleanest move available — fixes the LEAP overage *and* the cash floor in one trade. | ☐ |
| 0.2 | **Trim HIMS 26.7% → 22%.** Proceeds → **CASH.** Not to ORCL. | ☐ |
| 0.3 | **Get cash to 10%** (~$4,500). Steps 0.1 + 0.2 do most of it. | ☐ |
| 0.4 | **Consolidate to 6 names.** SOFI (6.5%) and NOW (11.2%) are the smallest convictions. One is a position; the other is a habit. Decide which. | ☐ |
| 0.5 | **Write the tranche ladder for every open name** — including the 1.5×ATR rungs. | ☐ |
| 0.6 | **Write the ORCL number.** 🔴 *Still open. Still refused.* | ☐ |

**GATE:** Book satisfies all six constraints in STRATEGY.md Part 6. If the dashboard's first run doesn't flag zero violations, Phase 0 isn't done.

---

## PHASE 1 — THE DASHBOARD
*Screener that scans SPY/QQQ, applies the criteria, emits BUY / SELL / HOLD.*

| Step | Task | Status |
|---|---|---|
| 1.1 | Repo scaffold + `config.yaml` — **every threshold a named key, zero magic numbers** | ☐ |
| 1.2 | `data.py` — Robinhood (MCP) fetch, parquet cache, **fail loudly on missing data, no fallback source** | ☑ (updated 2026-07-15, was yfinance) |
| 1.3 | **Daily → 3-day bar resampling.** Get this exactly right. RSI(14) on 3-day bars ≠ RSI(14) on daily. **Write a test.** | ☐ |
| 1.4 | `indicators.py` — RSI, SMA(200), ATR(14). Unit-test against a known reference. | ☐ |
| 1.5 | Universe build — SPY + QQQ constituents, dedupe, apply hard filters, tag `SHARES_ELIGIBLE` / `LEAP_ELIGIBLE` | ☐ |
| 1.6 | Signal engine — grade every name A / B / C / NO_TRADE | ☐ |
| 1.7 | `portfolio.py` — load `portfolio.yaml`, mark to market, compute % of book + tranche depth | ☐ |
| 1.8 | Sizing engine — emit tranche #, dollar amount, next ladder rung (1.5×ATR below) | ☐ |
| 1.9 | **Constraint checker** — slots, position cap, LEAP cap, cash floor, weekly cap, halt status. **Emit BLOCKED + reason.** | ☐ |
| 1.10 | **Cash rule enforcement** — write a test that tries to route sale proceeds into an underwater position and confirms it **fails.** | ☐ |
| 1.11 | UI — SIGNALS / BOOK / VIOLATIONS / BLOCKED panels. **Every signal shows its inputs.** Never a bare "BUY." | ☐ |

**GATE:** Run against the live book. It **must** flag the current violations (7 names, 38% LEAP, 1.5% cash, HIMS 26.7%, NFLX ineligible). If it doesn't, the constraint checker is broken.

---

## PHASE 2 — PINESCRIPT
*Same rules on the chart, so my eyes can confirm the code.*

| Step | Task | Status |
|---|---|---|
| 2.1 | Port entry/exit logic to Pine v5 | ☐ |
| 2.2 | Plot: RSI(14) on 3-day, SMA(200), tranche ladder rungs, entry/exit markers | ☐ |
| 2.3 | **Reconcile Pine vs Python on 3 names.** If they diverge, one is wrong. Find out which. | ☐ |

**GATE:** Pine signals and Python signals match. No divergence.

---

## PHASE 3 — THE BACKTEST 🎯
*The most important stage in the project. This is the verdict.*

| Step | Task | Status |
|---|---|---|
| 3.1 | 5 years, full SPY/QQQ universe, **all constraints enforced** (slots, tranches, cash floor, weekly cap, halt) | ☐ |
| 3.2 | Include commissions, slippage (0.1%), and **the cash drag from the 10% floor** | ☐ |
| 3.3 | **Report:** CAGR **vs SPY buy-and-hold**, **expectancy/trade**, win rate, avg win, avg loss, payoff ratio, max DD, recovery time | ☐ |
| 3.4 | **Slot utilization** — how often was capital idle? How long did frozen positions clog slots? How many names hit tranche 3 and stayed dead? | ☐ |
| 3.5 | **Cohort split: above-200-SMA vs below-200-SMA, separately.** 🎯 *This is my core hypothesis. This is the number I care most about.* | ☐ |
| 3.6 | **Ablation study** — run each variant, report each honestly: | ☐ |
| | • No 200 SMA filter — *does the filter earn its keep?* | |
| | • Fixed −7.5% ladder vs 1.5×ATR — *was the ATR change worth it?* | |
| | • 1 tranche vs 3 tranches — *does averaging down add value or destroy it?* | |
| | • **With a stop loss vs without** — *I reject stops. I still want the data.* | |
| | • Equities only vs equities + LEAP sleeve — *is the barbell real?* | |
| 3.7 | Current-state check: "would we be in a trade right now, and in what?" | ☐ |

### ⚠️ THE RULE FOR THIS PHASE
> **Run it once. Report it honestly. Do NOT tune parameters until the results look good.**
> That is overfitting, and it will cost real money. If the strategy doesn't work, **say so.**

**GATE — this is the decision point:**
- ✅ **Expectancy > +8%/trade AND beats SPY** → proceed to Phase 4.
- ❌ **Expectancy < +5% OR fails to beat SPY** → **STOP.** Go back to Phase 0. Change the strategy. Do not lever into a system with no edge.

---

## PHASE 4 — LIVE, SMALL

| Step | Task | Status |
|---|---|---|
| 4.1 | Trade the signals live. **1–2 tranches only.** No full ladder. | ☐ |
| 4.2 | **No LEAP sleeve yet.** Equities only. | ☐ |
| 4.3 | Journal every trade: signal, grade, tranche, size, thesis, exit, outcome | ☐ |
| 4.4 | Log the signals I *don't* take, and what would have happened | ☐ |

**GATE:** 20 logged trades. Live expectancy within shouting distance of the backtest.

---

## PHASE 5 — SCALE

| Step | Task | Status |
|---|---|---|
| 5.1 | Full 3-tranche ladder | ☐ |
| 5.2 | **Turn on the LEAP sleeve.** Deep-ITM, Mag7 only, IV-filtered. | ☐ |
| 5.3 | Full 25% position sizing | ☐ |

**Only if Phases 3 and 4 agree.** If the backtest says one thing and live trading says another, **live wins** — and I go back to Phase 0.

---

## ORDER OF ATTACK

1. **Close NFLX** *(today — fails 3 rules, fixes 2 violations)*
2. **Trim HIMS to cash** *(this week)*
3. **Build the dashboard** *(Phase 1)*
4. **Run the backtest** *(Phase 3 — the gate)*
5. **Then, and only then, decide if this strategy is real.**

---

## THE HONEST NOTE

Everything before Phase 3 is plumbing. **Phase 3 is the project.**

Every position in my book is green except one. Every time I've averaged down, the market bailed me out. **I have never traded through a bear market.** My edge and a bull market are currently indistinguishable from the inside.

**The backtest tells me which one I have.** If it says no edge, I don't proceed to Phase 5 — I go back to Phase 0 and change the strategy. **That is the entire reason this exists.**
