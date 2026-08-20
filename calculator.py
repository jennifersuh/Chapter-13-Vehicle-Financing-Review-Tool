"""Core calculations for the Vehicle Financing Bench-Screening Tool.

The module uses entered case information plus the Q1 2026 Experian
used-vehicle APR averages documented in the accompanying research memo.
It does not make approval or reasonableness decisions.
"""

from __future__ import annotations

from typing import Any


TIER_DATA = {
    "Super prime (781–850)": {"low": 781, "high": 850, "used_apr": 6.30},
    "Prime (661–780)": {"low": 661, "high": 780, "used_apr": 8.77},
    "Near prime (601–660)": {"low": 601, "high": 660, "used_apr": 14.03},
    "Subprime (501–600)": {"low": 501, "high": 600, "used_apr": 19.42},
    "Deep subprime (300–500)": {"low": 300, "high": 500, "used_apr": 21.77},
}

# Tool-defined screening triggers for unusually large deviations. These are
# not legal limits or market ceilings; ordinary deviations remain comparisons.
EXTREME_PRICE_OVER_VALUE_PCT = 20.0
EXTREME_LTV_PCT = 125.0
EXTREME_APR_ABOVE_BENCHMARK_PP = 5.0


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


def _signed_money(value: float | None) -> str:
    if value is None:
        return "—"
    if value > 0:
        return f"+${value:,.2f}"
    if value < 0:
        return f"-${abs(value):,.2f}"
    return "$0.00"


