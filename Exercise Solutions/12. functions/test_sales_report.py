"""
test_sales_report.py

Behaviour-preservation tests for the refactored sales_report module.

Structure
---------
Each helper function has its own TestCase class so failures are pinpointed
immediately.  The final class (TestOrchestrator) exercises generate_sales_report
end-to-end to prove the helpers compose correctly.

Run with:
    python -m unittest test_sales_report -v
"""

import unittest
from datetime import datetime
from sales_report import (
    validate_report_params,
    filter_sales_data,
    aggregate_sales,
    build_report_data,
    build_chart_data,
    render_report,
    generate_sales_report,
    _parse_date,
    _compute_groups,
    _compute_forecast,
    _enrich_transactions,
    _identity,
    VALID_REPORT_TYPES,
    VALID_OUTPUT_FORMATS,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def make_sales(*overrides):
    """Return a minimal list of sale dicts, with optional per-item overrides."""
    base = [
        {"date": "2024-01-15", "amount": 100.0, "product": "A", "region": "North"},
        {"date": "2024-01-20", "amount": 200.0, "product": "B", "region": "South"},
        {"date": "2024-02-05", "amount": 150.0, "product": "A", "region": "North"},
        {"date": "2024-02-18", "amount": 300.0, "product": "C", "region": "East"},
        {"date": "2024-03-10", "amount": 250.0, "product": "B", "region": "South"},
    ]
    for i, patch in enumerate(overrides):
        base[i].update(patch)
    return base


SALES = make_sales()


# ---------------------------------------------------------------------------
# 1. _parse_date
# ---------------------------------------------------------------------------

class TestParseDate(unittest.TestCase):

    def test_returns_datetime(self):
        result = _parse_date("2024-06-15")
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year,  2024)
        self.assertEqual(result.month,    6)
        self.assertEqual(result.day,     15)

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            _parse_date("15-06-2024")

    def test_invalid_date_raises(self):
        with self.assertRaises(ValueError):
            _parse_date("2024-13-01")


# ---------------------------------------------------------------------------
# 2. validate_report_params
# ---------------------------------------------------------------------------

class TestValidateReportParams(unittest.TestCase):

    def _ok(self, **kwargs):
        """Call validate with sensible defaults, overriding only what's specified."""
        defaults = dict(
            sales_data=SALES,
            report_type="summary",
            date_range=None,
            output_format="json",
        )
        defaults.update(kwargs)
        validate_report_params(**defaults)  # should not raise

    # --- sales_data ---
    def test_empty_list_raises(self):
        with self.assertRaises(ValueError):
            validate_report_params([], "summary", None, "json")

    def test_none_raises(self):
        with self.assertRaises(ValueError):
            validate_report_params(None, "summary", None, "json")

    def test_non_list_raises(self):
        with self.assertRaises(ValueError):
            validate_report_params("not a list", "summary", None, "json")

    # --- report_type ---
    def test_all_valid_report_types_pass(self):
        for rt in VALID_REPORT_TYPES:
            self._ok(report_type=rt)

    def test_invalid_report_type_raises(self):
        with self.assertRaises(ValueError):
            self._ok(report_type="annual")

    # --- output_format ---
    def test_all_valid_output_formats_pass(self):
        for fmt in VALID_OUTPUT_FORMATS:
            self._ok(output_format=fmt)

    def test_invalid_output_format_raises(self):
        with self.assertRaises(ValueError):
            self._ok(output_format="csv")

    # --- date_range ---
    def test_valid_date_range_passes(self):
        self._ok(date_range={"start": "2024-01-01", "end": "2024-12-31"})

    def test_date_range_missing_start_raises(self):
        with self.assertRaises(ValueError):
            self._ok(date_range={"end": "2024-12-31"})

    def test_date_range_missing_end_raises(self):
        with self.assertRaises(ValueError):
            self._ok(date_range={"start": "2024-01-01"})

    def test_start_after_end_raises(self):
        with self.assertRaises(ValueError):
            self._ok(date_range={"start": "2024-12-31", "end": "2024-01-01"})

    def test_same_start_and_end_passes(self):
        self._ok(date_range={"start": "2024-06-01", "end": "2024-06-01"})


# ---------------------------------------------------------------------------
# 3. filter_sales_data
# ---------------------------------------------------------------------------

