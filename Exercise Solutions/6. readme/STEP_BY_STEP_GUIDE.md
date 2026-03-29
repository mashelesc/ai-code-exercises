# TaskManager - Step-by-Step Guide

A beginner-friendly guide to get you up and running with the TaskManager application in minutes.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Your First Task](#your-first-task)
3. [Managing Tasks](#managing-tasks)
4. [Filtering and Finding Tasks](#filtering-and-finding-tasks)
5. [Using Advanced Features](#using-advanced-features)
6. [Practical Workflows](#practical-workflows)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Step 1: Install Python (if you haven't already)

Check if Python 3.11+ is installed on your system:

```bash
python --version
```

If you don't have Python 3.11 or higher, download it from [python.org](https://www.python.org/downloads/).

### Step 2: Get the TaskManager Code

Clone or download the TaskManager repository:

```bash
git clone <repository-url>
cd task-manager
```

### Step 3: Verify the Installation

Check that all required files are present:

```bash
ls -la
```

You should see these files:
- `cli.py`
- `models.py`
- `storage.py`
- `task_manager.py`
- `task_parser.py`
- `task_priority.py`
- `task_list_merge.py`
- `tests/` (directory)

That's it! No complex setup needed—TaskManager uses only Python's built-in libraries.

---

## Your First Task

### Step 1: Create Your First Task

Open your terminal and run:

```bash
python cli.py create "Buy groceries"
```

**What just happened?**
- A new task was created with the title "Buy groceries"
- The task was automatically saved to a `tasks.json` file
- You received back a task ID (a unique identifier for this task)

### Step 2: View Your Task

Now let's see the task you just created:

```bash
python cli.py list
```

You should see output like:

```
[ ] a1b2c3d4 - !! Buy groceries
  Created: 2024-01-15 14:30
```

**Understanding the output:**
- `[ ]` = Status (TODO - not started)
- `a1b2c3d4` = Task ID (shortened for display)
- `!!` = Priority (MEDIUM - default)
- `Buy groceries` = Your task title

### Step 3: Create a Task with More Details

Let's create a more detailed task:

```bash
python cli.py create "Fix login bug" \
  --description "Users cannot log in with Google OAuth" \
  --priority 4 \
  --due "2024-02-01" \
  --tags "bug,critical"
```

**What each flag does:**
- `--description` (or `-d`): Add context about the task
- `--priority` (or `-p`): Set importance (1=LOW, 2=MEDIUM, 3=HIGH, 4=URGENT)
- `--due` (or `-u`): Set deadline (format: YYYY-MM-DD)
- `--tags` (or `-t`): Add labels (comma-separated, helpful for grouping)

### Step 4: View All Your Tasks

```bash
python cli.py list
```

You should now see both tasks listed.

---

## Managing Tasks

### View a Specific Task

Get detailed information about a task using its ID:

```bash
python cli.py show a1b2c3d4
```

**Tip:** You can see task IDs in the list output—they're the 8-character codes after the status symbol.

### Mark a Task as Done

Update task status to mark it complete:

```bash
python cli.py update-status a1b2c3d4 done
```

**Available statuses:**
- `todo` - Work hasn't started
- `in_progress` - Currently working on it
- `review` - Waiting for review/approval
- `done` - Completed

### Change a Task's Priority

Need to adjust importance? Update the priority:

```bash
python cli.py update-priority a1b2c3d4 3
```

**What if you made a mistake?**
- `1` = LOW priority (not urgent)
- `2` = MEDIUM priority (normal work)
- `3` = HIGH priority (should do soon)
- `4` = URGENT priority (do immediately)

### Update a Task's Due Date

Change the deadline:

```bash
python cli.py update-due-date a1b2c3d4 "2024-02-15"
```

**Date format reminder:** Always use `YYYY-MM-DD`

---

## Filtering and Finding Tasks

### See Only TODO Tasks

Find all tasks you haven't started yet:

```bash
python cli.py list --status todo
```

Shorthand:
```bash
python cli.py list -s todo
```

### See Only High Priority Tasks

Find tasks that need urgent attention:

```bash
python cli.py list --priority 3
```

This shows all HIGH and URGENT tasks:
```bash
python cli.py list -p 3
python cli.py list -p 4
```

### Find Overdue Tasks

See tasks that are past their due date:

```bash
python cli.py list --overdue
```

Shorthand:
```bash
python cli.py list -o
```

**Tip:** Run this regularly to stay on top of deadlines!

### Combine Filters

Find overdue, high-priority tasks:

```bash
python cli.py list --overdue --priority 3
```

Find tasks in progress that are high priority:

```bash
python cli.py list --status in_progress --priority 4
```

---

## Using Advanced Features

### Natural Language Task Parsing

Instead of typing multiple flags, embed task properties directly in the text:

**Format:**
```
Task description @tag1 @tag2 !priority #due-date
```

**Examples:**

Simple priority and tag:
```bash
python cli.py create "Call dentist @health !2"
```

Multiple tags and high priority:
```bash
python cli.py create "Prepare presentation @project @work !high"
```

Priority by name (instead of number):
```bash
python cli.py create "Emergency server maintenance @devops !urgent"
```

Date parsing (relative dates):
```bash
python cli.py create "Submit report @work !3 #friday"
```

**Priority name reference:**
- `!1` or `!low`
- `!2` or `!medium`
- `!3` or `!high`
- `!4` or `!urgent`

### Manage Tags

Add a tag to an existing task:

```bash
python cli.py add-tag a1b2c3d4 "deadline-critical"
```

Remove a tag from a task:

```bash
python cli.py remove-tag a1b2c3d4 "old-tag"
```

### View Statistics

See an overview of your tasks:

```bash
python cli.py stats
```

This shows useful information like:
- Total tasks
- Tasks by status
- Tasks by priority
- Overdue task count

### Smart Task Prioritization

TaskManager automatically calculates task importance based on:
- Priority level
- Due date (overdue = highest score)
- Task status
- Special tags (like "critical" or "blocker")
- Recent updates

Use this to see tasks sorted by importance (highest first) when reviewing your workload.

---

## Practical Workflows

### Workflow 1: Daily Standup

Get everything you need to know for your standup meeting:

```bash
# See what you're currently working on
python cli.py list -s in_progress

# Check for overdue items
python cli.py list -o

# See high-priority tasks
python cli.py list -p 4
```

### Workflow 2: Sprint Planning

Create all sprint tasks efficiently:

```bash
# Using natural language parsing (fastest)
python cli.py create "Frontend redesign @frontend !3 #next-week"
python cli.py create "API optimization @backend @performance !3 #next-week"
python cli.py create "Write documentation @docs !2 #next-week"

# For complex tasks, use full options
python cli.py create "User authentication" \
  --description "Implement two-factor authentication" \
  --priority 3 \
  --due "2024-02-28" \
  --tags "security,backend,depends-on-db-migration"
```

### Workflow 3: Task Refinement

Review and refine tasks daily:

```bash
# Check all tasks
python cli.py list

# Find tasks that need attention
python cli.py list -o

# Move a task to in-progress
python cli.py update-status <task-id> in_progress

# Update priority if needed
python cli.py update-priority <task-id> 3
```

### Workflow 4: End-of-Day Review

Mark completed tasks and plan tomorrow:

```bash
# See completed tasks (satisfaction check!)
python cli.py list -s done

# Move finished work to done
python cli.py update-status <task-id> done

# Check what's left
python cli.py list -s todo

# Tomorrow's high-priority items
python cli.py list -p 3
```

### Workflow 5: Emergency Task Management

Responding to urgent issues:

```bash
# Create an emergency task with maximum priority and special tag
python cli.py create "Production database issue" \
  --description "Database connection pool exhausted" \
  --priority 4 \
  --tags "critical,blocker,production"

# Mark it as in progress immediately
python cli.py update-status <task-id> in_progress

# Check its details
python cli.py show <task-id>
```

---

## Troubleshooting

### "Command not found: python cli.py"

**Solution:** Make sure you're in the TaskManager directory:

```bash
cd path/to/task-manager
python cli.py list
```

### "Invalid date format"

**Problem:** Dates must be in `YYYY-MM-DD` format

**Wrong:**
```bash
python cli.py create "Task" --due "Feb 15, 2024"  # ❌
python cli.py create "Task" --due "15-02-2024"    # ❌
```

**Correct:**
```bash
python cli.py create "Task" --due "2024-02-15"    # ✓
```

### "Task not found" or "Invalid task ID"

**Problem:** Task ID was typed incorrectly

**Solution:** Get the correct ID:

```bash
# List all tasks to see their IDs
python cli.py list
```

IDs are shown after the status symbol (the 8-character code).

### Tasks disappeared or "Error loading tasks"

**Problem:** The `tasks.json` file may be corrupted or missing

**Solution:** Check if the file exists:

```bash
ls -la tasks.json
```

If corrupted, you can backup and reset:

```bash
# Backup the old file
mv tasks.json tasks.json.backup

# Next time you run a command, a fresh tasks.json will be created
python cli.py list
```

### "Invalid priority" or "Invalid status"

**Problem:** You used an invalid value

**Valid priorities:** 1, 2, 3, 4 (or: low, medium, high, urgent)

**Valid statuses:** todo, in_progress, review, done

### Permission denied when creating tasks

**Problem:** Directory is write-protected

**Solution:** Ensure you have write permissions in the directory:

```bash
# Check permissions
ls -l

# If needed, make directory writable
chmod u+w .
```

---

## Next Steps

Once you're comfortable with the basics:

1. **Run the tests** to see how the system works internally:
   ```bash
   python -m unittest discover -v tests
   ```

2. **Review the code** to understand the architecture:
   - Start with `models.py` (data structures)
   - Then `task_manager.py` (business logic)
   - Finally `task_parser.py` and `task_priority.py` (advanced features)

3. **Extend the system** by modifying source files to add custom features

4. **Integrate with other tools** using the `TaskStorage` and `TaskManager` classes programmatically

---

## Quick Reference Card

### Create Tasks
```bash
# Basic
python cli.py create "Task title"

# Full details
python cli.py create "Title" -d "Description" -p 3 -u "2024-02-15" -t "tag1,tag2"

# Natural language
python cli.py create "Title @tag1 @tag2 !high #date"
```

### List Tasks
```bash
python cli.py list              # All tasks
python cli.py list -s todo      # By status
python cli.py list -p 3         # By priority
python cli.py list -o           # Overdue only
```

### Update Tasks
```bash
python cli.py update-status <id> done
python cli.py update-priority <id> 3
python cli.py update-due-date <id> "2024-02-15"
python cli.py add-tag <id> "tag"
python cli.py remove-tag <id> "tag"
python cli.py show <id>
```

### Other
```bash
python cli.py stats             # Task statistics
python -m unittest discover -v tests  # Run tests
```

---

## Tips & Tricks

💡 **Tip 1:** Use consistent tag names to make filtering easier
- Good: `@backend`, `@frontend`, `@devops`
- Avoid: `@back`, `@fe`, `@ops` (inconsistent variations)

💡 **Tip 2:** Use status progression wisely
- START: Create with `todo` status
- PROGRESS: Move to `in_progress` when starting
- REVIEW: Use `review` if needs approval
- DONE: Mark complete with `done`

💡 **Tip 3:** Set realistic due dates
- Overdue tasks automatically score highest
- Don't set everything to today's date
- Use dates to reflect actual deadlines

💡 **Tip 4:** Leverage natural language parsing
- Fastest way to create tasks with properties
- Experiment to find your preferred format
- Mix and match `@tags`, `!priority`, `#dates`

💡 **Tip 5:** Run stats regularly
```bash
python cli.py stats
```
Great for understanding your task distribution and bottlenecks

---

**Happy task managing! 🎯**
