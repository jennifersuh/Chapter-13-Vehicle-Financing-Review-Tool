"""Core calculations for the Vehicle Financing Bench-Screening Tool.

The module uses only values supplied by the user. It does not infer missing
facts or make approval or reasonableness decisions.
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


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    cash_price = _num(data.get("cashPrice"))
    supported_value = _num(data.get("supportedValue"))

    taxes_fees = _num(data.get("taxesFees"))
    gap = _num(data.get("gap"))
    warranty = _num(data.get("warranty"))
    other_addons = _num(data.get("otherAddons"))
    other_financed = _num(data.get("otherFinanced"))
    rebates_credits = _num(data.get("rebatesCredits"))

    apr = _num(data.get("apr"))
    stated_rate = _num(data.get("statedRate"))
    amount_financed = _num(data.get("amountFinanced"))
    monthly_payment = _num(data.get("monthlyPayment"))
    term_months = _num(data.get("termMonths"))
    cash_down = _num(data.get("cashDown"))
    total_payments = _num(data.get("totalPayments"))
    finance_charge = _num(data.get("financeCharge"))

    credit_score = _num(data.get("creditScore"))
    credit_tier = str(data.get("creditTier") or "—")

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

    financed_addons = gap + warranty + other_addons

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

        ["Financed extras", "Taxes and fees", _money(taxes_fees) if taxes_fees > 0 else "—"],
        ["Financed extras", "GAP", _money(gap) if gap > 0 else "—"],
        ["Financed extras", "Warranty / service contract", _money(warranty) if warranty > 0 else "—"],
        ["Financed extras", "Other add-ons", _money(other_addons) if other_addons > 0 else "—"],
        ["Financed extras", "Other financed charges", _money(other_financed) if other_financed > 0 else "—"],
        ["Financed extras", "Rebates / other credits", _money(rebates_credits) if rebates_credits > 0 else "—"],
        ["Financed extras", "GAP + warranty + other add-ons", _money(financed_addons) if financed_addons > 0 else "—"],

        ["Financing", "Financing channel", str(data.get("financingChannel") or "Unknown")],
        ["Financing", "APR", f"{apr:.3f}%" if apr > 0 else "—"],
        ["Financing", "Interest rate", f"{stated_rate:.3f}%" if stated_rate > 0 else "—"],
        ["Financing", "Amount financed", _money(amount_financed)],
        ["Financing", "Term", f"{int(term_months)} months"],
        ["Financing", "Monthly payment", _money(monthly_payment)],
        ["Financing", "Cash down payment", _money(cash_down) if cash_down > 0 else "—"],
        ["Financing", "Finance charge", _money(finance_charge) if finance_charge > 0 else "—"],
        ["Financing", "Total of payments", _money(total_payments) if total_payments > 0 else "—"],

        ["Credit context", "VantageScore 4.0 credit tier", credit_tier],
        ["Credit context", "Credit score", str(int(credit_score)) if credit_score > 0 else "—"],

        ["Calculation", "LTV", _percent(ltv)],
        ["Calculation", "Amount financed above / below vehicle value", _money(amount_above_value)],
    ]

    return {
        "metrics": {
            "ltv": _percent(ltv),
            "amountAboveValue": _money(amount_above_value),
            "creditTier": credit_tier,
        },
        "reviewItems": review_items,
        "results": results,
    }
