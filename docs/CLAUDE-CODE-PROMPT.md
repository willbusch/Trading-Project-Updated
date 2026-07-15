# CLAUDE CODE — BUILD PROMPT

**Project:** Trader-Resp — RSI Mean-Reversion Screener + Backtest
**Owner:** Will Busch
**Read first:** `STRATEGY.md`, `investor-one-pager-will-busch.md`, `portfolio-audit-2026-07-14.md`

---

## CONTEXT FOR YOU (Claude Code)

You are building a **decision-support tool**, not an auto-trader. It emits signals; the human places the trades. Never execute orders.

The owner is a 22-year-old discretionary trader with a **$45k account, no fixed expenses, and no income backstop.** The capital is finite and non-replenishable. This is real money. Accuracy over encouragement.

**The single most important thing you will do on this project is the backtest (Stage 3).** It is the only thing that will tell the owner whether his strategy has an edge or whether he has been riding a bull market. **Report its results honestly, including — especially — if they are bad.** Do not tune parameters until the results look good. That is overfitting and it will cost him real money.

---

## THE STRATEGY (encode exactly this)

### Universe
- **Index:** Must be in **SPY or QQQ**. No exceptions.
- **Market cap — shares:** $10B – $499B
- **Market cap — LEAPs:** $500B+ **only** (the "Mag7 rule")
- **Sector:** Any
- **Fundamentals:** **None.** Technical only. This is a deliberate choice — do not add fundamental filters.
- **Price:** > $10
- **Avg volume:** > 2M/day

### Entry Signal
- **Primary trigger:** `RSI(3) < 35` on the **3-day chart**
- **Trend filter:** `close > SMA(200)` on the daily
- **Confirmation:** weekly chart not making lower lows

### Setup Grades
| Grade | Conditions | Size |
|---|---|---|
| **A** | RSI(3) < 30 **AND** above SMA(200) **AND** at defined support | Full tranche |
| **B** | RSI(3) < 35 **AND** above SMA(200) | Full tranche |
| **C** | RSI(3) < 35 **AND** below SMA(200) | **Half tranche** (still consumes a full tranche slot) |
| **NO TRADE** | RSI(3) < 35, below SMA(200), **AND** lower lows on weekly | Skip entirely |

### Position Sizing & The Tranche Ladder (EQUITIES)
- **6 slots max** (5 core + 1 flex)
- **Max position: 25% of book** — shares + LEAPs on the same underlying = **one** bucket
- **3 tranches max per name. Hard cap.**
- **Tranche spacing: 1.5 × ATR(14)** below the previous entry *(NOT a fixed %)*
- **After tranche 3: the name is LOCKED.** No further adds. Ever. Under any condition.
- Each tranche ≈ 1/3 of target max position

### The Slot Rule (frozen positions)
A tranche-3 locked position may be released **only** to fund an **A-grade setup** when no cash and no free slot exists. Not for a "better opportunity" — **A-grade only.**

### LEAP Rules (DIFFERENT FROM EQUITIES — implement separately)
- **Underlying:** $500B+ market cap only. **This disqualifies NFLX.**
- **Entry trigger:** Same — RSI(3) < 35, above SMA(200)
- **Strike:** **Deep ITM, 0.70–0.80 delta.** Never OTM.
- **Expiry:** **18+ months minimum** at entry
- **Force-close:** at **6 months to expiry**, regardless of P/L
- **IV filter:** **Skip if IV rank > 60.** Buy shares instead.
- **Sizing:** by **delta-adjusted notional exposure**, NOT premium paid
- **NO TRANCHE LADDER.** One entry, one exit. Never average down an option.
- **Sleeve cap:** 25% of book (delta-adjusted notional)

### Exit Rules (SAME for shares and LEAPs)
- **Trigger 1 — Euphoria:** `RSI(3) ≥ 80` → SELL
- **Trigger 2 — Momentum break:** `RSI(3)` touches ≥ 70, then crosses **below 60** → SELL *(primary exit)*
- **LEAPs:** Trigger 2 only. Do NOT exit LEAPs on Trigger 1.

