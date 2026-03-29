# Task Management System

A comprehensive Python-based task management system with a command-line interface, intelligent task prioritization, and advanced task list synchronization capabilities. This project demonstrates core software engineering practices including data persistence, algorithm design, and test-driven development.

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites & Installation](#prerequisites--installation)
- [Usage](#usage)
- [Key Components](#key-components)
- [Testing](#testing)
- [Development](#development)

## Features

### Core Task Management
- **Create Tasks** with title, description, priority, due dates, and tags
- **Status Tracking** with four states: TODO, IN_PROGRESS, REVIEW, DONE
- **Priority Levels** with four tiers: LOW (1), MEDIUM (2), HIGH (3), URGENT (4)
- **Due Date Management** with automatic overdue detection
- **Tag System** for task categorization and filtering
- **Task History** with creation, update, and completion timestamps

### Advanced Features
- **Intelligent Task Parsing**: Parse free-form text to automatically extract task properties
  - Format: `"Task description @tag1 @tag2 !priority #due-date"`
  - Examples: `"Buy milk @shopping !2 #tomorrow"`, `"Fix bug !urgent #friday @critical"`

- **Smart Task Prioritization**: Calculate importance scores based on:
  - Priority level
  - Due date proximity (overdue, due today, due soon)
  - Task status
  - Special tags (blocker, critical, urgent)
  - Recent updates

- **Task List Synchronization**: Merge local and remote task lists with intelligent conflict resolution:
  - Automatic identification of new tasks
  - Detection of changes across sources
  - Customizable merge strategies
  - Tracking of sync operations

- **JSON Persistence**: Save and load tasks from JSON with full datetime support

### CLI Commands
- Create, list, update, and delete tasks
- Filter tasks by status, priority, or overdue status
- View detailed task information and statistics
- Tag management (add/remove tags)

## Project Structure

```
TaskManager/
├── models.py              # Core data models (Task, TaskStatus, TaskPriority)
├── storage.py             # JSON-based task persistence with custom serialization
├── task_manager.py        # Main TaskManager class with business logic
├── task_parser.py         # Natural language task text parsing
├── task_priority.py       # Task scoring and prioritization algorithms
├── task_list_merge.py     # Task list synchronization and conflict resolution
├── cli.py                 # Command-line interface
├── tests/                 # Comprehensive unit tests
│   ├── test_task_manager.py
│   ├── test_task_parser.py
│   ├── test_task_priority.py
│   └── test_task_list_merge.py
└── README.md              # This file
```

## Key Components

### models.py
Defines the core data structures:
- **Task**: Main task entity with properties like title, description, priority, status, due date, and tags
- **TaskStatus**: Enum for task states (TODO, IN_PROGRESS, REVIEW, DONE)
- **TaskPriority**: Enum for priority levels (LOW, MEDIUM, HIGH, URGENT)

### storage.py
Handles persistent storage with custom JSON serialization:
- **TaskEncoder**: Converts Task objects to JSON-serializable format
- **TaskDecoder**: Reconstructs Task objects from JSON
- **TaskStorage**: Manages CRUD operations and file-based persistence

### task_manager.py
Core business logic orchestrator:
- Create and manage tasks
- Filter tasks by various criteria
- Update task properties
- Track task statistics

### task_parser.py
Natural language processing for task input:
- Parses freeform text to extract task components
- Recognizes priority markers (!1-4, !urgent, !high, etc.)
- Extracts tags marked with @ symbol
- Identifies due dates with # marker

### task_priority.py
Intelligent task scoring and sorting:
- `calculate_task_score()`: Computes importance based on multiple factors
- `sort_tasks_by_importance()`: Orders tasks by calculated priority
- Considers due dates, current status, tags, and update recency

### task_list_merge.py
Synchronization algorithm for merging task lists:
- `merge_task_lists()`: Combines local and remote task lists
- `resolve_task_conflict()`: Intelligent conflict resolution based on timestamps
- Tracks operations needed to sync both sources

## Prerequisites & Installation

### Requirements
- Python 3.11 or higher
- No external dependencies (uses Python standard library only)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd task-manager
```

2. No additional setup required - the project uses only Python standard library modules.

## Usage

### Run the CLI

The CLI provides various commands to manage tasks:

#### 1. Create a new task

```bash
# Basic task
python cli.py create "Buy groceries"

# Full task with all options
python cli.py create "Task Title" \
  --description "Task description" \
  --priority 2 \
  --due "2024-01-31" \
  --tags "tag1,tag2"

# Using shorthand flags
python cli.py create "Fix bug" -d "Critical production bug" -p 4 -u "2024-02-01" -t "critical,urgent"
```

#### 2. List tasks

```bash
# List all tasks
python cli.py list

# List by status (todo, in_progress, review, done)
python cli.py list --status todo
python cli.py list -s in_progress

# List by priority (1=LOW, 2=MEDIUM, 3=HIGH, 4=URGENT)
python cli.py list --priority 3
python cli.py list -p 4

# List only overdue tasks
python cli.py list --overdue
python cli.py list -o
```

#### 3. Update tasks

```bash
# Update task status
python cli.py update-status <task_id> todo
python cli.py update-status <task_id> review
python cli.py update-status <task_id> done

# Update task priority
python cli.py update-priority <task_id> 3

# Update due date
python cli.py update-due-date <task_id> "2024-02-15"
```

#### 4. Manage tags

```bash
# Add a tag to a task
python cli.py add-tag <task_id> "new-tag"

# Remove a tag from a task
python cli.py remove-tag <task_id> "tag-to-remove"
```

#### 5. View task details and statistics

```bash
# Show detailed task information
python cli.py show <task_id>

# Display task statistics
python cli.py stats
```

### Task Display Format

Tasks are displayed with visual indicators:

```
[Status] [ID] - [Priority] [Title]
  [Description]
  [Due Date Info] | [Tags]
  Created: [Timestamp]
```

- **Status symbols**: `[ ]` (TODO), `[>]` (IN_PROGRESS), `[?]` (REVIEW), `[✓]` (DONE)
- **Priority symbols**: `!` (LOW), `!!` (MEDIUM), `!!!` (HIGH), `!!!!` (URGENT)

Example output:
```
[ ] a1b2c3d4 - !! Buy groceries
  Need milk, eggs, and bread
  Due: 2024-02-01 | Tags: shopping, urgent
  Created: 2024-01-15 14:30
```

### Natural Language Task Parsing

Create tasks using natural language with embedded task properties:

```bash
# Format: description @tag @tag !priority #date

# Examples:
python cli.py create "Finish report for client XYZ @project !3 #friday"
python cli.py create "Call dentist @health #tomorrow !2"
python cli.py create "Deploy to production @devops !urgent #today"
```

This avoids the need for multiple flags when properties are inline.

## Testing

Run the comprehensive test suite using Python's unittest framework:

```bash
# Run all tests with verbose output
python -m unittest discover -v tests

# Run specific test file
python -m unittest tests.test_task_manager -v

# Run specific test class
python -m unittest tests.test_task_priority.TestTaskPriority -v

# Run with basic output (less verbose)
python -m unittest discover tests
```

### Test Coverage

The project includes unit tests for:
- **TaskManager**: CRUD operations, filtering, and status management
- **Task Parser**: Text parsing with various formats and edge cases
- **Task Priority**: Score calculation and sorting algorithms
- **Task List Merge**: Synchronization and conflict resolution

## Development

### Project Conventions

- **Task IDs**: UUID-based, automatically generated
- **Date Format**: ISO format (YYYY-MM-DD) for CLI input
- **DateTime Storage**: ISO format strings in JSON, converted to datetime objects at runtime
- **Priority Enum**: Values 1-4 (LOW to URGENT)
- **Status Enum**: String values (todo, in_progress, review, done)

### Storage

Tasks are persisted to `tasks.json` in the working directory. The custom JSON encoder/decoder handles:
- Enum serialization/deserialization
- DateTime object conversion
- Full task state preservation

### Adding New Features

To extend the task manager:

1. **New Task Properties**: Add to `Task.__init__()` in models.py
2. **New CLI Commands**: Add subparser in cli.py's `main()` function
3. **New Filtering**: Add method to TaskStorage in storage.py
4. **New Algorithms**: Add to task_priority.py or task_list_merge.py

### Code Organization

- `models.py`: Data structures only (no business logic)
- `storage.py`: Persistence layer
- `task_manager.py`: Business logic and orchestration
- `cli.py`: User interface
- Utility modules: task_parser.py, task_priority.py, task_list_merge.py
