import os
import shutil

ROOT_DIR = r"C:\ISB Capstone"
APP_PATH = os.path.join(ROOT_DIR, "app.js")
PUBLIC_APP_PATH = os.path.join(ROOT_DIR, "public", "app.js")

with open(APP_PATH, "r", encoding="utf-8") as f:
    js = f.read()

# 1. Update default theme to dark
js = js.replace("theme: localStorage.getItem('app_theme') || 'light',", "theme: localStorage.getItem('app_theme') || 'dark',", 1)

# 2. Add PILLARS definition and pillar navigation logic
pillar_code = """
  // ---------------------------------------------------------------------------
  // 4-PILLAR PRIMARY NAVIGATION ARCHITECTURE (100% PARITY WITH STREAMLIT)
  // ---------------------------------------------------------------------------
  const PILLARS = {
    'csuite': {
      key: 'csuite',
      badge: '💼 C-SUITE EXECUTIVE INTELLIGENCE',
      desc: 'Executive Telemetry Cockpit • Action Queue • Automated C-Suite PDF Briefings',
      defaultView: 'cockpit',
      submodules: [
        { id: 'cockpit', label: '🏠 Executive Cockpit' },
        { id: 'reports', label: '📄 C-Suite Reports' }
      ]
    },
    'forecasting_studio': {
      key: 'forecasting_studio',
      badge: '🎯 AI DEMAND FORECASTING STUDIO',
      desc: 'Predictive SKU Modeling • Algorithm Competition Leaderboard • Hierarchy Reconciliation',
      defaultView: 'forecasting',
      submodules: [
        { id: 'forecasting', label: '🎯 SKU Demand Forecasting' },
        { id: 'modellab', label: '🔬 Model Lab & Leaderboard' },
        { id: 'hierarchy', label: '🌐 Hierarchical Reconciliation' },
        { id: 'holdout', label: '✅ Holdout Validation (FY24-25)' }
      ]
    },
    'operations': {
      key: 'operations',
      badge: '📡 FORECASTING OPERATIONS & DRIFT RADAR',
      desc: 'Tracking Signal • Model Degradation Monitoring • Scenario Stress-Testing • APICS Inventory Calibration',
      defaultView: 'drift',
      submodules: [
        { id: 'drift', label: '📡 Forecast Monitoring & Drift' },
        { id: 'scenarios', label: '🔮 Scenario Simulator' },
        { id: 'inventory', label: '📦 Inventory Intelligence' }
      ]
    },
    'eda': {
      key: 'eda',
      badge: '📊 EXPLORATORY DATA ANALYSIS (EDA) WORKSPACE',
      desc: 'Multi-Dimensional Slicing • Statistical Deep-Dive • Data Quality • Cleaning Studio',
      defaultView: 'explorer',
      submodules: [
        { id: 'explorer', label: '🔍 Intelligence Explorer' },
        { id: 'statistical', label: '📈 Statistical Deep-Dive' },
        { id: 'radar', label: '🛡️ Data Quality Radar' },
        { id: 'cleaning', label: '🧹 Data Cleaning Studio' }
      ]
    }
  };

  state.currentPillar = 'csuite';

  function renderSubNav(pillarKey, activeSubId) {
    const pillar = PILLARS[pillarKey] || PILLARS['csuite'];
    const badgeEl = document.getElementById('subNavBadge');
    const descEl = document.getElementById('subNavDesc');
    const subNavBar = document.getElementById('subNavBar');

    if (badgeEl) badgeEl.textContent = pillar.badge;
    if (descEl) descEl.textContent = pillar.desc;

    if (!subNavBar) return;
    subNavBar.innerHTML = '';

    pillar.submodules.forEach(sub => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `sub-nav-btn ${sub.id === activeSubId ? 'active' : ''}`;
      btn.setAttribute('data-target', sub.id);
      btn.textContent = sub.label;
      btn.addEventListener('click', () => switchView(sub.id));
      subNavBar.appendChild(btn);
    });
  }

  function switchPillar(pillarKey, targetSubId) {
    if (!PILLARS[pillarKey]) return;
    state.currentPillar = pillarKey;

    // Update primary pillar buttons
    const pillarBtns = document.querySelectorAll('#primaryPillarGroup .top-segment-btn');
    pillarBtns.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-pillar') === pillarKey);
    });

    const activeSub = targetSubId || PILLARS[pillarKey].defaultView;
    renderSubNav(pillarKey, activeSub);
    switchView(activeSub);
  }

  // Wire primary pillar buttons
  setTimeout(() => {
    const pillarBtns = document.querySelectorAll('#primaryPillarGroup .top-segment-btn');
    pillarBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const p = btn.getAttribute('data-pillar');
        if (p) switchPillar(p);
      });
    });
  }, 10);
"""

