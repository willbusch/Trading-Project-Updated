"""Portfolio bookkeeping for the backtest engine: positions, a cash ledger
with full transaction history (so the cash rule is checkable, not just
asserted), and the aggregate portfolio state the constraint checks read.

This module holds NO strategy logic and NO constraint logic — it only
records what happened. backtest/constraints.py decides what's allowed;
backtest/simulator.py decides when things happen.
"""
from dataclasses import dataclass, field

import pandas as pd


class LedgerError(Exception):
    """Raised on impossible cash operations (overdraw, negative amounts)."""


@dataclass
class CashTransaction:
    date: pd.Timestamp
    amount: float           # positive = deposit, negative = withdrawal
    reason: str             # "seed" | "sale" | "entry" | ...
    ticker: str | None = None


class CashLedger:
    """A fungible cash balance plus the transaction history needed to
    answer "where did the money funding this entry come from" — which is
    what the cash rule check needs."""

    def __init__(self, seed: float, seed_date: pd.Timestamp):
        if seed < 0:
            raise LedgerError(f"seed cash must be >= 0, got {seed}")
        self.balance = float(seed)
        self.history: list[CashTransaction] = [
            CashTransaction(seed_date, float(seed), "seed")
        ]

    def deposit(self, date, amount: float, reason: str, ticker: str | None = None):
        if amount < 0:
            raise LedgerError(f"deposit amount must be >= 0, got {amount}")
        self.balance += amount
        self.history.append(CashTransaction(date, amount, reason, ticker))

    def withdraw(self, date, amount: float, reason: str, ticker: str | None = None):
        if amount < 0:
            raise LedgerError(f"withdraw amount must be >= 0, got {amount}")
        if amount > self.balance + 1e-9:
            raise LedgerError(
                f"overdraw: withdrawing {amount:.2f} with balance {self.balance:.2f}"
            )
        self.balance -= amount
        self.history.append(CashTransaction(date, -amount, reason, ticker))

    def sale_proceeds_on(self, date) -> float:
        """Total sale proceeds deposited on this exact date (same-bar)."""
        return sum(
            t.amount for t in self.history if t.reason == "sale" and t.date == date
        )


@dataclass
class Tranche:
    date: pd.Timestamp
    price: float            # fill price actually paid (incl. slippage)
    shares: float


@dataclass
class Position:
    ticker: str
    kind: str               # "equity" | "leap"
    tranches: list[Tranche] = field(default_factory=list)
    last_price: float = float("nan")     # underlying price, all kinds
    last_date: "pd.Timestamp | None" = None
    # LEAP-only (2026-07-21, Black-Scholes delta-curve engine — see
    # backtest/leap_bs_pricing.py). K and sigma are FROZEN at entry;
    # `shares` on a LEAP tranche means CONTRACTS, and `price` on a LEAP
    # tranche means PREMIUM PER CONTRACT (so cost_basis = contracts x
    # premium falls out of the existing Tranche math unchanged).
    strike: float | None = None
    expiry_date: "pd.Timestamp | None" = None
    sigma: float | None = None
    delta: float | None = None   # retained only for old-approx comparison reporting

    @property
    def shares(self) -> float:
        return sum(t.shares for t in self.tranches)

    @property
    def cost_basis(self) -> float:
        return sum(t.shares * t.price for t in self.tranches)

    @property
    def market_value(self) -> float:
        if self.kind == "leap" and self.strike is not None:
            from backtest.leap_bs_pricing import CONTRACT_MULTIPLIER, bs_call_price
            if self.last_date is not None and self.expiry_date is not None:
                t_remaining = max((self.expiry_date - self.last_date).days / 365.25, 0.0)
            else:
                t_remaining = 0.0
            premium = bs_call_price(self.last_price, self.strike, t_remaining, self.sigma)
            return self.shares * premium * CONTRACT_MULTIPLIER
        return self.shares * self.last_price

    @property
    def is_underwater(self) -> bool:
        return self.market_value < self.cost_basis


class PortfolioState:
    def __init__(self, seed_cash: float, seed_date: pd.Timestamp):
        self.cash = CashLedger(seed_cash, seed_date)
        self.positions: dict[str, Position] = {}
        self.peak_equity = float(seed_cash)
        self.halted_until: pd.Timestamp | None = None
        # date -> count of NEW positions opened (tranche adds don't count)
        self.new_positions_by_week: dict[str, int] = {}

    # ---- valuation -------------------------------------------------------

    def mark_to_market(self, date, prices: dict[str, float]):
        for tkr, pos in self.positions.items():
            if tkr in prices:
                pos.last_price = prices[tkr]
                pos.last_date = date
        self.peak_equity = max(self.peak_equity, self.total_equity)

    @property
    def total_equity(self) -> float:
        return self.cash.balance + sum(p.market_value for p in self.positions.values())

    @property
    def drawdown_from_peak(self) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return 1.0 - self.total_equity / self.peak_equity

    def slots_used(self, kind: str) -> int:
        return sum(1 for p in self.positions.values() if p.kind == kind)

    # ---- mutations (called by the simulator AFTER constraints pass) ------

    @staticmethod
    def week_key(date: pd.Timestamp) -> str:
        return str(pd.Timestamp(date).to_period("W-FRI"))

    def open_or_add(self, date, ticker, kind, price, shares, delta=None,
                    strike=None, expiry_date=None, sigma=None, underlying_price=None):
        cost = price * shares
        self.cash.withdraw(date, cost, "entry", ticker)
        if ticker in self.positions:
            self.positions[ticker].tranches.append(Tranche(date, price, shares))
        else:
            # last_price/last_date seeded now so market_value is correct
            # even before the first mark_to_market call this same bar.
            last_price = underlying_price if underlying_price is not None else price
            pos = Position(ticker, kind, [Tranche(date, price, shares)], last_price, date,
                          strike, expiry_date, sigma, delta)
            self.positions[ticker] = pos
            wk = self.week_key(date)
            self.new_positions_by_week[wk] = self.new_positions_by_week.get(wk, 0) + 1

    def close_position(self, date, ticker, price) -> float:
        """Sell the ENTIRE position at `price`. ALL proceeds go to cash —
        there is no other destination in this API, by design (the cash
        rule's first half is structural; the second half — never routing
        proceeds into an underwater name — is enforced by
        constraints.check_cash_rule on any subsequent entry)."""
        pos = self.positions.pop(ticker)
        proceeds = pos.shares * price
        self.cash.deposit(date, proceeds, "sale", ticker)
        return proceeds
