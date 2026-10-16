/* Emory Financial — site behaviour */
(function () {
  "use strict";

  /* ---------- Mobile navigation ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var links = document.getElementById("nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    links.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
    // tapping anywhere outside closes it
    document.addEventListener("click", function (e) {
      if (!links.classList.contains("is-open")) return;
      if (links.contains(e.target) || toggle.contains(e.target)) return;
      links.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && links.classList.contains("is-open")) {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  /* ---------- Scroll reveal ---------- */
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var revealables = document.querySelectorAll(".reveal");
  if (reduced || !("IntersectionObserver" in window)) {
    revealables.forEach(function (el) { el.classList.add("is-in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealables.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Current year ---------- */
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });

  /* ---------- Tabs ---------- */
  document.querySelectorAll("[data-tabs]").forEach(function (group) {
    var tabs = group.querySelectorAll(".tab");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        tabs.forEach(function (t) {
          t.setAttribute("aria-selected", "false");
          var p = document.getElementById(t.getAttribute("aria-controls"));
          if (p) p.hidden = true;
        });
        tab.setAttribute("aria-selected", "true");
        var panel = document.getElementById(tab.getAttribute("aria-controls"));
        if (panel) panel.hidden = false;
      });
    });
  });

  /* ---------- Hero: principal vs. interest over the life of a loan ---------- */
  var chart = document.getElementById("amort-chart");
  if (chart) {
    var P = 750000, annual = 0.0625, years = 30;
    var r = annual / 12, n = years * 12;
    var pay = P * r / (1 - Math.pow(1 + r, -n));

    // Yearly interest / principal split
    var bal = P, data = [];
    for (var y = 0; y < years; y++) {
      var yi = 0, yp = 0;
      for (var m = 0; m < 12; m++) {
        var i = bal * r, pr = pay - i;
        yi += i; yp += pr; bal -= pr;
      }
      data.push({ year: y + 1, interest: yi, principal: yp });
    }

    var W = 520, H = 250, padL = 6, padR = 6, padT = 10, padB = 26;
    var iw = W - padL - padR, ih = H - padT - padB;
    var maxY = Math.max.apply(null, data.map(function (d) { return d.interest + d.principal; }));
    var x = function (idx) { return padL + (idx / (years - 1)) * iw; };
    var yv = function (v) { return padT + ih - (v / maxY) * ih; };

    function areaPath(key, stacked) {
      var top = "", bottom = "";
      data.forEach(function (d, idx) {
        var upper = stacked ? d.principal + d.interest : d.principal;
        top += (idx === 0 ? "M" : "L") + x(idx).toFixed(1) + "," + yv(upper).toFixed(1) + " ";
      });
      for (var idx = data.length - 1; idx >= 0; idx--) {
        var lower = stacked ? data[idx].principal : 0;
        bottom += "L" + x(idx).toFixed(1) + "," + yv(lower).toFixed(1) + " ";
      }
      return top + bottom + "Z";
    }

    var gridLines = "";
    for (var g = 1; g <= 3; g++) {
      var gy = padT + (ih / 4) * g;
      gridLines += '<line x1="' + padL + '" y1="' + gy.toFixed(1) + '" x2="' + (W - padR) + '" y2="' + gy.toFixed(1) +
        '" stroke="rgba(255,255,255,.10)" stroke-width="1"/>';
    }

    var ticks = "";
    [1, 10, 20, 30].forEach(function (t) {
      var tx = x(t - 1);
      ticks += '<text x="' + tx.toFixed(1) + '" y="' + (H - 6) +
        '" fill="rgba(255,255,255,.45)" font-family="IBM Plex Mono, monospace" font-size="10" text-anchor="' +
        (t === 1 ? "start" : t === 30 ? "end" : "middle") + '">Yr ' + t + "</text>";
    });

    chart.innerHTML =
      '<svg viewBox="0 0 ' + W + " " + H + '" role="img" width="100%" ' +
      'aria-label="Stacked area chart showing that on a 30-year fixed loan, early payments are mostly interest and later payments are mostly principal.">' +
      gridLines +
      '<path d="' + areaPath("i", true) + '" fill="rgba(193,45,58,.90)" class="amort-area" />' +
      '<path d="' + areaPath("p", false) + '" fill="rgba(240,205,85,.94)" class="amort-area" />' +
      ticks +
      "</svg>";

    if (!reduced) {
      chart.querySelectorAll(".amort-area").forEach(function (el, idx) {
        el.style.opacity = "0";
        el.style.transform = "scaleY(.4)";
        el.style.transformOrigin = "bottom";
        el.style.transition = "opacity .8s ease " + (idx * 0.18 + 0.15) + "s, transform .9s cubic-bezier(.2,.7,.3,1) " + (idx * 0.18 + 0.15) + "s";
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            el.style.opacity = "1";
            el.style.transform = "none";
          });
        });
      });
    }

    var note = document.getElementById("amort-note");
    if (note) {
      var y1 = data[0], y30 = data[29];
      var pct1 = Math.round((y1.interest / (y1.interest + y1.principal)) * 100);
      var pct30 = Math.round((y30.principal / (y30.interest + y30.principal)) * 100);
      note.innerHTML = "On a $750,000 loan at 6.25%, <strong>" + pct1 +
        "% of your first year</strong> goes to interest — and <strong>" + pct30 +
        "% of your last year</strong> goes to principal. Understanding that curve is where the real savings live.";
    }
  }
})();

