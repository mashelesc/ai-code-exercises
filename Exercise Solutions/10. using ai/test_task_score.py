from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from task import calculate_task_score
from models import TaskStatus, TaskPriority


# ── Fixtures ───────────────────────────────────────────────────────────────────

# A fixed "now" used everywhere. Patching datetime.now() to return this value
# means time-sensitive tests produce identical results whenever they are run.
FROZEN_NOW = datetime(2024, 6, 15, 12, 0, 0)


@pytest.fixture(autouse=True)
def freeze_time():
    """Patch datetime.now() for every test in this module automatically."""
    with patch("task_scoring.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        yield


def make_task(**overrides):
    """Return a task with neutral defaults — only set what the test cares about.
    - MEDIUM priority  →  base score of 20 (easy mental arithmetic)
    - TODO status      →  no status penalty
    - due_date=None    →  no due-date bonus
    - tags=[]          →  no tag boost
    - updated_at 5d ago →  outside the 24-hour recency window, so no boost
    """
    defaults = dict(
        priority   = TaskPriority.MEDIUM,
        status     = TaskStatus.TODO,
        due_date   = None,
        tags       = [],
        updated_at = FROZEN_NOW - timedelta(days=5),
    )
    return SimpleNamespace(**{**defaults, **overrides})


# ── 1. Priority weight ─────────────────────────────────────────────────────────
# Each enum value has an explicit weight (LOW=1, MEDIUM=2, HIGH=4, URGENT=6).
# Base score = weight × 10. All other factors are neutralised by make_task().

class TestPriorityWeight:

    @pytest.mark.parametrize("priority, expected", [
        (TaskPriority.LOW,    10),
        (TaskPriority.MEDIUM, 20),
        (TaskPriority.HIGH,   40),
        (TaskPriority.URGENT, 60),
    ])
    def test_priority_produces_correct_base_score(self, priority, expected):
        assert calculate_task_score(make_task(priority=priority)) == expected

    def test_unknown_priority_scores_zero(self):
        # dict.get() returns 0 for an unrecognised priority — confirms the
        # silent fallback rather than an exception.
        assert calculate_task_score(make_task(priority="nonexistent")) == 0


# ── 2. Due date factor ─────────────────────────────────────────────────────────
# Five branches; each boundary is tested on both sides.
#   days < 0   → +35    (overdue)
#   days == 0  → +20    (due today)
#   days <= 2  → +15    (imminent)
#   days <= 7  → +10    (this week)
#   days > 7   → +0     (no bonus)

class TestDueDateFactor:

    @pytest.mark.parametrize("days_offset, expected_bonus", [
        # overdue ─ both "just overdue" and "long overdue" should give +35
        (-1,  35),
        (-30, 35),
        # due today
        (0,   20),
        # imminent boundary: inside and outside
        (1,   15),
        (2,   15),  # boundary — still +15
        (3,   10),  # boundary + 1 — drops to +10
        # weekly boundary: inside and outside
        (7,   10),  # boundary — still +10
        (8,    0),  # boundary + 1 — no bonus
        (30,   0),
    ])
    def test_due_date_bonus(self, days_offset, expected_bonus):
        due = FROZEN_NOW + timedelta(days=days_offset)
        score = calculate_task_score(make_task(due_date=due))
        assert score == 20 + expected_bonus  # 20 = MEDIUM base

    def test_no_due_date_gives_no_bonus(self):
        assert calculate_task_score(make_task(due_date=None)) == 20


# ── 3. Status penalty ──────────────────────────────────────────────────────────

class TestStatusPenalty:

    @pytest.mark.parametrize("status, expected_penalty", [
        (TaskStatus.DONE,        50),
        (TaskStatus.REVIEW,      15),
        (TaskStatus.TODO,         0),
        (TaskStatus.IN_PROGRESS,  0),
    ])
    def test_status_penalty(self, status, expected_penalty):
        score = calculate_task_score(make_task(status=status))
        assert score == 20 - expected_penalty  # 20 = MEDIUM base


# ── 4. Tag boost ───────────────────────────────────────────────────────────────

class TestTagBoost:

    @pytest.mark.parametrize("tags", [
        ["blocker"],
        ["critical"],
        ["urgent"],
    ])
    def test_each_trigger_tag_adds_8(self, tags):
        assert calculate_task_score(make_task(tags=tags)) == 28  # 20 + 8

    def test_multiple_trigger_tags_still_adds_only_8(self):
        # any() short-circuits — the boost is flat, not additive.
        task = make_task(tags=["blocker", "critical", "urgent"])
        assert calculate_task_score(task) == 28

    def test_non_trigger_tags_add_nothing(self):
        task = make_task(tags=["backend", "needs-review"])
        assert calculate_task_score(task) == 20

    def test_empty_tags_adds_nothing(self):
        assert calculate_task_score(make_task(tags=[])) == 20


# ── 5. Recency boost ───────────────────────────────────────────────────────────
# days_since_update < 1  →  +5   (updated within the last 24 hours)
# days_since_update >= 1 →  +0

class TestRecencyBoost:

    @pytest.mark.parametrize("hours_ago, expected_bonus", [
        (1,   5),   # well within 24h window
        (23,  5),   # boundary — still inside
        (24,  0),   # boundary — timedelta.days flips to 1 at exactly 24h
        (48,  0),
    ])
    def test_recency_bonus(self, hours_ago, expected_bonus):
        updated_at = FROZEN_NOW - timedelta(hours=hours_ago)
        score = calculate_task_score(make_task(updated_at=updated_at))
        assert score == 20 + expected_bonus


# ── 6. Combination ─────────────────────────────────────────────────────────────
# Additive factors interact; test two meaningful combinations.

class TestCombination:

    def test_urgent_overdue_blocker_recently_updated(self):
        # All boosts on, no penalty.
        # 60 (URGENT) + 35 (overdue) + 8 (blocker) + 5 (recent) = 108
        task = make_task(
            priority   = TaskPriority.URGENT,
            due_date   = FROZEN_NOW - timedelta(days=1),
            tags       = ["blocker"],
            updated_at = FROZEN_NOW - timedelta(hours=1),
        )
        assert calculate_task_score(task) == 108

    def test_done_overdue_task_scores_below_active_task(self):
        # Even with a big overdue bonus, DONE's -50 should floor the score
        # below a plain active task at the same priority.
        # 20 (MEDIUM) + 35 (overdue) - 50 (DONE) = 5
        done_task   = make_task(status=TaskStatus.DONE, due_date=FROZEN_NOW - timedelta(days=1))
        active_task = make_task()  # 20, no bonuses
        assert calculate_task_score(done_task) < calculate_task_score(active_task)