/* Emory Financial — mortgage calculators
   All figures are estimates for planning only. Real terms come from a lender's Loan Estimate. */
(function () {
  "use strict";

  var usd0 = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  var usd2 = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

  function num(id, fallback) {
    var el = document.getElementById(id);
    if (!el) return fallback;
    var v = parseFloat(String(el.value).replace(/,/g, ""));
    return isFinite(v) ? v : fallback;
  }
  function set(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }
  function setHTML(id, html) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  /* Monthly principal & interest */
  function pmt(principal, annualRate, years) {
    var r = annualRate / 100 / 12, n = years * 12;
    if (principal <= 0 || n <= 0) return 0;
    if (r === 0) return principal / n;
    return principal * r / (1 - Math.pow(1 + r, -n));
  }

  /* ============ 1. Monthly payment ============ */
  function runPayment() {
    var price = num("p-price", 900000);
    var downPct = num("p-down", 20);
    var rate = num("p-rate", 6.25);
    var term = num("p-term", 30);
    var taxRate = num("p-tax", 1.15);
    var ins = num("p-ins", 150);
    var hoa = num("p-hoa", 0);

    var down = price * (downPct / 100);
    var loan = Math.max(price - down, 0);
    var pi = pmt(loan, rate, term);
    var tax = (price * (taxRate / 100)) / 12;

    // PMI estimate: roughly 0.5%/yr of loan when LTV > 80%
    var ltv = price > 0 ? (loan / price) * 100 : 0;
    var pmi = ltv > 80 ? (loan * 0.005) / 12 : 0;

    var total = pi + tax + ins + hoa + pmi;

    set("p-out-total", usd0.format(Math.round(total)));
    set("p-out-loan", usd0.format(Math.round(loan)));
    set("p-out-down", usd0.format(Math.round(down)));
    set("p-out-pi", usd0.format(Math.round(pi)));
    set("p-out-tax", usd0.format(Math.round(tax)));
    set("p-out-ins", usd0.format(Math.round(ins)));
    set("p-out-hoa", usd0.format(Math.round(hoa)));
    set("p-out-pmi", pmi > 0 ? usd0.format(Math.round(pmi)) : "—");
    set("p-down-label", downPct.toFixed(0) + "%");

    var lifetime = pi * term * 12 - loan;
    setHTML("p-out-note", ltv > 80
      ? "At " + ltv.toFixed(0) + "% loan-to-value this estimate includes mortgage insurance. It drops off once you reach 20% equity. Total interest over " + term + " years: <strong>" + usd0.format(Math.round(lifetime)) + "</strong>."
      : "No mortgage insurance at " + ltv.toFixed(0) + "% loan-to-value. Total interest over " + term + " years: <strong>" + usd0.format(Math.round(lifetime)) + "</strong>.");
  }

  /* ============ 2. Affordability ============ */
  function runAfford() {
    var income = num("a-income", 220000);
    var debts = num("a-debts", 800);
    var down = num("a-down", 200000);
    var rate = num("a-rate", 6.25);
    var term = num("a-term", 30);
    var dti = num("a-dti", 43);
    var taxRate = num("a-tax", 1.15);
    var insMo = num("a-ins", 150);

    var monthlyIncome = income / 12;
    var budget = monthlyIncome * (dti / 100) - debts;
    if (budget < 0) budget = 0;

    // Solve for price: budget = PI(price - down) + tax(price) + insurance
    var r = rate / 100 / 12, n = term * 12;
    var factor = r === 0 ? 1 / n : r / (1 - Math.pow(1 + r, -n));
    var monthlyTaxRate = (taxRate / 100) / 12;
    // budget - insMo = (price - down)*factor + price*monthlyTaxRate
    var avail = budget - insMo;
    var price = (avail + down * factor) / (factor + monthlyTaxRate);
    if (!isFinite(price) || price < 0) price = 0;

    var loan = Math.max(price - down, 0);
    var pi = pmt(loan, rate, term);
    var tax = (price * (taxRate / 100)) / 12;

    set("a-out-price", usd0.format(Math.round(price)));
    set("a-out-loan", usd0.format(Math.round(loan)));
    set("a-out-budget", usd0.format(Math.round(budget)));
    set("a-out-pi", usd0.format(Math.round(pi)));
    set("a-out-tax", usd0.format(Math.round(tax)));
    set("a-out-ins", usd0.format(Math.round(insMo)));
    set("a-dti-label", dti.toFixed(0) + "%");

    var pctDown = price > 0 ? (down / price) * 100 : 0;
    setHTML("a-out-note", "That down payment is about <strong>" + pctDown.toFixed(0) +
      "%</strong> of the estimated price. Lenders weigh credit, reserves and property type too — this is a starting point, not a pre-approval.");
  }

  /* ============ 3. Refinance break-even ============ */
  function runRefi() {
    var bal = num("r-balance", 600000);
    var curRate = num("r-cur-rate", 7.25);
    var curLeft = num("r-cur-left", 26);
    var newRate = num("r-new-rate", 6.0);
    var newTerm = num("r-new-term", 30);
    var costs = num("r-costs", 6500);

    var curPay = pmt(bal, curRate, curLeft);
    var newPay = pmt(bal + costs, newRate, newTerm);
    var newPayNoRoll = pmt(bal, newRate, newTerm);
    var savings = curPay - newPayNoRoll;

    set("r-out-savings", (savings >= 0 ? "" : "−") + usd0.format(Math.round(Math.abs(savings))));
    set("r-out-cur", usd0.format(Math.round(curPay)));
    set("r-out-new", usd0.format(Math.round(newPayNoRoll)));
    set("r-out-costs", usd0.format(Math.round(costs)));

    if (savings > 0) {
      var months = costs / savings;
      set("r-out-be", months < 120 ? months.toFixed(0) + " months" : "Over 10 years");
      var curTotal = curPay * curLeft * 12;
      var newTotal = newPayNoRoll * newTerm * 12 + costs;
      var diff = curTotal - newTotal;
      setHTML("r-out-note", "You'd recover the closing costs in about <strong>" + months.toFixed(0) +
        " months</strong>. Note the new loan stretches back out to " + newTerm + " years — over the full term that's " +
        (diff >= 0 ? "still about <strong>" + usd0.format(Math.round(diff)) + " less</strong> paid overall."
                   : "about <strong>" + usd0.format(Math.round(-diff)) + " more</strong> paid overall, even with the lower payment. Worth a conversation about term.") );
    } else {
      set("r-out-be", "No break-even");
      setHTML("r-out-note", "At these numbers the new payment isn't lower, so there's no break-even. A refinance can still make sense to pull cash out, drop mortgage insurance, or leave an adjustable rate — <strong>let's talk about the goal, not just the rate</strong>.");
    }
  }

  /* ============ 4. Extra payment ============ */
  function amortize(principal, annualRate, years, extra) {
    var r = annualRate / 100 / 12;
    var base = pmt(principal, annualRate, years);
    var bal = principal, months = 0, interest = 0;
    var cap = years * 12 + 600;
    while (bal > 0.5 && months < cap) {
      var i = bal * r;
      var pr = base + extra - i;
      if (pr <= 0) return { months: Infinity, interest: Infinity, payment: base };
      if (pr > bal) pr = bal;
      bal -= pr; interest += i; months++;
    }
    return { months: months, interest: interest, payment: base };
  }

  function runExtra() {
    var loan = num("e-loan", 700000);
    var rate = num("e-rate", 6.25);
    var term = num("e-term", 30);
    var extra = num("e-extra", 300);

    var base = amortize(loan, rate, term, 0);
    var withExtra = amortize(loan, rate, term, extra);

    var savedInterest = base.interest - withExtra.interest;
    var savedMonths = base.months - withExtra.months;

    set("e-out-saved", usd0.format(Math.round(savedInterest)));
    set("e-out-base-pay", usd0.format(Math.round(base.payment)));
    set("e-out-new-pay", usd0.format(Math.round(base.payment + extra)));
    set("e-out-base-int", usd0.format(Math.round(base.interest)));
    set("e-out-new-int", usd0.format(Math.round(withExtra.interest)));

    var yrs = Math.floor(savedMonths / 12), mos = Math.round(savedMonths % 12);
    set("e-out-time", (yrs > 0 ? yrs + " yr " : "") + mos + " mo");
    setHTML("e-out-note", "Adding <strong>" + usd0.format(extra) + "</strong> a month pays the loan off " +
      (yrs > 0 ? "<strong>" + yrs + " years " + mos + " months</strong>" : "<strong>" + mos + " months</strong>") +
      " early. Every extra dollar goes straight to principal — there's no prepayment penalty on the loans we place.");
  }

  /* ---------- Wire up ---------- */
  var calcs = [
    { ids: ["p-price", "p-down", "p-rate", "p-term", "p-tax", "p-ins", "p-hoa"], run: runPayment },
    { ids: ["a-income", "a-debts", "a-down", "a-rate", "a-term", "a-dti", "a-tax", "a-ins"], run: runAfford },
    { ids: ["r-balance", "r-cur-rate", "r-cur-left", "r-new-rate", "r-new-term", "r-costs"], run: runRefi },
    { ids: ["e-loan", "e-rate", "e-term", "e-extra"], run: runExtra }
  ];

  calcs.forEach(function (c) {
    var present = c.ids.filter(function (id) { return document.getElementById(id); });
    if (!present.length) return;
    present.forEach(function (id) {
      var el = document.getElementById(id);
      el.addEventListener("input", c.run);
      el.addEventListener("change", c.run);
    });
    c.run();
  });
})();
