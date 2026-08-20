"use strict";

const $ = (id) => document.getElementById(id);
let pyodideReady = false;
let calculator = null;
let pendingExampleRun = false;

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
    cashPrice: numberValue("cashPrice"),
    supportedValue: numberValue("supportedValue"),
    valueSource: textValue("valueSource"),
    taxesFees: numberValue("taxesFees"),
    gap: numberValue("gap"),
    warranty: numberValue("warranty"),
    otherAddons: numberValue("otherAddons"),
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
  if (!(data.apr > 0)) missing.push("APR");
  if (!(data.amountFinanced > 0)) missing.push("Amount financed");
  if (!(data.monthlyPayment > 0)) missing.push("Monthly payment");
  if (!(data.termMonths > 0)) missing.push("Loan term / number of payments");
  if (!data.creditTier) missing.push("Experian Q1 2026 VantageScore 4.0 credit tier or unavailable");
  return missing;
}

function renderPairs(containerId, rows) {
  $(containerId).innerHTML = rows.map(([label, value]) =>
    `<div class="review-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`
  ).join("");
}

function render(output) {
  renderPairs("vehicleSummary", output.vehicleSummary);
  renderPairs("rateSummary", output.rateSummary);
  $("rateNote").textContent = output.rateNote || "";

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
  const result = pyResult.toJs({dict_converter: Object.fromEntries, create_proxies: false});
  pyData.destroy();
  pyResult.destroy();
  render(result);
}

function randomStep(min, max, step) {
  const count = Math.floor((max - min) / step);
  return min + Math.floor(Math.random() * (count + 1)) * step;
}

function randomDecimal(min, max, digits = 2) {
  return Number((min + Math.random() * (max - min)).toFixed(digits));
}

function choose(values) {
  return values[Math.floor(Math.random() * values.length)];
}

function setValue(id, value) {
  $(id).value = value;
}

function setFinancingChannel(value) {
  document.querySelectorAll('input[name="financingChannel"]').forEach((el) => {
    el.checked = el.value === value;
  });
}

function amortizedPayment(principal, annualRate, months) {
  const monthlyRate = annualRate / 1200;
  if (monthlyRate === 0) return principal / months;
  return principal * monthlyRate / (1 - Math.pow(1 + monthlyRate, -months));
}

async function loadExample() {
  clearAll();

  const vehicle = choose([
    {year: 2019, make: "Honda", model: "CR-V"},
    {year: 2020, make: "Toyota", model: "Camry"},
    {year: 2020, make: "Nissan", model: "Rogue"},
    {year: 2021, make: "Hyundai", model: "Tucson"}
  ]);

  const tier = choose([
    {
      name: "Near prime (601–660)", scoreMin: 615, scoreMax: 655,
      aprMin: 17.75, aprMax: 19.50,
      channel: "Dealer-arranged through outside lender",
      lender: "Outside auto finance company (illustrative)"
    },
    {
      name: "Subprime (501–600)", scoreMin: 525, scoreMax: 590,
      aprMin: 22.50, aprMax: 24.75,
      channel: "Dealer financing in-house / BHPH",
      lender: "Dealer in-house financing (illustrative)"
    }
  ]);

  const supportedValue = randomStep(15500, 22000, 100);
  const cashPrice = supportedValue + randomStep(1500, 2800, 100);
  const taxesFees = randomStep(1000, 1700, 50);
  const gap = randomStep(650, 950, 50);
  const warranty = randomStep(1300, 2200, 100);
  const otherAddons = randomStep(300, 700, 50);
  const cashDown = randomStep(500, 1500, 100);
  const amountFinanced = cashPrice + taxesFees + gap + warranty + otherAddons - cashDown;
  const apr = randomDecimal(tier.aprMin, tier.aprMax, 2);
  const statedRate = Math.max(0.01, Number((apr - randomDecimal(0.65, 1.20, 2)).toFixed(2)));
  const termMonths = choose([60, 72]);
  const monthlyPayment = Number(amortizedPayment(amountFinanced, statedRate, termMonths).toFixed(2));
  const totalPayments = Number((monthlyPayment * termMonths).toFixed(2));
  const financeCharge = Number((totalPayments - amountFinanced).toFixed(2));
  const age = 2026 - vehicle.year;
  const mileage = randomStep(age * 9000, age * 15000, 1000);

  setValue("vehicleStatus", "Used");
  setValue("year", vehicle.year);
  setValue("make", vehicle.make);
  setValue("model", vehicle.model);
  setValue("mileage", mileage);
  setValue("condition", choose(["Good", "Fair"]));
  setValue("cashPrice", cashPrice);
  setValue("supportedValue", supportedValue);
  setValue("valueSource", "Debtor-provided KBB estimate (illustrative)");
  setValue("taxesFees", taxesFees);
  setValue("gap", gap);
  setValue("warranty", warranty);
  setValue("otherAddons", otherAddons);
  setValue("apr", apr);
  setValue("statedRate", statedRate);
  setValue("amountFinanced", amountFinanced);
  setValue("monthlyPayment", monthlyPayment);
  setValue("termMonths", termMonths);
  setValue("cashDown", cashDown);
  setValue("totalPayments", totalPayments);
  setValue("financeCharge", financeCharge);
  setValue("lender", tier.lender);
  setValue("creditTier", tier.name);
  setValue("creditScore", randomStep(tier.scoreMin, tier.scoreMax, 1));
  setFinancingChannel(tier.channel);

  const extras = document.querySelector(".optional-details");
  if (extras) extras.open = true;

  if (pyodideReady && calculator) {
    await runReview();
  } else {
    pendingExampleRun = true;
    $("reviewPrompt").textContent = "Example loaded. The review will run when Python is ready.";
  }
}

async function bootPython() {
  try {
    window.pyodide = await loadPyodide();
    const response = await fetch(`calculator.py?v=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Calculator load failed: ${response.status}`);
    const source = await response.text();
    pyodide.FS.writeFile("calculator.py", source);
    calculator = pyodide.pyimport("calculator");
    pyodideReady = true;

    const status = $("pythonStatus");
    status.textContent = "Python ready";
    status.classList.add("ready");

    if (pendingExampleRun) {
      pendingExampleRun = false;
      await runReview();
    }
  } catch (error) {
    console.error(error);
    const status = $("pythonStatus");
    status.textContent = "Python failed to load";
    status.classList.add("error");
  }
}

function clearAll() {
  pendingExampleRun = false;
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
  const extras = document.querySelector(".optional-details");
  if (extras) extras.open = false;
  $("reviewOutput").classList.add("hidden");
  $("reviewPrompt").classList.remove("hidden");
  $("reviewPrompt").textContent = "Complete the required fields above, then select Run review.";
}

document.addEventListener("DOMContentLoaded", async () => {
  $("exampleButton").addEventListener("click", loadExample);
  $("runButton").addEventListener("click", runReview);
  $("printPageButton").addEventListener("click", () => window.print());
  $("clearButton").addEventListener("click", clearAll);
  await bootPython();
});