# Insert PILLARS code right before function switchView
js = js.replace("  function switchView(targetView) {", pillar_code + "\n  function switchView(targetView) {", 1)

# 3. Update switchView to sync sub-nav buttons and pillar if necessary
old_switch_sync = """    // Sync top segment buttons
    topNavBtns.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-target') === targetView);
    });"""

new_switch_sync = """    // Sync sub-navigation dock buttons
    const subNavBtns = document.querySelectorAll('#subNavBar .sub-nav-btn');
    subNavBtns.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-target') === targetView);
    });

    // Determine and sync owning pillar
    for (const [pKey, pVal] of Object.entries(PILLARS)) {
      if (pVal.submodules.some(s => s.id === targetView)) {
        if (state.currentPillar !== pKey) {
          state.currentPillar = pKey;
          const pBtns = document.querySelectorAll('#primaryPillarGroup .top-segment-btn');
          pBtns.forEach(b => b.classList.toggle('active', b.getAttribute('data-pillar') === pKey));
          renderSubNav(pKey, targetView);
        }
        break;
      }
    }"""

js = js.replace(old_switch_sync, new_switch_sync, 1)

# 4. Add chart renderers for Model Lab, Hierarchy, Drift, Scenarios, Inventory
new_charts_code = """
  // ---------------------------------------------------------------------------
  // VIEW: MODEL LAB CHARTS
  // ---------------------------------------------------------------------------
  function renderModelLabCharts() {
    const chartEl = document.getElementById('chartModelLabShap');
    if (!chartEl || !window.Plotly) return;

    const isDark = (state.theme === 'dark');
    const layout = getPlotlyLayoutTheme();
    layout.margin = { l: 150, r: 30, t: 30, b: 40 };

    const features = [
      'star_rating',
      'segment_inverter',
      'tonnage_val',
      'rolling_12w_std',
      'seasonal_profile_ratio',
      'rolling_4w_mean',
      'lag_1_demand'
    ];
    const importances = [0.055, 0.072, 0.089, 0.114, 0.165, 0.221, 0.284];

    const trace = {
      x: importances,
      y: features,
      type: 'bar',
      orientation: 'h',
      marker: {
        color: importances.map((_, i) => i >= 5 ? '#00E5FF' : (i >= 3 ? '#6366F1' : '#10B981')),
        line: { color: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)', width: 1 }
      },
      text: importances.map(v => (v * 100).toFixed(1) + '% impact'),
      textposition: 'auto',
      hoverinfo: 'x+y'
    };

    Plotly.react(chartEl, [trace], layout, { displayModeBar: false, responsive: true });
  }

  // ---------------------------------------------------------------------------
  // VIEW: HIERARCHY RECONCILIATION CHARTS
  // ---------------------------------------------------------------------------
  function renderHierarchyCharts() {
    const chartEl = document.getElementById('chartHierarchyWaterfall');
    if (!chartEl || !window.Plotly) return;

    const isDark = (state.theme === 'dark');
    const layout = getPlotlyLayoutTheme();
    layout.barmode = 'group';

    const categories = ['Chennai (MAA)', 'Secunderabad (SBD)', 'Vijayawada (SBD1)', 'Cochin (COK)', 'Bangalore (BLR)'];
    const unreconciled = [32609, 25793, 14923, 9949, 8844];
    const reconciled = [32501, 25707, 14873, 9916, 8814];

    const trace1 = {
      name: 'Base Unreconciled',
      x: categories,
      y: unreconciled,
      type: 'bar',
      marker: { color: isDark ? 'rgba(0, 229, 255, 0.45)' : 'rgba(2, 132, 199, 0.45)' }
    };

    const trace2 = {
      name: 'MinT Optimal Reconciled',
      x: categories,
      y: reconciled,
      type: 'bar',
      marker: { color: '#10B981' }
    };

    Plotly.react(chartEl, [trace1, trace2], layout, { displayModeBar: false, responsive: true });
  }

  // ---------------------------------------------------------------------------
  // VIEW: DRIFT RADAR CHARTS
  // ---------------------------------------------------------------------------
  function renderDriftCharts() {
    const chartEl = document.getElementById('chartDriftTracking');
    if (!chartEl || !window.Plotly) return;

    const isDark = (state.theme === 'dark');
    const layout = getPlotlyLayoutTheme();

    const weeks = Array.from({ length: 24 }, (_, i) => `Wk ${i + 1}`);
    const trackingSignal = [
      0.2, 0.5, 0.8, 1.2, 1.6, 2.1, 1.8, 1.5, 1.2, 0.9, 0.4, 0.1,
      -0.3, -0.7, -1.2, -1.8, -1.4, -0.9, -0.2, 0.4, 0.9, 1.2, 1.4, 1.42
    ];

    const traceSignal = {
      x: weeks,
      y: trackingSignal,
      mode: 'lines+markers',
      name: 'Tracking Signal',
      line: { color: isDark ? '#00E5FF' : '#0284C7', width: 3, shape: 'spline' },
      marker: { size: 6, color: '#6366F1' }
    };

    const traceUpper = {
      x: weeks,
      y: Array(24).fill(4.0),
      mode: 'lines',
      name: 'Upper Control (+4.0)',
      line: { color: '#F43F5E', width: 2, dash: 'dash' }
    };

    const traceLower = {
      x: weeks,
      y: Array(24).fill(-4.0),
      mode: 'lines',
      name: 'Lower Control (-4.0)',
      line: { color: '#F43F5E', width: 2, dash: 'dash' }
    };

    const traceZero = {
      x: weeks,
      y: Array(24).fill(0.0),
      mode: 'lines',
      name: 'Zero Bias Rail',
      line: { color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)', width: 1, dash: 'dot' }
    };

    Plotly.react(chartEl, [traceSignal, traceUpper, traceLower, traceZero], layout, { displayModeBar: false, responsive: true });
  }

  // ---------------------------------------------------------------------------
  // VIEW: SCENARIO SIMULATOR CHARTS
  // ---------------------------------------------------------------------------
  let currentScenarioMultiplier = 1.25;

  function renderScenarioCharts() {
    const chartEl = document.getElementById('chartScenarioCurve');
    if (!chartEl || !window.Plotly) return;

    const isDark = (state.theme === 'dark');
    const layout = getPlotlyLayoutTheme();

    const weeks = Array.from({ length: 12 }, (_, i) => `Forward Wk ${i + 1}`);
    const baseline = [7420, 7610, 7850, 8100, 8250, 8190, 7950, 7680, 7350, 7120, 6980, 7004];
    const shocked = baseline.map(v => Math.round(v * currentScenarioMultiplier));

    const traceBase = {
      x: weeks,
      y: baseline,
      mode: 'lines+markers',
      name: 'Baseline Plan',
      line: { color: isDark ? '#94A3B8' : '#64748B', width: 2.5, dash: 'dot' }
    };

    const traceShock = {
      x: weeks,
      y: shocked,
      mode: 'lines+markers',
      name: 'Shock-Stressed Trajectory',
      line: { color: currentScenarioMultiplier >= 1 ? '#F59E0B' : '#F43F5E', width: 3.5, shape: 'spline' },
      fill: 'tonexty',
      fillcolor: currentScenarioMultiplier >= 1 ? 'rgba(245, 158, 11, 0.12)' : 'rgba(244, 63, 94, 0.12)'
    };

    Plotly.react(chartEl, [traceBase, traceShock], layout, { displayModeBar: false, responsive: true });

    // Update KPI values
    const totalBase = baseline.reduce((a, b) => a + b, 0);
    const totalShocked = shocked.reduce((a, b) => a + b, 0);
    const delta = totalShocked - totalBase;
    const deltaPct = ((currentScenarioMultiplier - 1.0) * 100).toFixed(0);

    const baseEl = document.getElementById('scenBaseVal');
    const shockEl = document.getElementById('scenStressedVal');
    const subEl = document.getElementById('scenStressedSub');
    const capEl = document.getElementById('scenCapitalVal');

    if (baseEl) baseEl.textContent = totalBase.toLocaleString() + ' units';
    if (shockEl) shockEl.textContent = totalShocked.toLocaleString() + ' units';
    if (subEl) subEl.textContent = `${delta >= 0 ? '+' : ''}${delta.toLocaleString()} units net shock (${deltaPct >= 0 ? '+' : ''}${deltaPct}%)`;
    if (capEl) capEl.textContent = `₹ ${(totalShocked * 25000 / 10000000).toFixed(2)} Cr`;
  }

  // ---------------------------------------------------------------------------
  // VIEW: INVENTORY INTELLIGENCE CHARTS
  // ---------------------------------------------------------------------------
  let currentLeadTimeWeeks = 2;
  let currentServiceLevel = 0.95;
  let currentUnitCost = 25000;

  function renderInventoryCharts() {
    const chartEl = document.getElementById('chartInventoryCurve');
    if (!chartEl || !window.Plotly) return;

    const isDark = (state.theme === 'dark');
    const layout = getPlotlyLayoutTheme();

    const serviceLevels = [0.80, 0.85, 0.90, 0.92, 0.95, 0.97, 0.98, 0.99, 0.995];
    const zScores = [0.84, 1.04, 1.28, 1.41, 1.65, 1.88, 2.05, 2.33, 2.58];
    const stdDevLeadTime = 1650 * Math.sqrt(currentLeadTimeWeeks);

    const safetyStocks = zScores.map(z => Math.round(z * stdDevLeadTime));
    const labels = serviceLevels.map(sl => (sl * 100).toFixed(1) + '%');

    const traceCurve = {
      x: labels,
      y: safetyStocks,
      mode: 'lines+markers',
      name: 'Safety Stock Buffer',
      line: { color: '#10B981', width: 3.5, shape: 'spline' },
      marker: { size: 7, color: '#00E5FF' },
      fill: 'tozeroy',
      fillcolor: 'rgba(16, 185, 129, 0.12)'
    };

    Plotly.react(chartEl, [traceCurve], layout, { displayModeBar: false, responsive: true });

    // Update KPI cards
    const meanWeeklyDraw = 7625;
    const ltd = Math.round(meanWeeklyDraw * currentLeadTimeWeeks);
    const zCurrent = currentServiceLevel >= 0.99 ? 2.33 : (currentServiceLevel >= 0.98 ? 2.05 : (currentServiceLevel >= 0.95 ? 1.65 : (currentServiceLevel >= 0.90 ? 1.28 : 1.04)));
    const ss = Math.round(zCurrent * stdDevLeadTime);
    const rop = ltd + ss;
    const capCrores = (ss * currentUnitCost / 10000000).toFixed(2);

    const ltdEl = document.getElementById('invLtdVal');
    const ssEl = document.getElementById('invSsVal');
    const ropEl = document.getElementById('invRopVal');
    const capEl = document.getElementById('invCapitalVal');

    if (ltdEl) ltdEl.textContent = ltd.toLocaleString() + ' units';
    if (ssEl) ssEl.textContent = ss.toLocaleString() + ' units';
    if (ropEl) ropEl.textContent = rop.toLocaleString() + ' units';
    if (capEl) capEl.textContent = `₹ ${capCrores} Cr`;
  }
"""

