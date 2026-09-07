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

  // Live Streamlit Engine Controller
  const engineIframe = document.getElementById('engineIframe');
  const engineLoader = document.getElementById('engineLoader');
  const engineUrlInput = document.getElementById('engineUrlInput');
  const applyUrlBtn = document.getElementById('applyUrlBtn');
  const reloadEngineBtn = document.getElementById('reloadEngineBtn');
  const openNewTabBtn = document.getElementById('openNewTabBtn');
  const fullscreenBtn = document.getElementById('fullscreenBtn');

  // Load saved custom URL or default
  const savedUrl = localStorage.getItem('daikin_streamlit_url') || 'http://localhost:8501';
  if (engineUrlInput) {
    engineUrlInput.value = savedUrl;
  }

  function loadEngine(url) {
    if (!engineIframe) return;
    if (engineLoader) engineLoader.classList.remove('hidden');
    engineIframe.src = url;
    localStorage.setItem('daikin_streamlit_url', url);
  }

  if (engineIframe) {
    engineIframe.addEventListener('load', () => {
      if (engineLoader) engineLoader.classList.add('hidden');
    });

    // In case iframe doesn't trigger onload due to security/network
    setTimeout(() => {
      if (engineLoader) engineLoader.classList.add('hidden');
    }, 4000);
  }

  if (applyUrlBtn && engineUrlInput) {
    applyUrlBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const url = engineUrlInput.value.trim();
      if (url) loadEngine(url);
    });
  }

  if (reloadEngineBtn && engineIframe) {
    reloadEngineBtn.addEventListener('click', () => {
      if (engineUrlInput) loadEngine(engineUrlInput.value.trim());
    });
  }

  if (openNewTabBtn && engineUrlInput) {
    openNewTabBtn.addEventListener('click', () => {
      const url = engineUrlInput.value.trim() || 'http://localhost:8501';
      window.open(url, '_blank');
    });
  }

  if (fullscreenBtn) {
    fullscreenBtn.addEventListener('click', () => {
      const container = document.querySelector('.engine-iframe-wrapper');
      if (!document.fullscreenElement) {
        if (container.requestFullscreen) container.requestFullscreen();
        else if (container.webkitRequestFullscreen) container.webkitRequestFullscreen();
      } else {
        if (document.exitFullscreen) document.exitFullscreen();
      }
    });
  }

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