class TestFilterSalesData(unittest.TestCase):

    def test_no_filters_returns_all(self):
        result = filter_sales_data(SALES)
        self.assertEqual(len(result), len(SALES))

    def test_does_not_mutate_input(self):
        original = list(SALES)
        filter_sales_data(SALES, filters={"product": "A"})
        self.assertEqual(SALES, original)

    def test_date_range_inclusive(self):
        dr = {"start": "2024-01-15", "end": "2024-01-20"}
        result = filter_sales_data(SALES, date_range=dr)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(s["date"] in ("2024-01-15", "2024-01-20") for s in result))

    def test_date_range_exclusive_boundaries(self):
        dr = {"start": "2024-01-16", "end": "2024-01-19"}
        result = filter_sales_data(SALES, date_range=dr)
        self.assertEqual(len(result), 0)

    def test_scalar_filter(self):
        result = filter_sales_data(SALES, filters={"product": "A"})
        self.assertEqual(len(result), 2)
        self.assertTrue(all(s["product"] == "A" for s in result))

    def test_list_filter(self):
        result = filter_sales_data(SALES, filters={"product": ["A", "B"]})
        self.assertEqual(len(result), 4)

    def test_combined_date_and_filters(self):
        dr = {"start": "2024-01-01", "end": "2024-01-31"}
        result = filter_sales_data(SALES, date_range=dr, filters={"product": "A"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], "2024-01-15")

    def test_no_match_returns_empty(self):
        result = filter_sales_data(SALES, filters={"product": "Z"})
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# 4. aggregate_sales  &  private helpers
# ---------------------------------------------------------------------------

class TestAggregateBasicMetrics(unittest.TestCase):

    def setUp(self):
        self.metrics = aggregate_sales(SALES)

    def test_total_sales(self):
        self.assertAlmostEqual(self.metrics["total_sales"], 1000.0)

    def test_transaction_count(self):
        self.assertEqual(self.metrics["transaction_count"], 5)

    def test_average_sale(self):
        self.assertAlmostEqual(self.metrics["average_sale"], 200.0)

    def test_max_sale(self):
        self.assertEqual(self.metrics["max_sale"]["amount"], 300.0)
        self.assertEqual(self.metrics["max_sale"]["date"],  "2024-02-18")

    def test_min_sale(self):
        self.assertEqual(self.metrics["min_sale"]["amount"], 100.0)
        self.assertEqual(self.metrics["min_sale"]["date"],  "2024-01-15")

    def test_no_grouping_key_absent(self):
        self.assertNotIn("grouped", self.metrics)

    def test_no_forecast_key_absent(self):
        self.assertNotIn("forecast", self.metrics)


class TestComputeGroups(unittest.TestCase):

    def setUp(self):
        self.groups = _compute_groups(SALES, "product", total_sales=1000.0)

    def test_all_products_present(self):
        self.assertIn("A", self.groups)
        self.assertIn("B", self.groups)
        self.assertIn("C", self.groups)

    def test_product_A_total(self):
        self.assertAlmostEqual(self.groups["A"]["total"], 250.0)

    def test_product_B_total(self):
        self.assertAlmostEqual(self.groups["B"]["total"], 450.0)

    def test_product_A_average(self):
        self.assertAlmostEqual(self.groups["A"]["average"], 125.0)

    def test_percentages_sum_to_100(self):
        total_pct = sum(g["percentage"] for g in self.groups.values())
        self.assertAlmostEqual(total_pct, 100.0)


class TestComputeForecast(unittest.TestCase):

    def setUp(self):
        self.forecast = _compute_forecast(SALES)

    def test_monthly_sales_keys_are_present(self):
        self.assertIn("2024-01", self.forecast["monthly_sales"])
        self.assertIn("2024-02", self.forecast["monthly_sales"])
        self.assertIn("2024-03", self.forecast["monthly_sales"])

    def test_monthly_totals_correct(self):
        ms = self.forecast["monthly_sales"]
        self.assertAlmostEqual(ms["2024-01"], 300.0)   # 100 + 200
        self.assertAlmostEqual(ms["2024-02"], 450.0)   # 150 + 300
        self.assertAlmostEqual(ms["2024-03"], 250.0)

    def test_projected_sales_has_three_entries(self):
        self.assertEqual(len(self.forecast["projected_sales"]), 3)

    def test_projected_keys_follow_chronologically(self):
        keys = sorted(self.forecast["projected_sales"])
        self.assertEqual(keys, ["2024-04", "2024-05", "2024-06"])

    def test_average_growth_rate_is_float(self):
        self.assertIsInstance(self.forecast["average_growth_rate"], float)


class TestForecastYearRollover(unittest.TestCase):
    """Verify December → January rollover in projections."""

    def setUp(self):
        data = [
            {"date": "2024-10-01", "amount": 100.0},
            {"date": "2024-11-01", "amount": 110.0},
            {"date": "2024-12-01", "amount": 120.0},
        ]
        self.forecast = _compute_forecast(data)

    def test_first_projected_month_is_january(self):
        keys = sorted(self.forecast["projected_sales"])
        self.assertEqual(keys[0], "2025-01")

    def test_second_projected_month_is_february(self):
        keys = sorted(self.forecast["projected_sales"])
        self.assertEqual(keys[1], "2025-02")