# Update renderCurrentViewCharts to include new views
old_render_switch = """      case 'explorer':
        renderExplorerTable();
        break;"""

new_render_switch = """      case 'explorer':
        renderExplorerTable();
        break;
      case 'modellab':
        renderModelLabCharts();
        break;
      case 'hierarchy':
        renderHierarchyCharts();
        break;
      case 'drift':
        renderDriftCharts();
        break;
      case 'scenarios':
        renderScenarioCharts();
        break;
      case 'inventory':
        renderInventoryCharts();
        break;"""

js = js.replace(old_render_switch, new_render_switch, 1)

# Append new charts code before bootstrap
js = js.replace("  // ---------------------------------------------------------------------------\n  // INITIAL DATA BOOTSTRAP", new_charts_code + "\n  // ---------------------------------------------------------------------------\n  // INITIAL DATA BOOTSTRAP", 1)

# Wire interactive studio, scenario, and inventory controls in bootstrap
bootstrap_init_code = """
    // Wire In-Page Forecasting Studio controls
    const studioBranchSelect = document.getElementById('studioBranchSelect');
    const studioSkuSelect = document.getElementById('studioSkuSelect');
    const studioModelSelect = document.getElementById('studioModelSelect');
    const studioRunBtn = document.getElementById('studioRunBtn');

    if (studioBranchSelect && forecastBranchSelect) {
      studioBranchSelect.addEventListener('change', () => {
        forecastBranchSelect.value = studioBranchSelect.value;
        state.selectedBranch = studioBranchSelect.value;
        updateForecastStudio();
      });
    }
    if (studioSkuSelect && forecastSkuSelect) {
      studioSkuSelect.addEventListener('change', () => {
        forecastSkuSelect.value = studioSkuSelect.value;
        state.selectedSku = studioSkuSelect.value;
        updateForecastStudio();
      });
    }
    if (studioModelSelect && forecastModelSelect) {
      studioModelSelect.addEventListener('change', () => {
        forecastModelSelect.value = studioModelSelect.value;
        state.selectedModel = studioModelSelect.value;
        updateForecastStudio();
      });
    }
    if (studioRunBtn) {
      studioRunBtn.addEventListener('click', () => updateForecastStudio());
    }

    // Wire Scenario Simulator controls
    const scenPreset = document.getElementById('scenarioPresetSelect');
    const customShockWrap = document.getElementById('customShockWrap');
    const customSlider = document.getElementById('customShockSlider');
    const customVal = document.getElementById('customShockVal');
    const runScenBtn = document.getElementById('runScenarioBtn');

    if (scenPreset) {
      scenPreset.addEventListener('change', () => {
        const val = scenPreset.value;
        if (val === 'heatwave') {
          currentScenarioMultiplier = 1.25;
          if (customShockWrap) customShockWrap.style.display = 'none';
        } else if (val === 'port_delay') {
          currentScenarioMultiplier = 0.70;
          if (customShockWrap) customShockWrap.style.display = 'none';
        } else if (val === 'promotion') {
          currentScenarioMultiplier = 1.35;
          if (customShockWrap) customShockWrap.style.display = 'none';
        } else if (val === 'custom') {
          if (customShockWrap) customShockWrap.style.display = 'flex';
          const pct = parseInt(customSlider.value, 10) || 0;
          currentScenarioMultiplier = 1.0 + (pct / 100.0);
        }
        renderScenarioCharts();
      });
    }

    if (customSlider && customVal) {
      customSlider.addEventListener('input', () => {
        const pct = parseInt(customSlider.value, 10) || 0;
        customVal.textContent = (pct >= 0 ? '+' : '') + pct + '%';
        currentScenarioMultiplier = 1.0 + (pct / 100.0);
        renderScenarioCharts();
      });
    }

    if (runScenBtn) {
      runScenBtn.addEventListener('click', () => renderScenarioCharts());
    }

    // Wire Inventory Intelligence controls
    const ltSlider = document.getElementById('invLeadTimeSlider');
    const ltLabel = document.getElementById('invLeadTimeLabel');
    const slSelect = document.getElementById('invServiceLevelSelect');
    const costInput = document.getElementById('invUnitCostInput');

    if (ltSlider && ltLabel) {
      ltSlider.addEventListener('input', () => {
        currentLeadTimeWeeks = parseInt(ltSlider.value, 10) || 2;
        ltLabel.textContent = `${currentLeadTimeWeeks} Weeks`;
        renderInventoryCharts();
      });
    }

    if (slSelect) {
      slSelect.addEventListener('change', () => {
        currentServiceLevel = parseFloat(slSelect.value) || 0.95;
        renderInventoryCharts();
      });
    }

    if (costInput) {
      costInput.addEventListener('input', () => {
        currentUnitCost = parseFloat(costInput.value) || 25000;
        renderInventoryCharts();
      });
    }

    // Initialize 4-Pillar Sub-Navigation Dock
    renderSubNav(state.currentPillar, state.currentView);
"""

# Insert bootstrap wiring before renderCockpitCharts
js = js.replace("    // Initialize View Modules\n    renderCockpitCharts();", bootstrap_init_code + "\n    // Initialize View Modules\n    renderCockpitCharts();", 1)

# Write updated app.js
with open(APP_PATH, "w", encoding="utf-8") as f:
    f.write(js)
shutil.copy2(APP_PATH, PUBLIC_APP_PATH)
print(f"Updated app.js and public/app.js ({len(js)} bytes)")
