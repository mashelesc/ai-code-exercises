## AI TOOL USED: CLAUDE AI
## EXERCISE: USING AI TO HELP WITH TESTING

## PART 1: UNDERSTANDING WHAT TO TEST
- Using the **task_priority.py** script.

### PROMPT 1.1: BEHAVIOR ANALYSIS QUESTIONS

Here are the behavior analysis questions for the **calculate_task_score** function:

## Behavior Analysis Questions - Calculate_Task_Score (Usual Cases)

### Base Priority Scoring
1. What is the score for a task with medium priority and no other factors?
2. How does an urgent priority task's base score compare to a low priority task?
3. What is the exact score increment per priority level?

### Due Date Impact (Typical Scenarios)
4. How much does a task's score increase if it's due today versus due in 5 days?
5. What score boost applies to a task due within the next 2 days?
6. Does a task without a due date receive any automatic penalty?

### Status Effects (Normal Workflow)
7. By how much does a completed task's score decrease?
8. How does a task in review status affect the final score?
9. Does a pending/in-progress task receive any status-based adjustment?

### Tag Boosting (Typical Use)
10. How much score boost does a task with one special tag ("blocker", "critical", or "urgent") receive?
11. Does having multiple special tags increase the boost beyond 8 points?

### Recency Factor (Normal Conditions)
12. What score boost does a recently updated task (within 1 day) receive?
13. How many points exactly are added for recent updates?

### Combined Typical Scenarios
14. Score a high priority task due today with no tags, updated 2 hours ago?
15. Score an urgent task with "critical" tag due in 3 days, updated yesterday?
16. Score a medium priority task due in 10 days with no special tags, updated a week ago?

#### 5 TEST CASES

Based on the `calculate_task_score` function analysis, here are at least 5 test cases including edge cases:

## Test Cases for `calculate_task_score`

### Test Case 1: Base Score Only
**Input:** Medium priority, no due date, normal status, no tags, old update
**Expected Output:** 20
**Purpose:** Verify baseline score calculation with only priority factor

### Test Case 2: Overdue Urgent Task with Critical Tag
**Input:** Urgent priority, overdue by 2 days, normal status, "critical" tag, updated today
**Expected Output:** 60 (base) + 35 (overdue) + 8 (tag) + 5 (recent) = 108
**Purpose:** Verify maximum score accumulation with positive factors

### Test Case 3: Completed Task (Should be Deprioritized)
**Input:** High priority, due today, status=DONE, no tags
**Expected Output:** 40 (base) + 20 (due today) - 50 (done penalty) = 10
**Purpose:** Verify that completed tasks are deprioritized despite urgency

### Test Case 4: Task in Review with Penalty
**Input:** Medium priority, due in 3 days, status=REVIEW, no tags
**Expected Output:** 20 (base) + 15 (due in 2 days) - 15 (review penalty) = 20
**Purpose:** Verify review status penalty is applied correctly

### Test Case 5: Task with No Due Date vs Far Future Due Date
**Input:** Medium priority, due_date=None, normal status, no tags
**Expected Output:** 20
**Purpose:** Verify no score modification for tasks without due dates

### Edge Case 6: Multiple Special Tags (Boost Should Not Stack)
**Input:** Low priority, tags=["blocker", "critical", "urgent"]
**Expected Output:** 10 (base) + 8 (tag boost, applied once) = 18
**Purpose:** Verify that multiple qualifying tags don't multiply the 8-point boost

### Edge Case 7: Task Updated Exactly 1 Day Ago (Boundary)
**Input:** Medium priority, `days_since_update = 1`
**Expected Output:** 20
**Purpose:** Verify recency boost only applies to `< 1` day, not `<= 1`

### Edge Case 8: Unknown Priority Value
**Input:** task.priority not in priority_weights dictionary
**Expected Output:** 0
**Purpose:** Verify `.get(task.priority, 0)` returns 0 for unknown priorities

### Edge Case 9: Negative Score (Completed Urgent Task)
**Input:** Urgent priority, status=DONE, no other factors
**Expected Output:** 60 (base) - 50 (done penalty) = 10
**Purpose:** Verify scores can go negative with heavy penalties

