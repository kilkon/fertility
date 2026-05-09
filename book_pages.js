(function () {
  const chartStore = window.populationBookCharts || { charts: {}, meta: {} };

  function rowsFor(id) {
    return chartStore.charts[id] || [];
  }

  function metaFor(id) {
    return chartStore.meta[id] || {};
  }

  function chartNumber(value) {
    if (value === null || value === undefined || value === "") return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  function lineDataset(label, rows, key, color) {
    return {
      label,
      data: rows.map((row) => chartNumber(row[key])),
      borderColor: color,
      backgroundColor: color.replace("1)", ".14)"),
      spanGaps: true,
      tension: 0.25
    };
  }

  function svgEscape(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatKoNumber(value, digits = 0) {
    const n = Number(value);
    if (!Number.isFinite(n)) return "";
    return n.toLocaleString("ko-KR", { maximumFractionDigits: digits, minimumFractionDigits: digits });
  }

  function mixColor(a, b, t) {
    const clamp = Math.max(0, Math.min(1, t));
    const ar = parseInt(a.slice(1, 3), 16);
    const ag = parseInt(a.slice(3, 5), 16);
    const ab = parseInt(a.slice(5, 7), 16);
    const br = parseInt(b.slice(1, 3), 16);
    const bg = parseInt(b.slice(3, 5), 16);
    const bb = parseInt(b.slice(5, 7), 16);
    const part = (x, y) => Math.round(x + (y - x) * clamp).toString(16).padStart(2, "0");
    return `#${part(ar, br)}${part(ag, bg)}${part(ab, bb)}`;
  }

  function sigunguMapColor(value, cap) {
    const n = Number(value);
    if (!Number.isFinite(n)) return "#e5e7eb";
    if (n > 0) return mixColor("#fee2e2", "#b91c1c", Math.min(Math.abs(n) / cap, 1));
    if (n < 0) return mixColor("#dbeafe", "#1d4ed8", Math.min(Math.abs(n) / cap, 1));
    return "#f8fafc";
  }

  function renderLowFertilityPolicyTypology(rows) {
    const sortedRows = rows.slice().sort((a, b) => Number(a.order) - Number(b.order));
    return `
      <div class="policy-typology-grid">
        ${sortedRows.map((row) => `
          <article class="policy-typology-card">
            <div class="policy-typology-number">${svgEscape(row.order)}</div>
            <div>
              <h3>${svgEscape(row.category)}</h3>
              <p>${svgEscape(row.mechanism)}</p>
              <dl>
                <div>
                  <dt>대표 수단</dt>
                  <dd>${svgEscape(row.representative_tools)}</dd>
                </div>
                <div>
                  <dt>평가 질문</dt>
                  <dd>${svgEscape(row.evaluation_question)}</dd>
                </div>
              </dl>
            </div>
          </article>
        `).join("")}
      </div>`;
  }

  function topoArcToPoints(arc, transform) {
    let x = 0;
    let y = 0;
    const scale = transform?.scale || [1, 1];
    const translate = transform?.translate || [0, 0];
    return arc.map((point) => {
      x += point[0];
      y += point[1];
      return [x * scale[0] + translate[0], y * scale[1] + translate[1]];
    });
  }

  function topoRingToPoints(ring, arcs, transform) {
    const points = [];
    ring.forEach((arcIndex) => {
      const reverse = arcIndex < 0;
      const index = reverse ? ~arcIndex : arcIndex;
      let arc = topoArcToPoints(arcs[index] || [], transform);
      if (reverse) arc = arc.slice().reverse();
      if (points.length && arc.length) arc = arc.slice(1);
      points.push(...arc);
    });
    return points;
  }

  function topoGeometryPolygons(geometry, arcs, transform) {
    if (!geometry) return [];
    if (geometry.type === "Polygon") {
      return geometry.arcs.map((ring) => topoRingToPoints(ring, arcs, transform));
    }
    if (geometry.type === "MultiPolygon") {
      return geometry.arcs.flatMap((polygon) => polygon.map((ring) => topoRingToPoints(ring, arcs, transform)));
    }
    return [];
  }

  function renderSigunguPopulationSlopeMap(rows, chartId = "sigungu_population_slope_map") {
    const meta = metaFor(chartId);
    const topo = window.populationBookSigunguTopo;
    if (!topo || !topo.objects || !topo.arcs) {
      return '<div class="map-empty">지도 경계 자료를 불러오지 못했습니다.</div>';
    }
    const objectName = Object.keys(topo.objects)[0];
    const geometries = topo.objects[objectName]?.geometries || [];
    const rowByCode = new Map(rows.map((row) => [String(row.topo_code || row.C1 || ""), row]));
    const decoded = geometries.map((geometry) => ({
      geometry,
      code: String(geometry.properties?.code || geometry.id || ""),
      name: geometry.properties?.name || geometry.properties?.SIG_KOR_NM || "",
      polygons: topoGeometryPolygons(geometry, topo.arcs, topo.transform)
    }));
    const allPoints = decoded.flatMap((feature) => feature.polygons.flat());
    if (!allPoints.length) return '<div class="map-empty">지도 좌표를 해석하지 못했습니다.</div>';
    const xs = allPoints.map((point) => point[0]);
    const ys = allPoints.map((point) => point[1]);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const width = 760;
    const height = 900;
    const margin = 22;
    const scale = Math.min((width - margin * 2) / (maxX - minX), (height - 120 - margin * 2) / (maxY - minY));
    const offsetX = (width - (maxX - minX) * scale) / 2;
    const project = (point) => [
      offsetX + (point[0] - minX) * scale,
      margin + (maxY - point[1]) * scale
    ];
    const values = rows.map((row) => Math.abs(Number(row.slope_people_per_year))).filter(Number.isFinite).sort((a, b) => a - b);
    const cap = Math.max(1, values[Math.floor((values.length - 1) * 0.95)] || values[values.length - 1] || 1);
    const paths = decoded.map((feature) => {
      const row = rowByCode.get(feature.code);
      const slope = row ? Number(row.slope_people_per_year) : NaN;
      const fill = sigunguMapColor(slope, cap);
      const d = feature.polygons.map((ring) => {
        if (!ring.length) return "";
        const projected = ring.map(project);
        return `M${projected.map((point) => `${point[0].toFixed(2)},${point[1].toFixed(2)}`).join("L")}Z`;
      }).join("");
      const label = row
        ? `${row.C1_NM || feature.name}: 연 ${formatKoNumber(slope)}명, ${row.start_year || ""}-${row.end_year || ""} 변화 ${formatKoNumber(row.absolute_change)}명 (${formatKoNumber(row.change_pct, 1)}%)`
        : `${feature.name}: 자료 없음`;
      return `<path class="sigungu-map-path" d="${d}" fill="${fill}"><title>${svgEscape(label)}</title></path>`;
    }).join("");
    const legendSteps = [-1, -0.66, -0.33, 0, 0.33, 0.66, 1];
    const legendX = 130;
    const legendY = 828;
    const swatch = 64;
    const legend = legendSteps.map((step, index) => {
      const value = step * cap;
      return `<rect x="${legendX + index * swatch}" y="${legendY}" width="${swatch}" height="14" fill="${sigunguMapColor(value, cap)}"></rect>`;
    }).join("");
    const increasing = rows.filter((row) => Number(row.slope_people_per_year) > 0).length;
    const decreasing = rows.filter((row) => Number(row.slope_people_per_year) < 0).length;
    const topRows = rows
      .filter((row) => Number.isFinite(Number(row.slope_people_per_year)))
      .sort((a, b) => Number(b.slope_people_per_year) - Number(a.slope_people_per_year))
      .slice(0, 5);
    const topText = topRows.map((row, index) => `${index + 1}. ${row.C1_NM} ${formatKoNumber(row.slope_people_per_year)}명/년`).join(" · ");
    return `
      <div class="sigungu-slope-map-wrap">
        <svg class="sigungu-slope-map-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="시군구 인구 변화 속도 지도">
          <text class="sigungu-map-title" x="28" y="32">${svgEscape(meta.title || "시군구별 연평균 인구 변화 속도")}</text>
          <text class="sigungu-map-subtitle" x="28" y="56">주민등록인구 = a + b x 연도, b = 명/년</text>
          <g>${paths}</g>
          <text class="sigungu-map-note" x="28" y="795">증가 지역 ${increasing}곳 · 감소 지역 ${decreasing}곳 · 진할수록 회귀계수의 절댓값이 큼</text>
          <g class="sigungu-map-legend">
            ${legend}
            <text x="${legendX}" y="${legendY + 36}" text-anchor="start">-${formatKoNumber(cap)}명/년 이하</text>
            <text x="${legendX + swatch * 3.5}" y="${legendY + 36}" text-anchor="middle">0</text>
            <text x="${legendX + swatch * 7}" y="${legendY + 36}" text-anchor="end">+${formatKoNumber(cap)}명/년 이상</text>
          </g>
          <text class="sigungu-map-top" x="28" y="880">${svgEscape(topText)}</text>
        </svg>
      </div>`;
  }

  function renderSidoNetMigrationPanel(rows) {
    const regionOrder = [
      "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시",
      "울산광역시", "세종특별자치시", "경기도", "강원특별자치도", "충청북도", "충청남도",
      "전북특별자치도", "전라남도", "경상북도", "경상남도", "제주특별자치도"
    ];
    const regions = regionOrder.filter((region) => rows.some((row) => row.region === region));
    const years = [...new Set(rows.map((row) => Number(row.year)))].filter(Number.isFinite).sort((a, b) => a - b);
    const minYear = years[0];
    const maxYear = years[years.length - 1];
    const tickYears = years.filter((year) => year === minYear || year === maxYear || year % 5 === 0);
    const width = 360;
    const height = 220;
    const margin = { top: 34, right: 20, bottom: 38, left: 54 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    const x = (year) => margin.left + ((year - minYear) / Math.max(1, maxYear - minYear)) * innerWidth;
    const niceLimit = (values) => {
      const maxAbs = Math.max(1, ...values.map((value) => Math.abs(Number(value))).filter(Number.isFinite));
      const rough = maxAbs / 2;
      const exponent = Math.pow(10, Math.floor(Math.log10(rough)));
      const step = [1, 2, 5, 10].map((mult) => mult * exponent).find((candidate) => candidate >= rough) || 10 * exponent;
      return Math.ceil(maxAbs / step) * step;
    };
    const drawRegion = (region) => {
      const regionRows = rows
        .filter((row) => row.region === region)
        .map((row) => ({
          year: Number(row.year),
          value: Number(row.net_migration),
          avg: Number(row.avg_net_migration_recent ?? row.avg_net_migration_2015_2024 ?? row.avg_net_migration_2016_2025),
          latest: Number(row.latest_net_migration ?? row.net_migration_2024 ?? row.net_migration_2025),
          latestYear: Number(row.latest_year || 2025)
        }))
        .sort((a, b) => a.year - b.year);
      const limit = niceLimit(regionRows.map((row) => row.value));
      const y = (value) => margin.top + (1 - ((value + limit) / (limit * 2))) * innerHeight;
      const zeroY = y(0);
      const path = regionRows.map((point, index) => `${index === 0 ? "M" : "L"} ${x(point.year).toFixed(1)} ${y(point.value).toFixed(1)}`).join(" ");
      const color = regionRows.at(-1)?.latest >= 0 ? "#b91c1c" : "#2563eb";
      const yTicks = [-limit, 0, limit].map((tick) => {
        const ty = y(tick);
        return `
          <line class="panel-axis-grid" x1="${margin.left}" x2="${width - margin.right}" y1="${ty}" y2="${ty}"></line>
          <text class="panel-axis-tick" x="${margin.left - 6}" y="${ty + 4}" text-anchor="end">${formatKoNumber(tick)}</text>`;
      }).join("");
      const xTicks = tickYears.map((tick) => {
        const tx = x(tick);
        return `
          <line class="panel-axis-tick-line" x1="${tx}" x2="${tx}" y1="${height - margin.bottom}" y2="${height - margin.bottom + 4}"></line>
          <text class="panel-axis-tick" x="${tx}" y="${height - 12}" text-anchor="middle">${tick}</text>`;
      }).join("");
      const latest = regionRows.at(-1)?.latest || 0;
      const avg = regionRows.at(-1)?.avg || 0;
      const latestYear = regionRows.at(-1)?.latestYear || maxYear;
      const points = regionRows
        .filter((point) => point.year === minYear || point.year === maxYear || point.year % 5 === 0)
        .map((point) => `
          <circle class="panel-point" cx="${x(point.year).toFixed(1)}" cy="${y(point.value).toFixed(1)}" r="2.6" style="--panel-color:${color}">
            <title>${point.year} ${region}: ${formatKoNumber(point.value)}명</title>
          </circle>`)
        .join("");
      return `
        <article class="sido-migration-panel">
          <svg class="sido-migration-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${svgEscape(region)} 순이동 추세">
            <text class="panel-chart-title" x="${margin.left}" y="16">${svgEscape(region)}</text>
            <text class="panel-axis-label" x="${margin.left}" y="30">최근 10년 평균 ${formatKoNumber(avg)}명 · ${latestYear}년 ${formatKoNumber(latest)}명</text>
            ${yTicks}
            <line class="migration-zero-line" x1="${margin.left}" x2="${width - margin.right}" y1="${zeroY}" y2="${zeroY}"></line>
            <line class="panel-axis" x1="${margin.left}" x2="${width - margin.right}" y1="${height - margin.bottom}" y2="${height - margin.bottom}"></line>
            <line class="panel-axis" x1="${margin.left}" x2="${margin.left}" y1="${margin.top}" y2="${height - margin.bottom}"></line>
            ${xTicks}
            <path class="panel-line migration-panel-line" d="${path}" style="--panel-color:${color}"></path>
            ${points}
          </svg>
        </article>`;
    };
    return regions.map(drawRegion).join("");
  }

  function renderBookCharts() {
    if (!window.Chart) return;
    document.querySelectorAll("[data-book-chart]").forEach((canvas) => {
      const id = canvas.dataset.bookChart;
      const rows = rowsFor(id);
      const meta = metaFor(id);
      if (!rows.length) return;
      let config;
      const common = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { boxWidth: 10 } }, title: { display: true, text: meta.title || id } },
        scales: { x: { grid: { display: false } }, y: { grid: { color: "rgba(15,23,42,.08)" } } }
      };
      if (id === "low_fertility_policy_typology") {
        const parent = canvas.parentElement;
        if (!parent) return;
        canvas.remove();
        parent.classList.add("policy-typology-chart");
        parent.innerHTML = renderLowFertilityPolicyTypology(rows);
        return;
      } else if (id === "low_fertility_budget_trend") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("광의의 저출생 예산", rows, "broad_budget_trillion_krw", "rgba(37,99,235,1)"),
              lineDataset("협의의 저출생 예산", rows, "direct_budget_trillion_krw", "rgba(185,28,28,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              ...common.scales,
              y: {
                ...common.scales.y,
                title: { display: true, text: "조원" }
              }
            }
          }
        };
      } else if (id === "low_fertility_major_budget_2026") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.field),
            datasets: [
              {
                label: "2025년",
                data: rows.map((row) => Number(row.budget_2025_trillion_krw)),
                backgroundColor: "rgba(148,163,184,.72)"
              },
              {
                label: "2026년 예산안",
                data: rows.map((row) => Number(row.budget_2026_trillion_krw)),
                backgroundColor: "rgba(15,118,110,.72)"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              ...common.scales,
              y: {
                ...common.scales.y,
                title: { display: true, text: "조원" }
              }
            }
          }
        };
      } else if (id === "pronatalist_policy_country_comparison") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.country),
            datasets: [
              {
                label: "정책 강화 시점",
                data: rows.map((row) => Number(row.tfr_start)),
                backgroundColor: "rgba(148,163,184,.68)"
              },
              {
                label: "정책 이후 정점",
                data: rows.map((row) => Number(row.tfr_peak)),
                backgroundColor: "rgba(15,118,110,.72)"
              },
              {
                label: "최근 공표값",
                data: rows.map((row) => Number(row.tfr_latest)),
                backgroundColor: rows.map((row) => Number(row.change_start_to_latest) >= 0 ? "rgba(37,99,235,.74)" : "rgba(185,28,28,.74)")
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "국가" } },
              y: { grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "여성 1명당 출생아 수" }, suggestedMin: 0, suggestedMax: 1.8 }
            },
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  afterBody: (items) => {
                    const row = rows[items[0].dataIndex];
                    return [
                      `정책모형: ${row.policy_model}`,
                      `기준연도: ${row.start_year} → 정점: ${row.peak_year} → 최근: ${row.latest_year}`,
                      `평가: ${row.assessment}`
                    ];
                  }
                }
              }
            }
          }
        };
      } else if (id === "housing_support_policy_budget") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                label: "주거 분야",
                data: rows.map((row) => Number(row.housing_budget_trillion_krw)),
                backgroundColor: "rgba(37,99,235,.72)",
                yAxisID: "money"
              },
              {
                label: "주거 비중",
                type: "line",
                data: rows.map((row) => Number(row.housing_share_pct)),
                borderColor: "rgba(185,28,28,1)",
                backgroundColor: "rgba(185,28,28,.12)",
                tension: .2,
                yAxisID: "share"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "예산연도" } },
              money: { position: "left", grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "조원" } },
              share: { position: "right", grid: { display: false }, title: { display: true, text: "%" }, ticks: { callback: (value) => `${value}%` } }
            }
          }
        };
      } else if (id === "housing_security_outcomes_national") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              { ...lineDataset("40세 미만 주택보유율", rows, "under40_homeownership_rate", "rgba(37,99,235,1)"), yAxisID: "rate" },
              { ...lineDataset("조혼인율", rows, "crude_marriage_rate", "rgba(185,28,28,1)"), yAxisID: "vital" },
              { ...lineDataset("조출생률", rows, "crude_birth_rate", "rgba(15,118,110,1)"), yAxisID: "vital" }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              rate: { position: "left", grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "주택보유율(%)" } },
              vital: { position: "right", grid: { display: false }, title: { display: true, text: "천명당" } }
            }
          }
        };
      } else if (id === "capital_region_housing_marriage_birth") {
        const regions = ["서울특별시", "인천광역시", "경기도"];
        const colors = {
          "서울특별시": "rgba(185,28,28,1)",
          "인천광역시": "rgba(37,99,235,1)",
          "경기도": "rgba(15,118,110,1)"
        };
        const years = [...new Set(rows.map((row) => row.year))].sort((a, b) => Number(a) - Number(b));
        const valueFor = (region, key, year) => {
          const row = rows.find((item) => item.region === region && Number(item.year) === Number(year));
          return row ? chartNumber(row[key]) : null;
        };
        config = {
          type: "line",
          data: {
            labels: years,
            datasets: [
              ...regions.map((region) => ({
                label: `${region} 주택보유율`,
                data: years.map((year) => valueFor(region, "under40_homeownership_rate", year)),
                borderColor: colors[region],
                backgroundColor: colors[region].replace("1)", ".12)"),
                tension: .25,
                yAxisID: "rate"
              })),
              ...regions.map((region) => ({
                label: `${region} 조출생률`,
                data: years.map((year) => valueFor(region, "crude_birth_rate", year)),
                borderColor: colors[region],
                backgroundColor: colors[region].replace("1)", ".08)"),
                borderDash: [5, 4],
                tension: .25,
                yAxisID: "vital"
              })),
              ...regions.map((region) => ({
                label: `${region} 조혼인율`,
                data: years.map((year) => valueFor(region, "crude_marriage_rate", year)),
                borderColor: colors[region],
                backgroundColor: colors[region].replace("1)", ".08)"),
                borderDash: [2, 3],
                tension: .25,
                yAxisID: "vital"
              }))
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              rate: { position: "left", grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "주택보유율(%)" } },
              vital: { position: "right", grid: { display: false }, title: { display: true, text: "조혼인율·조출생률(천명당)" } }
            }
          }
        };
      } else if (id === "housing_security_outcome_regression") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => `${row.group} · ${row.outcome}`),
            datasets: [{
              label: "주택보유율 1%p 상승과 관련된 지표 변화",
              data: rows.map((row) => Number(row.homeownership_coef)),
              backgroundColor: rows.map((row) => String(row.outcome).includes("출생") ? "rgba(15,118,110,.72)" : "rgba(185,28,28,.72)")
            }]
          },
          options: {
            ...common,
            indexAxis: "y",
            scales: {
              x: { grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "회귀계수(천명당 지표 변화)" } },
              y: { grid: { display: false } }
            }
          }
        };
      } else if (id === "housing_tenure_young_newlywed") {
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const pick = (group, tenure, year) => {
          const row = rows.find((item) => item.group === group && item.tenure_type === tenure && Number(item.year) === Number(year));
          return row ? chartNumber(row.share_pct) : null;
        };
        const series = [
          ["신혼 자가", "신혼", "자가", "rgba(15,118,110,1)", []],
          ["신혼 전세", "신혼", "전세", "rgba(37,99,235,1)", []],
          ["신혼 보증금 월세", "신혼", "보증금 있는 월세", "rgba(185,28,28,1)", []],
          ["30대 이하 자가", "30대 이하", "자가", "rgba(71,85,105,1)", [5, 4]],
          ["미혼 보증금 월세", "미혼", "보증금 있는 월세", "rgba(147,51,234,1)", [2, 3]]
        ];
        config = {
          type: "line",
          data: {
            labels: years,
            datasets: series.map(([label, group, tenure, color, dash]) => ({
              label,
              data: years.map((year) => pick(group, tenure, year)),
              borderColor: color,
              backgroundColor: color.replace("1)", ".10)"),
              borderDash: dash,
              tension: .25,
              pointRadius: 2
            }))
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: { grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "점유형태 비중(%)" }, ticks: { callback: (value) => `${value}%` } }
            }
          }
        };
      } else if (id === "housing_finance_burden_by_age") {
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const pick = (ageGroup, key, year) => {
          const row = rows.find((item) => item.age_group === ageGroup && Number(item.year) === Number(year));
          return row ? chartNumber(row[key]) : null;
        };
        config = {
          type: "line",
          data: {
            labels: years,
            datasets: [
              {
                label: "29세 이하 부채/소득",
                data: years.map((year) => pick("29세 이하", "debt_to_disposable_income_pct", year)),
                borderColor: "rgba(37,99,235,1)",
                backgroundColor: "rgba(37,99,235,.10)",
                tension: .25,
                yAxisID: "ratio"
              },
              {
                label: "30~39세 부채/소득",
                data: years.map((year) => pick("30~39세", "debt_to_disposable_income_pct", year)),
                borderColor: "rgba(15,118,110,1)",
                backgroundColor: "rgba(15,118,110,.10)",
                tension: .25,
                yAxisID: "ratio"
              },
              {
                label: "29세 이하 원리금상환/소득",
                data: years.map((year) => pick("29세 이하", "repayment_to_disposable_income_pct", year)),
                borderColor: "rgba(37,99,235,1)",
                backgroundColor: "rgba(37,99,235,.08)",
                borderDash: [5, 4],
                tension: .25,
                yAxisID: "ratio"
              },
              {
                label: "30~39세 원리금상환/소득",
                data: years.map((year) => pick("30~39세", "repayment_to_disposable_income_pct", year)),
                borderColor: "rgba(15,118,110,1)",
                backgroundColor: "rgba(15,118,110,.08)",
                borderDash: [5, 4],
                tension: .25,
                yAxisID: "ratio"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              ratio: { position: "left", grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "처분가능소득 대비 비율(%)" }, ticks: { callback: (value) => `${value}%` } }
            }
          }
        };
      } else if (id === "youth_housing_consumption_pressure") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("주거비 비중", rows, "housing_share_pct", "rgba(185,28,28,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: { grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "가계소비 중 주거비 비중(%)" }, ticks: { callback: (value) => `${value}%` } }
            }
          }
        };
      } else if (id === "international_housing_fertility_cases") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => `${row.country}(${row.tfr_year})`),
            datasets: [
              {
                label: "합계출산율",
                data: rows.map((row) => Number(row.total_fertility_rate)),
                backgroundColor: rows.map((row) => {
                  if (row.country === "싱가포르") return "rgba(185,28,28,.72)";
                  if (row.country === "이스라엘") return "rgba(15,118,110,.72)";
                  if (row.country === "프랑스") return "rgba(37,99,235,.72)";
                  return "rgba(71,85,105,.72)";
                })
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "국가와 기준연도" } },
              y: { grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "여성 1명당 출생아 수" }, suggestedMax: 3.2 }
            }
          }
        };
      } else if (id === "private_education_cost_trend") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                ...lineDataset("사교육비 총액(조원)", rows, "private_education_total_trillion_krw", "rgba(37,99,235,1)"),
                yAxisID: "money"
              },
              {
                ...lineDataset("1인당 월평균 사교육비(만원)", rows, "monthly_private_education_10k_krw", "rgba(185,28,28,1)"),
                yAxisID: "money"
              },
              {
                ...lineDataset("사교육 참여율(%)", rows, "private_education_participation_rate", "rgba(15,118,110,1)"),
                yAxisID: "rate",
                borderDash: [5, 4]
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              money: { position: "left", grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "조원 / 만원" } },
              rate: { position: "right", grid: { display: false }, title: { display: true, text: "%" }, min: 0, max: 100 }
            }
          }
        };
      } else if (id === "private_education_school_level") {
        const levels = ["초등학교", "중학교", "고등학교"];
        const colors = ["rgba(37,99,235,1)", "rgba(185,28,28,1)", "rgba(15,118,110,1)"];
        const years = [...new Set(rows.map((row) => row.year))].sort((a, b) => Number(a) - Number(b));
        const valueFor = (level, key, year) => {
          const row = rows.find((item) => item.school_level === level && Number(item.year) === Number(year));
          return row ? chartNumber(row[key]) : null;
        };
        config = {
          type: "line",
          data: {
            labels: years,
            datasets: [
              ...levels.map((level, index) => ({
                label: `${level} 월평균 사교육비(만원)`,
                data: years.map((year) => valueFor(level, "monthly_private_education_10k_krw", year)),
                borderColor: colors[index],
                backgroundColor: colors[index].replace("1)", ".14)"),
                tension: 0.25,
                spanGaps: true,
                yAxisID: "money"
              })),
              ...levels.map((level, index) => ({
                label: `${level} 참여율(%)`,
                data: years.map((year) => valueFor(level, "private_education_participation_rate", year)),
                borderColor: colors[index],
                backgroundColor: "transparent",
                tension: 0.25,
                spanGaps: true,
                borderDash: [5, 4],
                yAxisID: "rate"
              }))
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              money: { position: "left", grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "만원" } },
              rate: { position: "right", grid: { display: false }, title: { display: true, text: "%" }, min: 0, max: 100 }
            }
          }
        };
      } else if (id === "high_school_private_education_drivers") {
        const items = ["전체 참여율", "일반교과", "수학", "영어", "국어", "사회·과학", "유료인터넷·통신강좌", "진로·진학 학습상담"];
        const colors = [
          "rgba(15,23,42,1)",
          "rgba(37,99,235,1)",
          "rgba(185,28,28,1)",
          "rgba(15,118,110,1)",
          "rgba(147,51,234,1)",
          "rgba(202,138,4,1)",
          "rgba(14,116,144,1)",
          "rgba(219,39,119,1)"
        ];
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const valueFor = (item, key, year) => {
          const row = rows.find((entry) => entry.item_label === item && Number(entry.year) === Number(year));
          return row ? chartNumber(row[key]) : null;
        };
        config = {
          type: "line",
          data: {
            labels: years,
            datasets: items.map((item, index) => ({
              label: item,
              data: years.map((year) => valueFor(item, "participation_rate", year)),
              borderColor: colors[index],
              backgroundColor: colors[index].replace("1)", ".10)"),
              borderDash: index > 5 ? [5, 4] : [],
              tension: .25,
              pointRadius: item === "전체 참여율" ? 3 : 2,
              spanGaps: true
            }))
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: { grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "참여율(%)" }, min: 0, max: 75 }
            }
          }
        };
      } else if (id === "private_education_income_gap") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.income_group_label),
            datasets: [
              {
                type: "bar",
                label: "월평균 사교육비(만원)",
                data: rows.map((row) => chartNumber(row.monthly_private_education_10k_krw)),
                backgroundColor: "rgba(37,99,235,.70)",
                yAxisID: "money"
              },
              {
                type: "line",
                label: "사교육 참여율(%)",
                data: rows.map((row) => chartNumber(row.private_education_participation_rate)),
                borderColor: "rgba(185,28,28,1)",
                backgroundColor: "rgba(185,28,28,.12)",
                tension: 0.25,
                yAxisID: "rate"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, ticks: { maxRotation: 35, minRotation: 20 } },
              money: { position: "left", grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "만원" } },
              rate: { position: "right", grid: { display: false }, title: { display: true, text: "%" }, min: 0, max: 100 }
            }
          }
        };
      } else if (id === "newlywed_income_fertility") {
        const latestYear = Math.max(...rows.map((row) => Number(row.year)).filter((year) => Number.isFinite(year)));
        const latestRows = rows
          .filter((row) => Number(row.year) === latestYear && row.income_group !== "합계")
          .sort((a, b) => {
            const order = ["1천만원 미만", "1천만원~3천만원 미만", "3천만원~5천만원 미만", "5천만원~7천만원 미만", "7천만원~1억원 미만", "1억원 이상"];
            return order.indexOf(a.income_group) - order.indexOf(b.income_group);
          });
        config = {
          type: "bar",
          data: {
            labels: latestRows.map((row) => row.income_group),
            datasets: [
              {
                type: "bar",
                label: "평균 출생아 수",
                data: latestRows.map((row) => chartNumber(row.avg_births)),
                backgroundColor: "rgba(15,118,110,.70)",
                yAxisID: "births"
              },
              {
                type: "line",
                label: "무자녀 비중",
                data: latestRows.map((row) => chartNumber(row.no_child_pct)),
                borderColor: "rgba(185,28,28,1)",
                backgroundColor: "rgba(185,28,28,.12)",
                tension: 0.25,
                yAxisID: "share"
              }
            ]
          },
          options: {
            ...common,
            plugins: {
              ...common.plugins,
              title: { display: true, text: `${meta.title || id}(${latestYear})` }
            },
            scales: {
              x: { grid: { display: false }, ticks: { maxRotation: 35, minRotation: 20 } },
              births: { position: "left", grid: { color: "rgba(15,23,42,.08)" }, title: { display: true, text: "명" }, suggestedMax: 0.9 },
              share: { position: "right", grid: { display: false }, title: { display: true, text: "무자녀 비중(%)" }, min: 0, max: 70 }
            }
          }
        };
      } else if (id === "school_age_private_education_pressure") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("0-14세 인구 지수", rows, "school_age_proxy_0_14_index_2007_100", "rgba(100,116,139,1)"),
              lineDataset("사교육비 총액 지수", rows, "private_education_total_trillion_krw_index_2007_100", "rgba(37,99,235,1)"),
              lineDataset("1인당 사교육비 지수", rows, "monthly_private_education_10k_krw_index_2007_100", "rgba(185,28,28,1)"),
              lineDataset("참여율 지수", rows, "private_education_participation_rate_index_2007_100", "rgba(15,118,110,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              ...common.scales,
              y: { ...common.scales.y, title: { display: true, text: "2007년=100" } }
            }
          }
        };
      } else if (id === "education_burden_perception") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("교육비 부담스럽다(%)", rows, "education_burden_heavy_or_somewhat_pct", "rgba(185,28,28,1)"),
              lineDataset("학교 납입금 외 교육비가 가장 부담(%)", rows, "non_school_payment_education_cost_most_burdensome_pct", "rgba(37,99,235,1)"),
              lineDataset("대학 이상 기대(%)", rows, "expect_university_or_more_pct", "rgba(15,118,110,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              ...common.scales,
              y: { ...common.scales.y, min: 0, max: 100, title: { display: true, text: "%" } }
            }
          }
        };
      } else if (["sigungu_population_slope_map", "sigungu_older_population_slope_map", "sigungu_working_age_population_slope_map"].includes(id)) {
        const parent = canvas.parentElement;
        if (!parent) return;
        canvas.remove();
        parent.classList.add("sigungu-slope-map-chart");
        parent.innerHTML = renderSigunguPopulationSlopeMap(rows, id);
        return;
      } else if (id === "sido_net_migration_panel") {
        const parent = canvas.parentElement;
        if (!parent) return;
        canvas.remove();
        parent.classList.add("sido-migration-panel-chart");
        parent.innerHTML = renderSidoNetMigrationPanel(rows);
        return;
      } else if (id === "sido_net_migration_age_contribution") {
        canvas.parentElement?.classList.add("migration-age-contribution-chart");
        const ageKeys = ["0-14세", "15-19세", "20-24세", "25-29세", "30-34세", "35-44세", "45-64세", "65세 이상"];
        const colors = ["#94a3b8", "#64748b", "#2563eb", "#1d4ed8", "#0f766e", "#b91c1c", "#ea580c", "#7c3aed"];
        const sortedRows = rows.slice().sort((a, b) => Number(a.avg_total_net_migration_recent ?? a.avg_total_net_migration_2015_2024 ?? a.avg_total_net_migration_2016_2025) - Number(b.avg_total_net_migration_recent ?? b.avg_total_net_migration_2015_2024 ?? b.avg_total_net_migration_2016_2025));
        config = {
          type: "bar",
          data: {
            labels: sortedRows.map((row) => row.region),
            datasets: ageKeys.map((key, index) => ({
              label: key,
              data: sortedRows.map((row) => Number(row[key] || 0)),
              backgroundColor: colors[index]
            }))
          },
          options: {
            ...common,
            indexAxis: "y",
            scales: {
              x: {
                stacked: true,
                grid: { color: "rgba(15,23,42,.08)" },
                ticks: { callback: (value) => `${Number(value).toLocaleString("ko-KR")}명` },
                title: { display: true, text: "최근 10년 평균 연간 순이동(명)" }
              },
              y: { stacked: true, grid: { display: false } }
            },
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (context) => `${context.dataset.label}: ${Number(context.raw).toLocaleString("ko-KR")}명`
                }
              }
            }
          }
        };
      } else if (id === "sigungu_population_concentration") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("성장거점 20개 비중", rows, "growth_hub_20_share_pct", "rgba(185,28,28,1)"),
              lineDataset("수도권 비중", rows, "capital_area_share_pct", "rgba(37,99,235,1)"),
              lineDataset("상위 10개 시군구 비중", rows, "top_10_share_pct", "rgba(15,118,110,1)"),
              lineDataset("상위 20개 시군구 비중", rows, "top_20_share_pct", "rgba(147,51,234,1)"),
              lineDataset("상위 50개 시군구 비중", rows, "top_50_share_pct", "rgba(180,83,9,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                ticks: { callback: (value) => `${value}%` },
                title: { display: true, text: "전국 인구 대비 비중(%)" }
              }
            }
          }
        };
      } else if (id === "sigungu_population_concentration_indices") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("지니계수(2004=100)", rows, "gini_index_2004_100", "rgba(185,28,28,1)"),
              lineDataset("HHI(2004=100)", rows, "hhi_index_2004_100", "rgba(37,99,235,1)"),
              lineDataset("유효 지역 수(2004=100)", rows, "effective_region_count_index_2004_100", "rgba(15,118,110,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "2004년=100" }
              }
            }
          }
        };
      } else if (id === "age_composition_projection") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("0-14세", rows, "age_0_14_share", "rgba(37,99,235,1)"),
              lineDataset("15-64세", rows, "age_15_64_share", "rgba(15,118,110,1)"),
              lineDataset("65세 이상", rows, "age_65_plus_share", "rgba(180,83,9,1)")
            ]
          },
          options: common
        };
      } else if (id === "population_pyramid_four_panel") {
        const parent = canvas.parentElement;
        if (!parent) return;
        canvas.remove();
        parent.classList.add("pyramid-panel-grid");
        const years = [1980, 1990, 2020, 2025];
        const rawMax = Math.max(...rows.flatMap((row) => [Number(row.male), Number(row.female)]));
        const maxValue = Math.ceil(rawMax / 500000) * 500000;
        const formatPeople = (value) => `${Math.round(Math.abs(Number(value)) / 10000).toLocaleString("ko-KR")}만 명`;
        const tickValues = [0, maxValue / 2, maxValue];
        years.forEach((year) => {
          const panel = document.createElement("div");
          panel.className = "pyramid-panel";
          const yearRows = rows.filter((row) => Number(row.year) === year).sort((a, b) => Number(a.age_start) - Number(b.age_start));
          const total = yearRows.reduce((sum, row) => sum + Number(row.total || 0), 0);
          const width = 640;
          const height = 500;
          const top = 56;
          const bottom = 438;
          const centerX = width / 2;
          const labelGap = 42;
          const leftEnd = centerX - labelGap;
          const rightStart = centerX + labelGap;
          const halfWidth = 232;
          const bandHeight = (bottom - top) / yearRows.length;
          const ticks = tickValues.map((tick) => {
            const dx = tick / maxValue * halfWidth;
            return `
              <line class="pyramid-grid-line" x1="${leftEnd - dx}" y1="${top}" x2="${leftEnd - dx}" y2="${bottom}"></line>
              <line class="pyramid-grid-line" x1="${rightStart + dx}" y1="${top}" x2="${rightStart + dx}" y2="${bottom}"></line>
              <text class="pyramid-tick" x="${leftEnd - dx}" y="${bottom + 24}" text-anchor="middle">${formatPeople(tick).replace(" 명", "")}</text>
              <text class="pyramid-tick" x="${rightStart + dx}" y="${bottom + 24}" text-anchor="middle">${formatPeople(tick).replace(" 명", "")}</text>`;
          }).join("");
          const bars = yearRows.map((row, index) => {
            const y = bottom - (index + 1) * bandHeight + 2;
            const barHeight = Math.max(6, bandHeight - 4);
            const male = Number(row.male);
            const female = Number(row.female);
            const maleWidth = male / maxValue * halfWidth;
            const femaleWidth = female / maxValue * halfWidth;
            const labelY = y + barHeight / 2 + 4;
            return `
              <rect class="pyramid-bar male" x="${leftEnd - maleWidth}" y="${y}" width="${maleWidth}" height="${barHeight}" rx="2">
                <title>${year}년 ${row.age_band} 남성 ${formatPeople(male)}</title>
              </rect>
              <rect class="pyramid-bar female" x="${rightStart}" y="${y}" width="${femaleWidth}" height="${barHeight}" rx="2">
                <title>${year}년 ${row.age_band} 여성 ${formatPeople(female)}</title>
              </rect>
              <text class="pyramid-age-label" x="${centerX}" y="${labelY}" text-anchor="middle">${row.age_band.replace("세", "")}</text>`;
          }).join("");
          panel.innerHTML = `
            <div class="pyramid-panel-header">
              <h3>${year}년</h3>
              <span>총 ${formatPeople(total)}</span>
            </div>
            <svg class="pyramid-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${year}년 남녀 5세 연령군 인구피라미드">
              <text class="pyramid-side-label male-label" x="164" y="30" text-anchor="middle">남성</text>
              <text class="pyramid-side-label female-label" x="476" y="30" text-anchor="middle">여성</text>
              <line class="pyramid-center-line" x1="${centerX}" y1="${top - 10}" x2="${centerX}" y2="${bottom + 6}"></line>
              ${ticks}
              ${bars}
              <text class="pyramid-axis-note" x="${centerX}" y="486" text-anchor="middle">좌우 축 동일, 단위: 명</text>
            </svg>`;
          parent.appendChild(panel);
        });
        return;
      } else if (id === "sex_ratio_projection") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("성비", rows, "sex_ratio", "rgba(37,99,235,1)"),
              lineDataset("인구성장률", rows, "population_growth_rate", "rgba(185,28,28,1)")
            ]
          },
          options: common
        };
      } else if (id === "population_measure_comparison") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("행정안전부 주민등록인구", rows, "registered_population_million", "rgba(185,28,28,1)"),
              lineDataset("통계청 인구총조사", rows, "census_population_million", "rgba(37,99,235,1)"),
              lineDataset("통계청 장래인구추계", rows, "projection_population_million", "rgba(15,118,110,1)")
            ]
          },
          options: {
            ...common,
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (context) => `${context.dataset.label}: ${Number(context.parsed.y).toFixed(3)}백만 명`
                }
              }
            },
            scales: {
              ...common.scales,
              y: {
                ...common.scales.y,
                title: { display: true, text: "인구(백만 명)" },
                min: 45.5,
                max: 52.2,
                ticks: {
                  callback: (value) => `${Number(value).toFixed(1)}`
                }
              }
            }
          }
        };
      } else if (id === "population_measure_gap") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("총조사 - 주민등록", rows, "census_minus_registered_10k", "rgba(37,99,235,1)"),
              lineDataset("장래추계 - 주민등록", rows, "projection_minus_registered_10k", "rgba(15,118,110,1)"),
              lineDataset("총조사 - 장래추계", rows, "census_minus_projection_10k", "rgba(185,28,28,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              ...common.scales,
              y: {
                ...common.scales.y,
                title: { display: true, text: "차이(만 명)" },
                ticks: {
                  callback: (value) => `${Number(value).toFixed(0)}`
                }
              }
            }
          }
        };
      } else if (id === "resident_registration_2010_jump") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                label: "전년 대비 주민등록인구 증가분",
                data: rows.map((row) => chartNumber(row.annual_change_10k)),
                backgroundColor: rows.map((row) => row.is_2010 ? "rgba(185,28,28,.82)" : "rgba(100,116,139,.48)"),
                borderColor: rows.map((row) => row.is_2010 ? "rgba(185,28,28,1)" : "rgba(100,116,139,1)"),
                borderWidth: 1
              }
            ]
          },
          options: {
            ...common,
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (context) => `${context.dataset.label}: ${formatKoNumber(context.parsed.y, 1)}만 명`
                }
              }
            },
            scales: {
              ...common.scales,
              y: {
                ...common.scales.y,
                title: { display: true, text: "증가분(만 명)" },
                ticks: {
                  callback: (value) => `${Number(value).toFixed(0)}`
                }
              }
            }
          }
        };
      } else if (id === "resident_registration_centenarian_trend") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                ...lineDataset("100세 이상 인구", rows, "population_100_plus", "rgba(185,28,28,1)"),
                yAxisID: "y"
              },
              {
                ...lineDataset("인구 10만 명당 100세 이상", rows, "share_100_plus_per_100k", "rgba(15,118,110,1)"),
                yAxisID: "y1",
                borderDash: [5, 4]
              }
            ]
          },
          options: {
            ...common,
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const suffix = context.dataset.yAxisID === "y1" ? "명/10만 명" : "명";
                    return `${context.dataset.label}: ${formatKoNumber(context.parsed.y, context.dataset.yAxisID === "y1" ? 2 : 0)}${suffix}`;
                  }
                }
              }
            },
            scales: {
              ...common.scales,
              y: {
                ...common.scales.y,
                title: { display: true, text: "100세 이상 인구(명)" },
                ticks: {
                  callback: (value) => formatKoNumber(value)
                }
              },
              y1: {
                type: "linear",
                position: "right",
                grid: { drawOnChartArea: false },
                title: { display: true, text: "인구 10만 명당(명)" },
                ticks: {
                  callback: (value) => Number(value).toFixed(1)
                }
              }
            }
          }
        };
      } else if (id === "yeonggwang_cohort") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.birth_year),
            datasets: [
              { label: "0세 인구", data: rows.map((row) => row.pop_0), backgroundColor: "#2563eb" },
              { label: "4세 인구", data: rows.map((row) => row.pop_4), backgroundColor: "#f97316" },
              { label: "감소율(%)", type: "line", yAxisID: "rate", data: rows.map((row) => row.decrease_ratio), borderColor: "#7c2d12", tension: .25 }
            ]
          },
          options: { ...common, scales: { ...common.scales, rate: { position: "right", grid: { display: false } } } }
        };
      } else if (id === "birth_incentive_region_retention") {
        const parent = canvas.parentElement;
        if (!parent) return;
        canvas.remove();
        parent.classList.add("cohort-panel-chart");
        const regions = [...new Set(rows.map((row) => row.region))];
        const colors = ["#2563eb", "#0f766e", "#b45309", "#be123c", "#7c3aed"];
        const years = [...new Set(rows.map((row) => Number(row.birth_year)))].sort((a, b) => a - b);
        const tickYears = [years[0], years[Math.floor(years.length / 2)], years[years.length - 1]];
        const drawLineSvg = (regionRows, metric, options) => {
          const width = 360;
          const height = 230;
          const margin = { top: 28, right: 18, bottom: 56, left: 48 };
          const innerWidth = width - margin.left - margin.right;
          const innerHeight = height - margin.top - margin.bottom;
          const minYear = years[0];
          const maxYear = years[years.length - 1];
          const yMin = options.yMin;
          const yMax = options.yMax;
          const x = (year) => margin.left + ((year - minYear) / Math.max(1, maxYear - minYear)) * innerWidth;
          const y = (value) => margin.top + (1 - ((value - yMin) / (yMax - yMin))) * innerHeight;
          const points = regionRows
            .filter((row) => row[metric] !== undefined && row[metric] !== null && row[metric] !== "")
            .map((row) => ({ year: Number(row.birth_year), age4Year: Number(row.age4_year), value: Number(row[metric]) }))
            .sort((a, b) => a.year - b.year);
          const path = points
            .map((point, index) => `${index === 0 ? "M" : "L"} ${x(point.year).toFixed(1)} ${y(point.value).toFixed(1)}`)
            .join(" ");
          const yTicks = options.yTicks.map((tick) => {
            const ty = y(tick);
            return `
              <line class="panel-axis-grid" x1="${margin.left}" x2="${width - margin.right}" y1="${ty}" y2="${ty}"></line>
              <text class="panel-axis-tick" x="${margin.left - 8}" y="${ty + 4}" text-anchor="end">${options.format(tick)}</text>`;
          }).join("");
          const xTicks = tickYears.map((tick) => {
            const tx = x(tick);
            const label = options.showAge4 ? `${tick}→${tick + 4}` : `${tick}`;
            return `
              <line class="panel-axis-tick-line" x1="${tx}" x2="${tx}" y1="${height - margin.bottom}" y2="${height - margin.bottom + 5}"></line>
              <text class="panel-axis-tick" x="${tx}" y="${height - margin.bottom + 20}" text-anchor="middle">${label}</text>`;
          }).join("");
          const circles = points.map((point) => `
            <circle class="panel-point" cx="${x(point.year).toFixed(1)}" cy="${y(point.value).toFixed(1)}" r="3">
              <title>${options.showAge4 ? `${point.year}년 출생, ${point.age4Year}년 4세 관측` : `${point.year}년`} ${options.title}: ${options.format(point.value)}</title>
            </circle>`).join("");
          return `
            <svg class="cohort-mini-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${options.title} 추세">
              <text class="panel-chart-title" x="${margin.left}" y="17">${options.title}</text>
              ${yTicks}
              <line class="panel-axis" x1="${margin.left}" x2="${width - margin.right}" y1="${height - margin.bottom}" y2="${height - margin.bottom}"></line>
              <line class="panel-axis" x1="${margin.left}" x2="${margin.left}" y1="${margin.top}" y2="${height - margin.bottom}"></line>
              ${xTicks}
              <path class="panel-line" d="${path}"></path>
              ${circles}
              <text class="panel-axis-label" x="${width / 2}" y="${height - 8}" text-anchor="middle">${options.xLabel}</text>
            </svg>`;
        };
        regions.forEach((region, index) => {
          const regionRows = rows.filter((row) => row.region === region).sort((a, b) => Number(a.birth_year) - Number(b.birth_year));
          const panel = document.createElement("article");
          panel.className = "cohort-region-panel";
          panel.style.setProperty("--panel-color", colors[index % colors.length]);
          panel.innerHTML = `
            <header>
              <h3>${region}</h3>
              <span>출생년도 ${years[0]}-${years[years.length - 1]} / 4세 관측 ${years[0] + 4}-${years[years.length - 1] + 4}</span>
            </header>
            <div class="cohort-region-pair">
              ${drawLineSvg(regionRows, "crude_birth_rate", {
                title: "조출생률(천명당)",
                yMin: 3,
                yMax: 12,
                yTicks: [3, 6, 9, 12],
                format: (value) => `${Number(value).toFixed(value % 1 ? 1 : 0)}`,
                xLabel: "X축: 출생년도(조출생률 기준연도)",
                showAge4: false
              })}
              ${drawLineSvg(regionRows, "retention_rate", {
                title: "0세→4세 코호트 잔존율",
                yMin: 45,
                yMax: 115,
                yTicks: [50, 75, 100],
                format: (value) => `${Number(value).toFixed(value % 1 ? 1 : 0)}%`,
                xLabel: "X축: 출생년도(0세 기준, 4세 관측=+4년)",
                showAge4: true
              })}
            </div>`;
          parent.appendChild(panel);
        });
        return;
      } else if (id === "elderly_labor_dt_1de8031s") {
        const parent = canvas.parentElement;
        if (!parent) return;
        canvas.remove();
        parent.classList.add("elderly-labor-panel-chart");
        const itemOrder = ["고령층인구", "경제활동인구", "취업자", "고용률", "실업자", "실업률", "비경제활동인구"];
        const ageOrder = ["55~79세 전체", "55~64세", "65~79세"];
        const colors = {
          "55~79세 전체": "#111827",
          "55~64세": "#2563eb",
          "65~79세": "#b45309"
        };
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const tickYears = years.filter((year) => year === years[0] || year === years[years.length - 1] || year % 5 === 0);
        const fmt = (value, unit) => {
          const number = Number(value);
          if (unit === "%") return `${number.toFixed(number % 1 ? 1 : 0)}%`;
          return number >= 1000 ? `${Math.round(number).toLocaleString("ko-KR")}` : `${number.toFixed(number % 1 ? 1 : 0)}`;
        };
        const niceStep = (maxValue) => {
          const rough = Math.max(maxValue / 4, 1);
          const exponent = Math.pow(10, Math.floor(Math.log10(rough)));
          for (const mult of [1, 2, 5, 10]) {
            const candidate = mult * exponent;
            if (candidate >= rough) return candidate;
          }
          return 10 * exponent;
        };
        const drawPanel = (item) => {
          const itemRows = rows.filter((row) => row.item === item);
          if (!itemRows.length) return "";
          const unit = itemRows[0].unit || "";
          const width = 520;
          const height = 290;
          const margin = { top: 36, right: 28, bottom: 58, left: 68 };
          const innerWidth = width - margin.left - margin.right;
          const innerHeight = height - margin.top - margin.bottom;
          const values = itemRows.map((row) => Number(row.value)).filter((value) => Number.isFinite(value));
          const maxValue = Math.max(...values);
          const minValue = Math.min(...values);
          const step = unit === "%" ? 10 : niceStep(maxValue);
          const yMin = unit === "%" ? Math.max(0, Math.floor((minValue - 4) / 10) * 10) : 0;
          const yMax = unit === "%" ? Math.ceil((maxValue + 4) / 10) * 10 : Math.ceil(maxValue / step) * step;
          const minYear = years[0];
          const maxYear = years[years.length - 1];
          const x = (year) => margin.left + ((year - minYear) / Math.max(1, maxYear - minYear)) * innerWidth;
          const y = (value) => margin.top + (1 - ((value - yMin) / Math.max(1, yMax - yMin))) * innerHeight;
          const yTicks = [];
          for (let tick = yMin; tick <= yMax + 0.0001; tick += step) yTicks.push(tick);
          const grid = yTicks.map((tick) => {
            const ty = y(tick);
            return `
              <line class="panel-axis-grid" x1="${margin.left}" x2="${width - margin.right}" y1="${ty}" y2="${ty}"></line>
              <text class="panel-axis-tick" x="${margin.left - 8}" y="${ty + 4}" text-anchor="end">${fmt(tick, unit)}</text>`;
          }).join("");
          const xTicks = tickYears.map((tick) => {
            const tx = x(tick);
            return `
              <line class="panel-axis-tick-line" x1="${tx}" x2="${tx}" y1="${height - margin.bottom}" y2="${height - margin.bottom + 5}"></line>
              <text class="panel-axis-tick" x="${tx}" y="${height - margin.bottom + 20}" text-anchor="middle">${tick}</text>`;
          }).join("");
          const lines = ageOrder.map((age) => {
            const points = itemRows
              .filter((row) => row.age_group === age && row.value !== "")
              .map((row) => ({ year: Number(row.year), value: Number(row.value), period: row.period }))
              .sort((a, b) => a.year - b.year);
            const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${x(point.year).toFixed(1)} ${y(point.value).toFixed(1)}`).join(" ");
            const circles = points
              .filter((point) => point.year === years[0] || point.year === years[years.length - 1] || point.year % 5 === 0)
              .map((point) => `
                <circle class="elderly-labor-point" cx="${x(point.year).toFixed(1)}" cy="${y(point.value).toFixed(1)}" r="3" style="--line-color:${colors[age]}">
                  <title>${point.year}년 5월 ${age} ${item}: ${fmt(point.value, unit)}${unit === "%" ? "" : ` ${unit}`}</title>
                </circle>`)
              .join("");
            return `
              <path class="elderly-labor-line" d="${path}" style="--line-color:${colors[age]}"></path>
              ${circles}`;
          }).join("");
          const legend = ageOrder.map((age, index) => `
            <g transform="translate(${margin.left + index * 136}, 24)">
              <line class="elderly-labor-legend-line" x1="0" x2="18" y1="0" y2="0" style="--line-color:${colors[age]}"></line>
              <text class="panel-axis-tick" x="24" y="4">${age}</text>
            </g>`).join("");
          return `
            <article class="elderly-labor-panel">
              <svg class="elderly-labor-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${item} 추세">
                <text class="panel-chart-title" x="${margin.left}" y="16">${item}</text>
                ${legend}
                ${grid}
                <line class="panel-axis" x1="${margin.left}" x2="${width - margin.right}" y1="${height - margin.bottom}" y2="${height - margin.bottom}"></line>
                <line class="panel-axis" x1="${margin.left}" x2="${margin.left}" y1="${margin.top}" y2="${height - margin.bottom}"></line>
                ${xTicks}
                ${lines}
                <text class="panel-axis-label" x="${width / 2}" y="${height - 10}" text-anchor="middle">조사연도(매년 5월)</text>
                <text class="panel-axis-label" x="18" y="${margin.top - 10}" text-anchor="start">단위: ${unit}</text>
              </svg>
            </article>`;
        };
        parent.innerHTML = itemOrder.map(drawPanel).join("");
        return;
      } else if (id === "birth_incentive_region_summary") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.region),
            datasets: [
              {
                label: "평균 잔존율(%)",
                data: rows.map((row) => Number(row.avg_retention_rate)),
                backgroundColor: "#0f766e"
              },
              {
                label: "평균 감소율(%)",
                data: rows.map((row) => Number(row.avg_decrease_ratio)),
                backgroundColor: "#f97316"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              ...common.scales,
              y: {
                ...common.scales.y,
                suggestedMax: 110,
                ticks: { callback: (value) => `${value}%` }
              }
            }
          }
        };
      } else if (id === "elderly_labor_dt_1de8031s_summary") {
        const summaryRows = rows.filter((row) => row.age_group === "55~79세 전체");
        config = {
          type: "bar",
          data: {
            labels: summaryRows.map((row) => row.item),
            datasets: [
              {
                label: "2010년 대비 2025년 변화율(%)",
                data: summaryRows.map((row) => Number(row.change_pct)),
                backgroundColor: "#0f766e"
              }
            ]
          },
          options: {
            ...common,
            plugins: {
              ...common.plugins,
              title: { display: true, text: "55~79세 전체: 2010년 대비 2025년 변화율" }
            }
          }
        };
      } else if (id === "elderly_activity_life_course_indicators") {
        const dataRows = rows.slice().sort((a, b) => Number(a.year) - Number(b.year));
        config = {
          type: "line",
          data: {
            labels: dataRows.map((row) => row.year),
            datasets: [
              {
                label: "장래 근로 희망률",
                data: dataRows.map((row) => chartNumber(row.future_work_hope_pct)),
                borderColor: "#0f766e",
                backgroundColor: "rgba(15,118,110,.12)",
                tension: 0.25,
                yAxisID: "rate"
              },
              {
                label: "지난 1년 구직 경험률",
                data: dataRows.map((row) => chartNumber(row.job_search_experience_pct)),
                borderColor: "#be123c",
                backgroundColor: "rgba(190,18,60,.10)",
                tension: 0.25,
                yAxisID: "rate"
              },
              {
                label: "지난 1년 취업 경험률",
                data: dataRows.map((row) => chartNumber(row.employment_experience_pct)),
                borderColor: "#2563eb",
                backgroundColor: "rgba(37,99,235,.10)",
                tension: 0.25,
                yAxisID: "rate"
              },
              {
                label: "평균 이직연령",
                data: dataRows.map((row) => chartNumber(row.avg_exit_age)),
                borderColor: "#b45309",
                backgroundColor: "rgba(180,83,9,.10)",
                borderDash: [5, 4],
                tension: 0.25,
                yAxisID: "age"
              },
              {
                label: "희망 근로연령",
                data: dataRows.map((row) => chartNumber(row.desired_work_age)),
                borderColor: "#111827",
                backgroundColor: "rgba(17,24,39,.10)",
                borderDash: [2, 4],
                tension: 0.25,
                yAxisID: "age"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "조사연도(매년 5월)" } },
              rate: {
                position: "left",
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "55~79세 중 비중(%)" },
                ticks: { callback: (value) => `${value}%` }
              },
              age: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "연령(세)" },
                min: 45,
                max: 80
              }
            }
          }
        };
      } else if (id === "elderly_activity_exit_reasons_2025" || id === "elderly_activity_future_work_reasons_2025") {
        const displayRows = rows
          .filter((row) => row.share_pct !== "")
          .map((row) => ({
            ...row,
            cleanCategory: String(row.category || "").replace(/^-/, "").replace(/(.{9})/g, "$1\n"),
            share: Number(row.share_pct)
          }))
          .sort((a, b) => a.share - b.share);
        config = {
          type: "bar",
          data: {
            labels: displayRows.map((row) => row.cleanCategory),
            datasets: [
              {
                label: "비중(%)",
                data: displayRows.map((row) => row.share),
                backgroundColor: id === "elderly_activity_exit_reasons_2025" ? "rgba(185,28,28,.72)" : "rgba(15,118,110,.72)"
              }
            ]
          },
          options: {
            ...common,
            indexAxis: "y",
            scales: {
              x: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "비중(%)" },
                ticks: { callback: (value) => `${value}%` }
              },
              y: { grid: { display: false } }
            }
          }
        };
      } else if (id === "elderly_activity_job_preferences_2025") {
        const order = ["일의양과시간대", "임금수준", "계속근로가능성", "일의내용", "과거취업경험연관성", "출퇴근거리 등 편리성", "전일제", "시간제"];
        const displayRows = rows
          .filter((row) => row.sex === "계" && ["일자리 선택기준", "희망 일자리 형태"].includes(row.group))
          .map((row) => ({
            ...row,
            label: `${row.group}: ${row.category}`,
            share: Number(row.share_pct)
          }))
          .sort((a, b) => order.indexOf(a.category) - order.indexOf(b.category));
        config = {
          type: "bar",
          data: {
            labels: displayRows.map((row) => row.label),
            datasets: [
              {
                label: "장래 근로 희망자 중 비중(%)",
                data: displayRows.map((row) => row.share),
                backgroundColor: displayRows.map((row) => row.group === "희망 일자리 형태" ? "rgba(37,99,235,.70)" : "rgba(180,83,9,.70)")
              }
            ]
          },
          options: {
            ...common,
            indexAxis: "y",
            scales: {
              x: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "비중(%)" },
                ticks: { callback: (value) => `${value}%` }
              },
              y: { grid: { display: false } }
            }
          }
        };
      } else if (id === "elderly_employment_structure_2025") {
        const displayRows = rows
          .filter((row) => row.dimension === "직업")
          .map((row) => ({ ...row, share: Number(row.category_share_of_elderly_pct) }))
          .sort((a, b) => a.share - b.share);
        config = {
          type: "bar",
          data: {
            labels: displayRows.map((row) => row.category),
            datasets: [
              {
                label: "55~79세 취업자 중 비중(%)",
                data: displayRows.map((row) => row.share),
                backgroundColor: "rgba(37,99,235,.72)"
              }
            ]
          },
          options: {
            ...common,
            indexAxis: "y",
            scales: {
              x: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "비중(%)" },
                ticks: { callback: (value) => `${value}%` }
              },
              y: { grid: { display: false } }
            }
          }
        };
      } else if (id === "elderly_regional_labor_60plus_slopes") {
        const parent = canvas.parentElement;
        if (!parent) return;
        canvas.remove();
        parent.classList.add("regional-slope-panel-chart");
        const items = ["취업자", "고용률", "실업자", "비경제활동인구"];
        const colors = {
          "취업자": "#2563eb",
          "고용률": "#0f766e",
          "실업자": "#be123c",
          "비경제활동인구": "#b45309"
        };
        const formatSlope = (value, unit) => {
          const n = Number(value);
          if (unit === "%") return `${n.toFixed(2)}%p/년`;
          return `${n.toFixed(1)}천명/년`;
        };
        const drawSlopePanel = (item) => {
          const itemRows = rows
            .filter((row) => row.item === item && row.slope_per_year !== "")
            .map((row) => ({ ...row, slope: Number(row.slope_per_year), r2: Number(row.r2) }))
            .sort((a, b) => b.slope - a.slope);
          if (!itemRows.length) return "";
          const width = 560;
          const rowHeight = 20;
          const margin = { top: 38, right: 96, bottom: 42, left: 86 };
          const height = margin.top + margin.bottom + itemRows.length * rowHeight;
          const slopes = itemRows.map((row) => row.slope);
          const minSlope = Math.min(0, ...slopes);
          const maxSlope = Math.max(...slopes);
          const pad = Math.max((maxSlope - minSlope) * 0.08, item === "고용률" ? 0.2 : 1);
          const xMin = minSlope - pad;
          const xMax = maxSlope + pad;
          const innerWidth = width - margin.left - margin.right;
          const x = (value) => margin.left + ((value - xMin) / Math.max(0.0001, xMax - xMin)) * innerWidth;
          const y = (index) => margin.top + index * rowHeight + rowHeight / 2;
          const unit = itemRows[0].unit || "";
          const axisTicks = [minSlope, (minSlope + maxSlope) / 2, maxSlope].map((tick) => {
            const tx = x(tick);
            return `
              <line class="panel-axis-grid" x1="${tx}" x2="${tx}" y1="${margin.top - 6}" y2="${height - margin.bottom}"></line>
              <text class="panel-axis-tick" x="${tx}" y="${height - 16}" text-anchor="middle">${formatSlope(tick, unit)}</text>`;
          }).join("");
          const zero = x(0);
          const dots = itemRows.map((row, index) => {
            const cy = y(index);
            const cx = x(row.slope);
            return `
              <text class="regional-slope-region" x="${margin.left - 8}" y="${cy + 4}" text-anchor="end">${row.region}</text>
              <line class="regional-slope-guide" x1="${margin.left}" x2="${width - margin.right}" y1="${cy}" y2="${cy}"></line>
              <circle class="regional-slope-dot" cx="${cx}" cy="${cy}" r="4.2" style="--dot-color:${colors[item]}">
                <title>${row.region} ${item}: ${formatSlope(row.slope, unit)}, R² ${Number(row.r2).toFixed(2)}</title>
              </circle>
              <text class="regional-slope-value" x="${width - margin.right + 8}" y="${cy + 4}">${formatSlope(row.slope, unit)}</text>`;
          }).join("");
          return `
            <article class="regional-slope-panel">
              <svg class="regional-slope-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${item} 회귀계수 지역 분포">
                <text class="panel-chart-title" x="${margin.left}" y="18">${item}</text>
                <text class="panel-axis-label" x="${margin.left}" y="34">회귀계수: 2010-2025년 연평균 변화 속도</text>
                ${axisTicks}
                <line class="regional-slope-zero" x1="${zero}" x2="${zero}" y1="${margin.top - 8}" y2="${height - margin.bottom}"></line>
                ${dots}
              </svg>
            </article>`;
        };
        parent.innerHTML = items.map(drawSlopePanel).join("");
        return;
      } else if (id === "nta_public_health_age_profile") {
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const ages = [...new Set(rows.map((row) => Number(row.age)))].sort((a, b) => a - b);
        const colors = {
          2010: "#64748b",
          2015: "#0f766e",
          2020: "#2563eb",
          2022: "#be123c"
        };
        config = {
          type: "line",
          data: {
            labels: ages.map((age) => age === 85 ? "85세 이상" : `${age}세`),
            datasets: years.map((year) => ({
              label: `${year}년`,
              data: ages.map((age) => {
                const row = rows.find((item) => Number(item.year) === year && Number(item.age) === age);
                return row ? chartNumber(row.amount_million_krw_per_person) : null;
              }),
              borderColor: colors[year] || "#111827",
              backgroundColor: `${colors[year] || "#111827"}22`,
              pointRadius: 0,
              tension: 0.22
            }))
          },
          options: {
            ...common,
            scales: {
              x: {
                grid: { display: false },
                ticks: { maxTicksLimit: 12 },
                title: { display: true, text: "연령(각세, 85세 이상은 열린 구간)" }
              },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "1인 공공보건소비(백만원)" },
                ticks: { callback: (value) => `${value}백만원` }
              }
            }
          }
        };
      } else if (id === "nta_public_health_age_group_trend") {
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const groups = ["0-14세", "15-44세", "45-64세", "65-74세", "75-84세", "85세 이상"];
        const colors = ["#94a3b8", "#64748b", "#2563eb", "#0f766e", "#b45309", "#be123c"];
        config = {
          type: "line",
          data: {
            labels: years,
            datasets: groups.map((group, index) => ({
              label: group,
              data: years.map((year) => {
                const row = rows.find((item) => Number(item.year) === year && item.age_group === group);
                return row ? chartNumber(row.amount_million_krw_per_person) : null;
              }),
              borderColor: colors[index],
              backgroundColor: `${colors[index]}22`,
              pointRadius: 2.5,
              tension: 0.24
            }))
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "연령대 평균 1인 공공보건소비(백만원)" },
                ticks: { callback: (value) => `${value}백만원` }
              }
            }
          }
        };
      } else if (id === "elderly_pension_dt_1de8051s") {
        const totalRows = rows.filter((row) => row.sex === "계").sort((a, b) => Number(a.year) - Number(b.year));
        const sexRows = (sex) => rows.filter((row) => row.sex === sex).sort((a, b) => Number(a.year) - Number(b.year));
        config = {
          type: "line",
          data: {
            labels: totalRows.map((row) => row.year),
            datasets: [
              {
                label: "전체 평균수령액",
                data: sexRows("계").map((row) => Number(row.average_amount_10k_krw)),
                borderColor: "#111827",
                backgroundColor: "rgba(17,24,39,.12)",
                tension: 0.25
              },
              {
                label: "남자 평균수령액",
                data: sexRows("남자").map((row) => Number(row.average_amount_10k_krw)),
                borderColor: "#2563eb",
                backgroundColor: "rgba(37,99,235,.12)",
                tension: 0.25
              },
              {
                label: "여자 평균수령액",
                data: sexRows("여자").map((row) => Number(row.average_amount_10k_krw)),
                borderColor: "#be123c",
                backgroundColor: "rgba(190,18,60,.12)",
                tension: 0.25
              },
              {
                label: "전체 연금수령률",
                type: "line",
                yAxisID: "rate",
                data: totalRows.map((row) => Number(row.recipient_rate)),
                borderColor: "#0f766e",
                backgroundColor: "rgba(15,118,110,.12)",
                borderDash: [5, 4],
                pointRadius: 3,
                tension: 0.25
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "조사연도(매년 5월)" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "월평균 연금수령액(만원)" },
                ticks: { callback: (value) => `${value}만원` }
              },
              rate: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "연금수령률(%)" },
                ticks: { callback: (value) => `${value}%` }
              }
            }
          }
        };
      } else if (id === "elderly_pension_amount_distribution") {
        const selectedYears = [2008, 2014, 2020, 2025];
        const displayRows = rows.filter((row) => row.sex === "계" && selectedYears.includes(Number(row.year)));
        const bands = ["10만원 미만", "10~25만원 미만", "25~50만원 미만", "50~100만원 미만", "100~150만원 미만", "150만원 이상"];
        const colors = ["#94a3b8", "#64748b", "#2563eb", "#0f766e", "#b45309", "#be123c"];
        config = {
          type: "bar",
          data: {
            labels: selectedYears,
            datasets: bands.map((band, index) => ({
              label: band,
              data: selectedYears.map((year) => {
                const row = displayRows.find((item) => Number(item.year) === year && item.amount_band === band);
                return row ? Number(row.share_of_recipients) : 0;
              }),
              backgroundColor: colors[index],
              stack: "share"
            }))
          },
          options: {
            ...common,
            scales: {
              x: { stacked: true, grid: { display: false }, title: { display: true, text: "조사연도(매년 5월)" } },
              y: {
                stacked: true,
                max: 100,
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "연금수령자 중 비중(%)" },
                ticks: { callback: (value) => `${value}%` }
              }
            }
          }
        };
      } else if (id === "fertility_comparison") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("영광군", rows, "yeonggwang", "rgba(180,83,9,1)"),
              lineDataset("전국", rows, "national", "rgba(15,118,110,1)")
            ]
          },
          options: common
        };
      } else if (id === "international_tfr_asia" || id === "international_tfr_europe") {
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const countryOrder = id === "international_tfr_asia"
          ? ["한국", "일본", "대만", "싱가포르"]
          : ["프랑스", "스웨덴", "독일", "영국", "이탈리아", "스페인"];
        const colors = {
          "한국": "#b91c1c",
          "일본": "#2563eb",
          "대만": "#0f766e",
          "싱가포르": "#b45309",
          "프랑스": "#2563eb",
          "스웨덴": "#0f766e",
          "독일": "#64748b",
          "영국": "#7c3aed",
          "이탈리아": "#b45309",
          "스페인": "#be123c"
        };
        const datasets = countryOrder
          .filter((country) => rows.some((row) => row.country_display === country))
          .map((country) => ({
            label: country,
            data: years.map((year) => {
              const found = rows.find((row) => Number(row.year) === year && row.country_display === country);
              return found ? Number(found.total_fertility_rate) : null;
            }),
            borderColor: colors[country] || "#475569",
            backgroundColor: `${colors[country] || "#475569"}22`,
            pointRadius: country === "한국" ? 3 : 2,
            borderWidth: country === "한국" ? 3 : 2,
            tension: 0.22
          }));
        config = {
          type: "line",
          data: { labels: years, datasets },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "합계출산율(여성 1명당 출생아 수)" },
                suggestedMin: 0,
                suggestedMax: 2.2
              }
            }
          }
        };
      } else if (id === "fertility_family_structure_comparison") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.country_display),
            datasets: [
              {
                type: "bar",
                label: "비혼 출산 비중(%)",
                data: rows.map((row) => row.nonmarital_birth_share_pct == null ? null : Number(row.nonmarital_birth_share_pct)),
                backgroundColor: "rgba(37,99,235,.68)",
                yAxisID: "pct"
              },
              {
                type: "bar",
                label: "외국 출생 모친 출생 비중(%)",
                data: rows.map((row) => row.foreign_born_mother_share_pct == null ? null : Number(row.foreign_born_mother_share_pct)),
                backgroundColor: "rgba(15,118,110,.68)",
                yAxisID: "pct"
              },
              {
                type: "line",
                label: "합계출산율",
                data: rows.map((row) => Number(row.total_fertility_rate)),
                borderColor: "rgba(185,28,28,1)",
                backgroundColor: "rgba(185,28,28,.14)",
                yAxisID: "tfr",
                pointRadius: 4,
                tension: 0.2
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "국가" } },
              pct: {
                position: "left",
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "비중(%)" },
                suggestedMax: 70,
                ticks: { callback: (value) => `${value}%` }
              },
              tfr: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "합계출산율" },
                suggestedMin: 0,
                suggestedMax: 2
              }
            }
          }
        };
      } else if (id === "sigungu_aging_top") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.C1_NM),
            datasets: [{ label: "고령화율(%)", data: rows.map((row) => row.aging_rate), backgroundColor: "#b45309" }]
          },
          options: { ...common, indexAxis: "y" }
        };
      } else if (id === "youth_population_enara") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [lineDataset("청년 생산가능인구", rows, "youth_working_age_population", "rgba(37,99,235,1)")]
          },
          options: common
        };
      } else if (id === "youth_employment_context") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("청년 생산가능인구", rows, "working_age_population_index", "rgba(37,99,235,1)"),
              lineDataset("청년 경제활동인구", rows, "economically_active_population_index", "rgba(15,118,110,1)"),
              lineDataset("청년 취업자", rows, "employed_population_index", "rgba(185,28,28,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "지수(2000=100)" }
              }
            }
          }
        };
      } else if (id === "multicultural_birth_rate") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [lineDataset("다문화 출생 비중(%)", rows, "multicultural_birth_share", "rgba(147,51,234,1)")]
          },
          options: common
        };
      } else if (id === "childcare_children") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [lineDataset("보육아동수", rows, "childcare_children", "rgba(15,118,110,1)")]
          },
          options: common
        };
      } else if (id === "parental_leave_gender_users") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                ...lineDataset("여성근로자", rows, "female_parental_leave_users", "rgba(185,28,28,1)"),
                yAxisID: "users"
              },
              {
                ...lineDataset("남성근로자", rows, "male_parental_leave_users", "rgba(37,99,235,1)"),
                yAxisID: "users"
              },
              {
                label: "남성 비중",
                data: rows.map((row) => Number(row.male_parental_leave_share_pct)),
                borderColor: "#0f766e",
                backgroundColor: "rgba(15,118,110,.12)",
                borderDash: [5, 4],
                pointRadius: 3,
                tension: 0.22,
                yAxisID: "share"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              users: {
                position: "left",
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "육아휴직급여 수급자 수(명)" },
                ticks: { callback: (value) => Number(value).toLocaleString("ko-KR") }
              },
              share: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "남성 비중(%)" },
                ticks: { callback: (value) => `${value}%` }
              }
            }
          }
        };
      } else if (id === "maternity_leave_support") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                ...lineDataset("출산전후휴가급여 수급자", rows, "maternity_leave_users", "rgba(37,99,235,1)"),
                yAxisID: "users"
              },
              {
                ...lineDataset("지원금액", rows, "maternity_leave_amount_million_krw", "rgba(15,118,110,1)"),
                yAxisID: "amount"
              },
              {
                ...lineDataset("1인당 지원금액", rows, "maternity_leave_per_user_million_krw", "rgba(185,28,28,1)"),
                yAxisID: "perUser",
                borderDash: [5, 4]
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              users: {
                position: "left",
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "수급자 수(명)" },
                ticks: { callback: (value) => Number(value).toLocaleString("ko-KR") }
              },
              amount: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "지원금액(백만원)" },
                ticks: { callback: (value) => Number(value).toLocaleString("ko-KR") }
              },
              perUser: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "1인당 지원금액(백만원)" }
              }
            }
          }
        };
      } else if (id === "maternity_parental_leave_financing_pressure") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("출산전후휴가급여", rows, "maternity_leave_amount_trillion_krw", "rgba(37,99,235,1)"),
              lineDataset("육아휴직급여", rows, "parental_leave_amount_trillion_krw", "rgba(15,118,110,1)"),
              {
                ...lineDataset("합계", rows, "total_maternity_parental_amount_trillion_krw", "rgba(185,28,28,1)"),
                borderWidth: 3
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "지원금액(조원)" }
              }
            }
          }
        };
      } else if (id === "parental_leave_per_user_support") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("전체", rows, "parental_leave_per_user_million_krw", "rgba(15,118,110,1)"),
              lineDataset("여성근로자", rows, "female_parental_leave_per_user_million_krw", "rgba(185,28,28,1)"),
              lineDataset("남성근로자", rows, "male_parental_leave_per_user_million_krw", "rgba(37,99,235,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "지원금액/초회수급자(백만원)" }
              }
            }
          }
        };
      } else if (id === "parental_leave_access_gap_2025") {
        const colors = rows.map((row) => {
          const label = String(row.access_class || "");
          if (label.includes("접근 가능") && !label.includes("취약")) return "rgba(15,118,110,.76)";
          if (label.includes("취약")) return "rgba(234,88,12,.74)";
          if (label.includes("별도")) return "rgba(148,163,184,.74)";
          return "rgba(185,28,28,.72)";
        });
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.group),
            datasets: [
              {
                label: "노동자 수(만 명)",
                data: rows.map((row) => Number(row.workers_10k)),
                backgroundColor: colors
              }
            ]
          },
          options: {
            ...common,
            plugins: {
              ...common.plugins,
              legend: { display: false },
              tooltip: {
                callbacks: {
                  afterLabel: (context) => rows[context.dataIndex]?.basis || ""
                }
              }
            },
            scales: {
              ...common.scales,
              x: {
                ...common.scales.x,
                ticks: { maxRotation: 35, minRotation: 0 }
              },
              y: {
                ...common.scales.y,
                title: { display: true, text: "만 명" }
              }
            }
          }
        };
      } else if (id === "preschool_childcare_time_by_parent") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                ...lineDataset("남편 돌보기", rows, "husband_care_minutes", "rgba(37,99,235,1)"),
                yAxisID: "minutes"
              },
              {
                ...lineDataset("아내 돌보기", rows, "wife_care_minutes", "rgba(185,28,28,1)"),
                yAxisID: "minutes"
              },
              {
                label: "남편 비중",
                data: rows.map((row) => Number(row.husband_care_share_pct)),
                borderColor: "#0f766e",
                backgroundColor: "rgba(15,118,110,.12)",
                borderDash: [5, 4],
                pointRadius: 3,
                tension: 0.22,
                yAxisID: "share"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              minutes: {
                position: "left",
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "하루 평균 시간(분)" },
                ticks: { callback: (value) => `${value}분` }
              },
              share: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "남편 비중(%)" },
                ticks: { callback: (value) => `${value}%` }
              }
            }
          }
        };
      } else if (id === "dual_earner_child_housework_time") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                ...lineDataset("남편 가사노동", rows, "husband_housework_minutes", "rgba(37,99,235,1)"),
                yAxisID: "minutes"
              },
              {
                ...lineDataset("아내 가사노동", rows, "wife_housework_minutes", "rgba(185,28,28,1)"),
                yAxisID: "minutes"
              },
              {
                label: "남편 비중",
                data: rows.map((row) => Number(row.husband_housework_share_pct)),
                borderColor: "#0f766e",
                backgroundColor: "rgba(15,118,110,.12)",
                borderDash: [5, 4],
                pointRadius: 3,
                tension: 0.22,
                yAxisID: "share"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              minutes: {
                position: "left",
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "하루 평균 시간(분)" },
                ticks: { callback: (value) => `${value}분` }
              },
              share: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "남편 비중(%)" },
                ticks: { callback: (value) => `${value}%` }
              }
            }
          }
        };
      } else if (id === "childcare_supply_by_type" || id === "childcare_users_by_type") {
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const typeOrder = ["국·공립", "민간", "가정", "직장", "사회복지법인", "법인·단체 등", "협동"];
        const colors = {
          "국·공립": "#2563eb",
          "민간": "#b45309",
          "가정": "#0f766e",
          "직장": "#7c3aed",
          "사회복지법인": "#be123c",
          "법인·단체 등": "#64748b",
          "협동": "#0891b2"
        };
        const valueKey = id === "childcare_supply_by_type" ? "childcare_facilities" : "childcare_children";
        const unitLabel = id === "childcare_supply_by_type" ? "개소" : "명";
        const datasets = typeOrder
          .filter((type) => rows.some((row) => row.type === type))
          .map((type) => ({
            label: type,
            data: years.map((year) => {
              const found = rows.find((row) => Number(row.year) === year && row.type === type);
              return found ? Number(found[valueKey]) : null;
            }),
            borderColor: colors[type] || "#475569",
            backgroundColor: `${colors[type] || "#475569"}22`,
            pointRadius: 2,
            tension: 0.22
          }));
        config = {
          type: "line",
          data: { labels: years, datasets },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: unitLabel },
                ticks: { callback: (value) => Number(value).toLocaleString("ko-KR") }
              }
            },
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (context) => `${context.dataset.label}: ${Number(context.parsed.y).toLocaleString("ko-KR")}${unitLabel}`
                }
              }
            }
          }
        };
      } else if (id === "childcare_time_flexible_facilities") {
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const typeOrder = ["야간 연장", "24시간", "휴일"];
        const colors = {
          "야간 연장": "#2563eb",
          "24시간": "#0f766e",
          "휴일": "#b45309"
        };
        const datasets = typeOrder
          .filter((type) => rows.some((row) => row.time_type === type))
          .map((type) => ({
            label: type,
            data: years.map((year) => {
              const found = rows.find((row) => Number(row.year) === year && row.time_type === type);
              return found ? Number(found.special_childcare_facilities) : null;
            }),
            borderColor: colors[type],
            backgroundColor: `${colors[type]}22`,
            pointRadius: 2,
            tension: 0.22
          }));
        config = {
          type: "line",
          data: { labels: years, datasets },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "어린이집 수(개소)" },
                ticks: { callback: (value) => Number(value).toLocaleString("ko-KR") }
              }
            },
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const row = rows.find((item) => Number(item.year) === Number(context.label) && item.time_type === context.dataset.label);
                    const share = row ? Number(row.share_of_total_facilities_pct).toFixed(2) : "";
                    return `${context.dataset.label}: ${Number(context.parsed.y).toLocaleString("ko-KR")}개소${share ? `, 전체 대비 ${share}%` : ""}`;
                  }
                }
              }
            }
          }
        };
      } else if (id === "openfiscal_debt_context") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("국가채무", rows, "national_debt", "rgba(185,28,28,1)"),
              lineDataset("금융성 채무", rows, "financial_debt", "rgba(37,99,235,1)")
            ]
          },
          options: common
        };
      } else if (id === "openfiscal_aging_budget_trends") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                label: "기초연금",
                data: rows.map((row) => Number(row["기초연금_trillion_krw"] || 0)),
                backgroundColor: "#2563eb",
                stack: "budget"
              },
              {
                label: "장기요양·치매",
                data: rows.map((row) => Number(row["장기요양·치매_trillion_krw"] || 0)),
                backgroundColor: "#0f766e",
                stack: "budget"
              },
              {
                label: "노인일자리",
                data: rows.map((row) => Number(row["노인일자리_trillion_krw"] || 0)),
                backgroundColor: "#b45309",
                stack: "budget"
              },
              {
                label: "노인돌봄",
                data: rows.map((row) => Number(row["노인돌봄_trillion_krw"] || 0)),
                backgroundColor: "#7c3aed",
                stack: "budget"
              },
              {
                label: "기타 노인·고령화",
                data: rows.map((row) => Number(row["기타 노인·고령화_trillion_krw"] || 0)),
                backgroundColor: "#64748b",
                stack: "budget"
              },
              {
                label: "세부사업 수",
                type: "line",
                yAxisID: "count",
                data: rows.map((row) => Number(row.program_count)),
                borderColor: "#be123c",
                backgroundColor: "rgba(190,18,60,.12)",
                pointRadius: 3,
                tension: 0.22
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { stacked: true, grid: { display: false }, title: { display: true, text: "회계연도" } },
              y: {
                stacked: true,
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "예산액(조원)" },
                ticks: { callback: (value) => `${value}조` }
              },
              count: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "고유 세부사업명 수" }
              }
            },
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (context) => {
                    if (context.dataset.yAxisID === "count") return `세부사업 수: ${context.parsed.y}개`;
                    return `${context.dataset.label}: ${Number(context.parsed.y).toFixed(3)}조원`;
                  }
                }
              }
            }
          }
        };
      } else if (id === "openfiscal_aging_budget_top_programs") {
        const displayRows = [...rows]
          .sort((a, b) => Number(b.budget_amount_trillion_krw) - Number(a.budget_amount_trillion_krw))
          .slice(0, 10)
          .reverse();
        config = {
          type: "bar",
          data: {
            labels: displayRows.map((row) => row.program_name),
            datasets: [
              {
                label: `${displayRows[0]?.year || ""}년 예산액(조원)`,
                data: displayRows.map((row) => Number(row.budget_amount_trillion_krw)),
                backgroundColor: displayRows.map((row) => row.category === "기초연금" ? "#2563eb" : row.category === "장기요양·치매" ? "#0f766e" : row.category === "노인일자리" ? "#b45309" : "#64748b")
              }
            ]
          },
          options: {
            ...common,
            indexAxis: "y",
            scales: {
              x: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "예산액(조원)" },
                ticks: { callback: (value) => `${value}조` }
              },
              y: { grid: { display: false } }
            }
          }
        };
      } else if (id === "vacant_housing_rate") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [lineDataset("빈집 비율", rows, "vacant_housing_rate", "rgba(180,83,9,1)")]
          },
          options: common
        };
      } else if (id === "household_population_gap_national") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("가구 수 지수", rows, "household_index_2015_100", "rgba(15,118,110,1)"),
              lineDataset("인구 지수", rows, "population_index_2015_100", "rgba(37,99,235,1)"),
              {
                ...lineDataset("평균 가구원 수", rows, "average_household_size", "rgba(185,28,28,1)"),
                yAxisID: "y1"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "2015년=100" }
              },
              y1: {
                position: "right",
                grid: { drawOnChartArea: false },
                title: { display: true, text: "명/가구" }
              }
            }
          }
        };
      } else if (id === "household_population_gap_regions") {
        canvas.parentElement?.classList.add("household-region-gap-chart");
        const sortedRows = rows.slice().sort((a, b) => Number(b.gap_change_pct) - Number(a.gap_change_pct));
        config = {
          type: "bar",
          data: {
            labels: sortedRows.map((row) => row.region),
            datasets: [
              {
                label: "가구 수 증가율",
                data: sortedRows.map((row) => Number(row.household_change_pct_since_2015)),
                backgroundColor: "#0f766e"
              },
              {
                label: "인구 증가율",
                data: sortedRows.map((row) => Number(row.population_change_pct_since_2015)),
                backgroundColor: "#2563eb"
              }
            ]
          },
          options: {
            ...common,
            indexAxis: "y",
            scales: {
              x: {
                grid: { color: "rgba(15,23,42,.08)" },
                ticks: { callback: (value) => `${value}%` },
                title: { display: true, text: "2015년 대비 2024년 변화율(%)" }
              },
              y: { grid: { display: false } }
            }
          }
        };
      } else if (id === "household_head_age_shift") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("65세 이상 가구주 가구 비중", rows, "older_head_share_pct", "rgba(185,28,28,1)"),
              lineDataset("20-34세 1인가구 비중", rows, "young_one_person_share_of_total_pct", "rgba(37,99,235,1)"),
              lineDataset("65세 이상 1인가구 비중", rows, "older_one_person_share_of_total_pct", "rgba(15,118,110,1)"),
              lineDataset("전체 1인가구 비중", rows, "one_person_share_pct", "rgba(147,51,234,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "일반가구 대비 비중(%)" }
              }
            }
          }
        };
      } else if (id === "household_one_person_age_index") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("총 일반가구", rows, "total_households_index_2015_100", "rgba(100,116,139,1)"),
              lineDataset("전체 1인가구", rows, "one_person_households_index_2015_100", "rgba(147,51,234,1)"),
              lineDataset("20-34세 1인가구", rows, "young_one_person_households_20_34_index_2015_100", "rgba(37,99,235,1)"),
              lineDataset("65세 이상 1인가구", rows, "older_one_person_households_65plus_index_2015_100", "rgba(15,118,110,1)"),
              lineDataset("65세 이상 가구주 가구", rows, "older_head_households_65plus_index_2015_100", "rgba(185,28,28,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "2015년=100" }
              }
            }
          }
        };
      } else if (id === "national_population_pressure") {
        const displayRows = rows.filter((row) => Number(row.year) % 5 === 0 || [2024, 2025, 2050, 2072].includes(Number(row.year)));
        config = {
          type: "line",
          data: {
            labels: displayRows.map((row) => row.year),
            datasets: [
              lineDataset("65세 이상 비중(%)", displayRows, "older_share", "rgba(185,28,28,1)"),
              lineDataset("노년부양비", displayRows, "old_age_dependency_ratio", "rgba(37,99,235,1)"),
              lineDataset("중위연령", displayRows, "median_age", "rgba(15,118,110,1)")
            ]
          },
          options: common
        };
      } else if (id === "aging_index_growth") {
        const displayRows = rows.filter((row) => Number(row.year) % 2 === 0 || [2025, 2052].includes(Number(row.year)));
        config = {
          type: "line",
          data: {
            labels: displayRows.map((row) => row.year),
            datasets: [
              {
                label: "노령화지수",
                data: displayRows.map((row) => Number(row.aging_index)),
                borderColor: "#be123c",
                backgroundColor: "rgba(190,18,60,.12)",
                tension: 0.25,
                yAxisID: "index"
              },
              {
                label: "65세 이상 비중(%)",
                data: displayRows.map((row) => Number(row.older_share)),
                borderColor: "#2563eb",
                backgroundColor: "rgba(37,99,235,.12)",
                tension: 0.25,
                yAxisID: "share"
              },
              {
                label: "0-14세 비중(%)",
                data: displayRows.map((row) => Number(row.child_share)),
                borderColor: "#0f766e",
                backgroundColor: "rgba(15,118,110,.12)",
                tension: 0.25,
                yAxisID: "share"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              index: {
                position: "left",
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "노령화지수(유소년 100명당 65세 이상)" }
              },
              share: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "인구 비중(%)" },
                ticks: { callback: (value) => `${value}%` }
              }
            }
          }
        };
      } else if (id === "sigungu_aging_distribution") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.aging_class),
            datasets: [{ label: "시군구 수", data: rows.map((row) => row.sigungu_count), backgroundColor: "#b45309" }]
          },
          options: common
        };
      } else if (id === "childcare_capacity_pressure") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                ...lineDataset("보육아동수", rows, "childcare_children", "rgba(15,118,110,1)"),
                yAxisID: "children"
              },
              {
                ...lineDataset("어린이집 수", rows, "childcare_facilities", "rgba(37,99,235,1)"),
                yAxisID: "facilities"
              },
              {
                ...lineDataset("시설당 아동수", rows, "children_per_facility", "rgba(185,28,28,1)"),
                yAxisID: "ratio",
                borderDash: [5, 4]
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              children: {
                position: "left",
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "보육아동수(명)" },
                ticks: { callback: (value) => Number(value).toLocaleString("ko-KR") }
              },
              facilities: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "어린이집 수(개소)" },
                ticks: { callback: (value) => Number(value).toLocaleString("ko-KR") }
              },
              ratio: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "시설당 아동수" }
              }
            }
          }
        };
      } else if (id === "foreigner_registered_total") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [lineDataset("등록외국인", rows, "registered_foreigners", "rgba(147,51,234,1)")]
          },
          options: common
        };
      } else if (id === "vacant_housing_policy") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("빈집 수", rows, "vacant_housing_count", "rgba(185,28,28,1)"),
              lineDataset("전체 주택", rows, "total_housing_count", "rgba(37,99,235,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "호" },
                ticks: { callback: (value) => Number(value).toLocaleString("ko-KR") }
              }
            }
          }
        };
      } else if (id === "vacant_housing_definition_gap_2022") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.definition),
            datasets: [
              {
                label: "빈집 수",
                data: rows.map((row) => Number(row.count)),
                backgroundColor: ["rgba(37,99,235,.72)", "rgba(185,28,28,.72)"]
              }
            ]
          },
          options: {
            ...common,
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (ctx) => `${ctx.dataset.label}: ${Number(ctx.raw).toLocaleString("ko-KR")}호`
                }
              }
            },
            scales: {
              x: { grid: { display: false } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "호" },
                ticks: { callback: (value) => Number(value).toLocaleString("ko-KR") }
              }
            }
          }
        };
      } else if (id === "molit_vacant_housing_2022") {
        config = {
          type: "bar",
          data: {
            labels: rows.map((row) => row.area_type),
            datasets: [
              {
                label: "장기 빈집 수",
                data: rows.map((row) => Number(row.vacant_housing_count)),
                backgroundColor: ["rgba(37,99,235,.68)", "rgba(15,118,110,.68)", "rgba(180,83,9,.68)"]
              }
            ]
          },
          options: {
            ...common,
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (ctx) => `${ctx.dataset.label}: ${Number(ctx.raw).toLocaleString("ko-KR")}호`
                }
              }
            },
            scales: {
              x: { grid: { display: false } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "호" },
                ticks: { callback: (value) => Number(value).toLocaleString("ko-KR") }
              }
            }
          }
        };
      } else if (id === "fiscal_aging_pressure") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("국가채무 지수", rows, "national_debt_index", "rgba(185,28,28,1)"),
              lineDataset("고령화율 지수", rows, "older_share_index", "rgba(37,99,235,1)")
            ]
          },
          options: common
        };
      } else if (id === "fertility_age_pattern") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("25-29세", rows, "asfr_25_29", "rgba(37,99,235,1)"),
              lineDataset("30-34세", rows, "asfr_30_34", "rgba(15,118,110,1)"),
              lineDataset("35-39세", rows, "asfr_35_39", "rgba(185,28,28,1)"),
              lineDataset("40-44세", rows, "asfr_40_44", "rgba(147,51,234,1)")
            ]
          },
          options: common
        };
      } else if (id === "fertility_measure_summary") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("합계출산율", rows, "tfr_index", "rgba(37,99,235,1)"),
              lineDataset("조출생률", rows, "cbr_index", "rgba(185,28,28,1)"),
              lineDataset("일반출산율", rows, "gfr_index", "rgba(15,118,110,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              ...common.scales,
              y: {
                ...common.scales.y,
                title: { display: true, text: "2000년=100" }
              }
            }
          }
        };
      } else if (id === "fertility_asfr_shift") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("20-24세", rows, "asfr_20_24", "rgba(234,88,12,1)"),
              lineDataset("25-29세", rows, "asfr_25_29", "rgba(37,99,235,1)"),
              lineDataset("30-34세", rows, "asfr_30_34", "rgba(15,118,110,1)"),
              lineDataset("35-39세", rows, "asfr_35_39", "rgba(185,28,28,1)"),
              lineDataset("40-44세", rows, "asfr_40_44", "rgba(147,51,234,1)")
            ]
          },
          options: common
        };
      } else if (id === "cohort_fertility_by_birth_year") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.cohort_birth_year),
            datasets: [
              lineDataset("20-39세 누적 출산율", rows, "cumulative_fertility_20_39", "rgba(37,99,235,1)")
            ]
          },
          options: {
            ...common,
            scales: {
              ...common.scales,
              x: {
                ...common.scales.x,
                title: { display: true, text: "여성 출생연도" }
              },
              y: {
                ...common.scales.y,
                title: { display: true, text: "명/여성" }
              }
            }
          }
        };
      } else if (id === "mean_birth_age_order") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("평균", rows, "mean_birth_age", "rgba(15,118,110,1)"),
              lineDataset("첫째아", rows, "first_child_age", "rgba(37,99,235,1)"),
              lineDataset("둘째아", rows, "second_child_age", "rgba(185,28,28,1)")
            ]
          },
          options: common
        };
      } else if (id === "marriage_attitude_unmarried_gender") {
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const genders = ["미혼 남성", "미혼 여성"];
        const colors = {
          "미혼 남성": "rgba(37,99,235,.72)",
          "미혼 여성": "rgba(185,28,28,.72)"
        };
        const valueFor = (gender, year) => {
          const found = rows.find((row) => row.gender === gender && Number(row.year) === Number(year));
          return found ? Number(found.marriage_positive_pct) : null;
        };
        config = {
          type: "bar",
          data: {
            labels: years,
            datasets: genders.map((gender) => ({
              label: gender,
              data: years.map((year) => valueFor(gender, year)),
              backgroundColor: colors[gender]
            }))
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "조사연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "결혼 긍정 인식(%)" },
                suggestedMin: 0,
                suggestedMax: 70,
                ticks: { callback: (value) => `${value}%` }
              }
            },
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (context) => `${context.dataset.label}: ${Number(context.parsed.y).toFixed(1)}%`
                }
              }
            }
          }
        };
      } else if (id === "family_norms_culture_shift") {
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const indicators = [
          "결혼해야 한다",
          "결혼하지 않아도 함께 살 수 있다",
          "결혼하지 않고도 자녀를 가질 수 있다"
        ];
        const colors = {
          "결혼해야 한다": "rgba(15,118,110,1)",
          "결혼하지 않아도 함께 살 수 있다": "rgba(37,99,235,1)",
          "결혼하지 않고도 자녀를 가질 수 있다": "rgba(185,28,28,1)"
        };
        const valueFor = (indicator, year) => {
          const found = rows.find((row) => row.indicator === indicator && Number(row.year) === Number(year));
          return found ? Number(found.positive_pct) : null;
        };
        config = {
          type: "line",
          data: {
            labels: years,
            datasets: indicators.map((indicator) => ({
              label: indicator,
              data: years.map((year) => valueFor(indicator, year)),
              borderColor: colors[indicator],
              backgroundColor: colors[indicator].replace("1)", ".12)"),
              pointRadius: 4,
              tension: 0.2
            }))
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "조사연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "동의·긍정 응답 비율(%)" },
                suggestedMin: 0,
                suggestedMax: 80,
                ticks: { callback: (value) => `${value}%` }
              }
            }
          }
        };
      } else if (id === "marriage_attitude_youth_profile_2022") {
        const ordered = ["19-34세 전체", "남자", "여자", "19-24세", "25-29세", "30-34세"]
          .map((category) => rows.find((row) => row.category === category))
          .filter(Boolean);
        const colors = ordered.map((row) => {
          if (row.axis === "성별") return row.category === "여자" ? "rgba(185,28,28,.72)" : "rgba(37,99,235,.72)";
          if (row.axis === "연령대") return row.category === "25-29세" ? "rgba(180,83,9,.78)" : "rgba(15,118,110,.62)";
          return "rgba(100,116,139,.68)";
        });
        config = {
          type: "bar",
          data: {
            labels: ordered.map((row) => `${row.axis} · ${row.category}`),
            datasets: [
              {
                label: "결혼 긍정 인식",
                data: ordered.map((row) => Number(row.positive_pct)),
                backgroundColor: colors
              }
            ]
          },
          options: {
            ...common,
            indexAxis: "y",
            scales: {
              x: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "긍정 응답 비율(%)" },
                suggestedMin: 0,
                suggestedMax: 50,
                ticks: { callback: (value) => `${value}%` }
              },
              y: { grid: { display: false } }
            },
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const row = ordered[context.dataIndex];
                    const change = Number.isFinite(Number(row.change_from_2012_pctp))
                      ? `, 2012년 대비 ${Number(row.change_from_2012_pctp).toFixed(1)}%p`
                      : "";
                    return `${Number(context.parsed.x).toFixed(1)}%${change}`;
                  }
                }
              }
            }
          }
        };
      } else if (id === "young_women_25_29_recent_attitudes") {
        const periods = [...new Set(rows.map((row) => row.period))];
        const indicators = ["결혼 의향", "자녀 필요성"];
        const colors = {
          "결혼 의향": "rgba(37,99,235,.72)",
          "자녀 필요성": "rgba(185,28,28,.72)"
        };
        const valueFor = (indicator, period) => {
          const found = rows.find((row) => row.indicator === indicator && row.period === period);
          return found ? Number(found.positive_pct) : null;
        };
        config = {
          type: "bar",
          data: {
            labels: periods,
            datasets: indicators.map((indicator) => ({
              label: indicator,
              data: periods.map((period) => valueFor(indicator, period)),
              backgroundColor: colors[indicator]
            }))
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "조사 시점" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "긍정 응답 비율(%)" },
                suggestedMin: 0,
                suggestedMax: 75,
                ticks: { callback: (value) => `${value}%` }
              }
            },
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  label: (context) => `${context.dataset.label}: ${Number(context.parsed.y).toFixed(1)}%`
                }
              }
            }
          }
        };
      } else if (id === "tfr_gender_conflict_timeline") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                label: "합계출산율",
                data: rows.map((row) => chartNumber(row.tfr)),
                borderColor: "rgba(37,99,235,1)",
                backgroundColor: "rgba(37,99,235,.12)",
                pointRadius: 3,
                tension: 0.18,
                yAxisID: "tfr"
              },
              {
                label: "남녀 갈등 매우 심각",
                data: rows.map((row) => chartNumber(row.gender_conflict_very_serious_pct)),
                borderColor: "rgba(185,28,28,1)",
                backgroundColor: "rgba(185,28,28,.14)",
                borderDash: [5, 4],
                pointRadius: 4,
                spanGaps: true,
                tension: 0.18,
                yAxisID: "conflict"
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              tfr: {
                position: "left",
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "합계출산율" },
                suggestedMin: 0.6,
                suggestedMax: 1.4
              },
              conflict: {
                position: "right",
                grid: { display: false },
                title: { display: true, text: "매우 심각 응답(%)" },
                suggestedMin: 0,
                suggestedMax: 14,
                ticks: { callback: (value) => `${value}%` }
              }
            },
            plugins: {
              ...common.plugins,
              tooltip: {
                callbacks: {
                  afterBody: (items) => {
                    const year = Number(items?.[0]?.label);
                    return year >= 2016 && year <= 2019 ? "2016-2019년은 합계출산율 급락 구간" : "";
                  }
                }
              }
            }
          }
        };
      } else if (id === "divorce_rate_30s_40s_trend") {
        const years = [...new Set(rows.map((row) => Number(row.year)))].sort((a, b) => a - b);
        const series = [
          { sex: "남편", decade: "30대", color: "rgba(37,99,235,1)", dash: [] },
          { sex: "아내", decade: "30대", color: "rgba(37,99,235,.72)", dash: [5, 4] },
          { sex: "남편", decade: "40대", color: "rgba(185,28,28,1)", dash: [] },
          { sex: "아내", decade: "40대", color: "rgba(185,28,28,.72)", dash: [5, 4] }
        ];
        config = {
          type: "line",
          data: {
            labels: years,
            datasets: series.map((item) => ({
              label: `${item.decade} ${item.sex}`,
              data: years.map((year) => {
                const row = rows.find((entry) => Number(entry.year) === year && entry.sex === item.sex && entry.decade === item.decade);
                return row ? chartNumber(row.divorce_rate_per_1000) : null;
              }),
              borderColor: item.color,
              backgroundColor: item.color.replace("1)", ".12)"),
              borderDash: item.dash,
              pointRadius: 2,
              tension: 0.22
            }))
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "해당연령 인구 천명당 이혼건수" },
                ticks: { callback: (value) => `${value}건` }
              }
            }
          }
        };
      } else if (id === "divorce_acceptance_trend") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              {
                label: "이유가 있으면 이혼하는 것이 좋다",
                data: rows.map((row) => chartNumber(row.positive_pct)),
                borderColor: "rgba(185,28,28,1)",
                backgroundColor: "rgba(185,28,28,.12)",
                pointRadius: 4,
                tension: 0.22
              }
            ]
          },
          options: {
            ...common,
            scales: {
              x: { grid: { display: false }, title: { display: true, text: "조사연도" } },
              y: {
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "응답 비중(%)" },
                suggestedMin: 0,
                suggestedMax: 25,
                ticks: { callback: (value) => `${value}%` }
              }
            }
          }
        };
      } else if (id === "divorce_acceptance_profile_2024") {
        const categories = rows.map((row) => row.category);
        const fields = [
          { label: "부정", key: "negative_pct", color: "#64748b" },
          { label: "중립", key: "neutral_pct", color: "#0f766e" },
          { label: "긍정", key: "positive_pct", color: "#be123c" },
          { label: "잘 모르겠다", key: "unknown_pct", color: "#cbd5e1" }
        ];
        config = {
          type: "bar",
          data: {
            labels: categories,
            datasets: fields.map((field) => ({
              label: field.label,
              data: rows.map((row) => chartNumber(row[field.key])),
              backgroundColor: field.color,
              stack: "opinion"
            }))
          },
          options: {
            ...common,
            indexAxis: "y",
            scales: {
              x: {
                stacked: true,
                max: 100,
                grid: { color: "rgba(15,23,42,.08)" },
                title: { display: true, text: "응답 비중(%)" },
                ticks: { callback: (value) => `${value}%` }
              },
              y: { stacked: true, grid: { display: false } }
            }
          }
        };
      } else if (id === "vital_events_policy") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("출생", rows, "births", "rgba(37,99,235,1)"),
              lineDataset("사망", rows, "deaths", "rgba(185,28,28,1)"),
              lineDataset("혼인", rows, "marriages", "rgba(15,118,110,1)"),
              lineDataset("이혼", rows, "divorces", "rgba(147,51,234,1)")
            ]
          },
          options: common
        };
      } else if (id === "young_migration_policy") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("서울 20대", rows, "seoul_20s", "rgba(37,99,235,1)"),
              lineDataset("서울 30대", rows, "seoul_30s", "rgba(185,28,28,1)"),
              lineDataset("경기 20대", rows, "gyeonggi_20s", "rgba(15,118,110,1)"),
              lineDataset("경기 30대", rows, "gyeonggi_30s", "rgba(147,51,234,1)")
            ]
          },
          options: common
        };
      } else if (id === "future_households_policy") {
        config = {
          type: "line",
          data: {
            labels: rows.map((row) => row.year),
            datasets: [
              lineDataset("총가구", rows, "total_households", "rgba(15,118,110,1)"),
              lineDataset("1인가구", rows, "one_person_households", "rgba(37,99,235,1)"),
              lineDataset("2인가구", rows, "two_person_households", "rgba(185,28,28,1)"),
              lineDataset("4인가구", rows, "four_person_households", "rgba(147,51,234,1)")
            ]
          },
          options: common
        };
      }
      if (config) new Chart(canvas, config);
    });
  }

  function findSectionPlan(title) {
    const plan = window.populationBookQuestionPlan || [];
    const normalize = (value) => String(value || "").replace(/^\d+(?:\.\d+)?\s+/, "");
    for (const chapter of plan) {
      for (const section of chapter.sections || []) {
        if (section.title === title || normalize(section.title) === normalize(title)) return section;
      }
    }
    return null;
  }

  function renderQuestionPlans() {
    document.querySelectorAll("[data-section-question-plan]").forEach((el) => {
      const section = findSectionPlan(el.dataset.sectionQuestionPlan || "");
      if (!section) {
        el.innerHTML = '<p class="source-note">질문 설계를 찾지 못했습니다.</p>';
        return;
      }
      el.innerHTML = `
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
            </article>`).join("")}
        </div>`;
    });
  }

  function focusMobileToc() {
    const toc = document.querySelector(".toc");
    const active = toc?.querySelector(".active");
    if (!toc || !active || !window.matchMedia("(max-width: 900px)").matches) return;
    active.scrollIntoView({ block: "nearest", inline: "center" });
  }

  document.addEventListener("DOMContentLoaded", () => {
    focusMobileToc();
    renderQuestionPlans();
    renderBookCharts();
  });
})();
