## AI Tool Used: Github Copilot
## Exercise: Algorithm Deconstruction Challenge

## Prompt: Decipher Code with Unclear Intent or Poor Documentation

### **Purpose**
This module converts free-form text input into structured `Task` objects by extracting task metadata using a special syntax.

### **Algorithm Breakdown**

**Regex-Based Text Parsing Strategy:**

The parser sequentially extracts three types of metadata using regex patterns:

#### **1. Priority Extraction** (`\s!([1-4]|urgent|high|medium|low)\b`)
- Searches for `!` followed by either a number (1-4) or a priority word
- Maps: `1/low` → LOW, `2/medium` → MEDIUM, `3/high` → HIGH, `4/urgent` → URGENT
- Removes matched markers from title using `re.sub()`
- **Default:** MEDIUM priority if no marker found

#### **2. Tag Extraction** (`\s@(\w+)`)
- Finds `@` followed by word characters
- Stores matched tags in a list
- Removes markers from title

#### **3. Due Date Extraction** (`\s#(\w+)`)
- Finds `#` followed by word characters
- Converts date references to actual `datetime` objects using logic:
  - **Keywords:** `today`, `tomorrow`, `next_week`
  - **Weekdays:** `monday`, `tuesday`, etc. → calls `get_next_weekday()` to find upcoming occurrence
  - **ISO Format:** Attempts to parse as `YYYY-MM-DD`
- Takes **first match only** (uses `break`)

#### **4. Title Cleanup**
- Removes all extracted markers using regex substitution
- Collapses multiple whitespace to single spaces using `\s+`

**Helper Function: `get_next_weekday()`**
- Calculates future weekday occurrence using weekday arithmetic
- If target weekday already passed this week, adds 7 days
- Returns `datetime` object for that date

### **Example Flow**
```
Input: "Buy milk @shopping !2 #tomorrow"
→ Title: "Buy milk"
→ Priority: MEDIUM (2)
→ Tags: ["shopping"]
→ Due Date: Tomorrow's date
```

### **Documentation Issues**
- ✅ Good: Function docstring explains the special syntax well.
- ❌ Missing: No docstring for `get_next_weekday()`.
- ❌ Missing: No explanation of why `break` is used (stops at first date match).
- ❌ Missing: No mention that order matters—multiple priorities/dates use only the first one found.

## Own Understanding
- This script accepts a string as an input, it then uses regular expressions to performs these 4 tasks in this particular order:
  - **Priority Extraction** - it looks for `!` and then converts the following nonwhitespace character(s) into a priority tag, has a default value of 2.
  - **Tag Extraction** - it looks for `@` and then converts the following nonwhitespace characters into a tag.
  - **Due Date Extraction** - it looks for `#` and then converts the following nonwhitespace characters into a `datetime` object. 
  - **Title Cleanup** - removes all extracted markers using regular expressions.
- Each task relies on regular expressions to extract and validate extracted characters.
  
```
Example text: "create project @python !3 #friday"
→ Title: "create project"
→ Priority: HIGH (3)
→ Tags: ["python"]
→ Due Date: Friday's date
```

## Reflection
- The AI explained the algorithm in a manner that was very easy to understand, I could almost immediately understand the extraction process after it had explained it.
- The AI did not explain how the program deals with invalid dates, and how the program communicates with it's user in the event that the user inputs an invalid date.  
- To ensure that junior developers understand the algorithm, I would add more descriptive comments to the script, that would make the script even more clearer to understand.
- I would add a validator class that would focus on handling invalid inputs, allow multiple dates so that there's a **start date**, **due date**, and a **reminder date** that acts as an alarm, I would also remove case sensitivity from the tags, so that `@W` & `@w` can be treated as the same character.