### Edge Case 10: Task Due in Exactly 2 Days (Boundary)
**Input:** Medium priority, `days_until_due = 2`
**Expected Output:** 20 (base) + 15 (due within 2 days) = 35
**Purpose:** Verify boundary condition on `<= 2` days boost
  
### PROMPT 1.2: TEST PLANNING GUIDANCE

## Test Planning Guidance

Here's a structured breakdown of what to test across this module.

---

### What the Code Does

The module exposes three public functions that form a pipeline: `calculate_task_score` → `sort_tasks_by_importance` → `get_top_priority_tasks`. The core logic lives in `calculate_task_score`, which accumulates a numeric score from five independent factors.

---

### Scoring Factor Coverage

Each factor in `calculate_task_score` needs its own dedicated tests:

**Priority weight** tests should verify all four enum values map to the expected base score (e.g. `URGENT` → 60), and also test an unknown/missing priority that falls through to the `get` default of 0.

**Due date factor** has five branches — overdue, due today, due in 1–2 days, due in 3–7 days, and no due date set. Test each boundary explicitly. The most important edge cases are `days_until_due == 0` vs `days_until_due == -1` (the overdue/today boundary) and `days_until_due == 2` vs `days_until_due == 3` (the 2-day/weekly boundary).

**Status penalty** — test `DONE` subtracts 50 and `REVIEW` subtracts 15. Also test that other statuses like `IN_PROGRESS` or `TODO` apply no penalty.

**Tag boost** — test each of the three trigger tags individually (`"blocker"`, `"critical"`, `"urgent"`), an empty tag list, and tags that don't match (confirms no false positive). Also test a task with multiple trigger tags to confirm the boost is flat (+8), not cumulative.

**Recency boost** — test `updated_at` within the last 24 hours (+5) vs. one day or more ago (+0). This is time-sensitive: use `datetime.now()` patched via `unittest.mock.patch` rather than hardcoded timestamps.

---

### Combination / Interaction Tests

Score factors are additive, so you need tests that combine them to catch unintended interactions:

- A worst-case "urgent, overdue, blocking" task to verify the score ceiling
- A `DONE` task that is also overdue — confirms the large subtraction brings it below active tasks even when other factors are high
- A `REVIEW` task with a high-priority tag, to ensure partial penalties work correctly

---

### Sorting and Limit Functions

`sort_tasks_by_importance` needs tests for an empty list, a single-element list, and a list where two tasks have equal scores (test that the output is stable — both orderings are acceptable, but the list length should be preserved). Also test that the original list is not mutated.

`get_top_priority_tasks` should test the default limit of 5, a custom limit, a limit larger than the task list (should return all tasks without error), and `limit=0` (should return an empty list).

---

### Error / Defensive Cases

The code has no explicit guards, so you should document how it behaves (and whether it *should* behave this way) under:

- `task.due_date` is `None` — already handled by the `if task.due_date:` guard, but test it explicitly
- `task.tags` is `None` rather than an empty list — the `any(... for tag in task.tags)` call will raise a `TypeError`; decide if that's acceptable or if a guard is needed
- `task.updated_at` is `None` — will raise `TypeError` in the timedelta arithmetic; same decision needed
- `task.priority` not in the enum — currently silently scores 0, which may or may not be intentional

---

### Suggested Test Structure

```
tests/
  test_calculate_task_score.py   # one test class per scoring factor
  test_sort_tasks.py             # sorting correctness, stability, mutation
  test_get_top_priority_tasks.py # limit behaviour, integration with sort
  conftest.py                    # shared task factory / fixtures
```

A `make_task()` factory fixture in `conftest.py` with sensible defaults for all fields will save a lot of boilerplate and make individual tests easier to read — each test only needs to override the field it cares about.

## PART 2: IMPROVING A SINGLE TEST

### PROMPT 2.1: SINGLE TEST ENHANCEMENT
- **test_calculate_task_score.py** script attached.
- Improved version: **test_task_score.py** script attached.
  
