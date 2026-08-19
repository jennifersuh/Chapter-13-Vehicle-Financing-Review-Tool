"""Core calculations for the Vehicle Financing Bench-Screening Tool.

This module contains deterministic calculation and review-item logic. It uses
only values supplied by the user and does not infer missing facts or make
approval/reasonableness decisions.
"""

from __future__ import annotations

from typing import Any


def _num(value: Any) -> float:
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
    cash_price = _num(data.get("cashPrice"))
    supported_value = _num(data.get("supportedValue"))

    taxes_fees = _num(data.get("taxesFees"))
    gap = _num(data.get("gap"))
    warranty = _num(data.get("warranty"))
    other_addons = _num(data.get("otherAddons"))
    other_financed = _num(data.get("otherFinanced"))
    rebates_credits = _num(data.get("rebatesCredits"))
    itemization_complete = bool(data.get("itemizationComplete"))

    apr = _num(data.get("apr"))
    amount_financed = _num(data.get("amountFinanced"))
    monthly_payment = _num(data.get("monthlyPayment"))
    term_months = _num(data.get("termMonths"))
    cash_down = _num(data.get("cashDown"))
    total_payments = _num(data.get("totalPayments"))
    finance_charge = _num(data.get("financeCharge"))
    equal_payments = bool(data.get("equalPayments"))

    plan_payment = _num(data.get("planPayment"))
    current_net_income = _num(data.get("currentNetIncome"))
    change_net_income = _num(data.get("changeNetIncome"))
    gross_income = _num(data.get("grossIncome"))
    monthly_expenses = _num(data.get("monthlyExpenses"))
    benchmark_apr = _num(data.get("benchmarkApr"))

    review_items: list[dict[str, str]] = []

    def add_review(area: str, item: str, basis: str) -> None:
        review_items.append({"area": area, "item": item, "basis": basis})

    ltv = None
    amount_above_value = None
    if supported_value > 0 and amount_financed > 0:
        ltv = amount_financed / supported_value * 100
        amount_above_value = amount_financed - supported_value
        if ltv > 100:
            add_review(
                "LTV",
                f"Amount financed exceeds the entered vehicle value by {_money(amount_above_value)}; LTV is {_percent(ltv)}.",
                "Amount financed ÷ entered vehicle value.",
            )

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
            - cash_down
            - rebates_credits
        )
        reconciliation_difference = amount_financed - expected_amount_financed
        if abs(reconciliation_difference) > 1.00:
            add_review(
                "Amount financed",
                "Disclosed amount financed differs from the entered reconstruction by "
                f"{_money(abs(reconciliation_difference))}.",
                "Entered price, credits, and financed extras compared with disclosed amount financed.",
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

    projected_net_income = current_net_income + change_net_income
    budget_cushion = projected_net_income - plan_payment
    if budget_cushion < 0:
        add_review(
            "Plan feasibility",
            f"Entered figures leave a projected monthly deficit of {_money(abs(budget_cushion))} after the current plan payment.",
            "Current net monthly income + entered change in net monthly income − current monthly plan payment.",
        )

    schedule_net = None
    if gross_income > 0 and monthly_expenses > 0:
        schedule_net = gross_income - monthly_expenses
        if abs(schedule_net - current_net_income) > 1.00:
            add_review(
                "Schedules I/J",
                "Entered Schedule I income minus Schedule J expenses does not match the entered current net monthly income.",
                "Gross monthly income − monthly expenses compared with entered current net monthly income.",
            )

    apr_difference = apr - benchmark_apr if apr > 0 and benchmark_apr > 0 else None

    vehicle_parts = [
        str(data.get("year") or "").strip(),
        str(data.get("make") or "").strip(),
        str(data.get("model") or "").strip(),
    ]
    vehicle_name = " ".join(part for part in vehicle_parts if part) or "—"

    results = [
        ["Vehicle", "Status", str(data.get("vehicleStatus") or "—")],
        ["Vehicle", "Vehicle", vehicle_name],
        ["Vehicle", "Mileage", f"{int(_num(data.get('mileage'))):,}" if _num(data.get("mileage")) > 0 else "—"],
        ["Vehicle", "Condition", str(data.get("condition") or "—")],
        ["Vehicle", "Dealer cash price", _money(cash_price)],
        ["Vehicle", "Entered vehicle value", _money(supported_value) if supported_value > 0 else "—"],
        ["Vehicle", "Value source", str(data.get("valueSource") or "—")],
        ["Financing", "Financing channel", str(data.get("financingChannel") or "Unknown")],
        ["Financing", "APR", f"{apr:.3f}%"],
        ["Financing", "Amount financed", _money(amount_financed)],
        ["Financing", "Term", f"{int(term_months)} months"],
        ["Financing", "Monthly payment", _money(monthly_payment)],
        ["Financing", "Finance charge", _money(finance_charge) if finance_charge > 0 else "—"],
        ["Financing", "Total of payments", _money(total_payments) if total_payments > 0 else "—"],
        ["Plan and budget", "Current monthly plan payment", _money(plan_payment)],
        ["Plan and budget", "Current net monthly income", _money(current_net_income)],
        ["Plan and budget", "Change in net monthly income", _money(change_net_income)],
        ["Plan and budget", "Projected net monthly income", _money(projected_net_income)],
        ["Plan and budget", "Projected amount remaining after plan payment", _money(budget_cushion)],
        ["Plan and budget", "Plan payment status", str(data.get("planStatus") or "Unknown")],
        ["Plan and budget", "Deficit explanation", str(data.get("deficitExplanation") or "—")],
        ["Calculation", "LTV", _percent(ltv)],
        ["Calculation", "Amount financed above / below vehicle value", _money(amount_above_value)],
        ["Calculation", "Reconstructed amount financed", _money(expected_amount_financed)],
        ["Calculation", "Amount-financed difference", _money(reconciliation_difference)],
        ["Calculation", "Equal-payment scheduled sum", _money(scheduled_sum)],
        ["Optional context", "Credit score", str(int(_num(data.get("creditScore")))) if _num(data.get("creditScore")) > 0 else "—"],
        ["Optional context", "Entered benchmark APR", f"{benchmark_apr:.3f}%" if benchmark_apr > 0 else "—"],
        ["Optional context", "APR difference", f"{apr_difference:+.3f} percentage points" if apr_difference is not None else "—"],
        ["Optional context", "Benchmark source / cohort", str(data.get("benchmarkLabel") or "—")],
        ["Optional context", "Financing attempts / alternatives", str(data.get("financingAttempts") or "—")],
    ]

    return {
        "metrics": {
            "ltv": _percent(ltv),
            "amountAboveValue": _money(amount_above_value),
            "budgetCushion": _money(budget_cushion),
            "aprDifference": _pp(apr_difference),
        },
        "reviewItems": review_items,
        "results": results,
    }
