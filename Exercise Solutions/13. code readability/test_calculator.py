import unittest
from calculator import calculate


class TestCompoundInterestCalculator(unittest.TestCase):

    def test_basic_interest_no_additions(self):
        """
        1000 principal, 5% annual rate, monthly compounding (default), 1 year.
        Expected: 1000 * (1 + 0.05/12)^12 = 1051.16
        No contributions, so interest_earned = final_amount - principal.
        """
        result = calculate(principal=1000, rate=5, time=1, additional=0)

        self.assertAlmostEqual(result["final_amount"], 1051.16, places=2,
            msg="Final amount should be 1000 compounded monthly at 5% for 1 year")
        self.assertAlmostEqual(result["interest_earned"], 51.16, places=2,
            msg="Interest earned should be final_amount - principal")
        self.assertEqual(result["total_contributions"], 1000,
            msg="No additional contributions, so total_contributions == principal")

    def test_different_compounding_frequency(self):
        """
        Higher compounding frequency earns more interest.
        Monthly (12x/year) should yield more than quarterly (4x/year).
        """
        result_quarterly = calculate(principal=10000, rate=4, time=2, frequency=4)
        result_monthly = calculate(principal=10000, rate=4, time=2, frequency=12)

        self.assertLess(result_quarterly["final_amount"], result_monthly["final_amount"],
            msg="Monthly compounding should yield more than quarterly at the same rate")
        
    def test_with_additional_contributions(self):
        """
        1000 principal, 5% rate, 3 years, 500 added at end of years 1 and 2.
        total_contributions = 1000 + (500 * 2) = 2000
        interest_earned = final_amount - principal - (additional * (time - 1))
                        = 2239.52 - 1000 - 1000 = 239.52
        Verified by running calculate(1000, 5, 3, 500).
        """
        result = calculate(principal=1000, rate=5, time=3, additional=500)

        self.assertAlmostEqual(result["final_amount"], 2239.52, places=2,
            msg="Final amount mismatch for 3-year investment with annual contributions")
        self.assertAlmostEqual(result["interest_earned"], 239.52, places=2,
            msg="Interest earned should exclude principal and all contributions")
        self.assertEqual(result["total_contributions"], 2000,
            msg="total_contributions = principal + (500 * 2 years of additions)")
        
    def test_zero_interest(self):
        """
        0% interest rate, 5 years, 1000 added at end of years 1-4.
        total_contributions = 5000 + (1000 * 4) = 9000
        final_amount should equal total_contributions (no interest earned).
        interest_earned = 9000 - 5000 - (1000 * 4) = 0
        """
        result = calculate(principal=5000, rate=0, time=5, additional=1000)

        self.assertAlmostEqual(result["final_amount"], 9000.00, places=2,
            msg="With 0% interest, final amount should just be principal + contributions")
        self.assertAlmostEqual(result["interest_earned"], 0.00, places=2,
            msg="No interest should be earned at 0% rate")
        self.assertEqual(result["total_contributions"], 9000,
            msg="total_contributions = 5000 + (1000 * 4)")

    def test_additional_contribution_not_added_in_final_year(self):
        """
        Verifies that the additional contribution is NOT added at the end of
        the final year. For time=2, additional=500:
        - Contribution added at end of year 1 only (period < total_periods)
        - total_contributions = 1000 + (500 * 1) = 1500, not 2000
        """
        result = calculate(principal=1000, rate=5, time=2, additional=500)

        self.assertEqual(result["total_contributions"], 1500,
            msg="Contribution should only be added at end of year 1, not year 2")

    def test_single_year_no_contribution_added(self):
        """
        With time=1, additional > 0 should have no effect — the loop condition
        `period < total_periods` means the contribution at period=12 is never added.
        Result should be identical to additional=0.
        """
        result_with = calculate(principal=1000, rate=5, time=1, additional=500)
        result_without = calculate(principal=1000, rate=5, time=1, additional=0)

        self.assertEqual(result_with["final_amount"], result_without["final_amount"],
            msg="Additional has no effect when time=1 (no period qualifies for contribution)")
        self.assertEqual(result_with["total_contributions"], 1000,
            msg="total_contributions = principal + (500 * 0) = 1000 when time=1")

    def test_annual_compounding_frequency(self):
        """
        frequency=1 means interest is applied once per year.
        1000 at 10% for 2 years: 1000 * 1.1 * 1.1 = 1210.00
        """
        result = calculate(principal=1000, rate=10, time=2, frequency=1)

        self.assertAlmostEqual(result["final_amount"], 1210.00, places=2,
            msg="Annual compounding: 1000 * 1.1^2 should equal 1210.00")

    def test_zero_principal(self):
        """
        Edge case: starting with 0 principal.
        Only contributions drive the final amount.
        With rate=5, time=2, additional=1000, frequency=12:
        Year 1: 0 compounds to ~0, then 1000 is added
        Year 2: 1000 compounds for 1 year at 5% monthly = ~1051.16
        """
        result = calculate(principal=0, rate=5, time=2, additional=1000)

        self.assertGreater(result["final_amount"], 1000,
            msg="Final amount should exceed the single contribution after compounding")
        self.assertEqual(result["total_contributions"], 1000,
            msg="total_contributions = 0 + (1000 * 1) = 1000 when time=2")


if __name__ == "__main__":
    unittest.main()