"use strict";

const $ = (id) => document.getElementById(id);
let pyodideReady = false;
let calculator = null;

function numberValue(id) {
  const el = $(id);
  if (!el) return 0;
  const value = parseFloat(el.value);
  return Number.isFinite(value) ? value : 0;
}

function textValue(id) {
  const el = $(id);
  return el ? (el.value || "").trim() : "";
}

function radioValue(name) {
  const selected = document.querySelector(`input[name="${name}"]:checked`);
  return selected ? selected.value : "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function collectData() {
  return {
    vehicleStatus: textValue("vehicleStatus"),
    year: textValue("year"),
    make: textValue("make"),
    model: textValue("model"),
    mileage: numberValue("mileage"),
    condition: textValue("condition"),
    vin: textValue("vin"),
    cashPrice: numberValue("cashPrice"),
    supportedValue: numberValue("supportedValue"),
    valueSource: textValue("valueSource"),

    taxesFees: numberValue("taxesFees"),
    gap: numberValue("gap"),
    warranty: numberValue("warranty"),
    otherAddons: numberValue("otherAddons"),
    otherFinanced: numberValue("otherFinanced"),
    rebatesCredits: numberValue("rebatesCredits"),
    itemizationComplete: $("itemizationComplete").checked,

    apr: numberValue("apr"),
    amountFinanced: numberValue("amountFinanced"),
    monthlyPayment: numberValue("monthlyPayment"),
    termMonths: numberValue("termMonths"),
    cashDown: numberValue("cashDown"),
    totalPayments: numberValue("totalPayments"),
    financeCharge: numberValue("financeCharge"),
    statedRate: numberValue("statedRate"),
    lender: textValue("lender"),
    financingChannel: radioValue("financingChannel"),

    creditScore: numberValue("creditScore"),
    scoreModel: textValue("scoreModel"),
    grossIncome: numberValue("grossIncome"),
    benchmarkApr: numberValue("benchmarkApr"),
    benchmarkLabel: textValue("benchmarkLabel"),
    financingAttempts: textValue("financingAttempts"),

    planPayment: numberValue("planPayment"),
    currentNetIncome: numberValue("currentNetIncome"),
    replacedVehiclePayment: numberValue("replacedVehiclePayment"),
    currentInsurance: numberValue("currentInsurance"),
    projectedInsurance: numberValue("projectedInsurance"),
    otherVehicleCostChange: numberValue("otherVehicleCostChange"),
    monthlyIncomeChange: numberValue("monthlyIncomeChange"),
    scheduleDate: textValue("scheduleDate"),
    planStatus: textValue("planStatus"),
    deficitExplanation: textValue("deficitExplanation")
  };
}

function missingRequiredFields(data) {
  const missing = [];
  if (!data.vehicleStatus) missing.push("Vehicle status");
  if (!data.year) missing.push("Year");
  if (!data.make) missing.push("Make");
  if (!data.model) missing.push("Model");
  if (!(data.cashPrice > 0)) missing.push("Dealer cash price");
  if (!(data.amountFinanced > 0)) missing.push("Amount financed");
  if (!(data.monthlyPayment > 0)) missing.push("Monthly payment");
  if (!(data.termMonths > 0)) missing.push("Loan term / number of payments");
  if (!(data.apr > 0) && !(data.statedRate > 0)) missing.push("APR or stated interest rate");
  if (textValue("planPayment") === "") missing.push("Current monthly plan payment");
  if (textValue("currentNetIncome") === "") missing.push("Current Schedule J monthly net income");
  if (textValue("replacedVehiclePayment") === "") missing.push("Vehicle payment being replaced");

  const insuranceOneOnly = (textValue("currentInsurance") === "") !== (textValue("projectedInsurance") === "");
  if (insuranceOneOnly) missing.push("Both current and projected vehicle insurance, or neither");

  const vehiclePaymentChange = data.monthlyPayment - data.replacedVehiclePayment;
  const insuranceChange = (textValue("currentInsurance") !== "" && textValue("projectedInsurance") !== "")
    ? data.projectedInsurance - data.currentInsurance
    : 0;
  const netVehicleCostChange = vehiclePaymentChange + insuranceChange + data.otherVehicleCostChange;
  const projectedNet = data.currentNetIncome + data.monthlyIncomeChange - netVehicleCostChange;
  const projectedRemaining = projectedNet - data.planPayment;
  if (projectedRemaining < 0 && !data.deficitExplanation) {
    missing.push("Explanation for projected budget deficit");
  }
  return missing;
}

