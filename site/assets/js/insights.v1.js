/* Insights search: filters every article (not just the current page) as the reader types.
   Reads /insights/search.json, built by src/build.py. */
(function () {
  var input = document.getElementById("insights-q");
  var results = document.getElementById("search-results");
  var grid = document.getElementById("article-grid");
  if (!input || !results || !grid) return;
  var pager = document.querySelector(".pager");
  var index = null, loading = null;

  function load() {
    if (index) return Promise.resolve(index);
    if (!loading) {
      loading = fetch("/insights/search.json").then(function (r) { return r.json(); })
        .then(function (d) { index = d; return d; });
    }
    return loading;
  }

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }

  function score(item, terms) {
    var t = item.t.toLowerCase(), c = item.c.toLowerCase(), p = item.p.toLowerCase(), x = item.x.toLowerCase();
    var total = 0;
    for (var i = 0; i < terms.length; i++) {
      var w = terms[i], s = 0;
      if (t.indexOf(w) > -1) s += 6;
      if (p.indexOf(w) > -1) s += 4;
      if (c.indexOf(w) > -1) s += 3;
      if (x.indexOf(w) > -1) s += 1;
      if (!s) return 0;           // every word must appear somewhere
      total += s;
    }
    return total;
  }

  function show(q) {
    var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) {
      results.hidden = true; results.innerHTML = "";
      grid.hidden = false; if (pager) pager.hidden = false;
      return;
    }
    load().then(function (data) {
      var hits = data.map(function (it) { return [score(it, terms), it]; })
        .filter(function (h) { return h[0] > 0; })
        .sort(function (a, b) { return b[0] - a[0] || (a[1].d < b[1].d ? 1 : -1); });
      grid.hidden = true; if (pager) pager.hidden = true; results.hidden = false;
      if (!hits.length) {
        results.innerHTML = '<p class="search-empty">No articles match &ldquo;' + esc(q) +
          '&rdquo; yet. Try a broader word, or <a href="/contact">ask Derek directly</a>; good questions become future articles.</p>';
        return;
      }
      results.innerHTML = '<p class="search-count">' + hits.length + (hits.length === 1 ? " article" : " articles") +
        ' match &ldquo;' + esc(q) + '&rdquo;</p><div class="grid grid-3">' +
        hits.map(function (h) {
          var it = h[1];
          return '<a class="card card-link article-card" href="' + it.u + '">' +
            '<img class="card-cover" src="/insights/img/' + it.u.split("/").pop() + '.jpg" alt="" width="1200" height="630" loading="lazy">' +
            '<span class="card-tag">' + esc(it.p) + '</span><h2>' + esc(it.t) + '</h2><p>' + esc(it.c) +
            '</p><span class="card-more">Read the article &rarr;</span></a>';
        }).join("") + "</div>";
    });
  }

  var timer;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    var q = input.value.trim();
    timer = setTimeout(function () { show(q); }, 120);
  });
  input.addEventListener("focus", load, { once: true });

  // Support links like /insights?q=heloc
  var m = location.search.match(/[?&]q=([^&]+)/);
  if (m) { input.value = decodeURIComponent(m[1].replace(/\+/g, " ")); show(input.value.trim()); }
})();
