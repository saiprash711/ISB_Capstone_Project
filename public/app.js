/**
 * Daikin AI Intelligence & Demand Forecasting Portal
 * Interactive Client Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  // Module Gallery Data
  const modulesData = {
    cockpit: {
      title: 'Executive Cockpit & Sales Telemetry',
      badge: 'Core Analytics',
      desc: 'Real-time bird’s-eye monitoring of total order volume, monthly tonnage distributions, channel splits, and regional branch performance across South India.',
      image: 'assets/verified_light_cockpit.png',
      features: [
        'Multi-metric KPI cards with dynamic trend calculations',
        'Interactive Plotly monthly volume vs. tonnage time series',
        'Sales channel distribution (Dealers, Direct, Projects)',
        'Executive telemetry with dynamic theme engine'
      ]
    },
    radar: {
      title: 'Data Quality Radar & Health Audit',
      badge: 'Automated Audit',
      desc: 'Automated data hygiene scoring, missing-value heatmaps, duplicate row audits, and column-level schema completeness checks before modeling.',
      image: 'assets/verified_light_radar.png',
      features: [
        'Calculated overall health score (99.8% clean)',
        'Column-by-column missing value & nullity distribution',
        'Duplicate invoice identification and row entropy metrics',
        'Data hygiene certification badge for capstone presentation'
      ]
    },
    cleaning: {
      title: 'Data Cleaning Studio & Transformer',
      badge: 'Transformation Engine',
      desc: 'Interactive data transformation engine supporting outlier truncation, statistical imputation, duplicate purging, and instant export of cleaned datasets.',
      image: 'assets/verified_light_cleaning.png',
      features: [
        'Configurable median/mean/mode imputation algorithms',
        'IQR and Z-score outlier filtering threshold controls',
        'Real-time before/after dataset comparison metrics',
        '1-click export of sanitized CSV/Excel payloads'
      ]
    },
    statistical: {
      title: 'Statistical Engine & Correlation Matrix',
      badge: 'Advanced Analytics',
      desc: 'In-depth statistical distributions, cross-variable correlation heatmaps, hypothesis testing, and product-tier sales variances.',
      image: 'assets/verified_light_statistical.png',
      features: [
        'Pearson & Spearman correlation matrix heatmaps',
        'Kernel density estimations (KDE) for order tonnage',
        'Parametric vs. non-parametric hypothesis tests',
        'Inter-branch statistical variance breakdowns'
      ]
    },
    explorer: {
      title: 'Detailed Data Explorer & Drill-Down',
      badge: 'Interactive Query',
      desc: 'High-speed tabular exploration tool with multi-column filtering, text search across material descriptions, and instant slice downloads.',
      image: 'assets/verified_light_explorer.png',
      features: [
        'Real-time faceted filtering across 5 South India hubs',
        'Sub-second search across 54,000+ line-item records',
        'Custom column selection and sorting mechanisms',
        'CSV/Excel download of filtered data subsets'
      ]
    },
    forecasting: {
      title: 'Predictive Demand Forecasting (ARIMA/SARIMAX)',
      badge: 'Machine Learning',
      desc: 'Time-series forecasting engine with ARIMA(1,1,1), SARIMAX seasonal decomposition, Random Forest regressors, and 95% confidence intervals.',
      image: 'assets/verified_light_forecasting.png',
      features: [
        'Configurable forecast horizons (30, 60, 90, 180 days)',
        'Historical vs. projected tonnage comparison with upper/lower bounds',
        'Seasonal component extraction & peak demand warning signals',
        'Direct download of model outputs in CSV format'
      ]
    }
  };

  // Module Gallery Switching
  const moduleBtns = document.querySelectorAll('.module-tab-btn');
  const moduleImage = document.getElementById('moduleImage');
  const moduleTitle = document.getElementById('moduleTitle');
  const moduleDesc = document.getElementById('moduleDesc');
  const moduleFeatures = document.getElementById('moduleFeatures');

  moduleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      moduleBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const modKey = btn.getAttribute('data-module');
      const data = modulesData[modKey];

      if (data) {
        moduleImage.src = data.image;
        moduleImage.alt = data.title;
        moduleTitle.textContent = data.title;
        moduleDesc.textContent = data.desc;

        moduleFeatures.innerHTML = data.features
          .map(f => `<li><span class="check">✓</span><span>${f}</span></li>`)
          .join('');
      }
    });
  });

  // Nav Tab Switching (Scroll to or Toggle)
  const navBtns = document.querySelectorAll('.nav-tab-btn');
  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      navBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const targetId = btn.getAttribute('data-target');
      const targetElem = document.getElementById(targetId);
      if (targetElem) {
        targetElem.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ---------------------------------------------------------------------------
  // NATIVE CLIENT-SIDE INTERACTIVE FORECASTING & ANALYTICS ENGINE
  // ---------------------------------------------------------------------------
  const branchSelect = document.getElementById('branchSelect');
  const skuSelect = document.getElementById('skuSelect');
  const viewTrendBtn = document.getElementById('viewTrendBtn');
  const viewBarBtn = document.getElementById('viewBarBtn');
  const resetFiltersBtn = document.getElementById('resetFiltersBtn');
  const exportSliceBtn = document.getElementById('exportSliceBtn');

  const kpiTotalQty = document.getElementById('kpiTotalQty');
  const kpiPeakQty = document.getElementById('kpiPeakQty');
  const kpiPeakWeek = document.getElementById('kpiPeakWeek');
  const kpiAvgQty = document.getElementById('kpiAvgQty');
  const kpiSkuCount = document.getElementById('kpiSkuCount');

  const tableSliceCount = document.getElementById('tableSliceCount');
  const forecastTableBody = document.getElementById('forecastTableBody');
  const chartContainer = document.getElementById('plotlyForecastChart');

  let forecastData = [];
  let currentChartMode = 'trend'; // 'trend' | 'bar'

  const BRANCH_NAMES = {
    'BLR': 'Bangalore (BLR)',
    'MAA': 'Chennai (MAA)',
    'COK': 'Cochin (COK)',
    'SBD': 'Secunderabad (SBD)',
    'SBD1': 'Vijayawada (SBD1)'
  };

  // Load and parse CSV
  async function initAnalyticsEngine() {
    try {
      const response = await fetch('assets/ARIMA_Forecast_Results.csv');
      if (!response.ok) throw new Error('Failed to load forecast data');
      const csvText = await response.text();
      forecastData = parseCSV(csvText);

      // Populate SKU Select Options
      const uniqueSkus = Array.from(new Set(forecastData.map(d => d.sku))).sort();
      if (skuSelect) {
        skuSelect.innerHTML = '<option value="ALL">All High-Volume SKUs (15 Products)</option>' +
          uniqueSkus.map(sku => `<option value="${sku}">${sku}</option>`).join('');
      }

      updateDashboard();
    } catch (err) {
      console.error('Error initializing analytics engine:', err);
      if (chartContainer) {
        chartContainer.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);">Failed to load forecast dataset.</div>`;
      }
    }
  }

  function parseCSV(text) {
    const lines = text.trim().split(/\r?\n/);
    if (lines.length <= 1) return [];
    const rows = [];
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      const parts = line.split(',');
      if (parts.length >= 5) {
        rows.push({
          branch: parts[0].trim(),
          sku: parts[1].trim(),
          forecastWeek: parseInt(parts[2].trim(), 10) || 0,
          weekStart: parts[3].trim(),
          forecastQty: parseFloat(parts[4].trim()) || 0
        });
      }
    }
    return rows;
  }

  function getFilteredData() {
    const branchVal = branchSelect ? branchSelect.value : 'ALL';
    const skuVal = skuSelect ? skuSelect.value : 'ALL';

    return forecastData.filter(item => {
      const matchBranch = (branchVal === 'ALL' || item.branch === branchVal);
      const matchSku = (skuVal === 'ALL' || item.sku === skuVal);
      return matchBranch && matchSku;
    });
  }

  function updateDashboard() {
    const filtered = getFilteredData();
    updateKPIs(filtered);
    renderPlotlyChart(filtered);
    updateTable(filtered);
  }

  function updateKPIs(data) {
    if (!data.length) {
      if (kpiTotalQty) kpiTotalQty.textContent = '0';
      if (kpiPeakQty) kpiPeakQty.textContent = '0';
      if (kpiPeakWeek) kpiPeakWeek.textContent = 'None';
      if (kpiAvgQty) kpiAvgQty.textContent = '0';
      if (kpiSkuCount) kpiSkuCount.textContent = '0';
      return;
    }

    const totalQty = data.reduce((acc, row) => acc + row.forecastQty, 0);
    
    // Group by week to find peak week demand
    const weekMap = {};
    data.forEach(row => {
      weekMap[row.weekStart] = (weekMap[row.weekStart] || 0) + row.forecastQty;
    });

    let peakQty = 0;
    let peakWeek = '';
    const weekKeys = Object.keys(weekMap);
    weekKeys.forEach(wk => {
      if (weekMap[wk] > peakQty) {
        peakQty = weekMap[wk];
        peakWeek = wk;
      }
    });

    const avgQty = weekKeys.length ? Math.round(totalQty / weekKeys.length) : 0;
    const uniqueSkus = new Set(data.map(d => d.sku)).size;

    if (kpiTotalQty) kpiTotalQty.textContent = Math.round(totalQty).toLocaleString();
    if (kpiPeakQty) kpiPeakQty.textContent = Math.round(peakQty).toLocaleString();
    if (kpiPeakWeek) kpiPeakWeek.textContent = peakWeek ? `Peak: ${peakWeek}` : 'N/A';
    if (kpiAvgQty) kpiAvgQty.textContent = avgQty.toLocaleString() + ' / wk';
    if (kpiSkuCount) kpiSkuCount.textContent = uniqueSkus.toString();
  }

  function renderPlotlyChart(data) {
    if (!chartContainer || typeof Plotly === 'undefined') return;

    if (!data.length) {
      chartContainer.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);font-size:0.95rem;">No data found matching filter selection.</div>`;
      return;
    }

    if (currentChartMode === 'trend') {
      // Group by WeekStart
      const weekSums = {};
      const weekOrder = [];
      data.forEach(row => {
        if (!weekSums[row.weekStart]) {
          weekSums[row.weekStart] = 0;
          weekOrder.push(row.weekStart);
        }
        weekSums[row.weekStart] += row.forecastQty;
      });

      const xVals = weekOrder;
      const yVals = weekOrder.map(wk => Math.round(weekSums[wk]));

      const trace = {
        x: xVals,
        y: yVals,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Projected Demand',
        line: {
          color: '#00E5FF',
          width: 3.5,
          shape: 'spline'
        },
        marker: {
          color: '#00E5FF',
          size: 8,
          symbol: 'circle',
          line: { color: '#0A0E1A', width: 2 }
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(0, 229, 255, 0.12)',
        hovertemplate: '<b>Week of %{x}</b><br>Forecast: %{y:,} units<extra></extra>'
      };

      const layout = {
        title: {
          text: 'ARIMA Weekly Demand Forecast Horizon (Units / Tonnage)',
          font: { family: 'Outfit, sans-serif', size: 16, color: '#FFFFFF' },
          x: 0.02
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Plus Jakarta Sans, sans-serif', color: '#94A3B8' },
        margin: { l: 60, r: 30, t: 50, b: 50 },
        xaxis: {
          title: 'Timeline (Week Start)',
          gridcolor: 'rgba(255, 255, 255, 0.06)',
          linecolor: 'rgba(255, 255, 255, 0.15)',
          tickfont: { size: 11, color: '#94A3B8' }
        },
        yaxis: {
          title: 'Forecast Units',
          gridcolor: 'rgba(255, 255, 255, 0.06)',
          linecolor: 'rgba(255, 255, 255, 0.15)',
          tickfont: { size: 11, color: '#94A3B8' }
        },
        hovermode: 'x unified'
      };

      const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']
      };

      Plotly.newPlot(chartContainer, [trace], layout, config);
    } else {
      // Group by Branch
      const branchSums = { BLR: 0, MAA: 0, COK: 0, SBD: 0, SBD1: 0 };
      data.forEach(row => {
        if (branchSums[row.branch] !== undefined) {
          branchSums[row.branch] += row.forecastQty;
        } else {
          branchSums[row.branch] = row.forecastQty;
        }
      });

      const branches = Object.keys(branchSums);
      const xLabels = branches.map(b => BRANCH_NAMES[b] || b);
      const yAmounts = branches.map(b => Math.round(branchSums[b]));

      const barColors = [
        'rgba(0, 229, 255, 0.85)',
        'rgba(99, 102, 241, 0.85)',
        'rgba(16, 185, 129, 0.85)',
        'rgba(245, 158, 11, 0.85)',
        'rgba(168, 85, 247, 0.85)'
      ];

      const trace = {
        x: xLabels,
        y: yAmounts,
        type: 'bar',
        marker: {
          color: barColors,
          line: { color: 'rgba(255, 255, 255, 0.2)', width: 1.5 }
        },
        text: yAmounts.map(v => v.toLocaleString() + ' u'),
        textposition: 'auto',
        textfont: { family: 'Outfit, sans-serif', color: '#FFFFFF', weight: 'bold' },
        hovertemplate: '<b>%{x}</b><br>Forecast: %{y:,} units<extra></extra>'
      };

      const layout = {
        title: {
          text: 'Regional Branch Forecast Allocation (South India Hubs)',
          font: { family: 'Outfit, sans-serif', size: 16, color: '#FFFFFF' },
          x: 0.02
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Plus Jakarta Sans, sans-serif', color: '#94A3B8' },
        margin: { l: 60, r: 30, t: 50, b: 60 },
        xaxis: {
          gridcolor: 'rgba(255, 255, 255, 0.06)',
          tickfont: { size: 11, color: '#FFFFFF' }
        },
        yaxis: {
          title: 'Total Forecast Units',
          gridcolor: 'rgba(255, 255, 255, 0.06)',
          tickfont: { size: 11, color: '#94A3B8' }
        }
      };

      const config = {
        responsive: true,
        displayModeBar: false
      };

      Plotly.newPlot(chartContainer, [trace], layout, config);
    }
  }

  function updateTable(data) {
    if (!forecastTableBody || !tableSliceCount) return;

    tableSliceCount.textContent = `Showing ${Math.min(data.length, 50)} of ${data.length} entries (${data.length === forecastData.length ? 'Full Dataset' : 'Filtered Slice'})`;

    const previewRows = data.slice(0, 50);
    forecastTableBody.innerHTML = previewRows.map(row => `
      <tr>
        <td><strong>${BRANCH_NAMES[row.branch] || row.branch}</strong></td>
        <td><code>${row.sku}</code></td>
        <td>Week ${row.forecastWeek}</td>
        <td>${row.weekStart}</td>
        <td style="color: var(--cyan-primary); font-weight: 700;">${Math.round(row.forecastQty).toLocaleString()}</td>
      </tr>
    `).join('');
  }

  // Filter Listeners
  if (branchSelect) branchSelect.addEventListener('change', updateDashboard);
  if (skuSelect) skuSelect.addEventListener('change', updateDashboard);

  if (viewTrendBtn) {
    viewTrendBtn.addEventListener('click', () => {
      currentChartMode = 'trend';
      viewTrendBtn.classList.add('active');
      if (viewBarBtn) viewBarBtn.classList.remove('active');
      updateDashboard();
    });
  }

  if (viewBarBtn) {
    viewBarBtn.addEventListener('click', () => {
      currentChartMode = 'bar';
      viewBarBtn.classList.add('active');
      if (viewTrendBtn) viewTrendBtn.classList.remove('active');
      updateDashboard();
    });
  }

  if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener('click', () => {
      if (branchSelect) branchSelect.value = 'ALL';
      if (skuSelect) skuSelect.value = 'ALL';
      currentChartMode = 'trend';
      if (viewTrendBtn) viewTrendBtn.classList.add('active');
      if (viewBarBtn) viewBarBtn.classList.remove('active');
      updateDashboard();
    });
  }

  if (exportSliceBtn) {
    exportSliceBtn.addEventListener('click', () => {
      const filtered = getFilteredData();
      if (!filtered.length) return;

      let csv = 'Branch,SKU,ForecastWeek,WeekStart,ForecastQty\r\n';
      filtered.forEach(r => {
        csv += `${r.branch},${r.sku},${r.forecastWeek},${r.weekStart},${r.forecastQty}\r\n`;
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Daikin_ARIMA_Forecast_${branchSelect ? branchSelect.value : 'ALL'}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  // Initialize engine
  initAnalyticsEngine();

  // Image Zoom Modal
  const modalOverlay = document.getElementById('imageModal');
  const modalImage = document.getElementById('modalImage');
  const modalCloseBtn = document.getElementById('modalCloseBtn');

  if (moduleImage && modalOverlay && modalImage) {
    moduleImage.addEventListener('click', () => {
      modalImage.src = moduleImage.src;
      modalOverlay.classList.add('active');
    });
  }

  if (modalCloseBtn && modalOverlay) {
    modalCloseBtn.addEventListener('click', () => {
      modalOverlay.classList.remove('active');
    });

    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) {
        modalOverlay.classList.remove('active');
      }
    });
  }

  // Escape key closes modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalOverlay) {
      modalOverlay.classList.remove('active');
    }
  });
});