### PROMPT 2.2: LEARNING FROM EXAMPLES
- Another aspect of the **calculate_task_score()** function to test: ```due date calculations```.
- The comprehensive test script **comprehensive_test.py** is attached.
- The **due_in()** helper function keeps test cases readable without repeating **FROZEN_NOW + timedelta(...)** everywhere. It also accepts hours and minutes so the intra-day boundary cases (**test_one_minute_overdue_adds_35**, **test_due_later_today_adds_20**) can be expressed precisely — those cases are impossible to write clearly with day offsets alone.
- **test_one_minute_overdue_adds_35** exists because **timedelta.days** truncates toward zero, not toward negative infinity. A task due 23h 59m ago has **timedelta.days == 0**, which the code treats as "due today" — so it gets +20, not +35. That's a real classification edge that day-only tests miss entirely.
- Boundary drop tests (**test_imminent_boundary_drop_is_5_points**, **test_weekly_boundary_drop_is_10_points**) assert the magnitude of the cliff between branches rather than just the absolute score. This is useful when the weights change — a refactor that accidentally flattens a boundary will fail here even if both absolute values are still "reasonable".
- **TestBranchMap** is deliberately redundant with the individual classes. It's a single parametrized sweep that serves as a compact reference table — useful for a reviewer who wants to see the whole bonus structure at once without reading nine test classes.
- **TestDueDateInteractions** is the most important class. The individual branch tests confirm the due-date logic in isolation; these four confirm it composes correctly with the other factors. **test_overdue_bonus_does_not_rescue_done_task** in particular pins a real product decision: a finished task should never float above an active one regardless of how overdue it was.
  
## PART 3: LEARNING TEST-DRIVEN DEVELOPMENT

### PROMPT 3.1: GUIDED TDD PRACTISE
- Failing test script **failing_test.py** is attached.
- This fails immediately because **calculate_task_score()** doesn't accept **current_user_id** yet.

- Minimal implementation to make it work:

```python
from datetime import datetime
from models import TaskStatus, TaskPriority

def calculate_task_score(task, current_user_id=None):  # ← new param
    priority_weights = {
        TaskPriority.LOW: 1,
        TaskPriority.MEDIUM: 2,
        TaskPriority.HIGH: 4,
        TaskPriority.URGENT: 6
    }

    score = priority_weights.get(task.priority, 0) * 10

    if task.due_date:
        days_until_due = (task.due_date - datetime.now()).days
        if days_until_due < 0:
            score += 35
        elif days_until_due == 0:
            score += 20
        elif days_until_due <= 2:
            score += 15
        elif days_until_due <= 7:
            score += 10

    if task.status == TaskStatus.DONE:
        score -= 50
    elif task.status == TaskStatus.REVIEW:
        score -= 15

    if any(tag in ["blocker", "critical", "urgent"] for tag in task.tags):
        score += 8

    days_since_update = (datetime.now() - task.updated_at).days
    if days_since_update < 1:
        score += 5

    if current_user_id and task.assigned_to == current_user_id:     # This conditional will ensure that the failing script now runs.
        score += 12


    return score
```

- Three of the four new tests already pass given the minimal implementation — the logic is correct for different users, missing **current_user_id**, and unassigned tasks. The stacking test also passes because ```+12``` is simply additive. Running the suite confirms all green, so no refactor is needed — the two-line implementation handles every case.

##### Here's where the TDD cycle ends and why:
- **Red → Green → Refactor, then stop**. The implementation is already minimal and the intent is clear. There's no duplication to remove, no abstraction waiting to be named, no complexity to simplify. Refactoring now would be change for its own sake.
- The progression also reveals something important about TDD done properly — cycle 1 proved the feature works, cycle 2 proved it doesn't break anything else. The backwards-compat test (**test_no_current_user_id_no_boost**) is the most valuable one: it would have caught a breaking signature change immediately, before any callers noticed.

### PROMPT 3.2: TDD CODE REVIEW GUIDANCE

- **Step 1 — understand the bug**
  - The bug is in this line:

    ```
    days_since_update = (datetime.now() - task.updated_at).days
    ```

  - In the Python codebase this looks correct, but the prompt tells us the real implementation is secretly using a JavaScript-style millisecond division,as if someone ported it from JS and left the wrong arithmetic in place:

    ```
    # buggy — JS-style milliseconds ported incorrectly to Python
    days_since_update = (datetime.now() - task.updated_at).seconds / 86400
    ```

    ```.seconds``` only returns the seconds component of the timedelta (0–86399), not the total duration. A task updated 2 days ago has ```.seconds == 0```, so ```0 / 86400 == 0.0```, which is ```< 1``` — meaning it always gets the recency boost, regardless of when it was last updated.

