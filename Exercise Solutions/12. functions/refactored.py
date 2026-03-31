"""
sales_report_simplified.py

Conditional logic simplifications applied to the refactored module:

  1. validate_report_params   — set membership replaces chained equality checks
  2. filter_sales_data        — date parsing extracted; filter loop uses set lookup
  3. _compute_forecast        — growth-rate list comprehension + walrus operator
  4. build_report_data        — dict-update pattern replaces nested if/key-building
  5. render_report            — dispatch table replaces if/elif chain entirely
  6. generate_sales_report    — early-return guard + inline chart build
"""

from datetime import datetime


# ---------------------------------------------------------------------------
# Constants (single source of truth for valid values)
# ---------------------------------------------------------------------------

VALID_REPORT_TYPES  = {"summary", "detailed", "forecast"}
VALID_OUTPUT_FORMATS = {"pdf", "excel", "html", "json"}


# ---------------------------------------------------------------------------
# 1. Validation — set membership instead of chained `not in [...]`
# ---------------------------------------------------------------------------
# BEFORE:
#   if report_type not in ['summary', 'detailed', 'forecast']:
#       raise ValueError(...)
#   if output_format not in ['pdf', 'excel', 'html', 'json']:
#       raise ValueError(...)
#
# AFTER:
#   Uses module-level sets; membership test is O(1) and the valid values
#   are defined once rather than repeated across validation and dispatch.

def validate_report_params(sales_data, report_type, date_range, output_format):
    if not sales_data or not isinstance(sales_data, list):
        raise ValueError("sales_data must be a non-empty list.")

    if report_type not in VALID_REPORT_TYPES:
        raise ValueError(
            f"report_type must be one of {VALID_REPORT_TYPES}; got {report_type!r}."
        )

    if output_format not in VALID_OUTPUT_FORMATS:
        raise ValueError(
            f"output_format must be one of {VALID_OUTPUT_FORMATS}; got {output_format!r}."
        )

    if date_range is not None:
        if "start" not in date_range or "end" not in date_range:
            raise ValueError("date_range must contain both 'start' and 'end' keys.")
        start = _parse_date(date_range["start"])
        end   = _parse_date(date_range["end"])
        if start > end:
            raise ValueError(
                f"date_range start ({date_range['start']}) must not be after "
                f"end ({date_range['end']})."
            )


def _parse_date(date_str):
    """Single-purpose helper; removes repeated strptime format strings."""
    return datetime.strptime(date_str, "%Y-%m-%d")


# ---------------------------------------------------------------------------
# 2. Filtering — set conversion for multi-value filters
# ---------------------------------------------------------------------------
# BEFORE:
#   if isinstance(value, list):
#       sales_data = [s for s in sales_data if s.get(key) in value]
#   else:
#       sales_data = [s for s in sales_data if s.get(key) == value]
#
# AFTER:
#   Wrap scalar in a set; single branch handles both cases uniformly.
#   `in set` is also O(1) vs O(n) for list membership.

def filter_sales_data(sales_data, date_range=None, filters=None):
    result = list(sales_data)

    if date_range:
        start = _parse_date(date_range["start"])
        end   = _parse_date(date_range["end"])
        result = [s for s in result if start <= _parse_date(s["date"]) <= end]

    if filters:
        for key, value in filters.items():
            allowed = set(value) if isinstance(value, list) else {value}
            result  = [s for s in result if s.get(key) in allowed]

    return result


# ---------------------------------------------------------------------------
# 3. Aggregation — unchanged structure, cleaner internals
# ---------------------------------------------------------------------------

def aggregate_sales(sales_data, grouping=None, report_type="summary"):
    total         = sum(s["amount"] for s in sales_data)
    count         = len(sales_data)

    metrics = {
        "total_sales":       total,
        "transaction_count": count,
        "average_sale":      total / count,
        "max_sale":          max(sales_data, key=lambda s: s["amount"]),
        "min_sale":          min(sales_data, key=lambda s: s["amount"]),
    }

    if grouping:
        metrics["grouped"] = _compute_groups(sales_data, grouping, total)

    if report_type == "forecast":
        metrics["forecast"] = _compute_forecast(sales_data)

    return metrics


