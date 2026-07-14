# STRATEGY.md

**Version:** 2.0
**Last updated:** July 14, 2026
**Owner:** Will Busch
**Companion files:** `PLAN.md`, `GOAL.md`, `investor-one-pager-will-busch.md`, `portfolio-audit-2026-07-14.md`

> **The one-line thesis:**
> *I buy quality that's temporarily broken, and I hold until the market is euphoric about it again.*
>
> Entry is fear. Exit is greed. This is a **full-cycle system**, not a bounce trade — which is why the average win is 25-30%, not 8%, and why holds run months instead of days.

---

## PART 1 — THE UNIVERSE (What We Buy)

### Hard Filters — fail any, disqualified

| Filter | Rule | Why |
|---|---|---|
| **Index** | Must be in **SPY or QQQ** | Institutional coverage, real liquidity, no delisting risk. Not in the index = doesn't exist. |
| **Market cap — shares** | **$10B – $499B** | Big enough to survive a drawdown, small enough to move. |
| **Market cap — LEAPs** | **$500B+ ONLY** | Leverage only on names that can't go to zero. Mega-cap or no LEAP. |
| **Sector** | **Any** | The chart is the thesis. The setup travels across sectors. |
| **Fundamentals** | **None** | Deliberate. Technicals only. Documented so I don't drift into thesis-creep. |
| **Price** | **> $10** | No wreckage. |
| **Avg volume** | **> 2M/day** | I need to exit as easily as I entered. |

### Anti-Portfolio — never, regardless of setup

- Penny stocks / sub-$1
- Meme stocks
- Crypto
- 0DTE, weeklies, any short-dated option
- **LEAPs on anything under $500B** — *the NFLX rule, named after the mistake that created it*
- **OTM LEAPs** — I buy leverage, not lottery tickets
- Any name where I can't state the tranche ladder before entry

---

## PART 2 — THE ENTRY (When We Buy)

### Core Signal

**`RSI(3) < 35` on the 3-day chart**
**AND** weekly chart not making lower lows

### The Trend Filter

**`close > SMA(200)`** on the daily.

**Why this is here even though my instinct says "oversold is oversold":**
RSI stays oversold *the entire way down* on a broken stock. It's not a signal — it's a description of a falling knife. **My own book is the evidence:** HIMS, HOOD, SOFI, NOW — every winner, bought above the 200. **ORCL — my only loser, bought below it.** n=5 and statistically meaningless, but it's the only testable hypothesis I have. The backtest settles it.

**The compromise:** below the 200 is still tradeable — at **half size.** I get to trade my instinct; my instinct doesn't get to size the trade.

### Setup Grades

| Grade | Conditions | Size |
|---|---|---|
| **A** | RSI(3) < 30 + above SMA(200) + at defined support | **Full tranche** |
| **B** | RSI(3) < 35 + above SMA(200) | **Full tranche** |
| **C** | RSI(3) < 35 + **below** SMA(200) | **Half tranche** (still burns a full tranche slot) |
| **NO TRADE** | RSI(3) < 35 + below SMA(200) + lower lows on weekly | **Skip.** This is the ORCL trap. |

---

## PART 3 — THE TRANCHE LADDER (Equities)

### The Rules

1. **3 tranches maximum per name. Hard cap. No exceptions.**
2. **Spacing: 1.5 × ATR(14)** below the previous entry. *Not a fixed %.*
3. **Max position: 25% of book** — shares + LEAPs on the same underlying = **one bucket.**
4. **After tranche 3, the name is LOCKED.** No adds. Not at −40%. Not at RSI 10. Not ever.
5. Each tranche ≈ 1/3 of the target max position.

### Why ATR, not a fixed −7.5%

A −7.5% move in MSFT is a rare event. In HIMS it's a Tuesday. Fixed spacing means I burn all three tranches on a volatile name in a week, and never fire tranche 2 on a stable one. **1.5 × ATR calibrates the ladder to the stock's own volatility.** Same idea, correct units.

### The Math (worked, $45k book, 6 slots)

Target max position: 25% = **$11,250** · Tranche ≈ **$3,750**

