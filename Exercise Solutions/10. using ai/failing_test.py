from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from task import calculate_task_score
from models import TaskStatus, TaskPriority


FROZEN_NOW = datetime(2024, 6, 15, 12, 0, 0)
CURRENT_USER_ID = "user-123"


@pytest.fixture(autouse=True)
def freeze_time():
    with patch("task_scoring.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        yield


def make_task(**overrides):
    defaults = dict(
        priority    = TaskPriority.MEDIUM,
        status      = TaskStatus.TODO,
        due_date    = None,
        tags        = [],
        updated_at  = FROZEN_NOW - timedelta(days=5),
        assigned_to = None,   # new field
    )
    return SimpleNamespace(**{**defaults, **overrides})


# ── Failing test ───────────────────────────────────────────────────────────────

class TestAssignedUserBoost:

    def test_task_assigned_to_current_user_adds_12(self):
        task = make_task(assigned_to=CURRENT_USER_ID)
        # calculate_task_score doesn't accept current_user_id yet — this fails
        # with TypeError: calculate_task_score() got an unexpected keyword argument
        score = calculate_task_score(task, current_user_id=CURRENT_USER_ID)
        assert score == 32  # 20 (MEDIUM base) + 12