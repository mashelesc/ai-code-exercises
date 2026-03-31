## AI TOOL USED:
## EXERCISE: CODE READABILITY

## PROMPT 1: Comment and Documentation Addition

- Using the `calculator.py` script.
- Documentation has been added to the `calculator.py` script.
- Key documentation decisions worth noting:
  - **`rate` clarified as a percentage** — `5.0` means 5%, not 0.05, which is a common source of bugs for callers.
  - **`additional` timing is explicit** — the docstring spells out that contributions happen at the end of each year *excluding the final year*, which matches the loop logic (`period < total_periods`) and prevents misuse.
  - **`total_contributions` formula explained** — since it counts `time - 1` contributions (not `time`), this asymmetry is documented so return values don't appear wrong to callers.
  - **A concrete `Example:` block** — follows standard doctest format so it can be run with `doctest.testmod()` and doubles as a quick sanity check.

- Bug fix — `test_with_additional_contributions` wrong expected values. The original asserted `2234.51` and `234.51`, which are incorrect. Running the actual formula gives `2239.52` and `239.52`. The comment showed the right logic but the asserted numbers didn't match it.
- `assertAlmostEqual` for `interest_earned` in `test_zero_interest`. The original used `assertEqual` for a float result. While it works here at 0.0, it's fragile — `assertAlmostEqual` is always the right choice for floats.

- Four new edge case tests added:
  - `test_additional_contribution_not_added_in_final_year` — explicitly guards the `period < total_periods` boundary condition, the most subtle logic in the function.
  - `test_single_year_no_contribution_added` — confirms `additional` is a no-op when `time = 1`.
  - `test_annual_compounding_frequency` — tests `frequency = 1` with a manually verifiable result `(1000 * 1.1² = 1210)`.
  - `test_zero_principal` — guards the degenerate case of starting with nothing.

## REFLECTION

- The code is now very much easier because it now has documentation that perfectly describes what the code actually does.
- The `calculate()` function is not clear as to what the function actually calculates. With a clearer function name like `calculate_compound_interest()`, it would have been a bit easier to figure it's purpose even with no documentation. The `assertAlmostEqual` for floats over `assertEqual`.
- The AI was happy with the `calculate()` function name, probably because it was then well documented.
- Clear names, even for the `test_calculator.py` script, you can tell exactly what each function or variable does just by reading it's name.
- The code became very easy to follow after having changed some names. 
- Descriptive names for every variable, class, and function that I create. Clear code saves time and resources, it's still no substitute for script documentation though.  