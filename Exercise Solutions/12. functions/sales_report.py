"""
sales_report.py

Refactored sales report module.  The public entry point is
generate_sales_report(); all logic lives in single-responsibility helpers.

Helper call chain
-----------------
generate_sales_report()
  ├── validate_report_params()
  ├── filter_sales_data()
  ├── aggregate_sales()
  │     ├── _compute_groups()          (when grouping is set)
  │     └── _compute_forecast()        (when report_type == 'forecast')
  ├── build_report_data()
  │     └── _enrich_transactions()     (when report_type == 'detailed')
  ├── build_chart_data()               (when include_charts is True)
  └── render_report()
        └── _SERIALISERS[format](data)
"""

from datetime import datetime

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

VALID_REPORT_TYPES   = {"summary", "detailed", "forecast"}
VALID_OUTPUT_FORMATS = {"pdf", "excel", "html", "json"}


# ---------------------------------------------------------------------------
# Internal date helper
# ---------------------------------------------------------------------------

def _parse_date(date_str: str) -> datetime:
    """Parse a YYYY-MM-DD string to datetime. Single definition, used everywhere."""
    return datetime.strptime(date_str, "%Y-%m-%d")


# ---------------------------------------------------------------------------
# 1. validate_report_params
# ---------------------------------------------------------------------------

def validate_report_params(
    sales_data,
    report_type: str,
    date_range: dict | None,
    output_format: str,
) -> None:
    """
    Validate all top-level parameters.

    Raises ValueError immediately on the first invalid argument.
    Returns None on success — callers need not inspect a return value.
    """
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
                f"date_range start ({date_range['start']}) must not be "
                f"after end ({date_range['end']})."
            )


# ---------------------------------------------------------------------------
# 2. filter_sales_data
# ---------------------------------------------------------------------------

def filter_sales_data(
    sales_data: list,
    date_range: dict | None = None,
    filters: dict | None = None,
) -> list:
    """
    Return the subset of sales_data that satisfies date_range and filters.

    Pure function — the input list is never mutated.

    Parameters
    ----------
    sales_data : list[dict]   Full list of sale records.
    date_range : dict | None  {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
    filters    : dict | None  {field: value} or {field: [value, ...]}

    Returns
    -------
    list[dict]  Matching records (may be empty).
    """
    result = list(sales_data)

    if date_range:
        start  = _parse_date(date_range["start"])
        end    = _parse_date(date_range["end"])
        result = [s for s in result if start <= _parse_date(s["date"]) <= end]

    if filters:
        for key, value in filters.items():
            # Wrap scalar in a set so both single-value and multi-value
            # filters share one comprehension branch.
            allowed = set(value) if isinstance(value, list) else {value}
            result  = [s for s in result if s.get(key) in allowed]

    return result


# ---------------------------------------------------------------------------
# 3. aggregate_sales  (+ private helpers)
# ---------------------------------------------------------------------------