/* ---------- Form submission, with graceful failure ----------
   Posts via fetch rather than a native form POST. If Netlify is handling
   forms, this records the submission and moves to the thank-you page. If
   anything goes wrong, the visitor sees a message with a phone number and
   email instead of a raw 404 — so an enquiry is never silently lost. */
(function () {
  "use strict";
  var forms = document.querySelectorAll('form[data-netlify="true"]');
  if (!forms.length || !window.fetch) return;

  forms.forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var btn = form.querySelector('button[type="submit"]') || form.querySelector("button");
      var label = btn ? btn.textContent : "";
      var note = form.querySelector(".form-note");
      if (!note) {
        note = document.createElement("p");
        note.className = "form-note";
        note.setAttribute("role", "status");
        note.setAttribute("aria-live", "polite");
        form.appendChild(note);
      }
      note.className = "form-note";
      note.textContent = "";
      if (btn) { btn.disabled = true; btn.textContent = "Sending\u2026"; }

      var action = form.getAttribute("action") || "";
      var external = /^https?:\/\//i.test(action);
      var endpoint = external ? action : "/";
      var opts = external
        ? { method: "POST", headers: { "Accept": "application/json" }, body: new FormData(form) }
        : { method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams(new FormData(form)).toString() };

      fetch(endpoint, opts).then(function (res) {
        if (!res.ok) throw new Error(res.status);
        window.location.href = "/thanks/";
      }).catch(function (err) {
        note.className = "form-note is-error";
        note.innerHTML = "That didn\u2019t go through. Please email " +
          '<a href="mailto:derekshao@emoryfinancial.com">derekshao@emoryfinancial.com</a> or call ' +
          '<a href="tel:+13108695678">310-869-5678</a> \u2014 we\u2019ll pick it up straight away.' +
          '<span class="form-ref">reference ' + (err && err.message ? err.message : "network") + '</span>';
        if (btn) { btn.disabled = false; btn.textContent = label; }
      });
    });
  });
})();

/* ---------- Book-a-consultation chooser ---------- */
(function () {
  "use strict";
  var menus = document.querySelectorAll(".book-menu");
  if (!menus.length) return;

  function close(menu) {
    var btn = menu.querySelector(".book-toggle");
    var panel = menu.querySelector(".book-panel");
    if (!btn || !panel) return;
    panel.classList.remove("is-open");
    btn.setAttribute("aria-expanded", "false");
  }

  menus.forEach(function (menu) {
    var btn = menu.querySelector(".book-toggle");
    var panel = menu.querySelector(".book-panel");
    if (!btn || !panel) return;

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      var open = !panel.classList.contains("is-open");
      menus.forEach(close);
      if (open) {
        panel.classList.add("is-open");
        btn.setAttribute("aria-expanded", "true");
        var first = panel.querySelector("a");
        if (first) first.focus();
      }
    });

    panel.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { close(menu); btn.focus(); }
    });
  });

  document.addEventListener("click", function (e) {
    menus.forEach(function (menu) {
      if (!menu.contains(e.target)) close(menu);
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") menus.forEach(close);
  });
})();