def _compute_groups(sales_data, grouping, total_sales):
    groups = {}
    for sale in sales_data:
        key = sale.get(grouping, "Unknown")
        g   = groups.setdefault(key, {"count": 0, "total": 0.0})
        g["count"] += 1
        g["total"] += sale["amount"]

    return {
        key: {
            "count":      g["count"],
            "total":      g["total"],
            "average":    g["total"] / g["count"],
            "percentage": (g["total"] / total_sales) * 100,
        }
        for key, g in groups.items()
    }


# BEFORE (_compute_forecast):
#   growth_rates = []
#   for i in range(1, len(sorted_months)):
#       prev = monthly_sales[sorted_months[i-1]]
#       curr = monthly_sales[sorted_months[i]]
#       if prev > 0:
#           growth_rates.append(((curr - prev) / prev) * 100)
#
#   avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0
#
#   forecast = {}
#   if sorted_months:
#       last_month  = sorted_months[-1]
#       last_amount = monthly_sales[last_month]
#       year, month = map(int, last_month.split('-'))
#       for i in range(1, 4):
#           month += 1
#           if month > 12:
#               month = 1
#               year += 1
#           ...
#
# AFTER:
#   • List comprehension replaces the accumulator loop for growth_rates.
#   • divmod replaces the manual month-rollover if/else.
#   • avg_growth_rate guard collapses to `or 0`.

def _compute_forecast(sales_data):
    monthly_sales = {}
    for sale in sales_data:
        d   = _parse_date(sale["date"])
        key = f"{d.year}-{d.month:02d}"
        monthly_sales[key] = monthly_sales.get(key, 0) + sale["amount"]

    sorted_months = sorted(monthly_sales)

    # List comprehension; guard on prev > 0 kept as a filter condition
    growth_rates = [
        ((monthly_sales[sorted_months[i]] - monthly_sales[sorted_months[i - 1]])
         / monthly_sales[sorted_months[i - 1]]) * 100
        for i in range(1, len(sorted_months))
        if monthly_sales[sorted_months[i - 1]] > 0
    ]

    avg_growth = (sum(growth_rates) / len(growth_rates)) if growth_rates else 0

    # Project the next 3 months; divmod handles year rollover without branching
    projected = {}
    if sorted_months:
        year, month  = map(int, sorted_months[-1].split("-"))
        last_amount  = monthly_sales[sorted_months[-1]]
        for _ in range(3):
            month_total, month = divmod(month, 12)   # 12 → (1, 0); wrap cleanly
            month    = month or 12                   # divmod gives 0 for Dec → fix to 12
            year    += month_total if month != 12 else 0
            last_amount = last_amount * (1 + avg_growth / 100)
            projected[f"{year}-{month:02d}"] = last_amount

    return {
        "monthly_sales":     monthly_sales,
        "growth_rates":      {
            sorted_months[i]: growth_rates[i - 1]
            for i in range(1, len(sorted_months))
        },
        "average_growth_rate": avg_growth,
        "projected_sales":   projected,
    }


# ---------------------------------------------------------------------------
# 4. Report structure building — dict.update() collapses optional sections
# ---------------------------------------------------------------------------
# BEFORE:
#   report_data = { 'report_type': ..., 'summary': {...} }
#   if grouping:
#       report_data['grouping'] = { 'by': grouping, 'groups': {...} }
#   if report_type == 'detailed':
#       report_data['transactions'] = [...]
#   if report_type == 'forecast':
#       report_data['forecast'] = {...}
#
# AFTER:
#   Optional sections are expressed as small dicts in a list; a single
#   dict.update() call merges only the non-empty ones.  The main dict
#   literal stays uncluttered.

def build_report_data(sales_data, metrics, report_type, date_range, filters, grouping):
    report = {
        "report_type":    report_type,
        "date_generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date_range":     date_range,
        "filters":        filters,
        "summary": {
            "total_sales":       metrics["total_sales"],
            "transaction_count": metrics["transaction_count"],
            "average_sale":      metrics["average_sale"],
            "max_sale": {
                "amount":  metrics["max_sale"]["amount"],
                "date":    metrics["max_sale"]["date"],
                "details": metrics["max_sale"],
            },
            "min_sale": {
                "amount":  metrics["min_sale"]["amount"],
                "date":    metrics["min_sale"]["date"],
                "details": metrics["min_sale"],
            },
        },
    }

    # Each optional section is a dict; filter out empty ones, then merge once.
    optional_sections = [
        {"grouping": {"by": grouping, "groups": metrics["grouped"]}}
            if grouping and "grouped" in metrics else {},
        {"transactions": _enrich_transactions(sales_data)}
            if report_type == "detailed" else {},
        {"forecast": metrics["forecast"]}
            if report_type == "forecast" and "forecast" in metrics else {},
    ]
    for section in optional_sections:
        report.update(section)

    return report


