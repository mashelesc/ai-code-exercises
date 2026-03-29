import re
from datetime import datetime, timedelta

from models import TaskStatus, TaskPriority, Task


def parse_task_from_text(text):
    """
    Parse free-form text to extract task properties and create a Task object.

    This function parses unstructured text input to extract task title, priority,
    tags, and due date information. It supports a simple markup syntax that allows
    users to specify task metadata inline with the task title.

    Supported Syntax:
    - Basic text: Task title (everything not matching special syntax)
    - Tags: @tag_name (can have multiple tags)
    - Priority: !N or !name where N is 1-4 or name is urgent/high/medium/low
    - Due date: #date_reference (can have multiple, first valid date is used)

    Args:
        text (str): Free-form task description with optional metadata markers.
                   Should be a non-empty string. Whitespace is trimmed.

    Returns:
        Task: A Task object with the following attributes populated from the input:
            - title (str): Cleaned task title with all markers removed
            - priority (TaskPriority): Parsed priority level (default: MEDIUM)
            - due_date (datetime or None): Parsed due date as datetime object
            - tags (list): List of extracted tag strings (empty list if none found)

    Supported Date References:
        - Relative: "today", "now", "tomorrow", "next_week", "nextweek"
        - Weekday names: "monday", "mon", "tuesday", "tue", "wednesday", "wed",
                         "thursday", "thu", "friday", "fri"
        - ISO format: "YYYY-MM-DD" (e.g., "2026-04-15")

    Priority Mappings:
        - !1 or !low → TaskPriority.LOW
        - !2 or !medium → TaskPriority.MEDIUM (default)
        - !3 or !high → TaskPriority.HIGH
        - !4 or !urgent → TaskPriority.URGENT

    Examples:
        >>> parse_task_from_text("Buy milk @shopping !2 #tomorrow")
        Task with title="Buy milk", priority=MEDIUM, tags=["shopping"],
        due_date=tomorrow

        >>> parse_task_from_text("Finish report for client XYZ !urgent #friday #work @project")
        Task with title="Finish report for client XYZ", priority=URGENT,
        tags=["project"], due_date=next_friday (ignores second #work)

        >>> parse_task_from_text("Call dentist")
        Task with title="Call dentist", priority=MEDIUM (default), tags=[],
        due_date=None

    Notes:
        - Whitespace in the task title is normalized (multiple spaces become one)
        - Multiple due date markers are allowed; the first parseable date is used
        - Tags are case-sensitive and must be alphanumeric (\\w+ pattern)
        - Priority markers are case-insensitive
        - Unrecognized date formats are silently ignored (no error raised)
    """
    # Default task properties
    title = text.strip()
    priority = TaskPriority.MEDIUM
    due_date = None
    tags = []

    # Extract priority markers (!N or !name)
    priority_matches = re.findall(r'\s!([1-4]|urgent|high|medium|low)\b', text, re.IGNORECASE)
    if priority_matches:
        priority_text = priority_matches[0].lower()
        # Remove from title
        title = re.sub(r'\s!([1-4]|urgent|high|medium|low)\b', '', title, flags=re.IGNORECASE)

        # Convert to TaskPriority
        if priority_text == '1' or priority_text == 'low':
            priority = TaskPriority.LOW
        elif priority_text == '2' or priority_text == 'medium':
            priority = TaskPriority.MEDIUM
        elif priority_text == '3' or priority_text == 'high':
            priority = TaskPriority.HIGH
        elif priority_text == '4' or priority_text == 'urgent':
            priority = TaskPriority.URGENT

    # Extract tags (@tag)
    tag_matches = re.findall(r'\s@(\w+)', text)
    if tag_matches:
        tags = tag_matches
        # Remove from title
        for tag in tag_matches:
            title = re.sub(r'\s@' + tag + r'\b', '', title)

    # Extract date markers (#date)
    date_matches = re.findall(r'\s#(\w+)', text)
    if date_matches:
        # Remove from title
        for date_str in date_matches:
            title = re.sub(r'\s#' + date_str + r'\b', '', title)

        # Try to parse date references
        for date_str in date_matches:
            date_str = date_str.lower()
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            if date_str in ('today', 'now'):
                due_date = today
                break
            elif date_str == 'tomorrow':
                due_date = today + timedelta(days=1)
                break
            elif date_str in ('next_week', 'nextweek'):
                due_date = today + timedelta(days=7)
                break
            elif date_str in ('monday', 'mon'):
                due_date = get_next_weekday(today, 0)  # 0 = Monday
                break
            elif date_str in ('tuesday', 'tue'):
                due_date = get_next_weekday(today, 1)
                break
            elif date_str in ('wednesday', 'wed'):
                due_date = get_next_weekday(today, 2)
                break
            elif date_str in ('thursday', 'thu'):
                due_date = get_next_weekday(today, 3)
                break
            elif date_str in ('friday', 'fri'):
                due_date = get_next_weekday(today, 4)
                break
            # Try to parse as YYYY-MM-DD
            try:
                due_date = datetime.strptime(date_str, '%Y-%m-%d')
                break
            except ValueError:
                pass

    # Trim excess whitespace from title
    title = re.sub(r'\s+', ' ', title).strip()

    # Create a new task with the extracted properties
    task = Task(title)
    task.priority = priority
    task.due_date = due_date
    task.tags = tags

    return task

def get_next_weekday(current_date, weekday):
    """
    Calculate the next occurrence of a specific weekday from a given date.

    This helper function is used internally by parse_task_from_text to resolve
    human-readable weekday names (e.g., "friday") into specific dates. It always
    returns a future date—if the target weekday has already occurred this week,
    it advances to the following week.

    Args:
        current_date (datetime): The reference date to calculate from. Should be
                                a datetime object with hour/minute/second normalized
                                to 0 (midnight). Timezone info is preserved.
        weekday (int): ISO weekday number where 0=Monday, 1=Tuesday, ..., 6=Sunday.
                      Must be in the range [0, 6].

    Returns:
        datetime: A datetime object representing midnight on the next occurrence
                 of the specified weekday. If today is the target weekday, returns
                 the same time next week (not today). Maintains the same timezone
                 info as the input date.

    Examples:
        >>> # If today is Monday (weekday 0), get next Friday (weekday 4)
        >>> today = datetime(2026, 3, 30)  # Monday
        >>> get_next_weekday(today, 4)
        datetime(2026, 4, 3)  # Friday

        >>> # If today is Friday and we ask for Friday, get next Friday
        >>> today = datetime(2026, 4, 3)  # Friday
        >>> get_next_weekday(today, 4)
        datetime(2026, 4, 10)  # Next Friday

        >>> # If today is Monday and we ask for Tuesday
        >>> today = datetime(2026, 3, 30)  # Monday
        >>> get_next_weekday(today, 1)
        datetime(2026, 3, 31)  # Tuesday (same week)

    Logic:
        1. Calculate days_ahead = target_weekday - current_weekday
        2. If days_ahead <= 0 (target is today or in the past this week),
           add 7 to advance to next week
        3. Return the new date

    Notes:
        - The function always returns a future date; it never returns the current
          date even if it's the target weekday
        - Requires the current_date to have been normalized to midnight (hour=0,
          minute=0, second=0) for correct results
    """
    days_ahead = weekday - current_date.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return current_date + timedelta(days=days_ahead)
