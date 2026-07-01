"""Tests for the orchestration scheduler (pure, deterministic clock)."""

from __future__ import annotations

from boosternews.scheduler import Job, is_due, run_cycle, run_scheduler


def test_is_due():
    assert is_due(0, 60, 60) is True
    assert is_due(0, 60, 59) is False
    assert is_due(100, 60, 159) is False
    assert is_due(100, 60, 160) is True


def test_is_due_disabled_when_interval_zero():
    assert is_due(float("-inf"), 0, 1_000_000) is False


def test_run_cycle_runs_due_and_advances():
    calls = []
    job = Job("t", 60, lambda: calls.append(1), last_run=0)
    run_cycle([job], now=100)  # due
    assert calls == [1] and job.last_run == 100
    run_cycle([job], now=120)  # not due yet
    assert calls == [1]


def test_run_cycle_isolates_failures():
    ran = []

    def boom():
        raise RuntimeError("kaboom")

    bad = Job("bad", 1, boom, last_run=0)
    good = Job("good", 1, lambda: ran.append(1), last_run=0)
    run_cycle([bad, good], now=1000)  # bad raises but good still runs
    assert ran == [1]
    assert bad.last_run == 1000  # advanced → will retry next interval, not hot-loop


def test_run_scheduler_bounded_with_fake_clock():
    counter = {"n": 0}
    job = Job(
        "tick",
        1,
        lambda: counter.__setitem__("n", counter["n"] + 1),
        last_run=float("-inf"),
    )
    ticks = iter([0, 10, 20, 30, 40])
    run_scheduler([job], tick=0, max_cycles=3, clock=lambda: next(ticks), sleep=lambda _: None)
    assert counter["n"] == 3  # ran once per cycle
