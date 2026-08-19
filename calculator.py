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
    stated_rate = _num(data.get("statedRate"))
    amount_financed = _num(data.get("amountFinanced"))
    monthly_payment = _num(data.get("monthlyPayment"))
    term_months = _num(data.get("termMonths"))
    cash_down = _num(data.get("cashDown"))
    total_payments = _num(data.get("totalPayments"))
    finance_charge = _num(data.get("financeCharge"))

    credit_score = _num(data.get("creditScore"))
    gross_income = _num(data.get("grossIncome"))
    benchmark_apr = _num(data.get("benchmarkApr"))

    plan_payment = _num(data.get("planPayment"))
    current_net_income = _num(data.get("currentNetIncome"))
    replaced_vehicle_payment = _num(data.get("replacedVehiclePayment"))
    current_insurance = _num(data.get("currentInsurance"))
    projected_insurance = _num(data.get("projectedInsurance"))
    other_vehicle_cost_change = _num(data.get("otherVehicleCostChange"))
    monthly_income_change = _num(data.get("monthlyIncomeChange"))

    review_items: list[dict[str, str]] = []

    def add_review(area: str, item: str, basis: str) -> None:
        review_items.append({"area": area, "item": item, "basis": basis})

    # Vehicle value and LTV.
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

    # Amount-financed reconstruction.
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

    # PTI is descriptive only.
    pti = monthly_payment / gross_income * 100 if gross_income > 0 and monthly_payment > 0 else None

    # Chapter 13 projected budget. The proposed payment entered above is reused here.
    vehicle_payment_change = monthly_payment - replaced_vehicle_payment

    insurance_change = 0.0
    insurance_entered = bool(data.get("currentInsurance") not in (None, "")) and bool(data.get("projectedInsurance") not in (None, ""))
    if insurance_entered:
        insurance_change = projected_insurance - current_insurance

    net_vehicle_cost_change = vehicle_payment_change + insurance_change + other_vehicle_cost_change
    projected_net_income = current_net_income + monthly_income_change - net_vehicle_cost_change
    budget_cushion = projected_net_income - plan_payment

    if budget_cushion < 0:
        add_review(
            "Plan feasibility",
            f"Entered figures leave a projected monthly deficit of {_money(abs(budget_cushion))} after the current plan payment.",
            "Projected Schedule J net income − current monthly plan payment.",
        )

    # APR comparison only when an APR, rather than merely a stated interest rate, is entered.
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
        ["Financing", "APR", f"{apr:.3f}%" if apr > 0 else "—"],
        ["Financing", "Stated interest rate", f"{stated_rate:.3f}%" if stated_rate > 0 else "—"],
        ["Financing", "Amount financed", _money(amount_financed)],
        ["Financing", "Term", f"{int(term_months)} months"],
        ["Financing", "Monthly payment", _money(monthly_payment)],
        ["Financing", "Finance charge", _money(finance_charge) if finance_charge > 0 else "—"],
        ["Financing", "Total of payments", _money(total_payments) if total_payments > 0 else "—"],
        ["Financing context", "Credit score", str(int(credit_score)) if credit_score > 0 else "—"],
        ["Financing context", "Credit score model", str(data.get("scoreModel") or "—")],
        ["Financing context", "Gross monthly income for PTI", _money(gross_income) if gross_income > 0 else "—"],
        ["Financing context", "PTI", _percent(pti)],
        ["Financing context", "Entered benchmark APR", f"{benchmark_apr:.3f}%" if benchmark_apr > 0 else "—"],
        ["Financing context", "APR difference", f"{apr_difference:+.3f} percentage points" if apr_difference is not None else "—"],
        ["Financing context", "Benchmark source / cohort", str(data.get("benchmarkLabel") or "—")],
        ["Financing context", "Financing attempts / alternatives", str(data.get("financingAttempts") or "—")],

        ["Plan and budget", "Current monthly plan payment", _money(plan_payment)],
        ["Plan and budget", "Current Schedule J monthly net income", _money(current_net_income)],
        ["Plan and budget", "Proposed monthly vehicle payment", _money(monthly_payment)],
        ["Plan and budget", "Vehicle payment being replaced", _money(replaced_vehicle_payment)],
        ["Plan and budget", "Vehicle-payment change", _money(vehicle_payment_change)],
        ["Plan and budget", "Insurance change", _money(insurance_change) if insurance_entered else "—"],
        ["Plan and budget", "Other monthly vehicle-cost change", _money(other_vehicle_cost_change)],
        ["Plan and budget", "Other monthly income change", _money(monthly_income_change)],
        ["Plan and budget", "Net increase in monthly vehicle costs", _money(net_vehicle_cost_change)],
        ["Plan and budget", "Projected Schedule J net income", _money(projected_net_income)],
        ["Plan and budget", "Projected amount remaining after plan payment", _money(budget_cushion)],
        ["Plan and budget", "Schedules I/J date", str(data.get("scheduleDate") or "—")],
        ["Plan and budget", "Plan payment status", str(data.get("planStatus") or "Unknown")],
        ["Plan and budget", "Deficit explanation", str(data.get("deficitExplanation") or "—")],

        ["Calculation", "LTV", _percent(ltv)],
        ["Calculation", "Amount financed above / below vehicle value", _money(amount_above_value)],
        ["Calculation", "Reconstructed amount financed", _money(expected_amount_financed)],
        ["Calculation", "Amount-financed difference", _money(reconciliation_difference)],
    ]

    return {
        "metrics": {
            "ltv": _percent(ltv),
            "amountAboveValue": _money(amount_above_value),
            "pti": _percent(pti),
            "projectedNetIncome": _money(projected_net_income),
            "budgetCushion": _money(budget_cushion),
            "aprDifference": _pp(apr_difference),
        },
        "reviewItems": review_items,
        "results": results,
    }