| Tranche | Trigger | $ In | Cumulative |
|---|---|---|---|
| 1 | RSI(3) < 35 | $3,750 | $3,750 |
| 2 | −1.5×ATR from T1 | $3,750 | $7,500 |
| 3 | −1.5×ATR from T2 | $3,750 | **$11,250** |
| — | **🔒 LOCKED** | $0 | $11,250 |

**Worst case is now a known, bounded, pre-decided number.** Without the lock, six tranches deep is $22,500 and one bad name has eaten half the account.

### The Point of the Lock

**I do not use stop losses. I will not sell at a loss.** That's who I am and I've stopped pretending otherwise.

**So the brake isn't an exit — it's a budget.** My max loss per name is capped not by selling, but by the fact that I've run out of permission to buy. **Being wrong now has a ceiling.**

### The Slot Rule

A locked (tranche-3) position may be released **only** to fund an **A-grade setup** when no cash and no free slot exists.

Not "a better opportunity" — that's the excuse I already use. **A-grade only:** RSI(3)<30, above the 200, at support. The highest bar in the system.

**I'm not cutting losers. I'm letting my best signal outbid my worst position.** That's competitive capital allocation, not capitulation.

**Why this matters more than the loss:** I have 6 slots and each trade takes ~3 months. That's ~24 trade-slots a year. A dead name clogging a slot for 12 months costs me **4 trade-slots** — at +13% expectancy each, that's far more expensive than the drawdown itself. **In a 6-slot system, dead capital costs more than the loss.**

---

## PART 4 — THE LEAP SLEEVE (Different Rules — Read Carefully)

> **This sleeve is the entire path to 50%.** The equity book, run perfectly, produces 25-30%/yr. The remaining 20-25 points come from here and nowhere else. It is simultaneously the reason 50% is possible and the thing that can blow up the account. **That is the trade I am consciously making.**

### The Rules

| Rule | Spec | Why |
|---|---|---|
| **Underlying** | **$500B+ market cap only** | Mag7 and equivalents. Cannot go to zero on me. **NFLX fails this.** |
| **Entry trigger** | Same: RSI(3)<35, above SMA(200) | The LEAP is my equity thesis with a multiplier — not a separate bet. |
| **Strike** | **Deep ITM, 0.70–0.80 delta** | ~2x leverage with ~80% of the stock's move. Low theta, low IV sensitivity. **I'm buying leverage, not a lottery ticket.** |
| **Expiry** | **18+ months minimum** at entry | Time to be right. |
| **Force close** | **At 6 months to expiry**, regardless of P/L | Theta accelerates hard past that line. Under 6 months it's not a LEAP, it's an expensive option. |
| **IV filter** | **Skip if IV rank > 60** → buy shares instead | RSI(3)<35 means the stock got crushed → IV is elevated → I'd be overpaying. |
| **Sizing** | By **delta-adjusted notional**, NOT premium paid | $9,579 in premium controlling $115k of MSFT is a $115k position, not a $9,579 one. |
| **Tranche ladder** | **NONE. One entry, one exit.** | Averaging down on options compounds leverage *and* decay. If it goes against me, I eat it. That's the price of leverage. |
| **Sleeve cap** | **25% of book** (delta-adjusted notional) | |
| **Exit** | **Trigger 2 only** (RSI 70 → cross below 60) | Don't sell mega-cap LEAPs on Trigger 1 — time value is the asset. |

### The NFLX Lesson

$112C, June 2027, NFLX at $73.65 = **34% OTM**, 11 months left. I labeled it "bad entry" myself before anyone asked. **It violates three rules at once:** sub-$500B underlying, deep OTM, and no RSI trigger at entry. It is the anomaly, not the pattern — and every LEAP rule above exists because of it.

---

## PART 5 — THE EXIT (When We Sell)

*This is the strongest part of my system. Mechanical, precise, doesn't ask my opinion.*

### Trigger 1 — Euphoria
**`RSI(3) ≥ 80` → SELL.** The market is paying a premium for my patience. Take it.

### Trigger 2 — Momentum Break *(primary)*
**`RSI(3)` touches ≥ 70, then crosses back below 60 → SELL.**
Trigger 1 sells into strength; **Trigger 2 sells when strength fails.** It confirms the rollover rather than guessing the top.

### Exit Sizing

