# TaskManager - Frequently Asked Questions (FAQ)

Quick answers to common questions about using and extending the TaskManager system.

## Table of Contents
- [Installation & Setup](#installation--setup)
- [Basic Usage](#basic-usage)
- [Task Management](#task-management)
- [Filtering & Searching](#filtering--searching)
- [Advanced Features](#advanced-features)
- [Data & Storage](#data--storage)
- [Troubleshooting](#troubleshooting)
- [Development & Customization](#development--customization)

---

## Installation & Setup

### Q: What are the system requirements?
**A:** TaskManager requires Python 3.11 or higher. No additional external dependencies are needed—it uses only Python's standard library. Any operating system that supports Python (Windows, macOS, Linux) will work.

### Q: Do I need to install any packages with pip?
**A:** No! TaskManager is designed to work out of the box without any third-party dependencies. Simply extract the files and start using the CLI.

### Q: How do I verify Python is installed correctly?
**A:** Open a terminal and run:
```bash
python --version
```
It should show Python 3.11 or higher.

### Q: Can I use Python 3.10 or earlier?
**A:** The project is designed for Python 3.11+. Older versions may work but aren't officially supported. We recommend upgrading to Python 3.11 or newer.

### Q: How do I get the TaskManager?
**A:** Clone the repository from GitHub:
```bash
git clone <repository-url>
cd task-manager
```
No installation script needed—all files are ready to use immediately.

---

## Basic Usage

### Q: How do I create my first task?
**A:** The simplest command is:
```bash
python cli.py create "Your task title here"
```
This creates a task with default settings (MEDIUM priority, no due date, TODO status).

### Q: What's the difference between `cli.py` and `task_manager.py`?
**A:** 
- `cli.py` is the **command-line interface**—what users interact with
- `task_manager.py` contains the **business logic**—core functionality
- If you want to use TaskManager programmatically in your own code, import `TaskManager` from `task_manager.py`

### Q: Do I have to be in the project directory to run commands?
**A:** Yes, you must run commands from the TaskManager directory where `cli.py` is located. Use `cd path/to/task-manager` first.

### Q: How do I get help on commands?
**A:** Run:
```bash
python cli.py --help
```
Or for a specific command:
```bash
python cli.py create --help
```

### Q: Can I use TaskManager without the CLI?
**A:** Yes! TaskManager can be used programmatically. Import the classes in your Python code:
```python
from task_manager import TaskManager
from models import TaskPriority, TaskStatus

manager = TaskManager()
task_id = manager.create_task("My Task", priority_value=3)
tasks = manager.list_tasks()
```

---

## Task Management

### Q: What's the difference between task status and priority?
**A:** 
- **Status** tracks workflow progress: TODO → IN_PROGRESS → REVIEW → DONE
- **Priority** indicates importance: LOW (1) → MEDIUM (2) → HIGH (3) → URGENT (4)

Example: A LOW priority task can be DONE, and an urgent task can still be TODO.

### Q: How do I mark a task as complete?
**A:** Update the task status to "done":
```bash
python cli.py update-status <task-id> done
```
Completed tasks are marked with `[✓]` in the display.

### Q: Can I undo marking a task as done?
**A:** Yes, change the status back to a previous state:
```bash
python cli.py update-status <task-id> todo
```

### Q: What are all the possible task statuses?
**A:** Four statuses in the workflow:
- `todo` - Work hasn't started (icon: `[ ]`)
- `in_progress` - Currently being worked on (icon: `[>]`)
- `review` - Waiting for review/approval (icon: `[?]`)
- `done` - Completed (icon: `[✓]`)

### Q: How do I delete a task?
**A:** TaskManager doesn't have a delete command—tasks are persistent. If you need to "delete" a task, mark it as done or modify the `tasks.json` file directly (not recommended).

### Q: Can I set a task to a past date?
**A:** Yes, you can set any date, past or future. However, TaskManager automatically detects overdue tasks (past due date in TODO/IN_PROGRESS/REVIEW status) and flags them accordingly.

### Q: What happens when I mark a task as done?
**A:** When a task is marked as done:
- Status changes to `done`
- `completed_at` timestamp is recorded
- Task's `updated_at` is updated to current time
- The task appears with a `[✓]` icon

### Q: Can I change a task's creation date?
**A:** Not through the CLI. The creation date is automatically set when the task is created. If absolutely necessary, you can manually edit `tasks.json`, but this isn't recommended.

---

## Filtering & Searching

### Q: How do I find tasks I created a week ago?
**A:** TaskManager doesn't have a date range filter in the CLI. Your options:
1. List all tasks and review manually: `python cli.py list`
2. Edit `tasks.json` manually to find tasks by creation date
3. Use status/priority filters as proxies

### Q: Can I search for tasks by title or description?
**A:** Not directly through the CLI. Options:
1. List all tasks and search in the output: `python cli.py list | grep "search term"`
2. View the `tasks.json` file and search there
3. Write a custom Python script using the TaskManager API

### Q: How do I find all tasks with a specific tag?
**A:** TaskManager doesn't have tag filtering in the CLI. Options:
1. Use grep on the JSON file: `grep "your-tag" tasks.json`
2. List all tasks and manually look for tags: `python cli.py list`
3. Write a custom filter function in Python

### Q: Can I combine multiple filters?
**A:** Yes! You can chain filters in one command:
```bash
python cli.py list --status in_progress --priority 4
```
This shows high-priority tasks currently in progress.

### Q: What does the "overdue" filter actually check?
**A:** A task is overdue if:
1. It has a due date set
2. That date is in the past (before today)
3. The task status is NOT "done"

Completed tasks are never considered overdue, even if they were finished late.

### Q: How are tasks ordered when I list them?
**A:** The default list order is the order they were added to storage. There's no automatic sorting by priority or due date in `list`, but `task_priority.py` provides sorting functions for custom use.

---

## Advanced Features

### Q: How does natural language parsing work?
**A:** The parser recognizes these patterns in task text:
- `@tag` - Adds a tag
- `!1` or `!low` - Sets LOW priority
- `!2` or `!medium` - Sets MEDIUM priority  
- `!3` or `!high` - Sets HIGH priority
- `!4` or `!urgent` - Sets URGENT priority
- `#date` - Attempts to parse a date

Example:
```bash
python cli.py create "Fix login bug @backend !urgent #tomorrow"
```

### Q: Why didn't natural language parsing recognize my date?
**A:** The date parser is basic and recognizes common patterns like:
- Tomorrow, today, tonight
- Day names (monday, friday, etc.)
- Relative dates (next week, in 3 days)

Complex dates might not parse correctly. Use explicit YYYY-MM-DD format if parsing fails:
```bash
python cli.py create "Task @tag !3" --due "2024-02-15"
```

### Q: What's the task scoring algorithm?
**A:** Task importance is calculated based on:
- **Priority weight**: 1-6 points per priority level
- **Due date factor**: +35 if overdue, +20 if due today, +15 if due within 2 days
- **Status factor**: -50 if done, -15 if in review
- **Tag boost**: +8 for special tags (blocker, critical, urgent)
- **Update recency**: +5 if updated in last 24 hours

The `calculate_task_score()` function in `task_priority.py` implements this.

### Q: Can I customize the scoring algorithm?
**A:** Yes! Edit the `calculate_task_score()` function in `task_priority.py` to adjust weights and factors.

### Q: How does task list merging work?
**A:** The sync algorithm in `task_list_merge.py`:
1. Identifies all unique task IDs across local and remote
2. For new-only-local tasks: adds them to remote
3. For new-only-remote tasks: adds them to local
4. For existing tasks: resolves conflicts based on `updated_at` timestamps

The newer version wins conflicts.

### Q: Can I sync tasks with another system?
**A:** TaskManager provides the merging logic in `task_list_merge.py`. To integrate:
1. Export your remote tasks as a dictionary
2. Call `merge_task_lists(local_tasks, remote_tasks)`
3. Get back merge operations to execute

Here's an example:
```python
from task_list_merge import merge_task_lists

merged, create_remote, update_remote, create_local, update_local = merge_task_lists(
    local_tasks_dict,
    remote_tasks_dict
)
```

---

## Data & Storage

### Q: Where are my tasks stored?
**A:** Tasks are stored in `tasks.json` in the same directory where you run the CLI. It's created automatically when you create your first task.

### Q: Can I manually edit `tasks.json`?
**A:** Technically yes, but not recommended unless you know what you're doing. The JSON has a specific format with encoded datetime objects. Invalid changes can break the system.

### Q: What format are dates stored in?
**A:** Dates are stored in ISO format (e.g., `2024-02-15T14:30:00.123456`) in the JSON file. The system automatically converts them to Python datetime objects when loading.

### Q: Can I backup my tasks?
**A:** Yes, make a copy of `tasks.json`:
```bash
cp tasks.json tasks.json.backup
```

### Q: Can I transfer my tasks to another computer?
**A:** Yes! Copy the `tasks.json` file to the other computer in the same TaskManager directory. The tasks will load automatically.

### Q: What happens if `tasks.json` gets corrupted?
**A:** TaskManager tries to load it gracefully. If it fails:
1. Backup the corrupted file: `mv tasks.json tasks.json.bad`
2. Run any CLI command to create a fresh `tasks.json`
3. Your old tasks are lost, but the system recovers

### Q: Can I use the same `tasks.json` with multiple computers?
**A:** Not simultaneously—you'll get merge conflicts. For multi-device sync:
1. Keep tasks local on each computer, OR
2. Use the merge functionality to reconcile periodically, OR
3. Implement a server-based sync

### Q: Is there a way to export tasks to CSV or JSON?
**A:** Not through the CLI directly. Your options:
1. The native format IS JSON (`tasks.json`)—no conversion needed
2. Write a Python script to export to CSV using the `tasks.json` data
3. Copy `tasks.json` and modify it for your needs

### Q: How much data can TaskManager handle?
**A:** TaskManager is designed for small to medium task lists (hundreds to thousands of tasks). Performance depends on your machine, but even 10,000 tasks should work fine. For very large datasets (100,000+), consider a database-backed solution.

---

## Troubleshooting

### Q: I get "command not found: python cli.py"
**A:** You're likely not in the TaskManager directory. Navigate there first:
```bash
cd /path/to/task-manager
python cli.py list
```

### Q: I get "ModuleNotFoundError: No module named 'models'"
**A:** Same issue—you're not running from the correct directory. The script needs to find its modules.

### Q: Date format keeps giving errors
**A:** Always use `YYYY-MM-DD` format for explicit dates:
```bash
# ✗ Wrong
python cli.py create "Task" --due "Feb 15"

# ✓ Correct
python cli.py create "Task" --due "2024-02-15"
```

### Q: Why does `list --overdue` show no results even though I have overdue tasks?
**A:** Overdue detection only works for tasks with:
1. A due date set
2. Status is NOT "done"
3. Due date is in the past

Mark a task as done and it's no longer considered overdue.

### Q: Can I have duplicate task titles?
**A:** Yes, you can create multiple tasks with the same title. Each gets a unique ID, so they're separate tasks.

### Q: My task IDs are very long. Can I use a shorter version?
**A:** Yes! In the CLI output, IDs are shown shortened. You only need to provide enough characters to disambiguate:
```bash
# Full ID (unlikely you'll memorize this)
python cli.py show a1b2c3d4-e5f6-7890-abcd-ef1234567890

# First 8 characters (usually enough)
python cli.py show a1b2c3d4

# More if there are conflicts (rare)
python cli.py show a1b2c3d4-e5
```

### Q: How do I recover deleted tasks?
**A:** TaskManager doesn't have a true delete feature. If you accidentally modified `tasks.json` or lost the file:
1. Restore from backup: `cp tasks.json.backup tasks.json`
2. Or recover from git history if using version control

### Q: Can I use special characters in task titles?
**A:** Yes, special characters work fine in titles, descriptions, and tags. Just remember to quote them properly in the terminal:
```bash
python cli.py create "Task with 'quotes' and @symbols"
```

### Q: Why is my task not showing when I list?
**A:** Check:
1. Did you apply a filter? Try `python cli.py list` with no filters
2. Is the task stored? Check `tasks.json` exists and has content: `cat tasks.json`
3. Did the create command succeed? It should return a task ID

### Q: The stats command shows nothing
**A:** You have no tasks yet. Create one first:
```bash
python cli.py create "First task"
python cli.py stats
```

---

## Development & Customization

### Q: Can I extend TaskManager with new features?
**A:** Absolutely! The code is well-structured for extension:
- Add new properties to the `Task` class in `models.py`
- Add new CLI commands in `cli.py`
- Add new storage methods in `storage.py`
- Add new algorithms in utility files

### Q: How do I add a new CLI command?
**A:** Edit `cli.py` and add a new subparser in the `main()` function:
```python
# Add to subparsers
new_parser = subparsers.add_parser("newcommand", help="Help text")
new_parser.add_argument("arg1", help="Argument help")

# Add handling in the if/elif chain
elif args.command == "newcommand":
    # Your code here
```

### Q: How do I add a new task property?
**A:** 
1. Add to `Task.__init__()` in `models.py`
2. Update `TaskEncoder` in `storage.py` if needed
3. Update `TaskDecoder` in `storage.py` if needed
4. Update CLI in `cli.py` to accept the new property

### Q: Can I use TaskManager as a library in other projects?
**A:** Yes! Import and use it programmatically:
```python
from task_manager import TaskManager
from models import TaskPriority

manager = TaskManager("custom_path/my_tasks.json")
task_id = manager.create_task("Task", priority_value=3)
print(manager.list_tasks())
```

### Q: Are there unit tests I can run?
**A:** Yes! Run the test suite:
```bash
python -m unittest discover -v tests
```
Tests are in the `tests/` directory and cover all major functionality.

### Q: How do I write a custom filter for tasks?
**A:** Use the TaskStorage API:
```python
from storage import TaskStorage
from models import TaskStatus

storage = TaskStorage()
all_tasks = storage.get_all_tasks()

# Custom filter: tasks created in the last 7 days
from datetime import datetime, timedelta
recent = [t for t in all_tasks 
          if datetime.now() - t.created_at < timedelta(days=7)]
```

### Q: Can I run multiple instances of TaskManager simultaneously?
**A:** Not with the default `tasks.json` storage—they'll conflict over file writes. Options:
1. Use different storage files: `TaskManager("user1_tasks.json")`
2. Implement database-backed storage instead of JSON
3. Use file locking to prevent conflicts

### Q: How do I contribute improvements?
**A:** 
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

We welcome contributions!

### Q: Where's the architecture documentation?
**A:** See:
- [README.md](README.md) - Project structure and component overview
- [STEP_BY_STEP_GUIDE.md](STEP_BY_STEP_GUIDE.md) - User guide with examples
- Code docstrings - Read the source files directly
- `tests/` directory - Tests show usage examples

### Q: Can I use TaskManager with a web framework like Django or Flask?
**A:** Yes! TaskManager can be integrated as a backend service. You'd need to:
1. Wrap TaskManager in an HTTP API
2. Update storage to use a database
3. Handle concurrent access properly

This is beyond the scope of the base library but totally possible.

---

## Still Have Questions?

- **Check the README**: [README.md](README.md) has detailed documentation
- **Review Examples**: [STEP_BY_STEP_GUIDE.md](STEP_BY_STEP_GUIDE.md) has practical examples
- **Read the Code**: Source files have comments and clear structure
- **Run Tests**: Tests show expected behavior: `python -m unittest discover -v tests`

---

**Happy task managing!** 🎯