- **Step 2 — the failing test**
  - FAIL, demonstrates the bug.

```python
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from task import calculate_task_score
from models import TaskStatus, TaskPriority


FROZEN_NOW = datetime(2024, 6, 15, 12, 0, 0)


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
        assigned_to = None,
    )
    return SimpleNamespace(**{**defaults, **overrides})


class TestRecencyBugFix:

    def test_stale_task_does_not_get_recency_boost(self):
        # A task last updated 5 days ago is well outside the 24-hour window.
        # Expected: no +5 boost → score == 20 (MEDIUM base only).
        #
        # BUG: the buggy implementation uses .seconds / 86400 instead of .days
        #   timedelta(days=5).seconds == 0
        #   0 / 86400 == 0.0, which is < 1
        #   so the boost fires incorrectly → score == 25
        #
        # This test fails against the buggy code and passes after the fix.
        task = make_task(updated_at=FROZEN_NOW - timedelta(days=5))
        assert calculate_task_score(task) == 20  # ← returns 25 with the bug

    def test_recency_boost_fires_for_task_updated_one_hour_ago(self):
        # Guard: ensure the fix doesn't break the case the boost is meant to cover.
        task = make_task(updated_at=FROZEN_NOW - timedelta(hours=1))
        assert calculate_task_score(task) == 25  # 20 + 5

    def test_recency_boost_fires_for_task_updated_23_hours_ago(self):
        # Upper edge of the valid window — still within 24 hours.
        task = make_task(updated_at=FROZEN_NOW - timedelta(hours=23))
        assert calculate_task_score(task) == 25  # 20 + 5

    def test_recency_boost_does_not_fire_at_exactly_24_hours(self):
        # timedelta(hours=24).days == 1, which is not < 1 → no boost.
        # With the bug: .seconds == 0, so 0/86400 < 1 → boost fires. Wrong.
        task = make_task(updated_at=FROZEN_NOW - timedelta(hours=24))
        assert calculate_task_score(task) == 20  # ← returns 25 with the bug

    def test_recency_boost_does_not_fire_for_task_updated_two_days_ago(self):
        # timedelta(days=2).seconds == 0 — the exact value that tricks the buggy
        # implementation. This is the clearest demonstration of the fault.
        task = make_task(updated_at=FROZEN_NOW - timedelta(days=2))
        assert calculate_task_score(task) == 20  # ← returns 25 with the bug
  ```


  - Against the buggy code, three of the five tests fail. Notice ```test_recency_boost_does_not_fire_for_task_updated_two_days_ago``` is the sharpest demonstration — ```timedelta(days=2).seconds``` is exactly ```0```, which is the value that makes ```.seconds / 86400``` silently return ```0.0``` and incorrectly trigger the boost.

- **Step 3 — the buggy implementation and the fix**
  - PASS — all 5 tests green after fix.