class TestAggregateWithGroupingAndForecast(unittest.TestCase):

    def test_grouped_key_present_when_grouping_set(self):
        m = aggregate_sales(SALES, grouping="product")
        self.assertIn("grouped", m)

    def test_forecast_key_present_for_forecast_type(self):
        m = aggregate_sales(SALES, report_type="forecast")
        self.assertIn("forecast", m)

    def test_single_record_gives_zero_growth(self):
        single = [{"date": "2024-01-01", "amount": 500.0}]
        m = aggregate_sales(single, report_type="forecast")
        self.assertAlmostEqual(m["forecast"]["average_growth_rate"], 0.0)


# ---------------------------------------------------------------------------
# 5. build_report_data  &  _enrich_transactions
# ---------------------------------------------------------------------------

class TestBuildReportData(unittest.TestCase):

    def _build(self, report_type="summary", grouping=None):
        metrics = aggregate_sales(SALES, grouping=grouping, report_type=report_type)
        return build_report_data(SALES, metrics, report_type, None, None, grouping)

    def test_summary_keys_present(self):
        r = self._build()
        for key in ("report_type", "date_generated", "summary"):
            self.assertIn(key, r)

    def test_summary_figures_match_aggregate(self):
        r = self._build()
        self.assertAlmostEqual(r["summary"]["total_sales"], 1000.0)
        self.assertEqual(r["summary"]["transaction_count"], 5)

    def test_detailed_has_transactions_key(self):
        r = self._build(report_type="detailed")
        self.assertIn("transactions", r)
        self.assertEqual(len(r["transactions"]), 5)

    def test_summary_has_no_transactions_key(self):
        r = self._build(report_type="summary")
        self.assertNotIn("transactions", r)

    def test_forecast_has_forecast_key(self):
        r = self._build(report_type="forecast")
        self.assertIn("forecast", r)

    def test_grouping_present_when_supplied(self):
        r = self._build(grouping="product")
        self.assertIn("grouping", r)
        self.assertEqual(r["grouping"]["by"], "product")


class TestEnrichTransactions(unittest.TestCase):

    def test_no_extra_fields_without_tax_or_cost(self):
        result = _enrich_transactions(SALES)
        for txn in result:
            self.assertNotIn("pre_tax", txn)
            self.assertNotIn("profit",  txn)
            self.assertNotIn("margin",  txn)

    def test_pre_tax_computed(self):
        data   = [{"date": "2024-01-01", "amount": 110.0, "tax": 10.0}]
        result = _enrich_transactions(data)
        self.assertAlmostEqual(result[0]["pre_tax"], 100.0)

    def test_profit_and_margin_computed(self):
        data   = [{"date": "2024-01-01", "amount": 200.0, "cost": 120.0}]
        result = _enrich_transactions(data)
        self.assertAlmostEqual(result[0]["profit"],  80.0)
        self.assertAlmostEqual(result[0]["margin"],  40.0)

    def test_original_records_not_mutated(self):
        data   = [{"date": "2024-01-01", "amount": 200.0, "cost": 120.0}]
        before = dict(data[0])
        _enrich_transactions(data)
        self.assertEqual(data[0], before)


# ---------------------------------------------------------------------------
# 6. build_chart_data
# ---------------------------------------------------------------------------

class TestBuildChartData(unittest.TestCase):

    def test_sales_over_time_always_present(self):
        charts = build_chart_data(SALES)
        self.assertIn("sales_over_time", charts)

    def test_sales_over_time_labels_sorted(self):
        charts = build_chart_data(SALES)
        labels = charts["sales_over_time"]["labels"]
        self.assertEqual(labels, sorted(labels))

    def test_sales_over_time_data_len_matches_labels(self):
        charts = build_chart_data(SALES)
        sot    = charts["sales_over_time"]
        self.assertEqual(len(sot["labels"]), len(sot["data"]))

    def test_grouping_chart_present_when_grouping_set(self):
        charts = build_chart_data(SALES, grouping="product")
        self.assertIn("sales_by_product", charts)

    def test_grouping_chart_absent_without_grouping(self):
        charts = build_chart_data(SALES)
        self.assertNotIn("sales_by_product", charts)

    def test_grouping_data_totals_sum_to_grand_total(self):
        charts = build_chart_data(SALES, grouping="product")
        total  = sum(charts["sales_by_product"]["data"])
        self.assertAlmostEqual(total, 1000.0)

    def test_daily_totals_aggregated(self):
        """Two sales on same date should be summed into one data point."""
        data = [
            {"date": "2024-01-01", "amount": 100.0},
            {"date": "2024-01-01", "amount":  50.0},
            {"date": "2024-01-02", "amount": 200.0},
        ]
        charts = build_chart_data(data)
        sot    = charts["sales_over_time"]
        self.assertEqual(len(sot["labels"]), 2)
        self.assertAlmostEqual(sot["data"][0], 150.0)


