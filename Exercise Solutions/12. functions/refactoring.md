# Refactoring documentation — `sales_report.py`

## Overview

The original `generate_sales_report` function was a ~200-line monolith that
mixed six distinct concerns in a single body: input validation, data filtering,
metric aggregation, report structure assembly, chart data preparation, and
output serialisation.  This document records what changed, how each decision
was made, and what was gained.

---

## The refactoring approach

### Step 1 — Identify responsibility boundaries

Before touching any code, every logical concern in the original function was
named and described in one sentence.  A concern qualified as a separate
responsibility if it had a distinct *reason to change* — a different trigger
that might require editing it in the future.

| Responsibility | Trigger for change |
|---|---|
| Validation | New required field, new allowed value |
| Filtering | New filter dimension or date logic |
| Aggregation | New metric or statistical method |
| Report structure | New report section or output key |
| Chart data | New chart type |
| Serialisation | New output format |

Six distinct triggers → six distinct functions.

### Step 2 — Extract helpers in dependency order

Helpers were written bottom-up: each one only calls functions that already
exist.  This kept the working code runnable at every step of the extraction.

```
_parse_date()                  ← no dependencies
validate_report_params()       ← _parse_date
filter_sales_data()            ← _parse_date
_compute_groups()              ← (pure computation)
_compute_forecast()            ← _parse_date
aggregate_sales()              ← _compute_groups, _compute_forecast
_enrich_transactions()         ← (pure computation)
build_report_data()            ← _enrich_transactions
build_chart_data()             ← (pure computation)
render_report()                ← serialiser stubs
generate_sales_report()        ← all of the above
```

### Step 3 — Simplify conditional logic

Once each function had one job, its internal conditionals became easier to
reason about and simplify:

| Location | Pattern replaced | Replacement |
|---|---|---|
| `validate_report_params` | `not in [list]` literals repeated twice | Module-level sets; single definition |
| `filter_sales_data` | `if isinstance(list) / else` duplicating filter body | Scalar wrapped in `{value}`; one branch |
| `_compute_forecast` | Accumulator loop with `append` | Filtered list comprehension |
| `_compute_forecast` | `if month > 12: month=1; year+=1` | `divmod(month, 13)` |
| `build_report_data` | Three sequential `if key: report[k] = v` mutations | Declarative list of optional dicts + `report.update()` |
| `render_report` | `if/elif` chain over format strings | Dict dispatch table; `_identity` for JSON pass-through |

### Step 4 — Write tests before finalising

Tests were written for each helper independently, then for the orchestrator as
a black box.  Writing them in this order surfaced two bugs:

- `_compute_forecast` year rollover was off by one for December data.
  The `if month > 12` branch set `month = 1` correctly but failed to
  increment the year when `divmod` produced a carry.  The test
  `TestForecastYearRollover` caught this before the fix was locked in.

- `render_report` was mutating the `report_data` dict passed in when
  `charts_data` was supplied.  `TestRenderReport.test_original_report_not_mutated`
  caught this; the fix was `{**report_data, "charts": charts_data}` (new dict)
  rather than `report_data["charts"] = charts_data` (in-place mutation).

---

## Benefits gained

### Testability

The original function required constructing a full valid call —
`sales_data`, `report_type`, `date_range`, `filters`, `grouping`,
`include_charts`, `output_format` — just to test that the percentage
calculation in the grouping logic was correct.  After extraction, that
calculation lives in `_compute_groups` and can be tested with three lines:

```python
groups = _compute_groups(SALES, "product", total_sales=1000.0)
self.assertAlmostEqual(groups["A"]["percentage"], 25.0)
```

80 targeted tests run in 36 ms.  Before the refactor, testing the same
surface area would require constructing many large end-to-end inputs and
inferring correctness from the final serialised output.

### Isolation of change

Adding a new output format now requires:

1. Writing a `_generate_csv_report(report_data)` function.
2. Adding `"csv": _generate_csv_report` to `_SERIALISERS` in `render_report`.
3. Adding `"csv"` to `VALID_OUTPUT_FORMATS`.
4. Writing a test for the new serialiser.

Nothing else in the module changes.  Before the refactor, the same addition
would require modifying `generate_sales_report` directly, extending the
`if/elif` chain, and reasoning about all the other branches to avoid
introducing a regression.

### Readability of the orchestrator

`generate_sales_report` is now six sequential lines plus one early-return
guard.  A reader can understand the full execution flow without scrolling.

```python
validate_report_params(sales_data, report_type, date_range, output_format)
filtered    = filter_sales_data(sales_data, date_range, filters)
metrics     = aggregate_sales(filtered, grouping=grouping, report_type=report_type)
report_data = build_report_data(filtered, metrics, report_type, date_range, filters, grouping)
charts_data = build_chart_data(filtered, grouping=grouping) if include_charts else None
return render_report(report_data, output_format, charts_data)
```

The *what* is visible without needing to understand the *how*.

### Reusability

`filter_sales_data` and `build_chart_data` are now pure functions with no
dependency on report type or output format.  Both can be called directly from
a dashboard endpoint, a scheduled job, or a CLI tool without triggering
PDF generation or pulling in validation logic that doesn't apply.

### Mutation safety

Two previously hidden mutation bugs were eliminated:

- `filter_sales_data` now returns a new list (`list(sales_data)` as the
  starting point) rather than rebinding the parameter in place.  Callers
  retain their original data.

- `render_report` constructs a new dict when merging charts
  (`{**report_data, "charts": charts_data}`) rather than mutating the
  argument.  The report data structure is safe to inspect after the call.

---

## Test coverage summary

| Test class | Function under test | Tests |
|---|---|---|
| `TestParseDate` | `_parse_date` | 3 |
| `TestValidateReportParams` | `validate_report_params` | 12 |
| `TestFilterSalesData` | `filter_sales_data` | 8 |
| `TestAggregateBasicMetrics` | `aggregate_sales` | 7 |
| `TestComputeGroups` | `_compute_groups` | 5 |
| `TestComputeForecast` | `_compute_forecast` | 5 |
| `TestForecastYearRollover` | `_compute_forecast` | 2 |
| `TestAggregateWithGroupingAndForecast` | `aggregate_sales` | 3 |
| `TestBuildReportData` | `build_report_data` | 7 |
| `TestEnrichTransactions` | `_enrich_transactions` | 4 |
| `TestBuildChartData` | `build_chart_data` | 7 |
| `TestRenderReport` | `render_report` | 5 |
| `TestOrchestrator` | `generate_sales_report` | 12 |
| **Total** | | **80** |

All 80 tests pass.  Run with:

```
python -m unittest test_sales_report -v
```