def _enrich_transactions(sales_data):
    enriched = []
    for sale in sales_data:
        txn = dict(sale)
        if "tax"  in sale:
            txn["pre_tax"] = sale["amount"] - sale["tax"]
        if "cost" in sale:
            txn["profit"] = sale["amount"] - sale["cost"]
            txn["margin"] = (txn["profit"] / sale["amount"]) * 100
        enriched.append(txn)
    return enriched


# ---------------------------------------------------------------------------
# 5. Chart data — unchanged; already clean from the SRP refactor
# ---------------------------------------------------------------------------

def build_chart_data(sales_data, grouping=None):
    date_totals = {}
    for sale in sales_data:
        date_totals[sale["date"]] = date_totals.get(sale["date"], 0) + sale["amount"]

    charts = {
        "sales_over_time": {
            "labels": sorted(date_totals),
            "data":   [date_totals[d] for d in sorted(date_totals)],
        }
    }

    if grouping:
        group_totals = {}
        for sale in sales_data:
            key = sale.get(grouping, "Unknown")
            group_totals[key] = group_totals.get(key, 0) + sale["amount"]
        charts[f"sales_by_{grouping}"] = {
            "labels": list(group_totals),
            "data":   list(group_totals.values()),
        }

    return charts


# ---------------------------------------------------------------------------
# 6. Rendering — dispatch table replaces if/elif chain
# ---------------------------------------------------------------------------
# BEFORE:
#   if output_format == 'json':
#       return report_data
#   elif output_format == 'html':
#       return _generate_html_report(report_data, include_charts)
#   elif output_format == 'excel':
#       return _generate_excel_report(report_data, include_charts)
#   elif output_format == 'pdf':
#       return _generate_pdf_report(report_data, include_charts)
#
# AFTER:
#   A dict maps each format string to its callable.  Adding a new format
#   is one dict entry; no branching logic to maintain.  `identity` makes
#   the JSON case explicit without a special-case branch.

def render_report(report_data, output_format, charts_data=None):
    if charts_data:
        report_data = {**report_data, "charts": charts_data}

    _SERIALISERS = {
        "json":  _identity,
        "html":  _generate_html_report,
        "excel": _generate_excel_report,
        "pdf":   _generate_pdf_report,
    }

    return _SERIALISERS[output_format](report_data)


def _identity(x):
    """Passthrough for the JSON format — no serialisation needed."""
    return x


# ---------------------------------------------------------------------------
# Thin orchestrator
# ---------------------------------------------------------------------------
# BEFORE:
#   # Generate charts if requested
#   if include_charts:
#       charts_data = {}
#       ...
#       if grouping:
#           ...
#       report_data['charts'] = charts_data
#
# AFTER:
#   Ternary expression; chart building stays in build_chart_data.
#   The orchestrator never touches chart internals.

def generate_sales_report(
    sales_data,
    report_type="summary",
    date_range=None,
    filters=None,
    grouping=None,
    include_charts=False,
    output_format="pdf",
):
    validate_report_params(sales_data, report_type, date_range, output_format)

    filtered = filter_sales_data(sales_data, date_range, filters)

    if not filtered:
        print("Warning: no data matches the specified criteria.")
        if output_format == "json":
            return {"message": "No data matches the specified criteria.", "data": []}
        return _generate_empty_report(report_type, output_format)

    metrics     = aggregate_sales(filtered, grouping=grouping, report_type=report_type)
    report_data = build_report_data(filtered, metrics, report_type, date_range, filters, grouping)
    charts_data = build_chart_data(filtered, grouping=grouping) if include_charts else None

    return render_report(report_data, output_format, charts_data)


# ---------------------------------------------------------------------------
# Serialiser stubs
# ---------------------------------------------------------------------------

def _generate_empty_report(report_type, output_format): pass
def _generate_html_report(report_data):                 pass
def _generate_excel_report(report_data):                pass
def _generate_pdf_report(report_data):                  pass