# ---------------------------------------------------------------------------
# 7. render_report
# ---------------------------------------------------------------------------

class TestRenderReport(unittest.TestCase):

    def _minimal_report(self):
        return {"report_type": "summary", "summary": {}}

    def test_json_returns_dict(self):
        result = render_report(self._minimal_report(), "json")
        self.assertIsInstance(result, dict)

    def test_json_is_passthrough(self):
        r = self._minimal_report()
        self.assertIs(render_report(r, "json"), r)

    def test_charts_merged_into_report(self):
        r      = self._minimal_report()
        charts = {"sales_over_time": {"labels": [], "data": []}}
        result = render_report(r, "json", charts_data=charts)
        self.assertIn("charts", result)

    def test_original_report_not_mutated_when_charts_added(self):
        r      = self._minimal_report()
        charts = {"sales_over_time": {"labels": [], "data": []}}
        render_report(r, "json", charts_data=charts)
        self.assertNotIn("charts", r)  # r itself must be unchanged

    def test_identity_returns_input(self):
        obj = {"x": 1}
        self.assertIs(_identity(obj), obj)


# ---------------------------------------------------------------------------
# 8. generate_sales_report — end-to-end orchestration
# ---------------------------------------------------------------------------

class TestOrchestrator(unittest.TestCase):
    """
    These tests treat generate_sales_report as a black box and verify that
    the helpers compose to produce correct output.  They mirror what the
    original monolithic function was supposed to do.
    """

    # --- validation forwarding ---
    def test_bad_report_type_raises(self):
        with self.assertRaises(ValueError):
            generate_sales_report(SALES, report_type="bad", output_format="json")

    def test_bad_output_format_raises(self):
        with self.assertRaises(ValueError):
            generate_sales_report(SALES, output_format="csv")

    def test_inverted_date_range_raises(self):
        with self.assertRaises(ValueError):
            generate_sales_report(
                SALES,
                date_range={"start": "2024-12-01", "end": "2024-01-01"},
                output_format="json",
            )

    # --- empty-data early return ---
    def test_empty_result_after_filter_returns_message(self):
        result = generate_sales_report(
            SALES, filters={"product": "Z"}, output_format="json"
        )
        self.assertIn("message", result)
        self.assertEqual(result["data"], [])

    # --- summary report ---
    def test_summary_report_total(self):
        r = generate_sales_report(SALES, output_format="json")
        self.assertAlmostEqual(r["summary"]["total_sales"], 1000.0)

    def test_summary_report_count(self):
        r = generate_sales_report(SALES, output_format="json")
        self.assertEqual(r["summary"]["transaction_count"], 5)

    # --- date filtering propagates ---
    def test_date_range_filters_records(self):
        r = generate_sales_report(
            SALES,
            date_range={"start": "2024-01-01", "end": "2024-01-31"},
            output_format="json",
        )
        self.assertAlmostEqual(r["summary"]["total_sales"], 300.0)
        self.assertEqual(r["summary"]["transaction_count"], 2)

    # --- grouping propagates ---
    def test_grouping_section_present(self):
        r = generate_sales_report(SALES, grouping="product", output_format="json")
        self.assertIn("grouping", r)
        self.assertEqual(r["grouping"]["by"], "product")

    # --- detailed report includes transactions ---
    def test_detailed_has_transactions(self):
        r = generate_sales_report(SALES, report_type="detailed", output_format="json")
        self.assertIn("transactions", r)
        self.assertEqual(len(r["transactions"]), 5)

    # --- forecast report includes projections ---
    def test_forecast_has_projected_sales(self):
        r = generate_sales_report(SALES, report_type="forecast", output_format="json")
        self.assertIn("forecast", r)
        self.assertIn("projected_sales", r["forecast"])
        self.assertEqual(len(r["forecast"]["projected_sales"]), 3)

    # --- charts propagate ---
    def test_charts_included_when_requested(self):
        r = generate_sales_report(SALES, include_charts=True, output_format="json")
        self.assertIn("charts", r)
        self.assertIn("sales_over_time", r["charts"])

    def test_charts_absent_by_default(self):
        r = generate_sales_report(SALES, output_format="json")
        self.assertNotIn("charts", r)

    # --- combined: date + filter + grouping + charts ---
    def test_combined_options(self):
        r = generate_sales_report(
            SALES,
            date_range={"start": "2024-01-01", "end": "2024-03-31"},
            filters={"region": ["North", "South"]},
            grouping="product",
            include_charts=True,
            output_format="json",
        )
        # Only North+South records
        self.assertEqual(r["summary"]["transaction_count"], 4)
        self.assertIn("grouping",        r)
        self.assertIn("charts",          r)
        self.assertNotIn("transactions", r)   # summary type, not detailed


if __name__ == "__main__":
    unittest.main(verbosity=2)