| Condition | Action |
|---|---|
| Position **> 25% of book** | Trim to 20% → **CASH** |
| Within cap, **1st** exit signal | Sell 50%. Let the rest run. Re-entry allowed on next RSI(3)<35. |
| Within cap, **2nd** exit signal | Close it. |
| **LEAP** | **Trigger 2 only.** |

### 🚨 THE CASH RULE — the most important line in this document

> **ALL proceeds from ANY sale go to CASH. Never directly into a position I am currently underwater on.**

This rule exists specifically to stop me. **Trimming HIMS to buy more ORCL** is the trade that converts my winners into my losers. It *feels* like buying low. It is **systematically rotating capital from what's working into what isn't.**

**Cash → wait → new entry that clears the criteria on its own merits.** No exceptions. The software must make the alternative structurally impossible.

### There Is No Loss Exit
By design and by choice. A losing position is **frozen**, not sold. It sits as dead capital and as a tax on being wrong. **That is the price I pay for refusing stops, and I'm paying it with open eyes.**

---

## PART 6 — RISK CONTROLS

| Control | Limit |
|---|---|
| Max positions | **6** (5 core + 1 flex) |
| Max single name (shares + LEAPs) | **25%** |
| Max LEAP sleeve (delta-adj notional) | **25%** |
| Min cash | **10%** |
| Max tranches per name | **3** |
| Tranche spacing | **1.5 × ATR(14)** |
| **Max new positions per week** | **2** |
| **🛑 ACCOUNT KILL SWITCH** | **−30% → HALT all new entries for 30 days** |

### Why 6 slots, not 10
$45k ÷ 10 = $4,500/slot ÷ 3 tranches = **$1,500 a buy.** That's four shares of MSFT. **Nobody compounds 50% a year owning ten things.** Concentration isn't a preference — it's arithmetic. 6 slots = ~$7,500 each, room to breathe, still concentrated.

### Why the weekly entry cap
My worst risk isn't a bad stock. It's **six positions all entered in the same drawdown week.** Everything oversold at once = everything correlated = one market move takes the whole book.

### Why the kill switch
**No stops + leverage + concentration = a real path to zero.** The halt doesn't force a sale. It just **stops me digging.** It's the only thing standing between me and a catastrophic year.

---

## PART 7 — CURRENT BOOK vs. THIS STRATEGY

*As of July 14, 2026 — the dashboard must flag every one of these*

| Violation | Current | Required |
|---|---|---|
| Position count | 7 | 6 |
| LEAP sleeve | 38% | 25% |
| Cash | 1.5% | 10% |
| HIMS size | 26.7% | 25% |
| **NFLX LEAP** | **Held** | **Ineligible — fails the $500B rule outright** |
| Invalidation levels | None written | All |

**Priority 1 — close the NFLX LEAP.** It fails the strategy on three counts, and closing it fixes the LEAP overage *and* the cash floor in one trade. It is the cleanest move available.

---

## OVERRIDE LOG

*Rules I argued against, and why they're in here anyway.*

| Date | Rule | My position | Resolution |
|---|---|---|---|
| 2026-07-14 | 200 SMA trend filter | *"Oversold is oversold"* | **Compromise:** below-200 setups allowed at **half size.** My own book: every winner above the 200, my only loser below it. |
| 2026-07-14 | Stop losses | *"I won't use stops"* | **Accepted.** Replaced with the **3-tranche lock** — bounds the loss without forcing a sale. **The backtest will still report what a stop would have done. I want the data even if I reject the rule.** |
| 2026-07-14 | ORCL invalidation price | *"There is no such price"* | **🔴 UNRESOLVED.** Documented as a known blind spot. The tranche lock is the only thing standing between me and this position. |
| 2026-07-14 | Slot count | *"Let's move to 10"* | **Rejected → 6.** Ten slots dilutes the book below the concentration required to compound at target. |
| 2026-07-14 | 66% win-rate target | *(mine)* | **Demoted.** Chasing win rate makes me cut winners early — the exact opposite of my RSI(3)≥80 exit. **Track expectancy, not win rate.** |

---

*Reviewed quarterly. No rule may be changed while a position it governs is underwater. Material changes require a 7-day cooldown before execution.*
