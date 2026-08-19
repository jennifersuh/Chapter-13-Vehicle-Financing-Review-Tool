"""Core calculations for the Vehicle Financing Bench-Screening Tool.

This module contains the calculation and review-item logic. It is deliberately
deterministic: it uses only values supplied by the user and does not infer
missing facts or make approval/reasonableness decisions.
"""

from __future__ import annotations

from typing import Any


def _num(value: Any) -> float:
    """Convert a value to float; blanks and invalid values become 0.0."""
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _money(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def _percent(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}%"


def _pp(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:+.3f} pp"


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    """Calculate results and objective review items from one transaction."""

    cash_price = _num(data.get("cashPrice"))
    supported_value = _num(data.get("supportedValue"))
    market_low = _num(data.get("marketLow"))
    market_high = _num(data.get("marketHigh"))

    apr = _num(data.get("apr"))
    amount_financed = _num(data.get("amountFinanced"))
    cash_down = _num(data.get("cashDown"))
    monthly_payment = _num(data.get("monthlyPayment"))
    term_months = _num(data.get("termMonths"))
    total_payments = _num(data.get("totalPayments"))
    finance_charge = _num(data.get("financeCharge"))

    has_trade = bool(data.get("hasTrade"))
    trade_allowance = _num(data.get("tradeAllowance")) if has_trade else 0.0
    trade_payoff = _num(data.get("tradePayoff")) if has_trade else 0.0

    taxes_fees = _num(data.get("taxesFees"))
    gap = _num(data.get("gap"))
    warranty = _num(data.get("warranty"))
    other_addons = _num(data.get("otherAddons"))
    other_financed = _num(data.get("otherFinanced"))
    rebates_credits = _num(data.get("rebatesCredits"))

    itemization_complete = bool(data.get("itemizationComplete"))
    equal_payments = bool(data.get("equalPayments"))

    gross_income = _num(data.get("grossIncome"))
    monthly_debt = _num(data.get("monthlyDebt"))
    benchmark_apr = _num(data.get("benchmarkApr"))

    review_items: list[dict[str, str]] = []

    def add_review(area: str, item: str, basis: str) -> None:
        review_items.append({"area": area, "item": item, "basis": basis})

    price_range_result = "—"
    if market_low > 0 and market_high > 0 and market_high >= market_low and cash_price > 0:
        if cash_price > market_high:
            difference = cash_price - market_high
            price_range_result = f"{_money(difference)} above entered range high"
            add_review(
                "Vehicle price",
                f"Cash price is {_money(difference)} above the entered market-range high.",
                "Dealer cash price compared with the entered market range.",
            )
        elif cash_price < market_low:
            difference = market_low - cash_price
            price_range_result = f"{_money(difference)} below entered range low"
            add_review(
                "Vehicle price",
                f"Cash price is {_money(difference)} below the entered market-range low.",
                "Dealer cash price compared with the entered market range.",
            )
        else:
            price_range_result = "Within entered market range"

    ltv = None
    amount_above_value = None
    if supported_value > 0 and amount_financed > 0:
        ltv = amount_financed / supported_value * 100
        amount_above_value = amount_financed - supported_value
        if ltv > 100:
            add_review(
                "LTV",
                f"Amount financed exceeds supported vehicle value by {_money(amount_above_value)}; "
                f"LTV is {_percent(ltv)}.",
                "Amount financed ÷ supported vehicle value.",
            )

    trade_equity = None
    negative_equity = 0.0
    positive_equity = 0.0
    if has_trade:
        trade_equity = trade_allowance - trade_payoff
        if trade_equity < 0:
            negative_equity = abs(trade_equity)
            add_review(
                "Trade-in",
                f"Negative trade-in equity is {_money(negative_equity)}.",
                "Trade-in allowance minus existing lien payoff.",
            )
        else:
            positive_equity = trade_equity

    expected_amount_financed = None
    reconciliation_difference = None
    if itemization_complete and cash_price > 0:
        expected_amount_financed = (
            cash_price
            + taxes_fees
            + gap
            + warranty
            + other_addons
            + other_financed
            + negative_equity
            - cash_down
            - rebates_credits
            - positive_equity
        )
        if amount_financed > 0:
            reconciliation_difference = amount_financed - expected_amount_financed
            if abs(reconciliation_difference) > 1.00:
                add_review(
                    "Amount financed",
                    "Disclosed amount financed differs from the entered reconstruction by "
                    f"{_money(abs(reconciliation_difference))}.",
                    "Entered transaction components compared with disclosed amount financed.",
                )

    scheduled_sum = None
    payment_schedule_difference = None
    if equal_payments and monthly_payment > 0 and term_months > 0:
        scheduled_sum = monthly_payment * term_months
        if total_payments > 0:
            payment_schedule_difference = total_payments - scheduled_sum
            if abs(payment_schedule_difference) > 1.00:
                add_review(
                    "Payment schedule",
                    "Monthly payment × number of payments differs from entered total of payments by "
                    f"{_money(abs(payment_schedule_difference))}.",
                    "Equal monthly payment × number of payments.",
                )

    pti = monthly_payment / gross_income * 100 if gross_income > 0 and monthly_payment > 0 else None
    dti = monthly_debt / gross_income * 100 if gross_income > 0 and monthly_debt > 0 else None
    apr_difference = apr - benchmark_apr if apr > 0 and benchmark_apr > 0 else None

    vehicle_parts = [
        str(data.get("year") or "").strip(),
        str(data.get("make") or "").strip(),
        str(data.get("model") or "").strip(),
        str(data.get("trim") or "").strip(),
    ]
    vehicle_name = " ".join(part for part in vehicle_parts if part) or "—"

    market_range = (
        f"{_money(market_low)} – {_money(market_high)}"
        if market_low > 0 and market_high > 0
        else "—"
    )

    results = [
        ["Vehicle", "Status", str(data.get("vehicleStatus") or "—")],
        ["Vehicle", "Vehicle", vehicle_name],
        ["Vehicle", "Mileage", f"{int(_num(data.get('mileage'))):,}" if _num(data.get("mileage")) > 0 else "—"],
        ["Vehicle", "Dealer cash price", _money(cash_price) if cash_price > 0 else "—"],
        ["Vehicle", "Supported vehicle value", _money(supported_value) if supported_value > 0 else "—"],
        ["Vehicle", "Entered market range", market_range],
        ["Vehicle", "Price vs. entered range", price_range_result],
        ["Financing", "Financing channel", str(data.get("financingChannel") or "Unknown")],
        ["Financing", "APR", f"{apr:.3f}%" if apr > 0 else "—"],
        ["Financing", "Amount financed", _money(amount_financed) if amount_financed > 0 else "—"],
        ["Financing", "Term", f"{int(term_months)} months" if term_months > 0 else "—"],
        ["Financing", "Monthly payment", _money(monthly_payment) if monthly_payment > 0 else "—"],
        ["Financing", "Finance charge", _money(finance_charge) if finance_charge > 0 else "—"],
        ["Financing", "Total of payments", _money(total_payments) if total_payments > 0 else "—"],
        ["Calculation", "LTV", _percent(ltv)],
        ["Calculation", "Amount financed above / below vehicle value", _money(amount_above_value)],
        ["Calculation", "Trade-in equity", _money(trade_equity)],
        ["Calculation", "Reconstructed amount financed", _money(expected_amount_financed)],
        ["Calculation", "Amount-financed difference", _money(reconciliation_difference)],
        ["Calculation", "Equal-payment scheduled sum", _money(scheduled_sum)],
        ["Context", "PTI (descriptive only)", _percent(pti)],
        ["Context", "DTI (descriptive only)", _percent(dti)],
        ["Context", "Entered benchmark APR", f"{benchmark_apr:.3f}%" if benchmark_apr > 0 else "—"],
        ["Context", "APR difference", f"{apr_difference:+.3f} percentage points" if apr_difference is not None else "—"],
        ["Context", "Benchmark source / cohort", str(data.get("benchmarkLabel") or "—")],
    ]

    return {
        "metrics": {
            "ltv": _percent(ltv),
            "amountAboveValue": _money(amount_above_value),
            "tradeEquity": _money(trade_equity),
            "aprDifference": _pp(apr_difference),
        },
        "reviewItems": review_items,
        "results": results,
    }