def _signed_percent(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:+.{digits}f}%"


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    vehicle_status = str(data.get("vehicleStatus") or "—")
    year = str(data.get("year") or "").strip()
    make = str(data.get("make") or "").strip()
    model = str(data.get("model") or "").strip()
    vehicle_name = " ".join(part for part in (year, make, model) if part) or "—"
    mileage = _num(data.get("mileage"))
    condition = str(data.get("condition") or "—")

    cash_price = _num(data.get("cashPrice"))
    supported_value = _num(data.get("supportedValue"))
    value_source = str(data.get("valueSource") or "—")

    taxes_fees = _num(data.get("taxesFees"))
    gap = _num(data.get("gap"))
    warranty = _num(data.get("warranty"))
    other_addons = _num(data.get("otherAddons"))

    apr = _num(data.get("apr"))
    stated_rate = _num(data.get("statedRate"))
    amount_financed = _num(data.get("amountFinanced"))
    monthly_payment = _num(data.get("monthlyPayment"))
    term_months = _num(data.get("termMonths"))
    cash_down = _num(data.get("cashDown"))
    cash_down_entered = bool(data.get("cashDownEntered"))
    total_payments = _num(data.get("totalPayments"))
    finance_charge = _num(data.get("financeCharge"))
    lender = str(data.get("lender") or "—")
    financing_channel = str(data.get("financingChannel") or "Unknown")

    credit_score = _num(data.get("creditScore"))
    credit_tier = str(data.get("creditTier") or "—")

    review_items: list[dict[str, str]] = []

    def add_review(text: str) -> None:
        review_items.append({"label": "Review:", "text": text})

    price_difference = None
    price_difference_pct = None
    if supported_value > 0 and cash_price > 0:
        price_difference = cash_price - supported_value
        price_difference_pct = price_difference / supported_value * 100
        if price_difference_pct > EXTREME_PRICE_OVER_VALUE_PCT:
            add_review(
                f"cash price is {_percent(price_difference_pct)} above the entered supported vehicle value "
                f"({_money(price_difference)} higher)."
            )

    ltv = None
    amount_above_value = None
    if supported_value > 0 and amount_financed > 0:
        ltv = amount_financed / supported_value * 100
        amount_above_value = amount_financed - supported_value
        if ltv > EXTREME_LTV_PCT:
            add_review(
                f"amount financed equals {_percent(ltv)} of the entered supported vehicle value "
                f"and exceeds that value by {_money(amount_above_value)}."
            )

    down_payment_pct = None
    if cash_down_entered and cash_price > 0:
        down_payment_pct = cash_down / cash_price * 100

    financed_addons = gap + warranty + other_addons
    financed_addons_share = (
        financed_addons / amount_financed * 100
        if financed_addons > 0 and amount_financed > 0
        else None
    )

    total_financed_extras = taxes_fees + financed_addons
    total_financed_extras_share = (
        total_financed_extras / amount_financed * 100
        if total_financed_extras > 0 and amount_financed > 0
        else None
    )

    tier_info = TIER_DATA.get(credit_tier)
    benchmark_apr = None
    apr_difference = None

    if vehicle_status == "Used" and apr > 0 and tier_info:
        benchmark_apr = float(tier_info["used_apr"])
        apr_difference = apr - benchmark_apr
        if apr_difference > EXTREME_APR_ABOVE_BENCHMARK_PP:
            add_review(
                f"APR is {apr_difference:.2f} percentage points above the Q1 2026 Experian "
                f"used-auto average for the selected VantageScore 4.0 tier."
            )

    if credit_score > 0 and tier_info:
        low = int(tier_info["low"])
        high = int(tier_info["high"])
        if not (low <= credit_score <= high):
            review_items.append({
                "label": "Record check:",
                "text": (
                    f"entered credit score {int(credit_score)} does not fall within the selected "
                    f"VantageScore 4.0 tier range of {low}–{high}."
                ),
            })

    if vehicle_status != "Used":
        rate_note = "No APR benchmark comparison is shown because the embedded benchmark is for used vehicles."
    elif not tier_info:
        rate_note = "No APR benchmark comparison is shown because the selected score information is unavailable or uses a different model."
    elif apr <= 0:
        rate_note = "No APR benchmark comparison is shown because APR was not entered. Interest rate is not substituted for APR."
    else:
        rate_note = (
            "Q1 2026 Experian used-vehicle tier average. Reference point only, not a ceiling. "
            "Only an unusually large deviation triggers a screening flag."
        )

    price_vs_value = "—"
    if price_difference is not None and price_difference_pct is not None:
        price_vs_value = f"{_signed_money(price_difference)} ({_signed_percent(price_difference_pct)})"

    down_payment_display = "—"
    if cash_down_entered and down_payment_pct is not None:
        down_payment_display = f"{_money(cash_down)} ({_percent(down_payment_pct)})"

    financed_addons_display = "—"
    if financed_addons > 0 and financed_addons_share is not None:
        financed_addons_display = f"{_money(financed_addons)} ({_percent(financed_addons_share)} of amount financed)"

    total_extras_display = "—"
    if total_financed_extras > 0 and total_financed_extras_share is not None:
        total_extras_display = f"{_money(total_financed_extras)} ({_percent(total_financed_extras_share)} of amount financed)"

    vehicle_summary = [
        ["Vehicle", vehicle_name],
        ["Mileage / condition", f"{int(mileage):,} / {condition}" if mileage > 0 else condition],
        ["Supported vehicle value", _money(supported_value) if supported_value > 0 else "—"],
        ["Value source", value_source],
        ["Cash price", _money(cash_price)],
        ["Price vs. value", price_vs_value],
        ["Amount financed", _money(amount_financed)],
        ["LTV", _percent(ltv)],
        ["Monthly payment / term", f"{_money(monthly_payment)} / {int(term_months)} months"],
        ["Down payment", down_payment_display],
        ["Finance charge", _money(finance_charge) if finance_charge > 0 else "—"],
        ["Total of payments", _money(total_payments) if total_payments > 0 else "—"],
        ["Financed add-ons", financed_addons_display],
        ["Total entered financed extras", total_extras_display],
        ["How financing was obtained", financing_channel],
        ["Lender / creditor", lender],
    ]

    rate_summary = [
        ["Credit tier", credit_tier],
        ["Credit score", str(int(credit_score)) if credit_score > 0 else "—"],
        ["Interest rate", f"{stated_rate:.2f}%" if stated_rate > 0 else "—"],
        ["Proposed APR", f"{apr:.2f}%" if apr > 0 else "—"],
        ["Q1 2026 used-auto benchmark", f"{benchmark_apr:.2f}%" if benchmark_apr is not None else "—"],
        ["Difference", f"{apr_difference:+.2f} percentage points" if apr_difference is not None else "—"],
    ]

    return {
        "vehicleSummary": vehicle_summary,
        "rateSummary": rate_summary,
        "rateNote": rate_note,
        "reviewItems": review_items,
    }