**Exit sizing:**
| Condition | Action |
|---|---|
| Position > 25% of book | Trim to 20% → **CASH** |
| Within cap, 1st exit signal | Sell 50%, let rest run. Re-entry allowed on next RSI(3)<35. |
| Within cap, 2nd exit signal | Close position. |

### 🚨 THE CASH RULE — hard-code this
> **ALL sale proceeds go to CASH. The system must NEVER route proceeds into a position currently underwater.**

If the code can generate a "sell X, buy more Y" where Y is a losing position, **the code is wrong.** This is the owner's single most costly behavioral flaw. The software exists to prevent it.

### There Is No Stop Loss
By explicit choice. A losing position is **frozen** (tranche lock), never stopped out. Do not add a stop-loss.

### Circuit Breakers
- **Max 2 new positions per week.** Prevents six correlated entries in one drawdown.
- **Account −30% → HALT.** No new entries for 30 days. Existing positions untouched.

### Portfolio Constraints (always enforce)
| Constraint | Limit |
|---|---|
| Max positions | 6 |
| Max single name (shares + LEAPs) | 25% |
| Max LEAP sleeve (delta-adj notional) | 25% |
| Min cash | 10% |
| Max tranches/name | 3 |
| Tranche spacing | 1.5 × ATR(14) |
| Max new entries/week | 2 |

---

## BUILD ORDER — EXECUTE IN THIS SEQUENCE

### STAGE 0 — Foundation
1. Repo scaffold: `screener/`, `tests/`, `backtest/`, `dashboard/`
2. `config.yaml` — **every threshold above as a named key.** No magic numbers in code.
3. `data.py` — yfinance fetch. Cache to disk (`.parquet`). Handle missing data explicitly; never silently fill.
4. **Resample daily → 3-day bars.** Get this right — RSI(3) on a 3-day chart is NOT RSI(3) on daily. Document the resampling rule. Write a test.
5. `indicators.py` — RSI, SMA(200), ATR(14). Unit-test each against a known-good reference series.

**Gate:** tests pass. Show me RSI(3) on 3-day bars for MSFT and I will eyeball it against TradingView.

### STAGE 1 — Universe
6. Fetch SPY + QQQ constituents (dedupe the overlap).
7. Apply hard filters: mkt cap, price, volume.
8. Tag each: `SHARES_ELIGIBLE` ($10B–499B) / `LEAP_ELIGIBLE` ($500B+).
9. Output: `universe.csv`.

**Gate:** print count. Should be ~500-550. If it's 50 or 5000, something is broken.

### STAGE 2 — Buy Signals
10. Compute RSI(3)/3-day, SMA(200)/daily, weekly structure for each name.
11. Grade every name: A / B / C / NO_TRADE / no-signal.
12. `portfolio.py` — load `portfolio.yaml`, mark to market, compute % of book, tranche count per name.
13. Sizing engine — outputs **tranche number, dollar amount, and next ladder level (1.5×ATR below).**
14. **Constraint checker** — before emitting a BUY, verify: slots, position cap, LEAP cap, cash floor, weekly entry cap, halt status. **Emit BLOCKED with the reason if any fail.**

**Gate:** run against the live book. It must flag the current violations (7 names, 38% LEAP, 1.5% cash, HIMS 26.7%). If it doesn't, the constraint checker is broken.

### STAGE 3 — Sell Signals
15. Exit triggers 1 and 2. **Trigger 2 requires state** — track whether RSI(3) previously touched 70.
16. Exit sizing per the table.
17. **Cash rule enforcement** — assert proceeds → cash. Write a test that tries to route a sale into a losing position and confirms it fails.
18. LEAP time-decay check: flag any LEAP inside 6 months to expiry.

### STAGE 4 — Dashboard *(Owner's Phase 1)*
19. Simple web UI (Streamlit or Flask — your call, keep it light).
20. Panels:
    - **SIGNALS:** every name firing BUY/SELL today, with grade, tranche #, size, and the RSI/SMA/ATR values that triggered it
    - **BOOK:** current positions, % of book, tranche depth, distance to next ladder rung, P/L
    - **VIOLATIONS:** every constraint currently breached, in red
    - **BLOCKED:** signals that fired but were blocked, **with the reason**
