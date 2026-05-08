(function () {
  const data = window.populationBookData;

  function makeChart(id, config) {
    const canvas = document.getElementById(id);
    if (!canvas || !window.Chart) return;
    return new Chart(canvas, config);
  }

  function renderMetrics() {
    const strip = document.querySelector("[data-metrics]");
    if (!strip) return;
    strip.innerHTML = data.metrics.map((item) => `
      <article class="metric-card">
        <span>${item.label}</span>
        <strong>${item.value}</strong>
        <em>${item.sub}</em>
      </article>
    `).join("");
  }

  function renderCharts() {
    const gridColor = "rgba(30, 41, 59, 0.09)";
    const common = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { boxWidth: 10, color: "#334155" } } },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#64748b" } },
        y: { grid: { color: gridColor }, ticks: { color: "#64748b" } }
      }
    };

    makeChart("fertilityChart", {
      type: "line",
      data: {
        labels: data.fertility.labels,
        datasets: [
          { label: "영광군", data: data.fertility.yeonggwang, borderColor: "#b45309", backgroundColor: "rgba(180,83,9,.12)", tension: .25 },
          { label: "전국", data: data.fertility.national, borderColor: "#0f766e", backgroundColor: "rgba(15,118,110,.12)", tension: .25 }
        ]
      },
      options: common
    });

    makeChart("structureChart", {
      type: "bar",
      data: {
        labels: data.structure.labels,
        datasets: [
          { label: "0-14세", data: data.structure.child, backgroundColor: "#38bdf8" },
          { label: "15-64세", data: data.structure.working, backgroundColor: "#0f766e" },
          { label: "65세 이상", data: data.structure.older, backgroundColor: "#b45309" }
        ]
      },
      options: { ...common, scales: { ...common.scales, x: { stacked: true, grid: { display: false } }, y: { stacked: true, grid: { color: gridColor }, max: 100 } } }
    });

    const cohortColors = ["#2563eb", "#0f766e", "#b45309", "#be123c", "#7c3aed"];
    makeChart("cohortChart", {
      type: "line",
      data: {
        labels: data.cohort.labels,
        datasets: Object.entries(data.cohort.byRegion).map(([region, values], index) => ({
          label: region,
          data: values,
          borderColor: cohortColors[index % cohortColors.length],
          backgroundColor: `${cohortColors[index % cohortColors.length]}24`,
          tension: .25,
          pointRadius: 3
        }))
      },
      options: {
        ...common,
        scales: {
          x: { grid: { display: false }, ticks: { color: "#64748b" } },
          y: { grid: { color: gridColor }, ticks: { color: "#64748b", callback: (value) => `${value}%` }, suggestedMin: 45, suggestedMax: 115 }
        }
      }
    });

    makeChart("fiscalChart", {
      type: "doughnut",
      data: {
        labels: data.fiscal.labels,
        datasets: [{ data: data.fiscal.values, backgroundColor: ["#0f766e", "#2563eb", "#b45309", "#9333ea", "#64748b"] }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "right" } } }
    });
  }

  function renderMap() {
    const map = document.getElementById("sigunguMap");
    if (!map || !window.renderSigunguMap) return;
    const mapData = window.populationBookSigunguAging || data.sigunguAging;
    window.renderSigunguMap(map, {
      ...mapData,
      thresholdFill: {
        threshold: 30,
        aboveColor: "#b91c1c",
        belowColor: "#94a3b8",
        aboveLabel: "30% 초과",
        belowLabel: "30% 이하"
      },
      showSource: true,
      source: "KOSIS 시군구 1세별 주민등록인구를 갱신 스크립트에서 집계"
    });
  }

  function renderQuestionPlan() {
    const container = document.querySelector("[data-question-plan]");
    const plan = window.populationBookQuestionPlan || [];
    if (!container || !plan.length) return;
    container.innerHTML = plan.map((chapter) => `
      <article class="plan-chapter">
        <header>
          <h3>${chapter.chapter}</h3>
          <p>${chapter.thesis}</p>
        </header>
        ${chapter.sections.map((section) => `
          <section class="plan-section">
            <h4>${section.title}</h4>
            <div class="plan-question-list">
              ${section.questions.map((item) => `
                <article class="plan-question">
                  <h5>${item.q}</h5>
                  <dl>
                    <div><dt>의미</dt><dd>${item.meaning}</dd></div>
                    <div><dt>자료수집</dt><dd>${item.data}</dd></div>
                    <div><dt>분석</dt><dd>${item.analysis}</dd></div>
                    <div><dt>해석</dt><dd>${item.interpretation}</dd></div>
                  </dl>
                </article>
              `).join("")}
            </div>
          </section>
        `).join("")}
      </article>
    `).join("");
  }

  document.addEventListener("DOMContentLoaded", () => {
    const safeRender = (name, fn) => {
      try {
        fn();
      } catch (error) {
        console.error(`Render failed: ${name}`, error);
      }
    };
    safeRender("question-plan", renderQuestionPlan);
    safeRender("metrics", renderMetrics);
    safeRender("charts", renderCharts);
    safeRender("map", renderMap);
  });
})();
