# GOAL.md

**Owner:** Will Busch
**Last updated:** July 14, 2026
**Horizon:** 12 months

---

## THE TARGET

**50% annual return.**
**Max drawdown < 30%.**
**Every trade traceable to a rule.**

---

## THE HONEST MATH

I need to be clear-eyed about what I'm attempting, because the number is aggressive and pretending otherwise is how people blow up.

### The expectancy required

| Input | Value |
|---|---|
| Win rate | ~66% |
| Avg win | ~28% *(RSI 35 → 80 is a full cycle, not an 8% bounce)* |
| Avg loss | ~15% *(a frozen tranche-3 position)* |
| **Expectancy per trade** | **+13.4%** |
| Trades per year | ~12–15 across 6 slots |

**+13.4% expectancy is a top-decile professional result.** Renaissance-tier funds do 40-70% with PhDs and colocated servers. I'm 22, with $45k and 5 hours a week.

**That doesn't mean don't try. It means I have to know exactly where the return comes from.**

### Where the 50% actually comes from

| Component | Mechanism | Contribution |
|---|---|---|
| **Equity book (~75%)** | RSI(3) mean reversion, 3-tranche ladder, RSI≥80 exit | **25–30%/yr.** Real. Achievable. This is the engine. |
| **LEAP sleeve (~25%)** | Same signal, deep-ITM Mag7, 2x delta leverage | **+20–25%.** This is the gap. |
| **Total** | The barbell | **~50%** |

**The conclusion, stated plainly: the LEAP sleeve is not a bonus. It IS the goal.**

- If the LEAP rules are wrong → I get 25% and miss.
- If they're right → I clear 50%.
- **A 25% LEAP sleeve going to zero is a −25% year before my equities do anything.**

**The barbell is what makes 50% possible AND what can blow me up. That's the trade. I'm making it with open eyes.**

---

## WHAT SUCCESS ACTUALLY LOOKS LIKE

**Not the P&L.** The P&L is an outcome; the process is the thing I control.

### The five markers

1. ✅ **Zero discretionary trades.** Every entry traces to a signal, every exit to a trigger.
2. ✅ **Every trade logged** — signal, grade, tranche, size, thesis, exit, outcome. No journal = no data = no edge, forever.
3. ✅ **Zero rule violations.** More important than the return. A 60% year with three broken rules is a failure.
4. ✅ **The backtest is run and reported honestly — including if it says the edge isn't there.**
5. ✅ **I know my real expectancy per trade**, computed from my own data, not from a spreadsheet fantasy.

### The metric I actually track

**Expectancy, not win rate.**

I originally set a 66% win-rate target. **I'm demoting it, because it's actively harmful.** Chasing win rate makes me cut winners early and hold losers — the exact disease I already have. My RSI(3)≥80 exit is a *let-it-run* rule; a win-rate target fights it.

> **A 45% win rate with a 3:1 payoff beats a 70% win rate at 1:1.**

Track: `Expectancy = (Win% × AvgWin) − (Loss% × AvgLoss)`

### The benchmark that matters

**SPY buy-and-hold.** If I don't beat it, this is a hobby, not a strategy. That comparison goes in every backtest report and every quarterly review.

---

## THE FAILURE MODE I ACTUALLY FEAR

**It is not missing 50%.**

**It is hitting 50% by luck and believing it was skill.**

Every position in my book is green except one. Every time I've averaged down, the market bailed me out. **I have never traded through a real bear market.** My "edge" and "a bull market" are currently indistinguishable, and I cannot tell them apart from the inside.

**The backtest exists to tell me which one I have.** That's its whole purpose. If it comes back at 52% win rate and +2% expectancy, **I don't have a strategy — I have a rising tide.** I need to know that before I lever into it, not after.

---

## THE THREE THINGS I'M BETTING ON

1. **The 200 SMA filter is real.** My book says every winner came from above it and my only loser from below it. n=5, statistically meaningless — but it's the only non-obvious, testable hypothesis I have. **If the backtest confirms it, that's my edge and I press it hard.**

2. **Full-cycle holds beat bounce-scalping.** Entering on RSI(3)<35 and exiting on RSI(3)≥80 captures a 25-30% move, not an 8% one. That single design choice is what makes the expectancy math work.

3. **Deep-ITM LEAPs on beaten-up Mag7 are leverage, not gambling.** Same thesis, same signal, 2x delta. The NFLX call was the anomaly. The MSFT setup is the pattern.

---

## THE THING I'M AVOIDING

**I still have no invalidation price on ORCL.** Asked point-blank, my honest answer was *"there is no such price."*

Every other hole in this system is now plugged. **That one is open because I want it open.** It is written here so I can't pretend I didn't know.

---

*Reviewed quarterly against actuals. If the backtest says no edge, I do not proceed to full sizing — I go back and change the strategy. That is the entire point of building this.*
