"""
Comprehensive tests for the due-date factor inside calculate_task_score().

The scoring logic has five branches:

    days_until_due < 0   → +35  (overdue)
    days_until_due == 0  → +20  (due today)
    days_until_due <= 2  → +15  (due in 1–2 days)
    days_until_due <= 7  → +10  (due this week)
    (no due_date)        → +0   (not set)

All tests use a fixed FROZEN_NOW so results never depend on wall-clock time.
Each class covers one concern; comments explain *why* each case exists, not
just what it asserts.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from task import calculate_task_score
from models import TaskStatus, TaskPriority


# ── Constants & fixtures ───────────────────────────────────────────────────────

FROZEN_NOW = datetime(2024, 6, 15, 12, 0, 0)

# The due-date bonus is added on top of the base priority score.
# MEDIUM (weight=2) × 10 = 20, giving a round number easy to reason about.
BASE_SCORE = 20


@pytest.fixture(autouse=True)
def freeze_time():
    with patch("task_scoring.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        yield


def make_task(due_date=None):
    """Task with all non-due-date factors neutralised:
    - MEDIUM priority  → BASE_SCORE of 20
    - TODO status      → no penalty
    - no tags          → no tag boost
    - updated 5d ago   → outside recency window, no boost
    """
    return SimpleNamespace(
        priority   = TaskPriority.MEDIUM,
        status     = TaskStatus.TODO,
        due_date   = due_date,
        tags       = [],
        updated_at = FROZEN_NOW - timedelta(days=5),
    )


def due_in(days=0, hours=0, minutes=0):
    """Return a due_date offset from FROZEN_NOW. Negative values = overdue."""
    return FROZEN_NOW + timedelta(days=days, hours=hours, minutes=minutes)


def score_for(due_date):
    return calculate_task_score(make_task(due_date=due_date))


# ── 1. No due date ─────────────────────────────────────────────────────────────

class TestNoDueDate:

    def test_none_due_date_applies_no_bonus(self):
        # The `if task.due_date:` guard short-circuits — score is base only.
        assert score_for(None) == BASE_SCORE

    def test_none_due_date_does_not_raise(self):
        # Confirm the guard exists; without it the timedelta arithmetic would
        # raise TypeError: unsupported operand type(s) for -: NoneType.
        score_for(None)  # must not raise


# ── 2. Overdue (days < 0) ──────────────────────────────────────────────────────

class TestOverdue:

    def test_one_day_overdue_adds_35(self):
        assert score_for(due_in(days=-1)) == BASE_SCORE + 35

    def test_one_minute_overdue_adds_35(self):
        # timedelta.days truncates toward zero, so 23h 59m ago → days == 0,
        # but 24h 01m ago → days == -1. One minute past midnight boundary.
        assert score_for(due_in(hours=-24, minutes=-1)) == BASE_SCORE + 35

    def test_long_overdue_still_adds_35(self):
        # The overdue bonus is flat — a task 90 days late scores the same as
        # one that was due yesterday. No escalating penalty exists.
        assert score_for(due_in(days=-90)) == BASE_SCORE + 35

    def test_overdue_bonus_higher_than_all_other_bonuses(self):
        # Sanity check: +35 > +20 > +15 > +10, so overdue tasks always
        # outrank same-priority tasks with any other due-date state.
        assert score_for(due_in(days=-1)) > score_for(due_in(days=0))
        assert score_for(due_in(days=-1)) > score_for(due_in(days=1))
        assert score_for(due_in(days=-1)) > score_for(due_in(days=7))


# ── 3. Due today (days == 0) ───────────────────────────────────────────────────

class TestDueToday:

    def test_due_exactly_now_adds_20(self):
        assert score_for(due_in()) == BASE_SCORE + 20

    def test_due_later_today_adds_20(self):
        # 11h 59m from now → timedelta.days == 0, so still "due today".
        assert score_for(due_in(hours=11, minutes=59)) == BASE_SCORE + 20

    def test_due_today_boundary_vs_tomorrow(self):
        # days==0 (+20) vs days==1 (+15): the transition is a 5-point drop.
        today    = score_for(due_in(hours=23))   # days == 0 → +20
        tomorrow = score_for(due_in(days=1))      # days == 1 → +15
        assert today - tomorrow == 5


# ── 4. Imminent: 1–2 days (days <= 2) ─────────────────────────────────────────

class TestImminentBoundary:

    @pytest.mark.parametrize("days", [1, 2])
    def test_days_1_and_2_add_15(self, days):
        assert score_for(due_in(days=days)) == BASE_SCORE + 15

    def test_day_2_is_inside_imminent_window(self):
        # days <= 2 is inclusive — day 2 must not fall through to the +10 branch.
        assert score_for(due_in(days=2)) == BASE_SCORE + 15

    def test_day_3_is_outside_imminent_window(self):
        # One day past the boundary must drop to the weekly +10 bonus.
        assert score_for(due_in(days=3)) == BASE_SCORE + 10

    def test_imminent_boundary_drop_is_5_points(self):
        # Quantifies the scoring cliff at day 2→3 for callers that need to
        # understand how aggressively urgency decays.
        assert score_for(due_in(days=2)) - score_for(due_in(days=3)) == 5


# ── 5. This week: 3–7 days (days <= 7) ────────────────────────────────────────

class TestWeeklyBoundary:

    @pytest.mark.parametrize("days", [3, 4, 5, 6, 7])
    def test_days_3_to_7_add_10(self, days):
        assert score_for(due_in(days=days)) == BASE_SCORE + 10

    def test_day_7_is_inside_weekly_window(self):
        # days <= 7 is inclusive — day 7 must not fall through to no-bonus.
        assert score_for(due_in(days=7)) == BASE_SCORE + 10

    def test_day_8_is_outside_weekly_window(self):
        assert score_for(due_in(days=8)) == BASE_SCORE

    def test_weekly_boundary_drop_is_10_points(self):
        assert score_for(due_in(days=7)) - score_for(due_in(days=8)) == 10


# ── 6. No bonus: 8+ days ──────────────────────────────────────────────────────

class TestNoBonus:

    @pytest.mark.parametrize("days", [8, 14, 30, 365])
    def test_far_future_due_dates_add_nothing(self, days):
        assert score_for(due_in(days=days)) == BASE_SCORE


# ── 7. Complete branch map ─────────────────────────────────────────────────────
# One parametrized test that walks every branch in a single sweep.
# Useful as a quick smoke test and as living documentation of the bonus table.

class TestBranchMap:

    @pytest.mark.parametrize("days_offset, expected_bonus, label", [
        # ── overdue ──────────────────────────────────────────────────
        (-90, 35, "90 days overdue"),
        ( -1, 35, "1 day overdue"),
        # ── due today ────────────────────────────────────────────────
        (  0, 20, "due today"),
        # ── imminent ─────────────────────────────────────────────────
        (  1, 15, "due tomorrow"),
        (  2, 15, "due in 2 days (boundary)"),
        # ── this week ────────────────────────────────────────────────
        (  3, 10, "due in 3 days (boundary+1)"),
        (  7, 10, "due in 7 days (boundary)"),
        # ── no bonus ─────────────────────────────────────────────────
        (  8,  0, "due in 8 days (boundary+1)"),
        ( 30,  0, "due in 30 days"),
    ], ids=lambda x: x if isinstance(x, str) else "")
    def test_complete_branch_map(self, days_offset, expected_bonus, label):
        assert score_for(due_in(days=days_offset)) == BASE_SCORE + expected_bonus


# ── 8. Interaction with other scoring factors ──────────────────────────────────
# Due-date bonuses are additive; these tests confirm they compose correctly
# with priority weight, status penalty, and tag boost.

class TestDueDateInteractions:

    def test_overdue_bonus_stacks_with_urgent_priority(self):
        # 60 (URGENT) + 35 (overdue) = 95
        task = make_task(due_date=due_in(days=-1))
        task.priority = TaskPriority.URGENT
        assert calculate_task_score(task) == 95

    def test_overdue_bonus_does_not_rescue_done_task(self):
        # 20 (MEDIUM) + 35 (overdue) - 50 (DONE) = 5
        # A completed task should never outrank an active one at the same
        # priority, even if it is overdue.
        done_overdue   = make_task(due_date=due_in(days=-1))
        done_overdue.status = TaskStatus.DONE
        active_no_date = make_task()

        assert calculate_task_score(done_overdue) == 5
        assert calculate_task_score(done_overdue) < calculate_task_score(active_no_date)

    def test_weekly_bonus_stacks_with_blocker_tag(self):
        # 20 (MEDIUM) + 10 (this week) + 8 (blocker) = 38
        task = make_task(due_date=due_in(days=5))
        task.tags = ["blocker"]
        assert calculate_task_score(task) == 38

    def test_due_date_bonus_independent_of_recency_boost(self):
        # Both bonuses fire independently — neither suppresses the other.
        # 20 (MEDIUM) + 15 (imminent) + 5 (recent update) = 40
        task = make_task(due_date=due_in(days=1))
        task.updated_at = FROZEN_NOW - timedelta(hours=1)
        assert calculate_task_score(task) == 40