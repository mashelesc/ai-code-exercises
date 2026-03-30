"""
Integration tests for the full scoring pipeline:

    calculate_task_score → sort_tasks_by_importance → get_top_priority_tasks

Unit tests verify each function in isolation with all other factors neutralised.
These tests verify the three functions working together on realistic task sets,
where every factor (priority, due date, status, tags, recency) is live at once.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from task import calculate_task_score, sort_tasks_by_importance, get_top_priority_tasks
from models import TaskStatus, TaskPriority

# ── Fixtures ───────────────────────────────────────────────────────────────────

FROZEN_NOW = datetime(2024, 6, 15, 12, 0, 0)

@pytest.fixture(autouse=True)
def freeze_time():
    with patch("task_scoring.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        yield

def make_task(name, **overrides):
    # `name` is carried through so assertion failures name the task,
    # not just its position in the list.
    defaults = dict(
        name        = name,
        priority    = TaskPriority.MEDIUM,
        status      = TaskStatus.TODO,
        due_date    = None,
        tags        = [],
        updated_at  = FROZEN_NOW - timedelta(days=5),
        assigned_to = None,
    )
    return SimpleNamespace(**{**defaults, **overrides})

def names(tasks):
    """Extract task names for readable assertions."""
    return [t.name for t in tasks]

# ── 1. Rank ordering ───────────────────────────────────────────────────────────
# Verify that the pipeline produces the expected order for a realistic
# mix of tasks where multiple factors are active simultaneously.

class TestRankOrdering:

    def test_urgent_overdue_outranks_everything(self):
        # URGENT(60) + overdue(35) = 95 — should be first regardless of
        # what else is in the list.
        tasks = [
            make_task("low_no_date",    priority=TaskPriority.LOW),
            make_task("high_this_week", priority=TaskPriority.HIGH,
                      due_date=FROZEN_NOW + timedelta(days=5)),
            make_task("urgent_overdue", priority=TaskPriority.URGENT,
                      due_date=FROZEN_NOW - timedelta(days=2)),
            make_task("medium_blocker", tags=["blocker"]),
        ]
        result = sort_tasks_by_importance(tasks)
        assert names(result)[0] == "urgent_overdue"

    def test_done_tasks_sink_to_bottom(self):
        # DONE penalty (-50) should push completed tasks below all active ones,
        # even if they carry a high priority or an overdue bonus.
        tasks = [
            make_task("done_urgent_overdue", priority=TaskPriority.URGENT,
                      status=TaskStatus.DONE,
                      due_date=FROZEN_NOW - timedelta(days=1)),  # 60+35-50 = 45
            make_task("active_low",         priority=TaskPriority.LOW),   # 10
            make_task("active_medium"),                                    # 20
        ]
        result = sort_tasks_by_importance(tasks)
        # active tasks should both rank above the done one
        done_index   = names(result).index("done_urgent_overdue")
        active_index = names(result).index("active_low")
        assert active_index < done_index

    def test_full_realistic_ordering(self):
        # Six tasks with different factor combinations — asserts the complete
        # expected order so any ranking regression is immediately visible.
        #
        # Scores:
        #   critical_overdue  : HIGH(40) + overdue(35) + blocker(8) = 83
        #   urgent_this_week  : URGENT(60) + weekly(10)             = 70
        #   high_due_tomorrow : HIGH(40) + imminent(15)             = 55
        #   medium_blocker    : MEDIUM(20) + blocker(8)             = 28
        #   low_no_date       : LOW(10)                             = 10
        #   done_high         : HIGH(40) - done(50)                 = -10
        tasks = [
            make_task("done_high",         priority=TaskPriority.HIGH,
                      status=TaskStatus.DONE),
            make_task("low_no_date",       priority=TaskPriority.LOW),
            make_task("medium_blocker",    tags=["blocker"]),
            make_task("high_due_tomorrow", priority=TaskPriority.HIGH,
                      due_date=FROZEN_NOW + timedelta(days=1)),
            make_task("urgent_this_week",  priority=TaskPriority.URGENT,
                      due_date=FROZEN_NOW + timedelta(days=6)),
            make_task("critical_overdue",  priority=TaskPriority.HIGH,
                      due_date=FROZEN_NOW - timedelta(days=3),
                      tags=["blocker"]),
        ]
        result = sort_tasks_by_importance(tasks)
        assert names(result) == [
            "critical_overdue",   # 83
            "urgent_this_week",   # 70
            "high_due_tomorrow",  # 55
            "medium_blocker",     # 28
            "low_no_date",        # 10
            "done_high",          # -10
        ]

# ── 2. get_top_priority_tasks limit behaviour ──────────────────────────────────

class TestTopPriorityTasks:

    @pytest.fixture
    def ranked_tasks(self):
        # Seven tasks with clearly separated scores so limit slicing is unambiguous.
        return [
            make_task("t1", priority=TaskPriority.URGENT,
                      due_date=FROZEN_NOW - timedelta(days=1)),   # 95
            make_task("t2", priority=TaskPriority.URGENT),                      # 60
            make_task("t3", priority=TaskPriority.HIGH,
                      due_date=FROZEN_NOW + timedelta(days=1)),    # 55
            make_task("t4", priority=TaskPriority.HIGH),                        # 40
            make_task("t5", priority=TaskPriority.MEDIUM),                      # 20
            make_task("t6", priority=TaskPriority.LOW),                         # 10
            make_task("t7", priority=TaskPriority.LOW,
                      status=TaskStatus.DONE),                       # -40
        ]

    def test_default_limit_returns_five(self, ranked_tasks):
        result = get_top_priority_tasks(ranked_tasks)
        assert names(result) == ["t1", "t2", "t3", "t4", "t5"]

    def test_custom_limit_returns_correct_count(self, ranked_tasks):
        result = get_top_priority_tasks(ranked_tasks, limit=3)
        assert names(result) == ["t1", "t2", "t3"]

    def test_limit_larger_than_list_returns_all(self, ranked_tasks):
        result = get_top_priority_tasks(ranked_tasks, limit=100)
        assert len(result) == len(ranked_tasks)

    def test_done_tasks_excluded_from_top_results(self, ranked_tasks):
        # With 7 tasks and default limit of 5, t7 (DONE) must not appear.
        result = get_top_priority_tasks(ranked_tasks)
        assert "t7" not in names(result)

    def test_limit_zero_returns_empty_list(self, ranked_tasks):
        assert get_top_priority_tasks(ranked_tasks, limit=0) == []

# ── 3. Pipeline data contracts ─────────────────────────────────────────────────
# Verify guarantees that must hold regardless of input — these are the
# properties a caller relies on when consuming the pipeline's output.

class TestPipelineContracts:

    def test_output_scores_are_non_increasing(self):
        # The fundamental guarantee: every task's score must be >= the next one's.
        tasks = [
            make_task("a", priority=TaskPriority.LOW),
            make_task("b", priority=TaskPriority.URGENT,
                      due_date=FROZEN_NOW - timedelta(days=1)),
            make_task("c", priority=TaskPriority.MEDIUM, tags=["blocker"]),
            make_task("d", priority=TaskPriority.HIGH,
                      due_date=FROZEN_NOW + timedelta(days=2)),
            make_task("e", status=TaskStatus.DONE),
        ]
        result = sort_tasks_by_importance(tasks)
        scores = [calculate_task_score(t) for t in result]
        assert scores == sorted(scores, reverse=True)

    def test_sort_does_not_mutate_input_list(self):
        tasks = [
            make_task("a", priority=TaskPriority.LOW),
            make_task("b", priority=TaskPriority.URGENT),
            make_task("c", priority=TaskPriority.HIGH),
        ]
        original_order = names(tasks)
        sort_tasks_by_importance(tasks)
        assert names(tasks) == original_order

    def test_top_tasks_is_prefix_of_sorted_tasks(self):
        # get_top_priority_tasks(tasks, N) must always return the first N items
        # from sort_tasks_by_importance(tasks) — the two functions must agree.
        tasks = [
            make_task("a", priority=TaskPriority.LOW),
            make_task("b", priority=TaskPriority.URGENT,
                      due_date=FROZEN_NOW + timedelta(days=1)),
            make_task("c", priority=TaskPriority.MEDIUM, tags=["critical"]),
            make_task("d", priority=TaskPriority.HIGH),
            make_task("e", priority=TaskPriority.LOW, status=TaskStatus.DONE),
            make_task("f", priority=TaskPriority.HIGH,
                      due_date=FROZEN_NOW - timedelta(days=1)),
        ]
        limit = 3
        top    = get_top_priority_tasks(tasks, limit=limit)
        sorted_all = sort_tasks_by_importance(tasks)
        assert names(top) == names(sorted_all)[:limit]

    def test_pipeline_handles_empty_input(self):
        assert sort_tasks_by_importance([]) == []
        assert get_top_priority_tasks([]) == []

    def test_pipeline_handles_single_task(self):
        task = make_task("only", priority=TaskPriority.HIGH)
        assert names(sort_tasks_by_importance([task])) == ["only"]
        assert names(get_top_priority_tasks([task])) == ["only"]

    def test_all_equal_scores_preserves_all_tasks(self):
        # When scores are tied, every task must still appear in the output —
        # no task should be silently dropped during sorting.
        tasks = [make_task(f"t{i}") for i in range(4)]  # all MEDIUM, no extras
        result = sort_tasks_by_importance(tasks)
        assert len(result) == 4
        assert set(names(result)) == {"t0", "t1", "t2", "t3"}