21. Every signal shows its **inputs**. Never a bare "BUY" — always "BUY: Grade B, RSI(3)=31.2, above 200SMA, tranche 1 of 3, $7,500."

### STAGE 5 — Pinescript *(Owner's Phase 2)*
22. Port entry/exit to Pine v5. Plot RSI(3) on 3-day, SMA(200), tranche ladder levels, entry/exit markers.
23. **The Pine signals and the Python signals must match.** Reconcile them on 3 names. If they diverge, one of them is wrong — find out which.

### STAGE 6 — BACKTEST *(Owner's Phase 3 — THE MOST IMPORTANT STAGE)*
24. **5 years, full SPY/QQQ universe, all rules enforced** — slots, tranches, cash floor, weekly entry cap, halt.
25. Include: commissions, slippage (assume 0.1%), and **the cash drag from the 10% floor.**
26. **Report, honestly:**
    - Total return, CAGR, **vs. buy-and-hold SPY** *(this is the benchmark that matters — if you don't beat SPY, the strategy is a hobby)*
    - **Expectancy per trade** *(the real metric)*
    - Win rate, avg win %, avg loss %, payoff ratio
    - **Max drawdown** and time to recover
    - Slot utilization — how often was capital idle? How long did frozen positions clog slots?
    - How many names hit tranche 3 and stayed dead
    - **Above-200-SMA vs below-200-SMA cohorts, separately.** This is the owner's core hypothesis. Test it.
27. **Ablation study — run these variants and report each:**
    - No 200 SMA filter (does the filter actually help?)
    - Fixed −7.5% ladder vs 1.5×ATR (was the ATR change worth it?)
    - 1 tranche vs 3 tranches (does averaging down add or destroy value?)
    - With a stop loss vs without (**tell him the truth here, even though he doesn't want a stop**)
    - Equities only vs equities + LEAP sleeve
28. Current-state check: "would we be in a trade right now, and in what?"

**⚠️ CRITICAL:** Do not tune parameters to improve backtest results. Run it once, honestly, and report. If the strategy doesn't work, **say so.** The owner explicitly asked for real advice over a yes-man.

---

## NON-NEGOTIABLES

1. **Never place a trade.** Signals only.
2. **Never let proceeds flow into an underwater position.** Test for it.
3. **Every threshold in `config.yaml`.** Zero magic numbers.
4. **Never silently fill missing data.** Fail loudly.
5. **Report backtest results honestly.** No parameter tuning to make them look good.
6. **A feature that's built but commented out in config is NOT done.** Never mark it done.
7. **Distinguish "passes synthetic tests" from "run on live data."** They are not the same and the difference has bitten this project before.

---

## KNOWN VIOLATIONS IN THE CURRENT BOOK

The dashboard must flag all of these on first run:

| Item | Current | Rule | Status |
|---|---|---|---|
| Position count | 7 | 6 | ❌ |
| LEAP sleeve | 38% | 25% | ❌ |
| Cash | 1.5% | 10% | ❌ |
| HIMS | 26.7% | 25% | ❌ |
| **NFLX LEAP** | Held | **$500B+ only** | ❌ **Ineligible — NFLX fails the LEAP market-cap rule outright** |
| ORCL invalidation | None | Required | ❌ |

---

## THE OWNER'S BLIND SPOTS (build guardrails for these)

1. **He averages down without limit.** The tranche cap is the only thing stopping him. Enforce it in code, not in a comment.
2. **He rotates winners into losers.** The cash rule is the fix. Make it structurally impossible.
3. **He has no invalidation price on ORCL** and told me point-blank there isn't one. The tranche lock is the only brake on that position.
4. **He does not use stops.** Accepted. Do not add one — but **do report in the backtest what a stop would have done.** He deserves the data even if he rejects the rule.