function render(output) {
  $("metricLtv").textContent = output.metrics.ltv;
  $("metricAboveValue").textContent = output.metrics.amountAboveValue;
  $("metricPti").textContent = output.metrics.pti;
  $("metricProjectedNet").textContent = output.metrics.projectedNetIncome;
  $("metricBudgetCushion").textContent = output.metrics.budgetCushion;
  $("metricAprDiff").textContent = output.metrics.aprDifference;

  const resultsBody = $("resultsBody");
  resultsBody.innerHTML = output.results.map(([section, item, result]) =>
    `<tr><td>${escapeHtml(section)}</td><td>${escapeHtml(item)}</td><td>${escapeHtml(result)}</td></tr>`
  ).join("");

  const empty = $("flagsEmpty");
  const wrap = $("flagsTableWrap");
  const body = $("flagsBody");

  if (!output.reviewItems.length) {
    empty.classList.remove("hidden");
    wrap.classList.add("hidden");
    body.innerHTML = "";
  } else {
    empty.classList.add("hidden");
    wrap.classList.remove("hidden");
    body.innerHTML = output.reviewItems.map(entry =>
      `<tr><td>${escapeHtml(entry.area)}</td><td>${escapeHtml(entry.item)}</td><td>${escapeHtml(entry.basis)}</td></tr>`
    ).join("");
  }

  $("reviewPrompt").classList.add("hidden");
  $("reviewOutput").classList.remove("hidden");
}

async function runReview() {
  if (!pyodideReady || !calculator) {
    alert("The calculator is still loading. Please try again once Python is ready.");
    return;
  }

  const data = collectData();
  const missing = missingRequiredFields(data);
  if (missing.length) {
    alert(`Please complete the following required field${missing.length > 1 ? "s" : ""}:\n\n${missing.join("\n")}`);
    return;
  }

  const pyData = pyodide.toPy(data);
  const pyResult = calculator.evaluate(pyData);
  const result = pyResult.toJs({
    dict_converter: Object.fromEntries,
    create_proxies: false
  });
  pyData.destroy();
  pyResult.destroy();
  render(result);
}

async function bootPython() {
  try {
    window.pyodide = await loadPyodide();
    const response = await fetch("calculator.py");
    const source = await response.text();
    pyodide.FS.writeFile("calculator.py", source);
    calculator = pyodide.pyimport("calculator");
    pyodideReady = true;

    const status = $("pythonStatus");
    status.textContent = "Python ready";
    status.classList.add("ready");
  } catch (error) {
    console.error(error);
    const status = $("pythonStatus");
    status.textContent = "Python failed to load";
    status.classList.add("error");
  }
}

function clearAll() {
  document.querySelectorAll("input").forEach((el) => {
    if (el.type === "checkbox") {
      el.checked = false;
    } else if (el.type === "radio") {
      el.checked = el.name === "financingChannel" && el.value === "Unknown";
    } else {
      el.value = "";
    }
  });
  document.querySelectorAll("select").forEach((el) => {
    el.selectedIndex = 0;
  });
  $("vehicleStatus").value = "Used";
  $("planStatus").value = "Unknown";
  $("reviewOutput").classList.add("hidden");
  $("reviewPrompt").classList.remove("hidden");
}

document.addEventListener("DOMContentLoaded", async () => {
  $("runButton").addEventListener("click", runReview);
  $("printButton").addEventListener("click", () => window.print());
  $("clearButton").addEventListener("click", clearAll);
  await bootPython();
});
