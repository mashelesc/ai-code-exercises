"""
sales_report.py — refactored for single responsibility.

Public API
----------
generate_sales_report(...)   Thin orchestrator; delegates to the helpers below.

Extracted helpers (each testable in isolation)
-----------------------------------------------
validate_report_params(...)  Guard clauses only — raises ValueError on bad input.
filter_sales_data(...)       Pure filter — returns a subset list, no side-effects.
aggregate_sales(...)         Computes all metrics; returns a metrics dict.
build_report_data(...)       Assembles the output structure from pre-computed metrics.
build_chart_data(...)        Constructs chart-ready label/data arrays.
render_report(...)           Format dispatch only — calls the appropriate serialiser.
"""

from datetime import datetime


# ---------------------------------------------------------------------------
# 1. Validation
# ---------------------------------------------------------------------------

def validate_report_params(sales_data, report_type, date_range, output_format):
    """
    Validate all top-level parameters.

    Raises ValueError with a descriptive message if anything is wrong.
    Returns nothing — callers check by catching (or not) the exception.
    """
    if not sales_data or not isinstance(sales_data, list):
        raise ValueError("sales_data must be a non-empty list.")

    if report_type not in {"summary", "detailed", "forecast"}:
        raise ValueError(
            f"report_type must be 'summary', 'detailed', or 'forecast'; got {report_type!r}."
        )

    if output_format not in {"pdf", "excel", "html", "json"}:
        raise ValueError(
            f"output_format must be 'pdf', 'excel', 'html', or 'json'; got {output_format!r}."
        )

    if date_range is not None:
        if "start" not in date_range or "end" not in date_range:
            raise ValueError("date_range must contain both 'start' and 'end' keys.")

        start = datetime.strptime(date_range["start"], "%Y-%m-%d")
        end   = datetime.strptime(date_range["end"],   "%Y-%m-%d")

        if start > end:
            raise ValueError(
                f"date_range start ({date_range['start']}) must not be after "
                f"end ({date_range['end']})."
            )


# ---------------------------------------------------------------------------
# 2. Filtering
# ---------------------------------------------------------------------------

def filter_sales_data(sales_data, date_range=None, filters=None):
    """
    Return the subset of sales_data that satisfies date_range and filters.

    Pure function — does not mutate the input list.

    Parameters
    ----------
    sales_data  : list[dict]
    date_range  : dict with 'start' and 'end' date strings (YYYY-MM-DD), or None.
    filters     : dict mapping field names to a value or list of values, or None.

    Returns
    -------
    list[dict]  Filtered records (may be empty).
    """
    result = list(sales_data)

    if date_range:
        start = datetime.strptime(date_range["start"], "%Y-%m-%d")
        end   = datetime.strptime(date_range["end"],   "%Y-%m-%d")
        result = [
            sale for sale in result
            if start <= datetime.strptime(sale["date"], "%Y-%m-%d") <= end
        ]

    if filters:
        for key, value in filters.items():
            allowed = set(value) if isinstance(value, list) else {value}
            result = [sale for sale in result if sale.get(key) in allowed]

    return result


# ---------------------------------------------------------------------------
# 3. Aggregation
# ---------------------------------------------------------------------------

def aggregate_sales(sales_data, grouping=None, report_type="summary"):
    """
    Compute all numeric metrics from a (pre-filtered) list of sales records.

    Parameters
    ----------
    sales_data  : list[dict]  Non-empty list of sales records.
    grouping    : str | None  Field name to group by ('product', 'region', …).
    report_type : str         Drives whether forecast projections are computed.

    Returns
    -------
    dict with keys:
        total_sales, transaction_count, average_sale, max_sale, min_sale
        grouped   (dict, present when grouping is not None)
        forecast  (dict, present when report_type == 'forecast')
    """
    total_sales       = sum(sale["amount"] for sale in sales_data)
    transaction_count = len(sales_data)
    average_sale      = total_sales / transaction_count
    max_sale          = max(sales_data, key=lambda s: s["amount"])
    min_sale          = min(sales_data, key=lambda s: s["amount"])

    metrics = {
        "total_sales":       total_sales,
        "transaction_count": transaction_count,
        "average_sale":      average_sale,
        "max_sale":          max_sale,
        "min_sale":          min_sale,
    }

    if grouping:
        metrics["grouped"] = _compute_groups(sales_data, grouping, total_sales)

    if report_type == "forecast":
        metrics["forecast"] = _compute_forecast(sales_data)

    return metrics


def _compute_groups(sales_data, grouping, total_sales):
    """Group sales by a field and compute per-group statistics."""
    groups = {}
    for sale in sales_data:
        key = sale.get(grouping, "Unknown")
        if key not in groups:
            groups[key] = {"count": 0, "total": 0.0}
        groups[key]["count"] += 1
        groups[key]["total"] += sale["amount"]

    return {
        key: {
            "count":      data["count"],
            "total":      data["total"],
            "average":    data["total"] / data["count"],
            "percentage": (data["total"] / total_sales) * 100,
        }
        for key, data in groups.items()
    }