```python

from datetime import datetime
from models import TaskStatus, TaskPriority

def calculate_task_score(task, current_user_id=None):
    priority_weights = {
        TaskPriority.LOW: 1,
        TaskPriority.MEDIUM: 2,
        TaskPriority.HIGH: 4,
        TaskPriority.URGENT: 6
    }

    score = priority_weights.get(task.priority, 0) * 10

    if task.due_date:
        days_until_due = (task.due_date - datetime.now()).days
        if days_until_due < 0:
            score += 35
        elif days_until_due == 0:
            score += 20
        elif days_until_due <= 2:
            score += 15
        elif days_until_due <= 7:
            score += 10

    if task.status == TaskStatus.DONE:
        score -= 50
    elif task.status == TaskStatus.REVIEW:
        score -= 15

    if any(tag in ["blocker", "critical", "urgent"] for tag in task.tags):
        score += 8

    # line to change has been commented out
    # days_since_update = (datetime.now() - task.updated_at).seconds / 86400 

    days_since_update = (datetime.now() - task.updated_at).days

    if days_since_update < 1:
        score += 5

    if current_user_id and task.assigned_to == current_user_id:
        score += 12

    return score
```
  
  - One character change — ```.seconds``` → ```.days``` — and all five tests go green. A few things worth noting about how this played out:
    - Why ```.seconds``` is such a dangerous bug. ```timedelta``` has three components: ```.days```, ```.seconds``` (0–86399), and ```.microseconds```. For a delta of exactly 2 days, ```.days == 2``` and ```.seconds == 0```. The JS equivalent ```ms / 86_400_000``` would correctly return ```2.0```, but ```.seconds / 86400``` returns ```0.0``` — which silently passes the ```< 1``` check. The bug only affects tasks updated more than 24 hours ago, and only on whole-day boundaries where ```.seconds``` happens to be zero. That makes it intermittent and hard to spot without a frozen clock.
    - Why ```test_recency_boost_does_not_fire_for_task_updated_two_days_ago``` is the key test. It targets the exact value — ```timedelta(days=2)``` — where ```.seconds``` is guaranteed to be ```0```. Without the frozen clock, this test could pass or fail depending on the time of day the suite runs, because a real ```timedelta``` of "2 days ago" almost never has ```.seconds == 0``` unless the update happened at precisely the same time of day.
    - The guard test matters. ```test_recency_boost_fires_for_task_updated_one_hour_ago``` ensures the fix didn't overcorrect. A naive fix like ```days_since_update = 1``` would make all the "no boost" tests green while silently breaking the feature entirely.

## PART 4: INTEGRATION TESTING

### PROMPT 4.1: TESTING THE FULL WORKFLOW

- For integration tests, the goal shifts from "does each function compute the right number" to "does the pipeline produce the right ranked list for realistic inputs."
- Integration testing script has been **integration_test.py** attached.
- Three classes, three different kinds of integration concern:
  - ```TestRankOrdering``` tests that the pipeline produces the right order for realistic inputs where multiple factors fire at once. ```test_full_realistic_ordering``` is the most valuable — it pins the complete ranked list as a regression anchor. If any weight changes, or a new factor is added, this test fails loudly and the developer has to consciously update the expected order.
  - ```TestTopPriorityTasks``` tests the limit behaviour of ```get_top_priority_tasks``` against a fixture with clearly separated scores. The key test here is ```test_done_tasks_excluded_from_top_results``` — it only passes if ```calculate_task_score``` and ```sort_tasks_by_importance``` both work correctly, so it's genuinely testing the pipeline, not just the slice.
  - ```TestPipelineContracts``` tests properties rather than specific values — things that must always be true regardless of input. ```test_output_scores_are_non_increasing``` is the most robust of these: instead of asserting a fixed order, it verifies the underlying guarantee directly by re-scoring the output and checking it's sorted. ```test_top_tasks_is_prefix_of_sorted_tasks``` is the contract that ties all three functions together — it would fail if ```get_top_priority_tasks``` ever diverged from ```sort_tasks_by_importance``` in its ranking logic.
  - The ```names()``` helper function is worth calling out: it makes assertion failures readable. Without it, a failure would show ```[<SimpleNamespace ...>, ...]``` — with it, you see ```["urgent_this_week, "high_due_tomorrow", ...]``` immediately.


### REFLECTION

- In this exercise, I have learned that:
  - You have to understand the requirements of a script or function. This understanding can be obtained through documentation, otherwise your tests will just confirm anything that the code currently does.
  - There's a difference between **testing behavior** and **testing implementation**, a weak test would assert that **calculate_task_score()** returns an exact integer, while a stronger test would assert that an overdue high priority task ranks above a non-overdue high priority task.
  - Test data is very important during the tests. All the ```Task``` objects with ```priority```, ```due_date```, ```status```, ```tags```, and ```updated_at``` have to be assigned meaningful values, otherwise the whole code would crash if some variables were to have null values(```None```).
  - A test can pass today, but still fail tomorrow without having changed any line of code. This code's reliance on the ```datetime.now()``` function is an example of a hidden non-determinism problem. You need to identify and control time-dependent inputs that deal with dates.
  - Unit tests catch where bugs live, integration tests confirm whether the whole code does work together or not. Both tests are necessary for a conclusive test status.      
