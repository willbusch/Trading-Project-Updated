# Portfolio Audit — Will Busch

**As of:** July 20, 2026 (live quotes + records reconciliation)
**Account:** ~$41,356 total exposure across 2 accounts | ~$75 cash (0.2%, estimated)
**Supersedes:** `portfolio-audit-2026-07-14.md` for current figures — that file stays as the historical baseline this reconciliation is measured against.
**Companion to:** `investor-one-pager-will-busch.md`, `portfolio.yaml`, `STRATEGY.md` v3.0

> This file is a **snapshot**, not a framework. It goes stale the moment you trade.

---

## 🔴 What changed since July 14

1. **The "zero equities" scare from the live scanner (2026-07-19) is resolved.** It wasn't a sold book — the equities live in a **second Robinhood account this session's connection can't reach.** Only the LEAP account (NFLX + MSFT) was ever visible to the scanner. Two accounts, reconciled here manually.
2. **ORCL: +5 shares @ $125.00 this morning.** 31 → **36 shares**, basis re-blends from $148.00 to **$144.81**. See the flag below — this is reported as fact, not judged.
3. Equity marks refreshed to **live intraday quotes** (2026-07-20) instead of the July 14 audit's stale prices.

---

## Current Book (two accounts, not merged)

### Account 1 — margin (...803) — reachable this session, pulled live

| Ticker | Contracts | Avg Price | Notional (approx) |
|---|---|---|---|
| NFLX | 3 | $937.67 | — 34% OTM, self-flagged "bad entry," fails $500B rule outright |
| MSFT | 3 | $3,193.33 | — real LEAP, within v3.0 delta/expiry norms at entry |

**Account 1 total value: $14,799** | Cash: $0

### Account 2 — equities — NOT reachable this session; shares/basis carried from the 2026-07-14 audit, marked to live 2026-07-20 quotes

| Ticker | Shares | Basis | Live | Value | % of combined book | P/L |
|---|---|---|---|---|---|---|
| HIMS | 348 | $28.00 | $32.70 | $11,379.60 | **27.5%** | +16.8% |
| NOW | 48 | $100.00 | $104.77 | $5,028.96 | 12.2% | +4.8% |
| HOOD | 30 | $71.00 | $99.31 | $2,979.30 | 7.2% | +39.9% |
| SOFI | 160 | $16.80 | $17.03 | $2,724.80 | 6.6% | +1.4% |
| **ORCL** | **36** (was 31) | **$144.81** (was $148.00) | $121.37 | $4,369.32 | 10.6% | **−16.2%** |

**Account 2 equities: $26,481.98** | Cash: **~$75 (estimated — see flag)**

> **Cash estimate flag:** $700 (July 14 audit) − $625 (today's ORCL buy) = ~$75. This is a derived estimate, NOT owner-confirmed — any other cash flows in Account 2 since July 14 are unknown to this record.

---

## Rule Violations — Live, vs STRATEGY.md v3.0 (combined book, both accounts)

| Rule | Limit (v3.0) | Actual | Status |
|---|---|---|---|
| Total named positions | 6 (5 equity + 1 LEAP) | **7** (5 equity + 2 LEAP) | ❌ VIOLATED — LEAP slot |
| Max single equity position | 15% | **HIMS at 27.5%** | ❌ VIOLATED (badly, and worse than July 14's 26.7% — pure appreciation) |
| LEAP sleeve | 25% of combined book | **35.8%** | ❌ VIOLATED |
| Min cash floor | 5% | **~0.2%** | ❌ VIOLATED (badly) |
| **NFLX LEAP** | Ineligible — fails $500B rule | **Still held** | ❌ VIOLATED |

**Every rule in the book is still broken.** Nothing has been fixed since July 14; HIMS's violation grew (appreciation, not adding), and a new average-down (ORCL) was added on top.

---

## 🔴 THE ORCL ADD — FACTS, NOT A VERDICT

**What happened:** +5 shares @ $125.00 this morning, averaging the 31-share $148.00 lot down to a $144.81 blended basis on 36 shares. The name is already trading below the new buy price ($121.37 live, same day).

**Does it fit the v3.0 Fib rules?** Checked directly against the same code the backtest and live scanner use (`backtest.fib_features.build_fib_frame`), not a manual eyeball:
- Drawdown gate: ORCL is **62.2% below its hybrid 2-year high** ($328.33 → $124.21 on the last cached daily bar) — clears the 40% gate easily.
- UT-Bot trigger: **`entry_ut_buy = False`** on that same bar — no buy signal fired.

**The v3.0 entry rule requires both the gate AND the trigger.** Only the gate cleared. **This add does not read as a rule-triggered Fib entry — it reads as a discretionary average-down.** That's a fact about the mechanics, not a verdict on the decision. The owner decides what it means.

---

*Snapshot only. Regenerate before any material decision. Rules live in STRATEGY.md v3.0, not here.*