def _compute_forecast(sales_data):
    """Derive monthly growth trend and project the next three months."""
    monthly_sales = {}
    for sale in sales_data:
        sale_date = datetime.strptime(sale["date"], "%Y-%m-%d")
        month_key = f"{sale_date.year}-{sale_date.month:02d}"
        monthly_sales[month_key] = monthly_sales.get(month_key, 0) + sale["amount"]

    sorted_months = sorted(monthly_sales)
    growth_rates = [
        ((monthly_sales[sorted_months[i]] - monthly_sales[sorted_months[i - 1]])
         / monthly_sales[sorted_months[i - 1]]) * 100
        for i in range(1, len(sorted_months))
        if monthly_sales[sorted_months[i - 1]] > 0
    ]
    avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0

    projected_sales = {}
    if sorted_months:
        year, month    = map(int, sorted_months[-1].split("-"))
        last_amount    = monthly_sales[sorted_months[-1]]
        for _ in range(3):
            month += 1
            if month > 12:
                month, year = 1, year + 1
            forecast_key         = f"{year}-{month:02d}"
            last_amount          = last_amount * (1 + avg_growth_rate / 100)
            projected_sales[forecast_key] = last_amount

    return {
        "monthly_sales":     monthly_sales,
        "growth_rates":      {
            sorted_months[i]: growth_rates[i - 1]
            for i in range(1, len(sorted_months))
        },
        "average_growth_rate": avg_growth_rate,
        "projected_sales":   projected_sales,
    }


# ---------------------------------------------------------------------------
# 4. Report structure building
# ---------------------------------------------------------------------------

def build_report_data(sales_data, metrics, report_type, date_range, filters, grouping):
    """
    Assemble the report output dictionary from pre-computed metrics.

    Does not perform any calculations — purely structural.

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
    dict  Report data structure ready for rendering or serialisation.
    """
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

    if grouping and "grouped" in metrics:
        report["grouping"] = {"by": grouping, "groups": metrics["grouped"]}

    if report_type == "detailed":
        report["transactions"] = _enrich_transactions(sales_data)

    if report_type == "forecast" and "forecast" in metrics:
        report["forecast"] = metrics["forecast"]

    return report


def _enrich_transactions(sales_data):
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
# 5. Chart data preparation
# ---------------------------------------------------------------------------

def build_chart_data(sales_data, grouping=None):
    """
    Build chart-ready data structures from a filtered list of sales records.

    Independent of report type and output format — the same arrays are used
    whether the report is rendered as HTML, PDF, or JSON.

    Parameters
    ----------
    sales_data : list[dict]
    grouping   : str | None  When provided, adds a breakdown pie chart.

    Returns
    -------
    dict  Keys are chart names; values are dicts with 'labels' and 'data'.
    """
    charts = {}

    # Time-series: daily totals
    date_totals = {}
    for sale in sales_data:
        date_totals[sale["date"]] = date_totals.get(sale["date"], 0) + sale["amount"]

    charts["sales_over_time"] = {
        "labels": sorted(date_totals),
        "data":   [date_totals[d] for d in sorted(date_totals)],
    }

    # Breakdown pie chart (only when a grouping dimension is present)
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
# 6. Rendering / serialisation dispatch
# ---------------------------------------------------------------------------

def render_report(report_data, output_format, charts_data=None):
    """
    Dispatch the assembled report data to the appropriate serialiser.

    Responsible only for routing — no metrics, no structure building.

    Parameters
    ----------
    report_data   : dict         Output of build_report_data().
    output_format : str          'pdf' | 'excel' | 'html' | 'json'
    charts_data   : dict | None  Output of build_chart_data(), when charts requested.

    Returns
    -------
    The return value of the chosen serialiser (file path, bytes, or dict).
    """
    if charts_data:
        report_data = {**report_data, "charts": charts_data}

    serialisers = {
        "json":  lambda d: d,                          # already a dict
        "html":  _generate_html_report,
        "excel": _generate_excel_report,
        "pdf":   _generate_pdf_report,
    }

    return serialisers[output_format](report_data)


# ---------------------------------------------------------------------------
# Thin orchestrator
# ---------------------------------------------------------------------------

def generate_sales_report(
    sales_data,
    report_type="summary",
    date_range=None,
    filters=None,
    grouping=None,
    include_charts=False,
    output_format="pdf",
):
    """
    Generate a comprehensive sales report.

    Orchestrates the six single-responsibility helpers; contains no logic
    of its own beyond sequencing and the empty-data early-return.

    Parameters
    ----------
    sales_data     : list[dict]   Sales transaction records.
    report_type    : str          'summary' | 'detailed' | 'forecast'
    date_range     : dict | None  {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
    filters        : dict | None  {field: value} or {field: [value, …]}
    grouping       : str  | None  Field to group by ('product', 'region', …)
    include_charts : bool         Whether to build chart data.
    output_format  : str          'pdf' | 'excel' | 'html' | 'json'

    Returns
    -------
    Report data (dict) or file path (str), depending on output_format.
    """
    # 1. Validate — raises immediately on bad input
    validate_report_params(sales_data, report_type, date_range, output_format)

    # 2. Filter
    filtered = filter_sales_data(sales_data, date_range, filters)

    if not filtered:
        print("Warning: no data matches the specified criteria.")
        if output_format == "json":
            return {"message": "No data matches the specified criteria.", "data": []}
        return _generate_empty_report(report_type, output_format)

    # 3. Aggregate
    metrics = aggregate_sales(filtered, grouping=grouping, report_type=report_type)

    # 4. Build report structure
    report_data = build_report_data(
        filtered, metrics, report_type, date_range, filters, grouping
    )

    # 5. Build chart data (optional)
    charts_data = build_chart_data(filtered, grouping=grouping) if include_charts else None

    # 6. Render
    return render_report(report_data, output_format, charts_data)


# ---------------------------------------------------------------------------
# Serialiser stubs (implementations unchanged from original)
# ---------------------------------------------------------------------------

def _generate_empty_report(report_type, output_format):
    pass

def _generate_html_report(report_data):
    pass

def _generate_excel_report(report_data):
    pass

def _generate_pdf_report(report_data):
    pass