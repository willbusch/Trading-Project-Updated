from backtest.fib_universe import gate_of_tiered


def test_tiered_gate_breakpoints():
    caps = {"MEGA": 600e9, "MID": 300e9, "SMALL": 50e9, "TINY": 5e9,
           "EXACT500": 500e9, "EXACT150": 150e9}
    assert gate_of_tiered("MEGA", caps) == 0.25
    assert gate_of_tiered("EXACT500", caps) == 0.25          # boundary inclusive
    assert gate_of_tiered("MID", caps) == 0.30
    assert gate_of_tiered("EXACT150", caps) == 0.30           # boundary inclusive
    assert gate_of_tiered("SMALL", caps) == 0.40
    assert gate_of_tiered("TINY", caps) == 0.40


def test_tiered_gate_missing_ticker_defaults_to_strictest():
    assert gate_of_tiered("NOTFOUND", {}) == 0.40
