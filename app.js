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

    apr: numberValue("apr"),
    amountFinanced: numberValue("amountFinanced"),
    monthlyPayment: numberValue("monthlyPayment"),
    termMonths: numberValue("termMonths"),
    cashDown: numberValue("cashDown"),
    cashDownEntered: textValue("cashDown") !== "",
    totalPayments: numberValue("totalPayments"),
    financeCharge: numberValue("financeCharge"),
    statedRate: numberValue("statedRate"),
    lender: textValue("lender"),
    financingChannel: radioValue("financingChannel"),

    creditTier: textValue("creditTier"),
    creditScore: numberValue("creditScore")
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
  if (!(data.apr > 0) && !(data.statedRate > 0)) missing.push("APR or interest rate");
  if (!data.creditTier) missing.push("Experian Q1 2026 VantageScore 4.0 credit tier or unavailable");
  return missing;
}

function renderPairs(containerId, rows) {
  const container = $(containerId);
  container.innerHTML = rows.map(([label, value]) =>
    `<div class="review-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`
  ).join("");
}

function render(output) {
  renderPairs("vehicleSummary", output.vehicleSummary);
  renderPairs("rateSummary", output.rateSummary);
  $("rateNote").textContent = output.rateNote || "";

  const resultsBody = $("resultsBody");
  resultsBody.innerHTML = output.results.map(([section, item, result]) =>
    `<tr><td>${escapeHtml(section)}</td><td>${escapeHtml(item)}</td><td>${escapeHtml(result)}</td></tr>`
  ).join("");

  const empty = $("flagsEmpty");
  const list = $("flagsList");
  if (!output.reviewItems.length) {
    empty.classList.remove("hidden");
    list.classList.add("hidden");
    list.innerHTML = "";
  } else {
    empty.classList.add("hidden");
    list.classList.remove("hidden");
    list.innerHTML = output.reviewItems.map(entry =>
      `<li><strong>${escapeHtml(entry.label)}</strong> ${escapeHtml(entry.text)}</li>`
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
    if (el.type === "radio") {
      el.checked = el.name === "financingChannel" && el.value === "Unknown";
    } else {
      el.value = "";
    }
  });
  document.querySelectorAll("select").forEach((el) => {
    el.selectedIndex = 0;
  });
  $("vehicleStatus").value = "Used";
  $("reviewOutput").classList.add("hidden");
  $("reviewPrompt").classList.remove("hidden");
}

document.addEventListener("DOMContentLoaded", async () => {
  $("runButton").addEventListener("click", runReview);
  $("printButton").addEventListener("click", () => window.print());
  $("clearButton").addEventListener("click", clearAll);
  await bootPython();
});