def aggregate_sales(
    sales_data: list,
    grouping: str | None = None,
    report_type: str = "summary",
) -> dict:
    """
    Compute all numeric metrics from a pre-filtered list of sale records.

    Parameters
    ----------
    sales_data  : list[dict]  Non-empty; assumed already filtered.
    grouping    : str | None  Field name to group by.
    report_type : str         Drives optional forecast computation.

    Returns
    -------
    dict  Keys: total_sales, transaction_count, average_sale, max_sale,
          min_sale, and optionally 'grouped' and 'forecast'.
    """
    total = sum(s["amount"] for s in sales_data)
    count = len(sales_data)

    metrics: dict = {
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


def _compute_groups(sales_data: list, grouping: str, total_sales: float) -> dict:
    """Group records by a field; compute per-group count, total, average, %."""
    groups: dict = {}
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


def _compute_forecast(sales_data: list) -> dict:
    """
    Derive a monthly growth trend from historical data and project
    the next three months.

    Uses a list comprehension (not an accumulator loop) for growth rates
    and divmod for clean month/year rollover.
    """
    # Accumulate monthly totals
    monthly_sales: dict = {}
    for sale in sales_data:
        d   = _parse_date(sale["date"])
        key = f"{d.year}-{d.month:02d}"
        monthly_sales[key] = monthly_sales.get(key, 0) + sale["amount"]

    sorted_months = sorted(monthly_sales)

    # Growth rates as a filtered comprehension; guard on zero avoids ZeroDivisionError
    growth_rates = [
        ((monthly_sales[sorted_months[i]] - monthly_sales[sorted_months[i - 1]])
         / monthly_sales[sorted_months[i - 1]]) * 100
        for i in range(1, len(sorted_months))
        if monthly_sales[sorted_months[i - 1]] > 0
    ]

    avg_growth = (sum(growth_rates) / len(growth_rates)) if growth_rates else 0.0

    # Project next 3 months; divmod handles Dec→Jan rollover without branching
    projected: dict = {}
    if sorted_months:
        year, month  = map(int, sorted_months[-1].split("-"))
        last_amount  = monthly_sales[sorted_months[-1]]
        for _ in range(3):
            month += 1
            month_carry, month = divmod(month, 13)  # 13 → (1, 0); Jan of next year
            if month == 0:
                month  = 1
                year  += 1
            elif month_carry:
                year  += month_carry
            last_amount = last_amount * (1 + avg_growth / 100)
            projected[f"{year}-{month:02d}"] = last_amount

    return {
        "monthly_sales":      monthly_sales,
        "growth_rates":       {
            sorted_months[i]: growth_rates[i - 1]
            for i in range(1, len(sorted_months))
        },
        "average_growth_rate": avg_growth,
        "projected_sales":    projected,
    }


# ---------------------------------------------------------------------------
# 4. build_report_data  (+ private helper)
# ---------------------------------------------------------------------------

def build_report_data(
    sales_data: list,
    metrics: dict,
    report_type: str,
    date_range: dict | None,
    filters: dict | None,
    grouping: str | None,
) -> dict:
    """
    Assemble the report output dictionary from pre-computed metrics.

    Purely structural — no calculations performed here.

    Parameters
    ----------
    sales_data  : list[dict]  Filtered records (used only for detailed txn list).
    metrics     : dict        Output of aggregate_sales().
    report_type : str
    date_range  : dict | None
    filters     : dict | None
    grouping    : str  | None

    Returns
    -------
    dict  Report data structure ready for rendering.
    """
    report: dict = {
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

    # Optional sections expressed as a declarative list; one update loop merges them.
    optional_sections = [
        {"grouping": {"by": grouping, "groups": metrics["grouped"]}}
            if (grouping and "grouped" in metrics) else {},
        {"transactions": _enrich_transactions(sales_data)}
            if report_type == "detailed" else {},
        {"forecast": metrics["forecast"]}
            if (report_type == "forecast" and "forecast" in metrics) else {},
    ]
    for section in optional_sections:
        report.update(section)

    return report


def _enrich_transactions(sales_data: list) -> list:
    """Add derived fields (pre-tax amount, profit, margin) to each transaction."""
    enriched = []
    for sale in sales_data:
        txn = dict(sale)
        if "tax" in sale:
            txn["pre_tax"] = sale["amount"] - sale["tax"]
        if "cost" in sale:
            txn["profit"] = sale["amount"] - sale["cost"]
            txn["margin"] = (txn["profit"] / sale["amount"]) * 100
        enriched.append(txn)
    return enriched


# ---------------------------------------------------------------------------
# 5. build_chart_data
# ---------------------------------------------------------------------------

def build_chart_data(
    sales_data: list,
    grouping: str | None = None,
) -> dict:
    """
    Build chart-ready label/data arrays from a filtered list of sale records.

    Decoupled from report type and output format; the same arrays are used
    whether the final render is HTML, PDF, or JSON.

    Parameters
    ----------
    sales_data : list[dict]
    grouping   : str | None  When set, adds a per-group breakdown chart.

    Returns
    -------
    dict  Keys are chart names; values are {'labels': [...], 'data': [...]}.
    """
    date_totals: dict = {}
    for sale in sales_data:
        date_totals[sale["date"]] = date_totals.get(sale["date"], 0) + sale["amount"]

    charts: dict = {
        "sales_over_time": {
            "labels": sorted(date_totals),
            "data":   [date_totals[d] for d in sorted(date_totals)],
        }
    }

    if grouping:
        group_totals: dict = {}
        for sale in sales_data:
            key = sale.get(grouping, "Unknown")
            group_totals[key] = group_totals.get(key, 0) + sale["amount"]
        charts[f"sales_by_{grouping}"] = {
            "labels": list(group_totals),
            "data":   list(group_totals.values()),
        }

    return charts


# ---------------------------------------------------------------------------
# 6. render_report
# ---------------------------------------------------------------------------

def _identity(x):
    """Pass-through serialiser for JSON — the dict is already the output."""
    return x


def render_report(
    report_data: dict,
    output_format: str,
    charts_data: dict | None = None,
) -> object:
    """
    Dispatch the assembled report data to the appropriate serialiser.

    Responsible only for routing — no metrics, no structure building here.

    Parameters
    ----------
    report_data   : dict         Output of build_report_data().
    output_format : str          'pdf' | 'excel' | 'html' | 'json'
    charts_data   : dict | None  Output of build_chart_data(), if charts requested.

    Returns
    -------
    Return value of the chosen serialiser (file path, bytes, or dict).
    """
    if charts_data:
        report_data = {**report_data, "charts": charts_data}

    _SERIALISERS = {
        "json":  _identity,
        "html":  _generate_html_report,
        "excel": _generate_excel_report,
        "pdf":   _generate_pdf_report,
    }

    return _SERIALISERS[output_format](report_data)


# ---------------------------------------------------------------------------
# Public orchestrator
# ---------------------------------------------------------------------------

def generate_sales_report(
    sales_data: list,
    report_type: str = "summary",
    date_range: dict | None = None,
    filters: dict | None = None,
    grouping: str | None = None,
    include_charts: bool = False,
    output_format: str = "pdf",
) -> object:
    """
    Generate a comprehensive sales report.

    Orchestrates the six single-responsibility helpers in sequence.
    Contains no business logic of its own — only sequencing and the
    empty-data early-return guard.

    Parameters
    ----------
    sales_data     : list[dict]   Sale transaction records.
    report_type    : str          'summary' | 'detailed' | 'forecast'
    date_range     : dict | None  {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
    filters        : dict | None  {field: value} or {field: [value, ...]}
    grouping       : str | None   Field to group by ('product', 'region', ...)
    include_charts : bool         Whether to build chart data arrays.
    output_format  : str          'pdf' | 'excel' | 'html' | 'json'

    Returns
    -------
    dict (json) or file path / bytes depending on output_format.
    """
    # Step 1 — guard: raise immediately on bad input
    validate_report_params(sales_data, report_type, date_range, output_format)

    # Step 2 — narrow the working dataset
    filtered = filter_sales_data(sales_data, date_range, filters)

    if not filtered:
        print("Warning: no data matches the specified criteria.")
        if output_format == "json":
            return {"message": "No data matches the specified criteria.", "data": []}
        return _generate_empty_report(report_type, output_format)

    # Step 3 — compute all metrics
    metrics = aggregate_sales(filtered, grouping=grouping, report_type=report_type)

    # Step 4 — assemble the report structure
    report_data = build_report_data(
        filtered, metrics, report_type, date_range, filters, grouping
    )

    # Step 5 — optionally build chart arrays
    charts_data = build_chart_data(filtered, grouping=grouping) if include_charts else None

    # Step 6 — serialise / render
    return render_report(report_data, output_format, charts_data)


# ---------------------------------------------------------------------------
# Serialiser stubs (implementations out of scope for this module)
# ---------------------------------------------------------------------------

def _generate_empty_report(report_type, output_format):
    pass

def _generate_html_report(report_data):
    pass

def _generate_excel_report(report_data):
    pass

def _generate_pdf_report(report_data):
    pass
