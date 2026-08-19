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

    apr: numberValue("apr"),
    amountFinanced: numberValue("amountFinanced"),
    cashDown: numberValue("cashDown"),
    monthlyPayment: numberValue("monthlyPayment"),
    termMonths: numberValue("termMonths"),
    totalPayments: numberValue("totalPayments"),
    financeCharge: numberValue("financeCharge"),
    statedRate: numberValue("statedRate"),
    lender: textValue("lender"),
    financingChannel: radioValue("financingChannel"),

    hasTrade: $("hasTrade").checked,
    tradeAllowance: numberValue("tradeAllowance"),
    tradePayoff: numberValue("tradePayoff"),

    itemizationComplete: $("itemizationComplete").checked,
    taxesFees: numberValue("taxesFees"),
    gap: numberValue("gap"),
    warranty: numberValue("warranty"),
    otherAddons: numberValue("otherAddons"),
    otherFinanced: numberValue("otherFinanced"),
    rebatesCredits: numberValue("rebatesCredits"),

    creditScore: numberValue("creditScore"),
    scoreModel: textValue("scoreModel"),
    grossIncome: numberValue("grossIncome"),
    monthlyDebt: numberValue("monthlyDebt"),
    benchmarkApr: numberValue("benchmarkApr"),
    benchmarkLabel: textValue("benchmarkLabel"),
    equalPayments: $("equalPayments").checked
  };
}

function render(output) {
  document.getElementById("metricLtv").textContent = output.metrics.ltv;
  document.getElementById("metricAboveValue").textContent = output.metrics.amountAboveValue;
  document.getElementById("metricTradeEquity").textContent = output.metrics.tradeEquity;
  document.getElementById("metricAprDiff").textContent = output.metrics.aprDifference;

  const resultsBody = document.getElementById("resultsBody");
  resultsBody.innerHTML = output.results.map(([section, item, result]) =>
    `<tr><td>${escapeHtml(section)}</td><td>${escapeHtml(item)}</td><td>${escapeHtml(result)}</td></tr>`
  ).join("");

  const empty = document.getElementById("flagsEmpty");
  const wrap = document.getElementById("flagsTableWrap");
  const body = document.getElementById("flagsBody");

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
}

async function calculate() {
  if (!pyodideReady || !calculator) return;
  const data = collectData();
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

    const status = document.getElementById("pythonStatus");
    status.textContent = "Python ready";
    status.classList.add("ready");
    await calculate();
  } catch (error) {
    console.error(error);
    const status = document.getElementById("pythonStatus");
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

  document.getElementById("vehicleStatus").value = "Used";
  document.getElementById("condition").value = "";
  document.getElementById("tradeFields").classList.add("hidden");
  calculate();
}

document.addEventListener("DOMContentLoaded", async () => {
  document.getElementById("hasTrade").addEventListener("change", () => {
    document.getElementById("tradeFields").classList.toggle(
      "hidden",
      !document.getElementById("hasTrade").checked
    );
    calculate();
  });
  document.querySelectorAll("input, select").forEach((el) => {
    el.addEventListener("input", calculate);
    el.addEventListener("change", calculate);
  });
  document.getElementById("printButton").addEventListener("click", () => window.print());
  document.getElementById("clearButton").addEventListener("click", clearAll);
  await bootPython();
});
