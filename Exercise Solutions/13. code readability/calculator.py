def calculate(principal, rate, time, additional=0, frequency=12):
    """
    Calculate compound interest growth over time with optional annual contributions.

    Computes the future value of an investment by applying compound interest at a
    specified frequency, with optional lump-sum contributions added at the end of
    each complete year (excluding the final year).

    Args:
        principal (float): The initial investment amount in currency units (e.g. dollars).
        rate (float): The annual interest rate as a percentage (e.g. 5.0 for 5%).
        time (int): The total investment duration in years.
        additional (float, optional): The amount in currency units added at the end
            of each year, excluding the final year. Defaults to 0.
        frequency (int, optional): The number of compounding periods per year
            (e.g. 12 for monthly, 4 for quarterly, 1 for annually). Defaults to 12.

    Returns:
        dict: A dictionary containing:
            - "final_amount" (float): The total value of the investment at the end
              of the period, rounded to 2 decimal places.
            - "interest_earned" (float): The total interest earned over the investment
              period (final_amount minus principal and all additional contributions),
              rounded to 2 decimal places.
            - "total_contributions" (float): The sum of the initial principal and all
              additional annual contributions made (excludes final year contribution).

    Example:
        >>> calculate(1000, 5, 10, additional=100, frequency=12)
        {'final_amount': 2145.14, 'interest_earned': 244.14, 'total_contributions': 1900}
    """
    result = principal
    rate_per_period = rate / 100 / frequency
    total_periods = time * frequency
    for period in range(1, total_periods + 1):
        interest = result * rate_per_period
        result += interest
        if period % frequency == 0 and period < total_periods:
            result += additional
    return {
        "final_amount": round(result, 2),
        "interest_earned": round(result - principal - (additional * (time - 1)), 2),
        "total_contributions": principal + (additional * (time - 1))
    }