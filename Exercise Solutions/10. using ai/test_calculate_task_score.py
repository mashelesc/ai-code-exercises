from datetime import datetime, timedelta
from types import SimpleNamespace
import pytest

from task import calculate_task_score
from models import TaskStatus, TaskPriority


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_task(**overrides):
    """Minimal task with safe defaults — override only what each test cares about."""
    defaults = dict(
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.TODO,
        due_date=None,
        tags=[],
        updated_at=datetime.now() - timedelta(days=5),  # no recency boost by default
    )
    return SimpleNamespace(**{**defaults, **overrides})


# ── Priority weight ────────────────────────────────────────────────────────────

class TestPriorityWeight:

    def test_urgent_priority(self):
        task = make_task(priority=TaskPriority.URGENT)
        assert calculate_task_score(task) == 60

    def test_high_priority(self):
        task = make_task(priority=TaskPriority.HIGH)
        assert calculate_task_score(task) == 40

    def test_medium_priority(self):
        task = make_task(priority=TaskPriority.MEDIUM)
        assert calculate_task_score(task) == 20

    def test_low_priority(self):
        task = make_task(priority=TaskPriority.LOW)
        assert calculate_task_score(task) == 10


# ── Due date factor ────────────────────────────────────────────────────────────

class TestDueDateFactor:

    def test_overdue_task_adds_35(self):
        task = make_task(due_date=datetime.now() - timedelta(days=1))
        assert calculate_task_score(task) == 55  # 20 base + 35

    def test_due_today_adds_20(self):
        task = make_task(due_date=datetime.now())
        assert calculate_task_score(task) == 40  # 20 base + 20

    def test_no_due_date_adds_nothing(self):
        task = make_task(due_date=None)
        assert calculate_task_score(task) == 20  # base only


# ── Status penalty ─────────────────────────────────────────────────────────────

class TestStatusPenalty:

    def test_done_subtracts_50(self):
        task = make_task(status=TaskStatus.DONE)
        assert calculate_task_score(task) == -30  # 20 base - 50

    def test_review_subtracts_15(self):
        task = make_task(status=TaskStatus.REVIEW)
        assert calculate_task_score(task) == 5   # 20 base - 15

    def test_todo_has_no_penalty(self):
        task = make_task(status=TaskStatus.TODO)
        assert calculate_task_score(task) == 20  # base only


# ── Tag boost ──────────────────────────────────────────────────────────────────

class TestTagBoost:

    def test_blocker_tag_adds_8(self):
        task = make_task(tags=["blocker"])
        assert calculate_task_score(task) == 28  # 20 base + 8

    def test_irrelevant_tag_adds_nothing(self):
        task = make_task(tags=["backend", "needs-review"])
        assert calculate_task_score(task) == 20  # base only


# ── Recency boost ─────────────────────────────────────────────────────────────

class TestRecencyBoost:

    def test_recently_updated_adds_5(self):
        task = make_task(updated_at=datetime.now() - timedelta(hours=2))
        assert calculate_task_score(task) == 25  # 20 base + 5

    def test_stale_task_adds_nothing(self):
        task = make_task(updated_at=datetime.now() - timedelta(days=3))
        assert calculate_task_score(task) == 20  # base only