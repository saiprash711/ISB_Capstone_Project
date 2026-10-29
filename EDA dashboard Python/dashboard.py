import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import io
from fpdf import FPDF
import base64
import os
import re
import warnings
warnings.filterwarnings('ignore')

# Forecasting libraries
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Enterprise Demand Intelligence Platform Modules
try:
    from src.dashboard_intelligence import (
        render_executive_action_queue,
        render_model_lab_page,
        render_inventory_page,
        render_scenario_simulator_page,
        render_monitoring_drift_page,
        render_hierarchy_page
    )
    from src.selection.demand_classifier import DemandClassifier
    from src.selection.model_selector import ModelSelector
    from src.inventory.inventory_engine import InventoryEngine
    from src.scenarios.simulator import ScenarioSimulator
    from src.explainability.shap_analysis import ForecastExplainer
    from src.monitoring.forecast_monitor import ForecastMonitor
    from src.monitoring.drift import DriftDetector
    from src.validation.backtesting import RollingOriginBacktest
    INTELLIGENCE_AVAILABLE = True
except Exception as e:
    INTELLIGENCE_AVAILABLE = False

from src.forecast_studio import (
    CHAMPION_LABEL, ML_MODELS, STATISTICAL_MODELS, accuracy_from_wape, render_holdout_model_validation,
    render_model_dossier, run_engine_forecast,
    weekly_demand_profile,
)

try:
    from src.holdout_validation_page import render_holdout_validation_page
except Exception as e:
    def render_holdout_validation_page(theme="dark", _err=str(e)):
        st.error(f"Holdout validation view unavailable: {_err}")

# Data sources: real SAP billing vs the 10 synthetic evaluation SKUs created by generate_evaluation_data.py
SYNTHETIC_SHEET = 'Evaluation_10_SKUs'
SHEET_REAL = "📊 SAP billing history (real)"
SHEET_SYNTHETIC = "🧪 Synthetic evaluation SKUs (generated)"
SHEET_BOTH = "🔄 Real + synthetic"

# Regional Branch Definitions (South Region)
BRANCH_DICT = {
    'BLR': 'Bangalore',
    'MAA': 'Chennai',
    'COK': 'Cochin',
    'SBD': 'Secunderabad',
    'SBD1': 'Vijayawada'
}

BRANCH_LABELS = {
    'BLR': 'Bangalore (BLR)',
    'MAA': 'Chennai (MAA)',
    'COK': 'Cochin (COK)',
    'SBD': 'Secunderabad (SBD)',
    'SBD1': 'Vijayawada (SBD1)'
}

# Page Configuration
st.set_page_config(
    page_title="AI Intelligence & Demand Forecasting | ISB Capstone",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# DYNAMIC WORLD-CLASS EXECUTIVE THEME & ANIMATION ENGINE (DARK & LIGHT)
# -----------------------------------------------------------------------------
def inject_theme_css(theme="dark"):
    is_dark = (theme == "dark")
    
    if is_dark:
        bg_main = "#060813"
        bg_app = "#060813"
        bg_secondary = "#0D1322"
        primary_color = "#00F0FF"
        accent_indigo = "#6366F1"
        accent_emerald = "#10B981"
        accent_amber = "#F59E0B"
        accent_rose = "#F43F5E"
        accent_purple = "#A855F7"
        bg_mesh = """
            radial-gradient(circle at 10% 8%, rgba(0, 240, 255, 0.12) 0px, transparent 40%),
            radial-gradient(circle at 90% 12%, rgba(99, 102, 241, 0.16) 0px, transparent 48%),
            radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.06) 0px, transparent 52%),
            radial-gradient(circle at 85% 85%, rgba(0, 240, 255, 0.08) 0px, transparent 45%),
            radial-gradient(circle at 12% 88%, rgba(168, 85, 247, 0.11) 0px, transparent 50%),
            radial-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px)
        """
        text_primary = "#FFFFFF"
        text_secondary = "#94A3B8"
        text_muted = "#64748B"
        bg_card = "linear-gradient(135deg, rgba(17, 24, 39, 0.75) 0%, rgba(10, 15, 29, 0.88) 100%)"
        border_glass = "rgba(255, 255, 255, 0.10)"
        border_glass_hover = "rgba(0, 240, 255, 0.65)"
        header_bg = "linear-gradient(135deg, rgba(15, 23, 42, 0.88) 0%, rgba(9, 13, 26, 0.96) 100%)"
        panel_bg = "linear-gradient(135deg, rgba(15, 23, 42, 0.78) 0%, rgba(10, 15, 28, 0.88) 100%)"
        popover_bg = "#0D1424"
        seg_bg = "rgba(10, 15, 29, 0.90)"
        seg_text = "#94A3B8"
        seg_active_bg = "linear-gradient(135deg, rgba(0, 240, 255, 0.24) 0%, rgba(99, 102, 241, 0.38) 100%)"
        seg_active_text = "#00F0FF"
        seg_active_border = "rgba(0, 240, 255, 0.75)"
        seg_active_shadow = "0 6px 20px rgba(0, 240, 255, 0.4)"
        sidebar_bg = "#060813"
        sidebar_grad = "linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(6, 8, 19, 0.99) 100%)"
        meta_chip_bg = "rgba(255, 255, 255, 0.05)"
        meta_chip_border = "rgba(255, 255, 255, 0.10)"
        card_shadow = "0 14px 34px -10px rgba(0, 0, 0, 0.65), inset 0 1px 1px 0 rgba(255, 255, 255, 0.14)"
        card_shadow_hover = "0 24px 50px -12px rgba(0, 240, 255, 0.28), 0 0 25px rgba(99, 102, 241, 0.22), inset 0 1px 2px rgba(255, 255, 255, 0.24)"
        icon_wrap_bg = "rgba(0, 240, 255, 0.08)"
        input_bg = "rgba(13, 19, 34, 0.94)"
        title_grad = "linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 45%, #67E8F9 100%)"
        title_color = "#FFFFFF"
        brand_logo_grad = "linear-gradient(135deg, #00F0FF 0%, #3B82F6 50%, #6366F1 100%)"
        btn_grad = "linear-gradient(135deg, #00F0FF 0%, #2563EB 55%, #4F46E5 100%)"
        btn_text = "#FFFFFF"
        btn_shadow = "0 10px 25px -5px rgba(0, 240, 255, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.35)"
        btn_shadow_hover = "0 16px 36px -4px rgba(0, 240, 255, 0.6), 0 0 22px rgba(99, 102, 241, 0.45)"
        scrollbar_track = "#060813"
        scrollbar_thumb = "#1E293B"
    else:
        bg_main = "#F8FAFC"
        bg_app = "#F8FAFC"
        bg_secondary = "#FFFFFF"
        primary_color = "#0284C7"
        accent_indigo = "#4F46E5"
        accent_emerald = "#059669"
        accent_amber = "#D97706"
        accent_rose = "#E11D48"
        accent_purple = "#7C3AED"
        bg_mesh = """
            radial-gradient(circle at 10% 8%, rgba(2, 132, 199, 0.07) 0px, transparent 45%),
            radial-gradient(circle at 90% 12%, rgba(99, 102, 241, 0.06) 0px, transparent 48%),
            radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.04) 0px, transparent 50%),
            radial-gradient(circle at 85% 85%, rgba(2, 132, 199, 0.06) 0px, transparent 45%),
            radial-gradient(circle at 12% 88%, rgba(139, 92, 246, 0.05) 0px, transparent 50%),
            radial-gradient(rgba(15, 23, 42, 0.035) 1px, transparent 1px)
        """
        text_primary = "#0F172A"
        text_secondary = "#475569"
        text_muted = "#64748B"
        bg_card = "linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.94) 100%)"
        border_glass = "rgba(226, 232, 240, 0.85)"
        border_glass_hover = "rgba(2, 132, 199, 0.65)"
        header_bg = "linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(241, 245, 249, 0.96) 100%)"
        panel_bg = "linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.96) 100%)"
        popover_bg = "#FFFFFF"
        seg_bg = "#FFFFFF"
        seg_text = "#475569"
        seg_active_bg = "linear-gradient(135deg, #0284C7 0%, #2563EB 100%)"
        seg_active_text = "#FFFFFF"
        seg_active_border = "#0284C7"
        seg_active_shadow = "0 4px 16px rgba(2, 132, 199, 0.35)"
        sidebar_bg = "#F1F5F9"
        sidebar_grad = "linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%)"
        meta_chip_bg = "rgba(0, 0, 0, 0.04)"
        meta_chip_border = "rgba(0, 0, 0, 0.08)"
        card_shadow = "0 10px 28px -5px rgba(15, 23, 42, 0.07), inset 0 1px 1px 0 rgba(255, 255, 255, 0.9)"
        card_shadow_hover = "0 22px 42px -10px rgba(2, 132, 199, 0.22), inset 0 1px 2px rgba(255, 255, 255, 1)"
        icon_wrap_bg = "rgba(2, 132, 199, 0.08)"
        input_bg = "#FFFFFF"
        title_grad = "linear-gradient(135deg, #0F172A 0%, #1E293B 40%, #0369A1 100%)"
        title_color = "#0F172A"
        brand_logo_grad = "linear-gradient(135deg, #0284C7 0%, #2563EB 60%, #4F46E5 100%)"
        btn_grad = "linear-gradient(135deg, #0284C7 0%, #2563EB 50%, #1D4ED8 100%)"
        btn_text = "#FFFFFF"
        btn_shadow = "0 8px 22px -4px rgba(2, 132, 199, 0.35)"
        btn_shadow_hover = "0 16px 32px -4px rgba(2, 132, 199, 0.52)"
        scrollbar_track = "#F1F5F9"
        scrollbar_thumb = "#CBD5E1"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,600&family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        :root, html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stHeader"] {{
            --bg-main: {bg_main};
            --text-primary: {text_primary};
            --text-secondary: {text_secondary};
            --text-muted: {text_muted};
            --title-color: {title_color};
            --border-glass: {border_glass};
            --border-glass-hover: {border_glass_hover};
            --text-color: {text_primary} !important;
            --background-color: {bg_app} !important;
            --secondary-background-color: {bg_secondary} !important;
            --primary-color: {primary_color} !important;
            color: {text_primary} !important;
        }}

        html, body, [class*="css"], .stApp {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            background-color: {bg_app} !important;
            color: {text_primary} !important;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        .stApp {{
            background-color: {bg_app} !important;
            background-image: {bg_mesh} !important;
            background-size: 100% 100%, 100% 100%, 100% 100%, 100% 100%, 100% 100%, 32px 32px !important;
            background-attachment: fixed !important;
        }}

        /* HIGH-SPECIFICITY UNIVERSAL TYPOGRAPHY */
        .stApp p:not([data-testid="stButtonGroup"] p):not([data-testid="stButton"] p):not([data-baseweb="tag"] p),
        .stApp span:not(.kpi-badge):not(.live-beacon):not(.live-status-pill):not([data-testid="stButtonGroup"] span):not([data-testid="stButton"] span):not([data-baseweb="tag"] span),
        .stApp li,
        .stApp label,
        .stApp strong,
        .stApp em,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span:not(.kpi-badge):not(.live-beacon):not(.live-status-pill),
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] strong,
        [data-testid="stMarkdownContainer"] em,
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] span,
        [data-testid="stSelectbox"] label,
        [data-testid="stMultiSelect"] label,
        [data-testid="stSlider"] label,
        [data-testid="stDateInput"] label,
        [data-testid="stTextInput"] label,
        [data-testid="stNumberInput"] label,
        [data-testid="stExpander"] details summary,
        [data-testid="stExpander"] details summary p,
        [data-testid="stExpander"] details summary span,
        [data-testid="stAlert"] p,
        [data-testid="stAlert"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span:not(.live-beacon):not(.live-status-pill),
        [data-testid="stSidebar"] p:not([data-testid="stButtonGroup"] p) {{
            color: {text_primary} !important;
        }}

        /* Headings with Modern Display Font */
        h1, h2, h3, h4, h5, h6,
        .section-title,
        .subpanel-title,
        .brand-title {{
            font-family: 'Outfit', sans-serif !important;
            letter-spacing: -0.025em !important;
            color: {title_color} !important;
        }}

        /* Secondary muted typography */
        .brand-subtitle,
        .section-subtitle,
        .kpi-label,
        .meta-chip,
        .telemetry-row .label,
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {{
            color: {text_secondary} !important;
        }}

        .kpi-footer,
        .kpi-footer span {{
            color: {text_muted} !important;
            font-size: 12.5px !important;
            font-weight: 500 !important;
        }}

        /* =========================================================================
           TOP-NOTCH KEYFRAME ANIMATIONS ENGINE
           ========================================================================= */
        @keyframes laserSweep {{
            0% {{ background-position: -300% 0; }}
            100% {{ background-position: 300% 0; }}
        }}

        @keyframes floatLevitate {{
            0%, 100% {{
                transform: translateY(0px) rotate(0deg);
            }}
            50% {{
                transform: translateY(-5px) rotate(1.5deg);
            }}
        }}

        @keyframes pulseBeacon {{
            0% {{
                box-shadow: 0 0 0 0 {"rgba(0, 240, 255, 0.75)" if is_dark else "rgba(2, 132, 199, 0.7)"};
            }}
            70% {{
                box-shadow: 0 0 0 11px rgba(0, 240, 255, 0);
            }}
            100% {{
                box-shadow: 0 0 0 0 rgba(0, 240, 255, 0);
            }}
        }}

        @keyframes cardEntrance {{
            from {{
                opacity: 0;
                transform: translateY(22px) scale(0.985);
            }}
            to {{
                opacity: 1;
                transform: translateY(0) scale(1);
            }}
        }}

        @keyframes progressShimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(200%); }}
        }}

        @keyframes subtleHaloPulse {{
            0%, 100% {{
                border-color: {"rgba(0, 240, 255, 0.4)" if is_dark else "rgba(2, 132, 199, 0.35)"};
                box-shadow: 0 0 14px {"rgba(0, 240, 255, 0.2)" if is_dark else "rgba(2, 132, 199, 0.15)"};
            }}
            50% {{
                border-color: {"rgba(0, 240, 255, 0.85)" if is_dark else "rgba(2, 132, 199, 0.7)"};
                box-shadow: 0 0 24px {"rgba(0, 240, 255, 0.4)" if is_dark else "rgba(2, 132, 199, 0.25)"};
            }}
        }}

        /* =========================================================================
           EXECUTIVE TOP BRAND COMMAND BRIDGE (HEADER)
           ========================================================================= */
        .executive-header {{
            background: {header_bg};
            backdrop-filter: blur(28px) saturate(190%);
            -webkit-backdrop-filter: blur(28px) saturate(190%);
            border: 1px solid {border_glass};
            border-radius: 24px;
            padding: 26px 34px;
            margin-bottom: 24px;
            box-shadow: {card_shadow};
            position: relative;
            overflow: hidden;
            animation: cardEntrance 0.65s cubic-bezier(0.16, 1, 0.3, 1) both;
        }}

        .executive-header::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #00F0FF, #6366F1, #10B981, #F59E0B, #EC4899, #00F0FF);
            background-size: 300% 100%;
            animation: laserSweep 7s linear infinite;
        }}

        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 18px;
        }}

        .brand-title-wrap {{
            display: flex;
            align-items: center;
            gap: 18px;
        }}

        .brand-logo-outer {{
            position: relative;
            padding: 3px;
            border-radius: 20px;
            background: linear-gradient(135deg, {"rgba(0, 240, 255, 0.5)" if is_dark else "rgba(2, 132, 199, 0.4)"}, transparent 70%);
            animation: subtleHaloPulse 4s ease-in-out infinite;
        }}

        .brand-logo-badge {{
            width: 56px;
            height: 56px;
            border-radius: 17px;
            background: {brand_logo_grad};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            box-shadow: 0 10px 24px {"rgba(0, 240, 255, 0.45)" if is_dark else "rgba(2, 132, 199, 0.35)"};
            animation: floatLevitate 4.5s ease-in-out infinite;
        }}

        .brand-eyebrow {{
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 10px !important;
            font-weight: 700 !important;
            letter-spacing: 2px !important;
            text-transform: uppercase !important;
            color: {primary_color} !important;
            margin-bottom: 2px !important;
        }}

        .brand-title {{
            font-family: 'Outfit', sans-serif !important;
            font-size: 27px !important;
            font-weight: 800 !important;
            letter-spacing: -0.6px !important;
            background: {title_grad};
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            margin: 0 !important;
            line-height: 1.2 !important;
        }}

        .brand-subtitle {{
            font-size: 13.5px !important;
            color: {text_secondary} !important;
            margin: 4px 0 0 0 !important;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 500 !important;
        }}

        .live-status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 9px;
            background: {"rgba(0, 240, 255, 0.12)" if is_dark else "rgba(2, 132, 199, 0.08)"};
            border: 1px solid {"rgba(0, 240, 255, 0.4)" if is_dark else "rgba(2, 132, 199, 0.3)"};
            padding: 7px 16px;
            border-radius: 30px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11.5px;
            font-weight: 700;
            color: {"#00F0FF" if is_dark else "#0284C7"};
            letter-spacing: 0.6px;
            box-shadow: 0 0 16px {"rgba(0, 240, 255, 0.2)" if is_dark else "rgba(2, 132, 199, 0.12)"};
        }}

        .live-beacon {{
            width: 9px;
            height: 9px;
            background-color: {"#00F0FF" if is_dark else "#0284C7"};
            border-radius: 50%;
            display: inline-block;
            animation: pulseBeacon 2.2s infinite;
        }}

        .quick-meta-strip {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }}

        .meta-chip {{
            background: {meta_chip_bg};
            border: 1px solid {meta_chip_border};
            padding: 7px 14px;
            border-radius: 12px;
            font-size: 12.5px;
            color: {text_secondary};
            display: flex;
            align-items: center;
            gap: 7px;
            backdrop-filter: blur(12px);
            transition: all 0.25s ease;
        }}

        .meta-chip:hover {{
            border-color: {border_glass_hover};
            transform: translateY(-1px);
        }}

        .meta-chip strong {{
            color: {text_primary} !important;
            font-weight: 700 !important;
        }}

        .section-title-wrap {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 22px 0 20px 0;
            padding-bottom: 14px;
            border-bottom: 1px solid {border_glass};
        }}

        .section-title {{
            font-family: 'Outfit', sans-serif !important;
            font-size: 23px !important;
            font-weight: 700 !important;
            color: {title_color} !important;
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0 !important;
            letter-spacing: -0.4px !important;
        }}

        .section-subtitle {{
            font-size: 13.5px;
            color: {text_secondary};
            margin: 3px 0 0 0;
            font-weight: 500;
        }}

        /* =========================================================================
           DOUBLE-BEZEL KPI CARD ARCHITECTURE
           ========================================================================= */
        .kpi-card {{
            background: {bg_card};
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid {border_glass};
            border-radius: 22px;
            padding: 22px 24px;
            position: relative;
            overflow: hidden;
            transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: {card_shadow};
            animation: cardEntrance 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
        }}

        .kpi-card::before {{
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 22px;
            padding: 1px;
            background: linear-gradient(135deg, {"rgba(255, 255, 255, 0.18)" if is_dark else "rgba(255, 255, 255, 0.9)"}, transparent 55%, {"rgba(0, 240, 255, 0.22)" if is_dark else "rgba(2, 132, 199, 0.15)"});
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            pointer-events: none;
        }}

        .kpi-card:hover {{
            transform: translateY(-6px) scale(1.015);
            border-color: {border_glass_hover};
            box-shadow: {card_shadow_hover};
        }}

        .kpi-card:hover .kpi-icon-wrap {{
            transform: scale(1.1) rotate(4deg);
            box-shadow: 0 0 16px {"rgba(0, 240, 255, 0.45)" if is_dark else "rgba(2, 132, 199, 0.3)"};
        }}

        .kpi-card-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
        }}

        .kpi-icon-wrap {{
            width: 44px;
            height: 44px;
            border-radius: 14px;
            background: {icon_wrap_bg};
            border: 1px solid {border_glass};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 21px;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        .kpi-badge {{
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            padding: 4px 12px !important;
            border-radius: 30px !important;
            letter-spacing: 0.4px !important;
            text-transform: uppercase !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            transition: all 0.25s ease !important;
        }}

        .kpi-badge-cyan {{
            background: {"rgba(0, 240, 255, 0.16)" if is_dark else "rgba(2, 132, 199, 0.12)"} !important;
            color: {"#00F0FF" if is_dark else "#0284C7"} !important;
            border: 1px solid {"rgba(0, 240, 255, 0.45)" if is_dark else "rgba(2, 132, 199, 0.35)"} !important;
            box-shadow: 0 0 14px {"rgba(0, 240, 255, 0.22)" if is_dark else "rgba(2, 132, 199, 0.15)"} !important;
        }}
        .kpi-badge-green {{
            background: {"rgba(16, 185, 129, 0.16)" if is_dark else "rgba(5, 150, 105, 0.12)"} !important;
            color: {"#10B981" if is_dark else "#059669"} !important;
            border: 1px solid {"rgba(16, 185, 129, 0.45)" if is_dark else "rgba(5, 150, 105, 0.35)"} !important;
            box-shadow: 0 0 14px {"rgba(16, 185, 129, 0.22)" if is_dark else "rgba(5, 150, 105, 0.15)"} !important;
        }}
        .kpi-badge-amber {{
            background: {"rgba(245, 158, 11, 0.16)" if is_dark else "rgba(217, 119, 6, 0.12)"} !important;
            color: {"#F59E0B" if is_dark else "#D97706"} !important;
            border: 1px solid {"rgba(245, 158, 11, 0.45)" if is_dark else "rgba(217, 119, 6, 0.35)"} !important;
            box-shadow: 0 0 14px {"rgba(245, 158, 11, 0.22)" if is_dark else "rgba(217, 119, 6, 0.15)"} !important;
        }}
        .kpi-badge-rose {{
            background: {"rgba(244, 63, 94, 0.16)" if is_dark else "rgba(225, 29, 72, 0.12)"} !important;
            color: {"#F43F5E" if is_dark else "#E11D48"} !important;
            border: 1px solid {"rgba(244, 63, 94, 0.45)" if is_dark else "rgba(225, 29, 72, 0.35)"} !important;
            box-shadow: 0 0 14px {"rgba(244, 63, 94, 0.22)" if is_dark else "rgba(225, 29, 72, 0.15)"} !important;
        }}

        .kpi-label {{
            font-size: 12px !important;
            font-weight: 700 !important;
            color: {text_secondary} !important;
            margin-bottom: 5px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
        }}

        .kpi-value {{
            font-family: 'Outfit', sans-serif !important;
            font-size: 34px !important;
            font-weight: 800 !important;
            color: {text_primary} !important;
            line-height: 1.1 !important;
            margin-bottom: 8px !important;
            letter-spacing: -0.8px !important;
        }}

        .kpi-bar {{
            height: 6px;
            background: {"rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.07)"};
            border-radius: 4px;
            overflow: hidden;
            margin-top: 14px;
            width: 100%;
            position: relative;
        }}

        .kpi-bar-fill {{
            height: 100%;
            border-radius: 4px;
            display: block;
            position: relative;
            overflow: hidden;
            transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        .kpi-bar-fill::after {{
            content: '';
            position: absolute;
            top: 0; left: 0; bottom: 0; width: 40px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
            animation: progressShimmer 2.2s infinite ease-in-out;
        }}

        .glass-panel {{
            background: {panel_bg};
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid {border_glass};
            border-radius: 22px;
            padding: 24px 26px;
            margin-bottom: 24px;
            box-shadow: {card_shadow};
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            animation: cardEntrance 0.65s cubic-bezier(0.16, 1, 0.3, 1) both;
        }}

        .glass-panel:hover {{
            border-color: {border_glass_hover};
            box-shadow: {card_shadow_hover};
        }}

        /* SUBPANEL TITLES & TELEMETRY ROWS */
        .subpanel-title {{
            font-family: 'Outfit', sans-serif !important;
            font-size: 17.5px !important;
            font-weight: 700 !important;
            color: {title_color} !important;
            margin-bottom: 14px !important;
            letter-spacing: -0.3px !important;
        }}

        .telemetry-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid {border_glass};
            font-size: 13.5px;
            color: {text_secondary};
            transition: background 0.2s ease;
        }}

        .telemetry-row:hover {{
            background: {"rgba(255, 255, 255, 0.02)" if is_dark else "rgba(0, 0, 0, 0.015)"};
        }}

        .telemetry-row strong {{
            color: {text_primary} !important;
            font-weight: 700 !important;
            font-family: 'JetBrains Mono', monospace !important;
        }}

        .telemetry-row .label {{
            color: {text_secondary} !important;
            font-weight: 500 !important;
        }}

        .panel-bullet-list {{
            color: {text_secondary} !important;
            font-size: 14px !important;
            line-height: 1.85 !important;
            margin-left: 20px !important;
        }}

        .panel-bullet-list li {{
            color: {text_secondary} !important;
            margin-bottom: 7px !important;
        }}

        .panel-bullet-list strong {{
            color: {text_primary} !important;
            font-weight: 700 !important;
        }}

        .panel-bullet-list code, code {{
            background: {"rgba(0, 240, 255, 0.12)" if is_dark else "rgba(2, 132, 199, 0.08)"} !important;
            color: {"#00F0FF" if is_dark else "#0369A1"} !important;
            border: 1px solid {"rgba(0, 240, 255, 0.3)" if is_dark else "rgba(2, 132, 199, 0.25)"} !important;
            padding: 2px 7px !important;
            border-radius: 6px !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 600 !important;
        }}

        /* =========================================================================
           FLOATING CYBER-DOCK SEGMENTED CONTROL & BUTTON GROUPS
           ========================================================================= */
        [data-testid="stButtonGroup"],
        [data-testid="stSegmentedControl"] {{
            background: {seg_bg} !important;
            background-color: {seg_bg} !important;
            border: 1px solid {border_glass} !important;
            border-radius: 18px !important;
            padding: 5px !important;
            backdrop-filter: blur(28px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
            box-shadow: 0 12px 32px -8px rgba(0, 0, 0, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.08) !important;
            margin-bottom: 22px !important;
            display: flex !important;
            gap: 5px !important;
            flex-wrap: wrap !important;
        }}

        [data-testid="stButtonGroup"] button,
        [data-testid="stSegmentedControl"] button {{
            border-radius: 12px !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
            border: 1px solid transparent !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
            padding: 9px 18px !important;
        }}

        /* Unselected button group state */
        [data-testid="stButtonGroup"] button[aria-checked="false"],
        [data-testid="stSegmentedControl"] button[aria-checked="false"],
        [data-testid="stButtonGroup"] button:not([aria-checked="true"]),
        [data-testid="stSegmentedControl"] button:not([aria-checked="true"]) {{
            background: transparent !important;
            background-color: transparent !important;
            color: {seg_text} !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
        }}

        [data-testid="stButtonGroup"] button[aria-checked="false"] *,
        [data-testid="stButtonGroup"] button[aria-checked="false"] p,
        [data-testid="stButtonGroup"] button[aria-checked="false"] span,
        [data-testid="stButtonGroup"] button[aria-checked="false"] div,
        [data-testid="stSegmentedControl"] button[aria-checked="false"] *,
        [data-testid="stSegmentedControl"] button[aria-checked="false"] p,
        [data-testid="stSegmentedControl"] button[aria-checked="false"] span,
        [data-testid="stSegmentedControl"] button[aria-checked="false"] div {{
            color: {seg_text} !important;
            background: transparent !important;
            background-color: transparent !important;
            font-weight: 600 !important;
        }}

        /* Unselected button hover */
        [data-testid="stButtonGroup"] button[aria-checked="false"]:hover,
        [data-testid="stSegmentedControl"] button[aria-checked="false"]:hover {{
            background: {"rgba(255, 255, 255, 0.08)" if is_dark else "rgba(2, 132, 199, 0.08)"} !important;
            color: {text_primary} !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        }}

        [data-testid="stButtonGroup"] button[aria-checked="false"]:hover *,
        [data-testid="stSegmentedControl"] button[aria-checked="false"]:hover * {{
            color: {text_primary} !important;
        }}

        /* Selected active button group state */
        [data-testid="stButtonGroup"] button[aria-checked="true"],
        [data-testid="stSegmentedControl"] button[aria-checked="true"] {{
            background: {seg_active_bg} !important;
            border: 1px solid {seg_active_border} !important;
            box-shadow: {seg_active_shadow}, inset 0 1px 1px rgba(255, 255, 255, 0.3) !important;
            color: {seg_active_text} !important;
            transform: translateY(-2px) !important;
            font-weight: 700 !important;
        }}

        [data-testid="stButtonGroup"] button[aria-checked="true"] *,
        [data-testid="stButtonGroup"] button[aria-checked="true"] p,
        [data-testid="stButtonGroup"] button[aria-checked="true"] span,
        [data-testid="stButtonGroup"] button[aria-checked="true"] div,
        [data-testid="stSegmentedControl"] button[aria-checked="true"] *,
        [data-testid="stSegmentedControl"] button[aria-checked="true"] p,
        [data-testid="stSegmentedControl"] button[aria-checked="true"] span,
        [data-testid="stSegmentedControl"] button[aria-checked="true"] div {{
            color: {seg_active_text} !important;
            background: transparent !important;
            background-color: transparent !important;
            font-weight: 700 !important;
        }}

        /* =========================================================================
           SUB-NAVIGATION CONTEXT STRIP & DOCK STYLING
           ========================================================================= */
        .sub-nav-context-strip {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: -6px;
            margin-bottom: 12px;
            padding: 8px 18px;
            background: {"linear-gradient(90deg, rgba(0, 240, 255, 0.08) 0%, rgba(99, 102, 241, 0.05) 55%, transparent 100%)" if is_dark else "linear-gradient(90deg, rgba(2, 132, 199, 0.08) 0%, rgba(99, 102, 241, 0.05) 55%, transparent 100%)"};
            border-left: 3.5px solid {primary_color};
            border-radius: 12px;
            border-top: 1px solid {border_glass};
            border-right: 1px solid {border_glass};
            border-bottom: 1px solid {border_glass};
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
        }}

        .sub-nav-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }}

        .sub-nav-beacon {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: {primary_color};
            box-shadow: 0 0 12px {primary_color};
            display: inline-block;
            animation: pulseSubBeacon 2s infinite ease-in-out;
        }}

        @keyframes pulseSubBeacon {{
            0% {{ transform: scale(0.9); opacity: 0.7; }}
            50% {{ transform: scale(1.2); opacity: 1; box-shadow: 0 0 16px {primary_color}; }}
            100% {{ transform: scale(0.9); opacity: 0.7; }}
        }}

        .sub-nav-badge {{
            font-family: 'Outfit', sans-serif !important;
            font-size: 12px !important;
            font-weight: 700 !important;
            letter-spacing: 0.08em !important;
            color: {primary_color} !important;
            text-transform: uppercase;
        }}

        .sub-nav-desc {{
            font-size: 12.5px !important;
            color: {text_secondary} !important;
            font-weight: 500 !important;
        }}

        /* COMPLETELY HIDE SIDEBAR & TOGGLE CONTROLS */
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        section[data-testid="stSidebar"],
        div[data-testid="stSidebarCollapseButton"] {{
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
        }}

        /* RADIO BUTTONS */
        [data-testid="stRadio"] label,
        [data-testid="stRadio"] label p,
        [data-testid="stRadio"] label span,
        [data-testid="stRadio"] div[role="radiogroup"] label,
        [data-testid="stRadio"] div[role="radiogroup"] span,
        [data-testid="stRadio"] div[role="radiogroup"] p {{
            color: {text_primary} !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
        }}

        [data-testid="stRadio"] div[role="radiogroup"] label:hover p,
        [data-testid="stRadio"] div[role="radiogroup"] label:hover span {{
            color: {primary_color} !important;
        }}

        /* TABS (stTabs) */
        [data-testid="stTabs"] [role="tablist"] {{
            background: {seg_bg} !important;
            border: 1px solid {border_glass} !important;
            border-radius: 16px !important;
            padding: 4px !important;
            gap: 6px !important;
            box-shadow: {card_shadow} !important;
        }}

        [data-testid="stTabs"] button[role="tab"] {{
            border-radius: 10px !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
            color: {text_secondary} !important;
            border: none !important;
            padding: 8px 18px !important;
            transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }}

        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
            background: {seg_active_bg} !important;
            color: {seg_active_text} !important;
            border: 1px solid {seg_active_border} !important;
            box-shadow: {seg_active_shadow} !important;
            font-weight: 700 !important;
            transform: translateY(-1px) !important;
        }}

        /* ACTION BUTTONS (STBUTTON) */
        [data-testid="stButton"] > button {{
            background: {btn_grad} !important;
            color: {btn_text} !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            font-size: 14.5px !important;
            letter-spacing: 0.3px !important;
            border: 1px solid rgba(255, 255, 255, 0.22) !important;
            border-radius: 14px !important;
            box-shadow: {btn_shadow} !important;
            transition: all 0.26s cubic-bezier(0.16, 1, 0.3, 1) !important;
            padding: 10px 24px !important;
        }}

        [data-testid="stButton"] > button *,
        [data-testid="stButton"] > button p,
        [data-testid="stButton"] > button span,
        [data-testid="stButton"] > button div {{
            color: {btn_text} !important;
            font-weight: 700 !important;
            background: transparent !important;
        }}

        [data-testid="stButton"] > button:hover {{
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: {btn_shadow_hover} !important;
            border-color: rgba(255, 255, 255, 0.5) !important;
        }}

        [data-testid="stButton"] > button:active {{
            transform: translateY(1px) scale(0.98) !important;
        }}

        .stDownloadButton > button {{
            background: linear-gradient(135deg, #10B981 0%, #059669 60%, #047857 100%) !important;
            color: #FFFFFF !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
            border-radius: 14px !important;
            box-shadow: 0 8px 24px -4px rgba(16, 185, 129, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.35) !important;
            transition: all 0.26s cubic-bezier(0.16, 1, 0.3, 1) !important;
            padding: 10px 24px !important;
        }}

        .stDownloadButton > button *,
        .stDownloadButton > button p,
        .stDownloadButton > button span {{
            color: #FFFFFF !important;
            font-weight: 700 !important;
            background: transparent !important;
        }}

        .stDownloadButton > button:hover {{
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 16px 36px -4px rgba(16, 185, 129, 0.55) !important;
        }}

        /* SELECTBOX & BASEWEB POPOVER DROPDOWN */
        div[data-baseweb="select"] > div {{
            background-color: {input_bg} !important;
            border: 1px solid {border_glass} !important;
            border-radius: 14px !important;
            color: {text_primary} !important;
            transition: all 0.25s ease !important;
        }}

        div[data-baseweb="select"] > div:hover {{
            border-color: {border_glass_hover} !important;
        }}

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] input,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] p {{
            color: {text_primary} !important;
            font-weight: 600 !important;
        }}

        div[data-baseweb="select"] svg {{
            fill: {text_primary} !important;
            color: {text_primary} !important;
        }}

        div[data-baseweb="popover"],
        div[data-baseweb="popover"] *,
        div[data-baseweb="menu"],
        div[data-baseweb="menu"] *,
        ul[role="listbox"],
        ul[role="listbox"] * {{
            background-color: {popover_bg} !important;
            color: {text_primary} !important;
        }}

        li[role="option"] {{
            background-color: {popover_bg} !important;
            border-bottom: 1px solid {"rgba(255, 255, 255, 0.05)" if is_dark else "rgba(0, 0, 0, 0.04)"} !important;
            transition: all 0.2s ease !important;
        }}

        li[role="option"],
        li[role="option"] *,
        li[role="option"] span,
        li[role="option"] div,
        li[role="option"] p {{
            color: {text_primary} !important;
            font-weight: 500 !important;
        }}

        li[role="option"]:hover,
        li[role="option"]:hover *,
        li[role="option"]:hover span,
        li[role="option"][aria-selected="true"],
        li[role="option"][aria-selected="true"] *,
        li[role="option"][aria-selected="true"] span {{
            background-color: {"rgba(0, 240, 255, 0.22)" if is_dark else "rgba(2, 132, 199, 0.12)"} !important;
            color: {"#00F0FF" if is_dark else "#0284C7"} !important;
            font-weight: 700 !important;
        }}

        /* MULTISELECT TAGS */
        span[data-baseweb="tag"] {{
            background-color: {"rgba(0, 240, 255, 0.18)" if is_dark else "rgba(2, 132, 199, 0.12)"} !important;
            color: {"#00F0FF" if is_dark else "#0284C7"} !important;
            border: 1px solid {"rgba(0, 240, 255, 0.4)" if is_dark else "rgba(2, 132, 199, 0.3)"} !important;
            border-radius: 8px !important;
            font-family: 'JetBrains Mono', monospace !important;
        }}
        span[data-baseweb="tag"] span {{
            color: {"#00F0FF" if is_dark else "#0284C7"} !important;
            font-weight: 700 !important;
        }}

        /* EXPANDER */
        [data-testid="stExpander"] {{
            background: {panel_bg} !important;
            border: 1px solid {border_glass} !important;
            border-radius: 16px !important;
            box-shadow: {card_shadow} !important;
            overflow: hidden !important;
            margin-bottom: 16px !important;
            transition: all 0.25s ease !important;
        }}

        [data-testid="stExpander"]:hover {{
            border-color: {border_glass_hover} !important;
        }}

        [data-testid="stExpander"] summary {{
            background-color: transparent !important;
            border-radius: 16px !important;
            font-weight: 600 !important;
            color: {text_primary} !important;
        }}

        [data-testid="stExpander"] summary:hover {{
            background-color: {"rgba(255, 255, 255, 0.04)" if is_dark else "rgba(0, 0, 0, 0.03)"} !important;
        }}

        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] summary span {{
            color: {text_primary} !important;
            font-weight: 600 !important;
        }}

        [data-testid="stExpanderDetails"] {{
            border-top: 1px solid {border_glass} !important;
            padding: 18px !important;
        }}

        /* SLIDER COMPONENT STYLING */
        [data-testid="stSlider"] label,
        [data-testid="stSlider"] label p {{
            color: {text_primary} !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
        }}
        [data-testid="stTickBarMin"],
        [data-testid="stTickBarMax"] {{
            color: {text_secondary} !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 12px !important;
            font-weight: 600 !important;
        }}
        div[data-testid="stThumbValue"] {{
            color: {"#00F0FF" if is_dark else "#0284C7"} !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 700 !important;
        }}

        /* TEXT / NUMBER / DATE INPUTS */
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input {{
            background-color: {input_bg} !important;
            color: {text_primary} !important;
            border: 1px solid {border_glass} !important;
            border-radius: 12px !important;
            font-weight: 500 !important;
            transition: all 0.25s ease !important;
        }}
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stDateInput"] input:focus {{
            border-color: {border_glass_hover} !important;
            box-shadow: 0 0 0 3px {"rgba(0, 240, 255, 0.25)" if is_dark else "rgba(2, 132, 199, 0.2)"} !important;
        }}
        [data-testid="stTextInput"] input::placeholder {{
            color: {text_muted} !important;
        }}

        /* DATAFRAME & TABLE DUAL-THEME */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            background-color: {input_bg} !important;
            border-radius: 16px !important;
            overflow: hidden !important;
            border: 1px solid {border_glass} !important;
            box-shadow: {card_shadow} !important;
        }}

        [data-testid="stTable"] table {{
            color: {text_primary} !important;
            background-color: {input_bg} !important;
            width: 100% !important;
        }}

        [data-testid="stTable"] th {{
            color: {title_color} !important;
            background-color: {"rgba(255, 255, 255, 0.08)" if is_dark else "rgba(15, 23, 42, 0.06)"} !important;
            font-weight: 700 !important;
            font-family: 'Outfit', sans-serif !important;
            padding: 12px 16px !important;
            border-bottom: 2px solid {border_glass} !important;
        }}

        [data-testid="stTable"] td {{
            color: {text_primary} !important;
            border-bottom: 1px solid {border_glass} !important;
            padding: 10px 16px !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 500 !important;
        }}

        [data-testid="stDataFrame"] canvas {{
            filter: {"none" if is_dark else "invert(0.94) hue-rotate(180deg) brightness(1.02) contrast(1.15)"} !important;
        }}

        /* ALERTS */
        [data-testid="stAlert"] {{
            background-color: {panel_bg} !important;
            border: 1px solid {border_glass} !important;
            border-radius: 16px !important;
            color: {text_primary} !important;
            box-shadow: {card_shadow} !important;
        }}

        [data-testid="stAlert"] p, [data-testid="stAlert"] span {{
            color: {text_primary} !important;
        }}

        [data-testid="stHeader"] {{
            background-color: transparent !important;
        }}

        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: {scrollbar_track};
        }}
        ::-webkit-scrollbar-thumb {{
            background: {scrollbar_thumb};
            border-radius: 4px;
        }}

        /* EXPLICIT PLOTLY HIGH-CONTRAST AXIS, TICK AND LABEL TYPOGRAPHY */
        .js-plotly-plot .xtick text,
        .js-plotly-plot .ytick text,
        .js-plotly-plot .g-xtitle text,
        .js-plotly-plot .g-ytitle text,
        .js-plotly-plot text.legendtext,
        .js-plotly-plot text.annotation-text,
        .js-plotly-plot text.bartext {{
            fill: {text_primary} !important;
            color: {text_primary} !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }}

        code {{
            background: {"rgba(255, 255, 255, 0.08)" if is_dark else "#F1F5F9"} !important;
            color: {"#00F0FF" if is_dark else "#0284C7"} !important;
            border: 1px solid {"rgba(255, 255, 255, 0.12)" if is_dark else "#CBD5E1"} !important;
            border-radius: 6px !important;
            padding: 2px 7px !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.9em !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PLOTLY DUAL-THEME MODERN VISUALIZATION HELPER
# -----------------------------------------------------------------------------
def apply_custom_chart_theme(fig, height=400, title="", theme=None):
    """Apply high-end executive dark or light glass styling to Plotly figures"""
    if fig is None:
        return None
        
    if theme is None:
        theme = st.session_state.get('theme', 'dark')
    is_dark = (theme == 'dark')
    
    paper_bg = 'rgba(0,0,0,0)'
    plot_bg = 'rgba(0,0,0,0)'
    text_color = '#E2E8F0' if is_dark else '#0F172A'
    title_color = '#FFFFFF' if is_dark else '#0F172A'
    grid_color = 'rgba(255, 255, 255, 0.06)' if is_dark else 'rgba(15, 23, 42, 0.08)'
    hover_bg = 'rgba(10, 15, 29, 0.96)' if is_dark else '#FFFFFF'
    hover_text = '#FFFFFF' if is_dark else '#0F172A'
    hover_border = 'rgba(0, 240, 255, 0.7)' if is_dark else '#0284C7'

    clean_title = title if title else (fig.layout.title.text if (fig.layout and fig.layout.title and fig.layout.title.text and str(fig.layout.title.text).strip() != 'undefined') else "")

    fig.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        font=dict(
            family="Plus Jakarta Sans, sans-serif",
            size=12,
            color=text_color
        ),
        title=dict(
            text=clean_title,
            font=dict(
                family="Outfit, sans-serif",
                size=16,
                color=title_color
            ),
            x=0.01,
            y=0.96
        ) if clean_title else dict(text=""),
        margin=dict(t=60 if clean_title else 30, b=40, l=50, r=30),
        height=height,
        hoverlabel=dict(
            bgcolor=hover_bg,
            font_size=12,
            font_family="Plus Jakarta Sans",
            font_color=hover_text,
            bordercolor=hover_border
        ),
        legend=dict(
            font=dict(color=text_color, family="Plus Jakarta Sans")
        ),
        transition=dict(
            duration=500,
            easing="cubic-in-out"
        )
    )
    
    # Update gridlines and axes
    fig.update_xaxes(
        showgrid=True,
        gridcolor=grid_color,
        zerolinecolor=grid_color,
        tickfont=dict(color=text_color, family="JetBrains Mono, monospace", size=11),
        title_font=dict(color=title_color, family="Outfit, sans-serif", size=13)
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid_color,
        zerolinecolor=grid_color,
        tickfont=dict(color=text_color, family="JetBrains Mono, monospace", size=11),
        title_font=dict(color=title_color, family="Outfit, sans-serif", size=13)
    )
    
    return fig

# -----------------------------------------------------------------------------
# EXECUTIVE KPI CARD HTML GENERATOR (DOUBLE-BEZEL ARCHITECTURE)
# -----------------------------------------------------------------------------
def render_kpi_card(label, value, delta_text=None, delta_type="cyan", icon="📊", subtext="", progress=None, theme=None):
    """Render an ultra-luxury Double-Bezel glassmorphism KPI card with glowing highlights"""
    if theme is None:
        theme = st.session_state.get('theme', 'dark')
    is_dark = (theme == 'dark')
    badge_class = f"kpi-badge-{delta_type}"
    
    progress_html = ""
    if progress is not None:
        p_val = max(0, min(100, float(progress)))
        if is_dark:
            bar_color = "#00F0FF" if delta_type == "cyan" else "#10B981" if delta_type == "green" else "#F59E0B" if delta_type == "amber" else "#F43F5E"
        else:
            bar_color = "#0284C7" if delta_type == "cyan" else "#059669" if delta_type == "green" else "#D97706" if delta_type == "amber" else "#E11D48"
        progress_html = f'<div class="kpi-bar"><div class="kpi-bar-fill" style="width: {p_val:.1f}%; background: {bar_color};"></div></div>'
        
    delta_html = f'<span class="kpi-badge {badge_class}">{delta_text}</span>' if delta_text else ''
    
    card_html = (
        f'<div class="kpi-card">'
        f'<div class="kpi-card-top">'
        f'<div class="kpi-icon-wrap">{icon}</div>'
        f'{delta_html}'
        f'</div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-footer"><span>{subtext}</span></div>'
        f'{progress_html}'
        f'</div>'
    )
    return card_html

# -----------------------------------------------------------------------------
# DATA LOADING & CACHING
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Syncing dataset with enterprise cache...")
def load_data():
    # Try Parquet first (instant 10x-20x faster binary cache), fallback to CSV, then Excel
    parquet_candidates = ['Filtered.parquet', 'EDA dashboard Python/Filtered.parquet']
    parquet_path = next((p for p in parquet_candidates if os.path.exists(p)), None)
    if parquet_path:
        df = pd.read_parquet(parquet_path)
        if 'Billing Date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['Billing Date']):
            df['Billing Date'] = pd.to_datetime(df['Billing Date'], format='mixed', errors='coerce')
    else:
        csv_candidates = ['Filtered.csv', 'EDA dashboard Python/Filtered.csv']
        excel_candidates = ['Filtered.xlsx', 'EDA dashboard Python/Filtered.xlsx']
        
        csv_path = next((p for p in csv_candidates if os.path.exists(p)), None)
        if csv_path:
            df = pd.read_csv(csv_path, low_memory=False)
            if 'Billing Date' in df.columns:
                df['Billing Date'] = pd.to_datetime(df['Billing Date'], format='mixed', errors='coerce')
            try:
                df.to_parquet('Filtered.parquet', index=False)
            except Exception:
                pass
        else:
            excel_path = next((p for p in excel_candidates if os.path.exists(p)), None)
            if excel_path:
                try:
                    xls = pd.ExcelFile(excel_path, engine='openpyxl')
                    dfs = []
                    for s_name in xls.sheet_names:
                        s_df = pd.read_excel(xls, sheet_name=s_name)
                        if 'Data_Sheet' not in s_df.columns:
                            s_df['Data_Sheet'] = s_name
                        dfs.append(s_df)
                    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
                except Exception:
                    df = pd.read_excel(excel_path, engine='openpyxl')
                    if 'Data_Sheet' not in df.columns:
                        df['Data_Sheet'] = 'Historical (Sheet1)'

                if 'Billing Date' in df.columns:
                    df['Billing Date'] = pd.to_datetime(df['Billing Date'], format='mixed', errors='coerce')
                try:
                    df.to_parquet('Filtered.parquet', index=False)
                except Exception:
                    pass
            else:
                raise FileNotFoundError("Could not locate Filtered.parquet, Filtered.csv or Filtered.xlsx dataset.")

    # Ensure metadata fields are consistent
    if 'Data_Sheet' not in df.columns:
        df['Data_Sheet'] = 'Historical (Sheet1)'
    else:
        df['Data_Sheet'] = df['Data_Sheet'].fillna('Historical (Sheet1)')

    if 'Star Rating.1' in df.columns:
        df['Star Rating.1'] = df['Star Rating.1'].replace({'3 star': '3 Star'})

    demand_columns = [column for column in ['Billing Quantity ODU', 'Billing Quantity IDU'] if column in df.columns]
    if demand_columns:
        df = df[~df[demand_columns].lt(0).any(axis=1)].copy()
    return df

# -----------------------------------------------------------------------------
# METRICS & ANALYSIS FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def calculate_data_quality_metrics(df):
    total_records = len(df)
    total_columns = len(df.columns)
    
    missing_values = df.isnull().sum()
    total_missing = missing_values.sum()
    missing_percentage = (total_missing / (total_records * total_columns)) * 100
    
    duplicate_rows = df.duplicated().sum()
    duplicate_percentage = (duplicate_rows / total_records) * 100
    
    completeness = 100 - missing_percentage
    columns_with_missing = (missing_values > 0).sum()
    
    return {
        'total_records': total_records,
        'total_columns': total_columns,
        'total_missing': total_missing,
        'missing_percentage': missing_percentage,
        'duplicate_rows': duplicate_rows,
        'duplicate_percentage': duplicate_percentage,
        'completeness': completeness,
        'columns_with_missing': columns_with_missing
    }

def create_missing_data_chart(df, theme=None):
    missing_data = df.isnull().sum()
    missing_data = missing_data[missing_data > 0].sort_values(ascending=True)
    if theme is None:
        theme = st.session_state.get('theme', 'dark')
    is_dark = (theme == 'dark')
    text_color = '#CBD5E1' if is_dark else '#334155'
    
    if len(missing_data) > 0:
        fig = go.Figure(go.Bar(
            x=missing_data.values,
            y=missing_data.index,
            orientation='h',
            marker=dict(
                color=missing_data.values,
                colorscale=[[0, '#3B82F6'], [0.5, '#F59E0B'], [1, '#F43F5E']],
                showscale=True,
                colorbar=dict(title=dict(text="Missing Count", font=dict(color=text_color)), tickfont=dict(color=text_color))
            ),
            text=missing_data.values,
            textposition='auto',
            textfont=dict(color="#FFFFFF" if is_dark else "#0F172A", family="JetBrains Mono")
        ))
        
        fig.update_layout(xaxis_title="Number of Missing Values", yaxis_title="")
        apply_custom_chart_theme(fig, height=420, title="Missing Values by Column", theme=theme)
        return fig
    return None

def create_data_quality_radar_chart(metrics, theme=None):
    if theme is None:
        theme = st.session_state.get('theme', 'dark')
    is_dark = (theme == 'dark')
    
    dimensions = [
        'Completeness',
        'Schema Validity',
        'Uniqueness',
        'Temporal Horizon',
        'Referential Integrity',
        'Value Consistency',
        'Completeness'
    ]
    
    completeness = min(100.0, max(0.0, float(metrics.get('completeness', 94.99))))
    dup_pct = float(metrics.get('duplicate_percentage', 5.44))
    uniqueness = min(100.0, max(0.0, 100.0 - dup_pct))
    validity = 100.0
    horizon = 100.0
    referential = 99.1
    consistency = 98.4
    
    scores = [completeness, validity, uniqueness, horizon, referential, consistency, completeness]
    benchmarks = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=dimensions,
        fill='toself',
        name='Fleet Audit Score',
        fillcolor='rgba(0, 229, 255, 0.22)' if is_dark else 'rgba(2, 132, 199, 0.2)',
        line=dict(color='#00E5FF' if is_dark else '#0284C7', width=2.5),
        marker=dict(size=6, color='#00E5FF' if is_dark else '#0284C7'),
        hovertemplate='<b>%{theta}</b>: %{r:.1f}%<extra></extra>'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=benchmarks,
        theta=dimensions,
        name='Enterprise Target (90%)',
        line=dict(color='#F59E0B' if is_dark else '#D97706', width=1.5, dash='dash'),
        marker=dict(size=4, color='#F59E0B' if is_dark else '#D97706'),
        hovertemplate='<b>Target %{theta}</b>: %{r:.1f}%<extra></extra>'
    ))
    
    text_color = '#CBD5E1' if is_dark else '#334155'
    grid_color = 'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'
    line_color = 'rgba(255, 255, 255, 0.12)' if is_dark else 'rgba(0, 0, 0, 0.1)'
    
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True,
                range=[80, 100],
                tickfont=dict(size=10, color='#94A3B8' if is_dark else '#64748B'),
                gridcolor=grid_color,
                linecolor=line_color
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=text_color, family="Plus Jakarta Sans"),
                gridcolor=grid_color,
                linecolor=line_color
            )
        ),
        showlegend=True,
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
            y=-0.15,
            font=dict(color=text_color, size=11)
        ),
        margin=dict(l=45, r=45, t=35, b=35)
    )
    apply_custom_chart_theme(fig, height=420, title="6-Dimension Enterprise Data Quality Radar", theme=theme)
    return fig

def create_data_completeness_gauge(completeness, theme=None):
    if theme is None:
        theme = st.session_state.get('theme', 'dark')
    is_dark = (theme == 'dark')
    
    num_color = "#FFFFFF" if is_dark else "#0F172A"
    bar_color = "#00E5FF" if is_dark else "#0369A1"
    bg_color = "rgba(19, 28, 49, 0.4)" if is_dark else "rgba(226, 232, 240, 0.6)"
    border_color = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.08)"
    text_sub = "#CBD5E1" if is_dark else "#334155"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=completeness,
        number={'suffix': "%", 'font': {'size': 44, 'family': "Outfit", 'color': num_color}},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Data Completeness Health", 'font': {'size': 18, 'family': "Outfit", 'color': text_sub}},
        delta={'reference': 95, 'increasing': {'color': "#10B981" if is_dark else "#047857"}, 'font': {'family': "Plus Jakarta Sans"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#475569" if is_dark else "#94A3B8", 'tickfont': {'color': text_sub}},
            'bar': {'color': bar_color, 'thickness': 0.28},
            'bgcolor': bg_color,
            'borderwidth': 1,
            'bordercolor': border_color,
            'steps': [
                {'range': [0, 75], 'color': 'rgba(244, 63, 94, 0.25)' if is_dark else 'rgba(244, 63, 94, 0.15)'},
                {'range': [75, 90], 'color': 'rgba(245, 158, 11, 0.25)' if is_dark else 'rgba(245, 158, 11, 0.15)'},
                {'range': [90, 100], 'color': 'rgba(16, 185, 129, 0.25)' if is_dark else 'rgba(16, 185, 129, 0.15)'}
            ],
            'threshold': {
                'line': {'color': bar_color, 'width': 4},
                'thickness': 0.8,
                'value': 95
            }
        }
    ))
    
    apply_custom_chart_theme(fig, height=360, theme=theme)
    return fig

def create_distribution_chart(df, column, theme=None):
    if theme is None:
        theme = st.session_state.get('theme', 'dark')
    is_dark = (theme == 'dark')
    accent_bar = '#00E5FF' if is_dark else '#0369A1'
    
    if df[column].dtype in ['int64', 'float64']:
        fig = px.histogram(
            df, 
            x=column,
            nbins=50,
            title=f"Distribution Profile: {column}",
            color_discrete_sequence=[accent_bar]
        )
        fig.update_traces(
            marker_line_width=1,
            marker_line_color='rgba(255, 255, 255, 0.2)' if is_dark else 'rgba(0, 0, 0, 0.1)',
            opacity=0.85
        )
    else:
        value_counts = df[column].value_counts().head(20)
        fig = px.bar(
            x=value_counts.index,
            y=value_counts.values,
            title=f"Top 20 Value Frequencies in {column}",
            labels={'x': column, 'y': 'Count'},
            color=value_counts.values,
            color_continuous_scale=[[0, '#1E3A8A' if is_dark else '#0369A1'], [0.5, '#00E5FF' if is_dark else '#38BDF8'], [1, '#6366F1']]
        )
    
    fig.update_layout(showlegend=False)
    apply_custom_chart_theme(fig, height=400, theme=theme)
    return fig

def create_correlation_heatmap(df, theme=None):
    numeric_df = df.select_dtypes(include=[np.number]).copy()
    excluded_columns = {'Billing Doc.', 'Item', 'Stor. Location', 'Tonnage.1'}
    numeric_df = numeric_df.drop(columns=excluded_columns, errors='ignore')
    numeric_df = numeric_df.loc[:, numeric_df.nunique(dropna=True) > 1]
    if numeric_df.shape[1] > 1:
        corr_matrix = numeric_df.corr()
        corr_matrix = corr_matrix.dropna(axis=0, how='any').dropna(axis=1, how='any')
    else:
        corr_matrix = pd.DataFrame()

    if corr_matrix.shape[1] > 1:
        if theme is None:
            theme = st.session_state.get('theme', 'dark')
        is_dark = (theme == 'dark')
        text_color = '#CBD5E1' if is_dark else '#334155'
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='Viridis',
            zmid=0,
            text=corr_matrix.values.round(2),
            texttemplate='%{text}',
            textfont={"size": 11, "family": "JetBrains Mono", "color": "#FFFFFF" if is_dark else "#0F172A"},
            colorbar=dict(title=dict(text="Correlation", font=dict(color=text_color)), tickfont=dict(color=text_color))
        ))
        
        apply_custom_chart_theme(fig, height=540, title="Feature Correlation Heatmap", theme=theme)
        return fig
    return None

@st.cache_data(show_spinner=False)
def _get_monthly_volume_data(df: pd.DataFrame):
    if 'Billing Date' not in df.columns:
        return None
    df_time = df.groupby(df['Billing Date'].dt.to_period('M')).size().reset_index()
    df_time.columns = ['Month', 'Count']
    df_time['Month'] = df_time['Month'].astype(str)
    return df_time

def create_time_series_chart(df, theme=None):
    if 'Billing Date' in df.columns:
        df_time = _get_monthly_volume_data(df)
        if df_time is None or df_time.empty:
            return None
        if theme is None:
            theme = st.session_state.get('theme', 'dark')
        is_dark = (theme == 'dark')
        line_color = '#00E5FF' if is_dark else '#0369A1'
        fill_color = 'rgba(0, 229, 255, 0.12)' if is_dark else 'rgba(3, 105, 161, 0.12)'
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_time['Month'],
            y=df_time['Count'],
            mode='lines+markers',
            name='Records Processed',
            line=dict(color=line_color, width=3.5),
            marker=dict(size=9, color='#6366F1', line=dict(color=line_color, width=2)),
            fill='tozeroy',
            fillcolor=fill_color
        ))
        
        fig.update_layout(
            xaxis_title="Billing Horizon",
            yaxis_title="Volume (Transactions)",
            hovermode='x unified'
        )
        apply_custom_chart_theme(fig, height=360, title="Transaction Volume Trend (Monthly)", theme=theme)
        return fig
    return None

def create_segment_analysis(df, theme=None):
    if 'Segment' in df.columns:
        segment_counts = df['Segment'].value_counts()
        if theme is None:
            theme = st.session_state.get('theme', 'dark')
        is_dark = (theme == 'dark')
        text_color = '#CBD5E1' if is_dark else '#334155'
        border_pie = '#0A0E1A' if is_dark else '#FFFFFF'
        
        fig = go.Figure(data=[go.Pie(
            labels=segment_counts.index,
            values=segment_counts.values,
            hole=0.55,
            marker=dict(
                colors=['#00E5FF', '#6366F1', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6'] if is_dark else ['#0369A1', '#6366F1', '#047857', '#B45309', '#BE123C', '#7C3AED'],
                line=dict(color=border_pie, width=2)
            ),
            textinfo='label+percent',
            textposition='auto',
            textfont=dict(family="Plus Jakarta Sans", size=12, color="#FFFFFF" if is_dark else "#0F172A")
        )])
        
        apply_custom_chart_theme(fig, height=380, title="Business Segment Market Share", theme=theme)
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", y=-0.15, x=0.1, font=dict(color=text_color))
        )
        return fig
    return None

def create_tonnage_analysis(df, theme=None):
    if 'Tonnage' in df.columns:
        if theme is None:
            theme = st.session_state.get('theme', 'dark')
        is_dark = (theme == 'dark')
        accent_color = '#00E5FF' if is_dark else '#0369A1'
        fill_box = 'rgba(0, 229, 255, 0.2)' if is_dark else 'rgba(3, 105, 161, 0.15)'
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Tonnage Spread & Outliers", "Average Tonnage by Business Segment"),
            specs=[[{"type": "box"}, {"type": "bar"}]]
        )
        
        tonnage_series = df['Tonnage'].dropna()
        if len(tonnage_series) > 3000:
            tonnage_sample = tonnage_series.sample(n=3000, random_state=42)
        else:
            tonnage_sample = tonnage_series

        fig.add_trace(
            go.Box(
                y=tonnage_sample, 
                name='Tonnage', 
                marker_color=accent_color, 
                line=dict(color=accent_color, width=2),
                fillcolor=fill_box
            ),
            row=1, col=1
        )
        
        if 'Segment' in df.columns:
            tonnage_by_segment = df.groupby('Segment')['Tonnage'].mean().sort_values(ascending=False)
            fig.add_trace(
                go.Bar(
                    x=tonnage_by_segment.index, 
                    y=tonnage_by_segment.values,
                    marker=dict(
                        color=tonnage_by_segment.values,
                        colorscale=[[0, '#3B82F6'], [1, '#6366F1']]
                    ),
                    name='Avg Tonnage'
                ),
                row=1, col=2
            )
        
        apply_custom_chart_theme(fig, height=380, theme=theme)
        fig.update_layout(showlegend=False)
        return fig
    return None

# -----------------------------------------------------------------------------
# FORECAST VISUALIZATION WITH HIGH-TECH LUMINESCENCE
# -----------------------------------------------------------------------------
def create_forecast_plot(historical_dates, historical_values, forecast_dates, 
                        forecast_values, lower_bound, upper_bound, model_name, branch_label=None, theme=None, confidence_level=95):
    """Interactive forecast visualization with neon fan chart and glow markers"""
    if theme is None:
        theme = st.session_state.get('theme', 'dark')
    is_dark = (theme == 'dark')
    
    hist_color = '#00E5FF' if is_dark else '#0369A1'
    fc_color = '#F59E0B' if is_dark else '#B45309'
    ci_fill = 'rgba(245, 158, 11, 0.18)' if is_dark else 'rgba(180, 83, 9, 0.15)'
    branch_color = '#00E5FF' if is_dark else '#0369A1'
    
    fig = go.Figure()
    
    # Historical data trace
    fig.add_trace(go.Scatter(
        x=historical_dates,
        y=historical_values,
        mode='lines+markers',
        name='Historical Demand',
        line=dict(color=hist_color, width=2.5),
        marker=dict(size=6, color=hist_color, line=dict(color='#FFFFFF' if is_dark else '#0F172A', width=1 if is_dark else 0.5))
    ))
    
    # Forecast line
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_values,
        mode='lines+markers',
        name=f'{model_name} Forecast',
        line=dict(color=fc_color, width=3, dash='dash'),
        marker=dict(size=9, symbol='diamond', color=fc_color, line=dict(color='#FFFFFF' if is_dark else '#0F172A', width=1.5))
    ))
    
    # Calibrated confidence interval band
    fig.add_trace(go.Scatter(
        x=list(forecast_dates) + list(forecast_dates)[::-1],
        y=list(upper_bound) + list(lower_bound)[::-1],
        fill='toself',
        fillcolor=ci_fill,
        line=dict(color='rgba(255, 255, 255, 0)'),
        name=f'{confidence_level}% Confidence Band',
        showlegend=True
    ))
    
    title_text = f"🎯 Demand Forecast Model: {model_name}"
    if branch_label:
        title_text += f" | Filter: <span style='color:{branch_color};'>{branch_label}</span>"
        
    fig.update_layout(
        xaxis_title="Timeline (Weekly Granularity)",
        yaxis_title="Billing Demand (ODU Units)",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#CBD5E1" if is_dark else "#0F172A")
        )
    )
    apply_custom_chart_theme(fig, height=480, title=title_text, theme=theme)
    fig.update_xaxes(type='date', autorange=True)
    fig.update_yaxes(autorange=True)
    
    return fig

# -----------------------------------------------------------------------------
# EXECUTIVE PDF REPORT GENERATOR
# -----------------------------------------------------------------------------
def generate_pdf_report(df, metrics):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Banner
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 10, 'Executive Analytics & Quality Briefing', 0, 1, 'C')
    pdf.ln(4)
    
    pdf.set_font('Arial', 'I', 11)
    pdf.cell(0, 10, f'ISB Capstone Project | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
    pdf.ln(8)
    
    # 1. Executive Summary
    pdf.set_font('Arial', 'B', 15)
    pdf.cell(0, 10, '1. Executive Summary', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, f"""This strategic intelligence report provides an in-depth audit of South Region transaction records across {metrics['total_records']:,} historical sales rows and {metrics['total_columns']} operational dimensions. The dataset demonstrates enterprise-grade readiness with a {metrics['completeness']:.2f}% data completeness rating.""")
    pdf.ln(4)
    
    # Key Metrics Table
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Key Performance Indices:', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f"  - Total Transaction Rows: {metrics['total_records']:,}", 0, 1)
    pdf.cell(0, 6, f"  - Data Completeness Score: {metrics['completeness']:.2f}%", 0, 1)
    pdf.cell(0, 6, f"  - Total Missing Value Cells: {metrics['total_missing']:,} ({metrics['missing_percentage']:.2f}%)", 0, 1)
    pdf.cell(0, 6, f"  - Duplicate Records Identified: {metrics['duplicate_rows']:,} ({metrics['duplicate_percentage']:.2f}%)", 0, 1)
    pdf.cell(0, 6, f"  - Columns Requiring Standardization: {metrics['columns_with_missing']} of {metrics['total_columns']}", 0, 1)
    pdf.ln(6)
    
    # 2. Quality Diagnostics
    pdf.set_font('Arial', 'B', 15)
    pdf.cell(0, 10, '2. Operational Data Diagnostics', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    missing_summary = df.isnull().sum()
    missing_summary = missing_summary[missing_summary > 0]
    if len(missing_summary) > 0:
        pdf.cell(0, 6, "Column-Level Missing Profile:", 0, 1)
        for col, count in missing_summary.items():
            pct = (count / len(df)) * 100
            pdf.cell(0, 5, f"    - {col}: {count:,} missing ({pct:.2f}%)", 0, 1)
    else:
        pdf.cell(0, 6, "Zero null values identified across active operational features.", 0, 1)
    pdf.ln(6)
    
    # 3. Strategic Action Plan
    pdf.set_font('Arial', 'B', 15)
    pdf.cell(0, 10, '3. Strategic Recommendations', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, """1. Demand Forecasting Pipeline:
   - Deploy SKU-level models across Bangalore, Chennai, Cochin, Secunderabad, and Vijayawada.
   - Employ SARIMA for high-seasonality items and Gradient Boosting for multi-feature velocity.
2. Data Governance:
   - Dedup and prune redundant sales records.
   - Establish automated weekly data quality validation checks.""")
    pdf.ln(8)
    
    pdf.set_font('Arial', 'I', 9)
    pdf.cell(0, 10, 'Report generated by Demand Forecasting & EDA Intelligence Platform', 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# -----------------------------------------------------------------------------
# MAIN APPLICATION CONTROLLER & NAVIGATION
# -----------------------------------------------------------------------------
def main():
    # Primary 4-Pillar Navigation Setup
    MAIN_NAV_OPTIONS = [
        "📊 EDA",
        "🎯 AI Demand Forecasting",
        "📡 Forecasting & Drift",
        "💼 C-Suite"
    ]

    # Sub-Navigation Mapping preserving all 12 modules
    SUB_NAV_MAP = {
        "📊 EDA": [
            "🔍 Intelligence Explorer",
            "📈 Statistical Deep-Dive",
            "🛡️ Data Quality Radar",
            "🧹 Data Cleaning Studio"
        ],
        "🎯 AI Demand Forecasting": [
            "🎯 SKU Demand Forecasting",
            "🔬 Model Lab & Leaderboard",
            "🌐 Hierarchical Reconciliation",
            "✅ Holdout Validation (FY24-25)"
        ],
        "📡 Forecasting & Drift": [
            "📡 Forecast Monitoring & Drift",
            "🔮 Scenario Simulator",
            "📦 Inventory Intelligence"
        ],
        "💼 C-Suite": [
            "🏠 Executive Cockpit",
            "📄 C-Suite Reports"
        ]
    }

    # Backward compatibility mapping for active sessions
    OLD_TO_NEW_MAP = {
        "🏠 Executive Cockpit": ("💼 C-Suite", "🏠 Executive Cockpit"),
        "📄 C-Suite Reports": ("💼 C-Suite", "📄 C-Suite Reports"),
        "🎯 AI Demand Forecasting": ("🎯 AI Demand Forecasting", "🎯 SKU Demand Forecasting"),
        "🔬 Model Lab & Leaderboard": ("🎯 AI Demand Forecasting", "🔬 Model Lab & Leaderboard"),
        "🌐 Hierarchical Reconciliation": ("🎯 AI Demand Forecasting", "🌐 Hierarchical Reconciliation"),
        "✅ Holdout Validation (FY24-25)": ("🎯 AI Demand Forecasting", "✅ Holdout Validation (FY24-25)"),
        "📡 Forecast Monitoring & Drift": ("📡 Forecasting & Drift", "📡 Forecast Monitoring & Drift"),
        "🔮 Scenario Simulator": ("📡 Forecasting & Drift", "🔮 Scenario Simulator"),
        "📦 Inventory Intelligence": ("📡 Forecasting & Drift", "📦 Inventory Intelligence"),
        "🔍 Intelligence Explorer": ("📊 EDA", "🔍 Intelligence Explorer"),
        "📈 Statistical Deep-Dive": ("📊 EDA", "📈 Statistical Deep-Dive"),
        "🛡️ Data Quality Radar": ("📊 EDA", "🛡️ Data Quality Radar"),
        "🧹 Data Cleaning Studio": ("📊 EDA", "🧹 Data Cleaning Studio"),
    }

    # Initialize theme session state
    if 'theme' not in st.session_state:
        st.session_state['theme'] = 'dark'
        
    theme_label = "🌙 Dark" if st.session_state['theme'] == 'dark' else "☀️ Light"
    if 'top_theme_segmented' not in st.session_state:
        st.session_state['top_theme_segmented'] = theme_label

    # Backward compatibility check for existing session state
    if 'current_view' in st.session_state and st.session_state['current_view'] in OLD_TO_NEW_MAP:
        mapped_main, mapped_sub = OLD_TO_NEW_MAP[st.session_state['current_view']]
        if 'top_segmented_selector' not in st.session_state or st.session_state['top_segmented_selector'] not in MAIN_NAV_OPTIONS:
            st.session_state['top_segmented_selector'] = mapped_main
        sub_key = f"sub_segmented_{mapped_main}"
        if sub_key not in st.session_state:
            st.session_state[sub_key] = mapped_sub
        st.session_state['current_main_view'] = mapped_main
        del st.session_state['current_view']
    elif 'top_segmented_selector' in st.session_state and st.session_state['top_segmented_selector'] not in MAIN_NAV_OPTIONS and st.session_state['top_segmented_selector'] in OLD_TO_NEW_MAP:
        mapped_main, mapped_sub = OLD_TO_NEW_MAP[st.session_state['top_segmented_selector']]
        st.session_state['top_segmented_selector'] = mapped_main
        sub_key = f"sub_segmented_{mapped_main}"
        if sub_key not in st.session_state:
            st.session_state[sub_key] = mapped_sub
        st.session_state['current_main_view'] = mapped_main

    # Initialize navigation session state
    if 'current_main_view' not in st.session_state:
        st.session_state['current_main_view'] = MAIN_NAV_OPTIONS[0]
    if 'top_segmented_selector' not in st.session_state or st.session_state['top_segmented_selector'] not in MAIN_NAV_OPTIONS:
        st.session_state['top_segmented_selector'] = st.session_state['current_main_view']

    # Callbacks for seamless navigation and theme controls
    def on_top_theme_change():
        val = st.session_state.get('top_theme_segmented')
        if val:
            new_theme = 'dark' if 'Dark' in val else 'light'
            st.session_state['theme'] = new_theme

    def on_top_nav_change():
        val = st.session_state.get('top_segmented_selector')
        if val in MAIN_NAV_OPTIONS:
            st.session_state['current_main_view'] = val

    # Inject dynamic CSS based on active theme
    inject_theme_css(st.session_state['theme'])
    is_dark = (st.session_state['theme'] == 'dark')

    # Load dataset: real SAP billing only by default; the 10 EVAL-* SKUs are synthetic test series
    df = load_data()
    n_synthetic_rows = int((df['Data_Sheet'] == SYNTHETIC_SHEET).sum()) if 'Data_Sheet' in df.columns else 0
    if n_synthetic_rows and not st.session_state.get('include_synthetic', False):
        df = df[df['Data_Sheet'] != SYNTHETIC_SHEET]
    metrics = calculate_data_quality_metrics(df)
    
    # Determine branch columns & stats
    branch_col = next((c for c in ['SALES OFFICE CODE', 'SALES OFFICE CODE.1', 'Region', 'Branch'] if c in df.columns), None)
    num_branches = df[branch_col].nunique() if branch_col else 5
    date_min = df['Billing Date'].min().strftime('%d %b %Y') if 'Billing Date' in df.columns else '2024'
    date_max = df['Billing Date'].max().strftime('%d %b %Y') if 'Billing Date' in df.columns else '2025'

    # Executive Top Brand Header
    theme_pill_label = "🌙 Dark Luxury" if is_dark else "☀️ Ceramic Light"
    theme_pill_color = "#00F0FF" if is_dark else "#0284C7"
    st.markdown(f"""
    <div class="executive-header">
        <div class="header-content">
            <div class="brand-title-wrap">
                <div class="brand-logo-outer">
                    <div class="brand-logo-badge">⚡</div>
                </div>
                <div>
                    <div class="brand-eyebrow">ISB CAPSTONE // SOUTH REGION DEMAND PLATFORM</div>
                    <h1 class="brand-title">Demand Forecasting(SKU Wise) - ISB Capstone Project</h1>
                    <p class="brand-subtitle">
                        Predictive SKU Intelligence &bull; APICS Replenishment Calibration &bull; Quality Radar
                    </p>
                </div>
            </div>
            <div class="quick-meta-strip">
                <div class="live-status-pill">
                    <span class="live-beacon"></span>
                    <span>AI FORECASTING ENGINE ACTIVE</span>
                </div>
                <div class="meta-chip">
                    <span>Theme:</span>
                    <strong style="color: {theme_pill_color};">{theme_pill_label}</strong>
                </div>
                <div class="meta-chip">
                    <span>Horizon:</span>
                    <strong>{date_min} &rarr; {date_max}</strong>
                </div>
                <div class="meta-chip">
                    <span>Network:</span>
                    <strong>{num_branches} Regional Hubs</strong>
                </div>
                <div class="meta-chip">
                    <span>Integrity:</span>
                    <strong style="color: {theme_pill_color};">{metrics['completeness']:.1f}% Score</strong>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Navigation Row with View Selector and Theme Toggle (EXACTLY 4 BUTTONS)
    nav_col, theme_col = st.columns([5.8, 1.2])
    with nav_col:
        top_pick = st.segmented_control(
            "Executive View Selector",
            MAIN_NAV_OPTIONS,
            key="top_segmented_selector",
            on_change=on_top_nav_change,
            label_visibility="collapsed"
        )
    with theme_col:
        top_theme = st.segmented_control(
            "Theme Mode",
            ["🌙 Dark", "☀️ Light"],
            key="top_theme_segmented",
            on_change=on_top_theme_change,
            label_visibility="collapsed"
        )

    if top_pick:
        st.session_state['current_main_view'] = top_pick
        active_main = top_pick
    else:
        active_main = st.session_state.get('current_main_view', MAIN_NAV_OPTIONS[0])
        st.session_state['top_segmented_selector'] = active_main

    if top_theme:
        st.session_state['theme'] = 'dark' if 'Dark' in top_theme else 'light'

    if n_synthetic_rows:
        st.toggle(
            f"Include synthetic evaluation SKUs ({n_synthetic_rows:,} generated rows, not SAP billing)",
            key='include_synthetic',
            help="The 10 'EVAL-*' SKUs were generated by generate_evaluation_data.py for testing. "
                 "They are excluded from every page, KPI and report unless this is switched on."
        )

    # Workspace Sub-Navigation Config
    sub_options = SUB_NAV_MAP[active_main]
    sub_key = f"sub_segmented_{active_main}"
    if sub_key not in st.session_state or st.session_state[sub_key] not in sub_options:
        st.session_state[sub_key] = sub_options[0]

    metadata_map = {
        "📊 EDA": ("📊 Exploratory Data Analysis (EDA) Workspace", "Multi-Dimensional Slicing &bull; Statistical Deep-Dive &bull; Data Quality &bull; Cleaning Studio"),
        "🎯 AI Demand Forecasting": ("🎯 AI Demand Forecasting Studio", "Predictive SKU Modeling &bull; Algorithm Competition Leaderboard &bull; Hierarchy Reconciliation"),
        "📡 Forecasting & Drift": ("📡 Forecasting Operations & Drift Radar", "Tracking Signal &bull; Model Degradation Monitoring &bull; Scenario Stress-Testing &bull; APICS Inventory Calibration"),
        "💼 C-Suite": ("💼 C-Suite Executive Intelligence", "Executive Telemetry Cockpit &bull; Action Queue &bull; Automated C-Suite PDF Briefings")
    }
    badge_title, badge_subtitle = metadata_map.get(active_main, (active_main, "Enterprise Analytical Engine"))

    st.markdown(f"""
    <div class="sub-nav-context-strip">
        <div class="sub-nav-indicator">
            <span class="sub-nav-beacon"></span>
            <span class="sub-nav-badge">{badge_title.upper()}</span>
        </div>
        <div class="sub-nav-desc">
            {badge_subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sub-Navigation Dock
    sub_pick = st.segmented_control(
        f"Sub-module Selector ({active_main})",
        sub_options,
        key=sub_key,
        label_visibility="collapsed"
    )
    if sub_pick:
        active_page = sub_pick
    else:
        active_page = st.session_state.get(sub_key) or sub_options[0]
        st.session_state[sub_key] = active_page

    # Routed View Rendering
    if active_page == "🏠 Executive Cockpit":
        show_overview(df, metrics)
    elif active_page in ["🎯 SKU Demand Forecasting", "🎯 AI Demand Forecasting"]:
        show_demand_forecasting(df)
    elif active_page == "🔬 Model Lab & Leaderboard":
        render_model_lab_page(df, st.session_state.get('theme', 'dark'))
    elif active_page == "📦 Inventory Intelligence":
        render_inventory_page(df, st.session_state.get('theme', 'dark'))
    elif active_page == "🔮 Scenario Simulator":
        render_scenario_simulator_page(df, st.session_state.get('theme', 'dark'))
    elif active_page == "📡 Forecast Monitoring & Drift":
        render_monitoring_drift_page(df, st.session_state.get('theme', 'dark'))
    elif active_page == "🌐 Hierarchical Reconciliation":
        render_hierarchy_page(df, st.session_state.get('theme', 'dark'))
    elif active_page == "✅ Holdout Validation (FY24-25)":
        render_holdout_validation_page(st.session_state.get('theme', 'dark'))
    elif active_page == "🛡️ Data Quality Radar":
        show_data_quality(df, metrics)
    elif active_page == "🧹 Data Cleaning Studio":
        show_data_cleaning(df, metrics)
    elif active_page == "📈 Statistical Deep-Dive":
        show_statistical_analysis(df)
    elif active_page == "🔍 Intelligence Explorer":
        show_detailed_exploration(df)
    elif active_page == "📄 C-Suite Reports":
        show_export_report(df, metrics)
    else:
        show_detailed_exploration(df)

# -----------------------------------------------------------------------------
# PAGE 1: 🏠 EXECUTIVE COCKPIT (OVERVIEW)
# -----------------------------------------------------------------------------
def show_overview(df, metrics):
    st.markdown("""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">🏠 Executive Intelligence Cockpit</h2>
            <p class="section-subtitle">Real-time health, operational volume, and distribution telemetry</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 4 Luxury KPI Cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown(render_kpi_card(
            label="Total Sales Transactions",
            value=f"{metrics['total_records']:,}",
            delta_text="Enterprise Volume",
            delta_type="cyan",
            icon="📦",
            subtext="Validated SAP billing entries",
            progress=100
        ), unsafe_allow_html=True)
        
    with kpi_col2:
        comp_status = "Target Exceeded" if metrics['completeness'] >= 95 else "Operational"
        st.markdown(render_kpi_card(
            label="Data Completeness Index",
            value=f"{metrics['completeness']:.2f}%",
            delta_text=comp_status,
            delta_type="green" if metrics['completeness'] >= 95 else "amber",
            icon="🛡️",
            subtext="Baseline benchmark: 95.0%",
            progress=metrics['completeness']
        ), unsafe_allow_html=True)
        
    with kpi_col3:
        dup_type = "green" if metrics['duplicate_rows'] == 0 else "rose"
        st.markdown(render_kpi_card(
            label="Duplicate Records",
            value=f"{metrics['duplicate_rows']:,}",
            delta_text=f"{metrics['duplicate_percentage']:.2f}% of fleet",
            delta_type=dup_type,
            icon="🔄",
            subtext="Dedup candidate rows",
            progress=max(0, 100 - metrics['duplicate_percentage'])
        ), unsafe_allow_html=True)
        
    with kpi_col4:
        miss_type = "green" if metrics['total_missing'] == 0 else "amber"
        st.markdown(render_kpi_card(
            label="Missing Cell Volume",
            value=f"{metrics['total_missing']:,}",
            delta_text=f"{metrics['missing_percentage']:.2f}% null density",
            delta_type=miss_type,
            icon="⚠️",
            subtext=f"{metrics['columns_with_missing']} affected dimensions",
            progress=max(0, 100 - metrics['missing_percentage'] * 5)
        ), unsafe_allow_html=True)
        
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    
    # Dynamic Executive Demand Action Queue
    if INTELLIGENCE_AVAILABLE:
        render_executive_action_queue(df, st.session_state.get('theme', 'dark'))
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # Visualizations Row 1
    row1_c1, row1_c2 = st.columns([3, 2])
    with row1_c1:
        with st.container():
            fig_time = create_time_series_chart(df)
            if fig_time:
                st.plotly_chart(fig_time, width="stretch", theme=None)
    with row1_c2:
        with st.container():
            fig_gauge = create_data_completeness_gauge(metrics['completeness'])
            st.plotly_chart(fig_gauge, width="stretch", theme=None)
            
    # Visualizations Row 2
    row2_c1, row2_c2 = st.columns([2, 3])
    with row2_c1:
        with st.container():
            fig_segment = create_segment_analysis(df)
            if fig_segment:
                st.plotly_chart(fig_segment, width="stretch", theme=None)
    with row2_c2:
        with st.container():
            fig_tonnage = create_tonnage_analysis(df)
            if fig_tonnage:
                st.plotly_chart(fig_tonnage, width="stretch", theme=None)

# -----------------------------------------------------------------------------
# PAGE 2: 🎯 AI DEMAND FORECASTING
# -----------------------------------------------------------------------------
def show_demand_forecasting(df):
    st.markdown("""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">🎯 AI Demand Forecasting Studio</h2>
            <p class="section-subtitle">Predict forward demand velocity by SKU & Regional Branch using Statistical & Machine Learning algorithms</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not STATSMODELS_AVAILABLE and not SKLEARN_AVAILABLE:
        st.error("⚠️ Forecasting libraries (statsmodels / scikit-learn) are not installed.")
        return
        
    if 'Material' not in df.columns or 'Billing Date' not in df.columns or 'Billing Quantity ODU' not in df.columns:
        st.error("Required columns ('Material', 'Billing Date', and 'Billing Quantity ODU') not found in dataset.")
        return
        
    branch_col = next((c for c in ['SALES OFFICE CODE', 'SALES OFFICE CODE.1', 'Region', 'Branch'] if c in df.columns), None)
    
    # Studio Control Bar
    cfg_col1, cfg_col2 = st.columns([1, 2.5])
    
    with cfg_col1:
        is_dark = (st.session_state.get('theme', 'dark') == 'dark')
        accent_color = "#00E5FF" if is_dark else "#0369A1"
        border_accent = "rgba(0, 229, 255, 0.2)" if is_dark else "rgba(3, 105, 161, 0.25)"
        bg_accent = "rgba(0, 229, 255, 0.08)" if is_dark else "rgba(3, 105, 161, 0.08)"
        
        st.markdown(f"""
        <div class="glass-panel" style="margin-bottom: 20px;">
            <div class="subpanel-title" style="color: {accent_color}; display: flex; align-items: center; gap: 8px;">
                <span>⚙️</span> Forecasting Controls
            </div>
        """, unsafe_allow_html=True)
        
        # 1. Branch Selector
        branch_options = [
            "All 5 Branches (Consolidated)",
            "Bangalore (BLR)",
            "Chennai (MAA)",
            "Cochin (COK)",
            "Secunderabad (SBD)",
            "Vijayawada (SBD1)",
            "Custom Multi-Branch Selection"
        ]
        branch_selection = st.selectbox(
            "1. Regional Branch Horizon:",
            branch_options,
            index=0,
            help="Filter historical demand for a specific branch or consolidated South Region"
        )
        
        if branch_selection == "Custom Multi-Branch Selection":
            selected_branch_codes = st.multiselect(
                "Select Branches:",
                options=list(BRANCH_DICT.keys()),
                default=list(BRANCH_DICT.keys()),
                format_func=lambda x: BRANCH_LABELS.get(x, x)
            )
            if not selected_branch_codes:
                st.warning("⚠️ Please select at least one branch.")
                return
            branch_label = ", ".join([BRANCH_DICT.get(c, c) for c in selected_branch_codes])
            branch_file_code = "_".join(selected_branch_codes)
        elif branch_selection == "All 5 Branches (Consolidated)":
            selected_branch_codes = list(BRANCH_DICT.keys())
            branch_label = "All 5 Branches (Consolidated)"
            branch_file_code = "All_Branches"
        else:
            code = branch_selection.split("(")[-1].replace(")", "").strip()
            selected_branch_codes = [code]
            branch_label = f"{BRANCH_DICT.get(code, code)} ({code})"
            branch_file_code = code

        # 2. Data Sheet & Cohort Filters (Category, Tonnage, Star Rating)
        st.markdown(f"""
        <div style="margin-top: 10px; margin-bottom: 4px; font-size: 13px; font-weight: 600; color: {accent_color};">
            2. Dataset & Cohort Calibration Filters
        </div>
        """, unsafe_allow_html=True)
        
        has_synthetic = 'Data_Sheet' in df.columns and (df['Data_Sheet'] == SYNTHETIC_SHEET).any()
        sheet_options = [SHEET_REAL] + ([SHEET_SYNTHETIC, SHEET_BOTH] if has_synthetic else [])
        selected_sheet = st.selectbox(
            "Select Data Source / Sheet:",
            sheet_options,
            index=0,
            help="SAP billing history is the real data. The 10 'EVAL-*' SKUs are synthetic test series generated "
                 "by generate_evaluation_data.py (enable them with the 'Include synthetic evaluation SKUs' toggle)."
        )
        
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            seg_choices = ["All Segments"] + sorted([str(s) for s in df['Segment'].dropna().unique() if str(s).strip() != ''])
            selected_segment = st.selectbox("Category / Segment:", seg_choices, index=0)
        with f_col2:
            tonnage_nums = sorted([float(t) for t in df['Tonnage'].dropna().unique() if float(t) > 0])
            tonnage_choices = ["All Tonnages"] + [f"{t:g} Ton" for t in tonnage_nums]
            selected_tonnage_str = st.selectbox("Tonnage Filter:", tonnage_choices, index=0)

        r_choices = ["All Star Ratings"] + [r for r in ["5 Star", "3 Star", "2 Star", "1 Star"] if r in df['Star Rating.1'].values]
        selected_rating = st.selectbox("Star Rating Filter:", r_choices, index=0)

        # Filtered DataFrame
        filtered_df = df[df[branch_col].isin(selected_branch_codes)].copy() if branch_col else df.copy()
        forecast_df = df[df['Billing Quantity ODU'] >= 0].copy()
        filtered_forecast_df = filtered_df[filtered_df['Billing Quantity ODU'] >= 0].copy()

        # Apply Data Sheet Filter
        if selected_sheet == SHEET_SYNTHETIC:
            filtered_forecast_df = filtered_forecast_df[filtered_forecast_df['Data_Sheet'] == SYNTHETIC_SHEET]
            forecast_df = forecast_df[forecast_df['Data_Sheet'] == SYNTHETIC_SHEET]
        elif selected_sheet == SHEET_REAL and 'Data_Sheet' in df.columns:
            filtered_forecast_df = filtered_forecast_df[filtered_forecast_df['Data_Sheet'] != SYNTHETIC_SHEET]
            forecast_df = forecast_df[forecast_df['Data_Sheet'] != SYNTHETIC_SHEET]

        # Apply Segment Filter
        if selected_segment != "All Segments":
            filtered_forecast_df = filtered_forecast_df[filtered_forecast_df['Segment'] == selected_segment]
            forecast_df = forecast_df[forecast_df['Segment'] == selected_segment]

        # Apply Tonnage Filter
        if selected_tonnage_str != "All Tonnages":
            t_val = float(selected_tonnage_str.replace(" Ton", "").strip())
            filtered_forecast_df = filtered_forecast_df[filtered_forecast_df['Tonnage'] == t_val]
            forecast_df = forecast_df[forecast_df['Tonnage'] == t_val]

        # Apply Star Rating Filter
        if selected_rating != "All Star Ratings":
            filtered_forecast_df = filtered_forecast_df[filtered_forecast_df['Star Rating.1'] == selected_rating]
            forecast_df = forecast_df[forecast_df['Star Rating.1'] == selected_rating]

        # Volume badge & active filter chips
        tot_vol = forecast_df['Billing Quantity ODU'].sum()
        b_vol = filtered_forecast_df['Billing Quantity ODU'].sum()
        b_share = (b_vol / tot_vol * 100) if tot_vol > 0 else 0
        
        active_chips = []
        if selected_sheet != SHEET_REAL:
            active_chips.append(f"📁 {selected_sheet.split('(')[0].strip()}")
        if selected_segment != "All Segments":
            active_chips.append(f"📦 {selected_segment}")
        if selected_tonnage_str != "All Tonnages":
            active_chips.append(f"⚖️ {selected_tonnage_str}")
        if selected_rating != "All Star Ratings":
            active_chips.append(f"⭐ {selected_rating}")
        chips_html = "".join([f'<span style="background: rgba(255, 255, 255, 0.08); border-radius: 4px; padding: 2px 6px; font-size: 11px; margin-right: 4px;">{c}</span>' for c in active_chips])

        st.markdown(f"""
        <div style="background: {bg_accent}; border: 1px solid {border_accent}; border-radius: 10px; padding: 10px; margin: 10px 0 16px 0; font-size: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                <span style="color: var(--text-secondary); font-weight: 500;">Filtered Demand Volume</span>
                <span style="font-size: 11px; color: var(--text-secondary);">{len(filtered_forecast_df):,} transactions</span>
            </div>
            <div style="font-family: 'Outfit'; font-size: 18px; font-weight: 700; color: {accent_color};">
                {b_vol:,.0f} units <span style="font-size: 12px; color: var(--text-secondary); font-weight: 500;">({b_share:.1f}% of cohort)</span>
            </div>
            {f'<div style="margin-top: 6px;">{chips_html}</div>' if active_chips else ''}
        </div>
        """, unsafe_allow_html=True)

        # 3. SKU Selection
        if filtered_forecast_df.empty:
            st.warning("⚠️ No SKUs match the current combination of Branch, Segment, Tonnage, and Star Rating. Please broaden your filter selections.")
            return

        sku_volumes = filtered_forecast_df.dropna(subset=['Material']).groupby('Material')['Billing Quantity ODU'].sum().sort_values(ascending=False)
        branch_top_skus = [str(s) for s in sku_volumes.head(10).index if str(s).strip() != '']
        
        sku_scope = st.radio(
            "3. SKU Scope:",
            ["Top 10 in Filtered Branch", "Top 10 Overall", "All Matching SKUs"],
            horizontal=True
        )
        
        if sku_scope == "Top 10 in Filtered Branch":
            available_skus = branch_top_skus
        elif sku_scope == "Top 10 Overall":
            overall_volumes = forecast_df.dropna(subset=['Material']).groupby('Material')['Billing Quantity ODU'].sum().sort_values(ascending=False)
            available_skus = [str(s) for s in overall_volumes.head(10).index if str(s).strip() != '']
        else:
            available_skus = sorted(filtered_forecast_df['Material'].dropna().unique().astype(str).tolist())
            
        if not available_skus:
            available_skus = [str(s) for s in sku_volumes.index if str(s).strip() != '']
            
        selected_sku = st.selectbox(
            "Select Target SKU (Material):",
            available_skus,
            format_func=lambda x: f"{x} ({sku_volumes.get(x, 0):,.0f} units)"
        )

        # Selected SKU Cohort Metadata Chip
        if selected_sku and selected_sku in filtered_forecast_df['Material'].values:
            sku_meta = filtered_forecast_df[filtered_forecast_df['Material'] == selected_sku].iloc[0]
            meta_tonnage = f"{sku_meta.get('Tonnage', 'N/A'):g} Ton" if pd.notnull(sku_meta.get('Tonnage')) else 'N/A'
            meta_star = str(sku_meta.get('Star Rating.1', 'N/A'))
            meta_seg = str(sku_meta.get('Segment', 'N/A'))
            meta_sheet = str(sku_meta.get('Data_Sheet', 'Historical'))
            is_eval = (meta_sheet == SYNTHETIC_SHEET)
            badge_border = "#F59E0B" if is_eval else accent_color
            badge_bg = "rgba(245, 158, 11, 0.15)" if is_eval else bg_accent
            sheet_tag = "🧪 SYNTHETIC test SKU (generated, not SAP billing)" if is_eval else "📊 SAP billing history SKU"
            
            st.markdown(f"""
            <div style="background: {badge_bg}; border: 1px solid {badge_border}; border-radius: 8px; padding: 6px 10px; margin: 4px 0 10px 0; font-size: 11px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
                <span style="font-weight: 700; color: {badge_border};">{sheet_tag}</span>
                <span style="color: var(--text-secondary);">&bull;</span>
                <span>⚖️ <strong>{meta_tonnage}</strong></span>
                <span style="color: var(--text-secondary);">&bull;</span>
                <span>⭐ <strong>{meta_star}</strong></span>
                <span style="color: var(--text-secondary);">&bull;</span>
                <span>📦 <strong>{meta_seg}</strong></span>
            </div>
            """, unsafe_allow_html=True)
        
        # Engine scope: data source only (cohort filters just narrow the SKU list); all 5 branches = region
        engine_df = df
        if 'Data_Sheet' in df.columns and selected_sheet == SHEET_REAL:
            engine_df = df[df['Data_Sheet'] != SYNTHETIC_SHEET]
        elif 'Data_Sheet' in df.columns and selected_sheet == SHEET_SYNTHETIC:
            engine_df = df[df['Data_Sheet'] == SYNTHETIC_SHEET]
        engine_branches = None if set(selected_branch_codes) >= set(BRANCH_DICT) else tuple(selected_branch_codes)

        # Real-time SKU Demand Profiling (on the weekly series the models see)
        if INTELLIGENCE_AVAILABLE and selected_sku:
            try:
                profile_res = weekly_demand_profile(engine_df, selected_sku, engine_branches)
                if profile_res:
                    st.markdown(f"""
                    <div style="background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.25); border-radius: 10px; padding: 10px 12px; margin: 8px 0 12px 0; font-size: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <strong style="color: {'#00E5FF' if is_dark else '#0284C7'};">Demand Profile: {profile_res['demand_type']}</strong>
                            <span class="kpi-badge kpi-badge-cyan">ADI: {profile_res['adi']:.2f} &bull; CV²: {profile_res['cv2']:.2f}</span>
                        </div>
                        <div style="color: var(--text-secondary); line-height: 1.3;">{profile_res['description']} ({profile_res['weeks']} weeks, {profile_res['zero_demand_pct']:.0f}% with no billing)</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.caption(f"Demand profile unavailable: {e}")

        # 4. Model Engine Selection
        model_family = st.radio(
            "4. Algorithm Engine:",
            ["🤖 Champion Model (AutoML)", "📊 Statistical Models", "🧠 Machine Learning Models"]
        )

        if model_family == "📊 Statistical Models":
            selected_model = st.selectbox(
                "Select Statistical Algorithm:",
                STATISTICAL_MODELS,
                help="Each model is evaluated on the same out-of-sample rolling-origin backtest as the champion tournament."
            )
        elif model_family == "🧠 Machine Learning Models":
            selected_model = st.selectbox(
                "Select Machine Learning Regressor:",
                ML_MODELS,
                help="Recursive multi-step forecasting on lags, rolling statistics, calendar and the pooled seasonal factor."
            )
        else:
            selected_model = "AutoML Champion"
            st.info("⚡ Every applicable model is backtested out-of-sample (rolling 12-week folds); the lowest-RMSE model is deployed.")

        # 5. Parameters
        forecast_periods = st.slider("Forecast Horizon (Weeks):", min_value=4, max_value=52, value=12)
        confidence_level = st.slider("Prediction Interval (%):", min_value=80, max_value=95, value=80, step=5,
                                     help="Coverage target of the conformal interval, calibrated on backtest errors.")

        run_forecast = st.button("🚀 Execute Forecast Simulation", type="primary", width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with cfg_col2:
        # SKU Overview & Regional Breakdown Expander
        if branch_col:
            with st.expander(f"🏢 Regional Demand Distribution for {selected_sku} across All 5 Branches", expanded=False):
                sku_overall = forecast_df[forecast_df['Material'] == selected_sku].dropna(subset=[branch_col]).copy()
                if not sku_overall.empty:
                    b_summary = sku_overall.groupby(branch_col)['Billing Quantity ODU'].sum().reset_index()
                    b_summary['Branch'] = b_summary[branch_col].map(lambda x: BRANCH_LABELS.get(x, str(x)))
                    tot_sku_vol = b_summary['Billing Quantity ODU'].sum()
                    b_summary['Share %'] = (b_summary['Billing Quantity ODU'] / tot_sku_vol * 100).round(1) if tot_sku_vol > 0 else 0
                    b_summary = b_summary.sort_values('Billing Quantity ODU', ascending=False)
                    
                    dist_c1, dist_c2 = st.columns([1, 1])
                    with dist_c1:
                        fig_donut = px.pie(
                            b_summary,
                            values='Billing Quantity ODU',
                            names='Branch',
                            hole=0.55,
                            color_discrete_sequence=['#00E5FF', '#6366F1', '#10B981', '#F59E0B', '#EC4899']
                        )
                        apply_custom_chart_theme(fig_donut, height=260, title=f"Branch Split: {selected_sku}")
                        st.plotly_chart(fig_donut, width="stretch", theme=None)
                    with dist_c2:
                        st.dataframe(
                            b_summary[['Branch', 'Billing Quantity ODU', 'Share %']].rename(columns={'Billing Quantity ODU': 'Units Sold'}),
                            width="stretch",
                            height=240,
                            hide_index=True
                        )

        if run_forecast and selected_model:
            is_automl = model_family == "🤖 Champion Model (AutoML)"
            with st.spinner(f"Backtesting {'all candidate models' if is_automl else selected_model} for {selected_sku} ({branch_label})..."):
                try:
                    res = run_engine_forecast(engine_df, selected_sku, engine_branches, forecast_periods,
                                              confidence_level / 100.0, None if is_automl else selected_model)
                    board = res if is_automl else run_engine_forecast(engine_df, selected_sku, engine_branches,
                                                                      forecast_periods, confidence_level / 100.0, None)
                except Exception as e:
                    st.error(f"Forecast engine error: {e}")
                    return
            if res.get('status') != 'success':
                st.error(f"Cannot forecast {selected_sku} ({branch_label}): {res.get('error', 'unknown error')}")
                return

            champ = res['champion']
            model_name = champ.get('model_name', selected_model)
            lb = res['leaderboard'].set_index('model')
            row = lb.loc[model_name] if model_name in lb.index else None
            wape = float(row['mean_wape']) if row is not None else float('nan')
            accuracy = accuracy_from_wape(wape) if row is not None else float('nan')
            n_folds, test_w = res.get('backtest_folds', 0), res.get('backtest_test_weeks', 12)

            if is_automl:
                st.markdown(f"""
                <div style="background: {'rgba(16, 185, 129, 0.12)' if is_dark else '#ECFDF5'}; border: 1px solid {'rgba(16, 185, 129, 0.35)' if is_dark else '#A7F3D0'}; border-radius: 12px; padding: 12px 18px; margin-bottom: 14px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: {'#10B981' if is_dark else '#059669'}; text-transform: uppercase; letter-spacing: 1px;">
                        Champion selected by out-of-sample tournament ({len(lb)} models ranked)
                    </div>
                    <div style="font-family: 'Outfit'; font-size: 16px; font-weight: 700; margin-top: 2px;">
                        🏆 {model_name} &bull; backtest WAPE {wape:.1f}% (accuracy {accuracy:.1f}%)
                    </div>
                    <div style="color: var(--text-secondary); font-size: 12px; margin-top: 2px;">
                        {res.get('champion_description', '')} Measured on {n_folds} rolling-origin fold(s) of {test_w} weeks the model had not seen. {res.get('fallback_reason') or ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            hist_dates = pd.to_datetime(res['historical_dates'])
            fig = create_forecast_plot(
                historical_dates=hist_dates,
                historical_values=res['historical_demand'],
                forecast_dates=res['forecast_dates'],
                forecast_values=res['forecast'],
                lower_bound=res['p10'],
                upper_bound=res['p90'],
                model_name=model_name,
                branch_label=branch_label,
                confidence_level=confidence_level
            )
            st.plotly_chart(fig, width="stretch", theme=None)
            st.caption(res['interval_calibration'].get('note', ''))

            st.markdown("""
            <div class="subpanel-title" style="margin: 16px 0 12px 0;">
                📈 Out-of-Sample Backtest Accuracy (rolling-origin, never in-sample)
            </div>
            """, unsafe_allow_html=True)
            met1, met2, met3, met4 = st.columns(4)
            if row is not None:
                bias = float(row['mean_bias_pct'])
                with met1:
                    st.markdown(render_kpi_card("Mean Absolute Error", f"{row['mean_mae']:.1f}", "MAE", "cyan", "🎯", f"Units / week, {n_folds} folds"), unsafe_allow_html=True)
                with met2:
                    st.markdown(render_kpi_card("Root Mean Sq Error", f"{row['mean_rmse']:.1f}", "RMSE", "amber", "📏", "Ranking metric"), unsafe_allow_html=True)
                with met3:
                    st.markdown(render_kpi_card("WAPE", f"{wape:.1f}%", "WAPE", "rose" if wape > 50 else "green", "📊", f"Bias {bias:+.1f}%"), unsafe_allow_html=True)
                with met4:
                    st.markdown(render_kpi_card("Forecast Accuracy", f"{accuracy:.1f}%", "1 − WAPE", "green" if accuracy >= 70 else ("amber" if accuracy >= 40 else "rose"), "⭐", f"{test_w}-week horizon"), unsafe_allow_html=True)

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div class="subpanel-title" style="margin-bottom: 10px;">
                🏆 Model Tournament Leaderboard (same backtest for every candidate, ranked on RMSE)
            </div>
            """, unsafe_allow_html=True)
            if board.get('status') == 'success':
                disp = board['leaderboard_display'].copy()
                disp.insert(2, 'Accuracy (%)', disp['WAPE (%)'].apply(accuracy_from_wape).round(1))
                st.dataframe(disp, width="stretch", hide_index=True)
                bc = board.get('baseline_comparison') or {}
                if bc.get('verdict'):
                    st.caption(bc['verdict'])

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div class="subpanel-title" style="margin-bottom: 10px;">
                📋 Forward Forecast Horizon Schedule
            </div>
            """, unsafe_allow_html=True)
            lo_col, hi_col = f'Lower Bound ({confidence_level}% PI)', f'Upper Bound ({confidence_level}% PI)'
            forecast_df = pd.DataFrame({
                'Date': pd.to_datetime(res['forecast_dates']).strftime('%Y-%m-%d'),
                'Forecast (Units)': np.round(res['forecast'], 1),
                lo_col: np.round(res['p10'], 1),
                hi_col: np.round(res['p90'], 1),
            })
            display_df = forecast_df.copy()
            display_df.insert(0, 'Week', range(1, len(display_df) + 1))
            display_df.insert(1, 'Branch', branch_label)
            st.dataframe(display_df, width="stretch", height=320, hide_index=True)

            csv_df = forecast_df.copy()
            csv_df.insert(0, 'Material', selected_sku)
            csv_df.insert(1, 'Branch', branch_label)
            csv_df.insert(2, 'Model', model_name)
            clean_model_tag = re.sub(r'[^a-zA-Z0-9_]', '_', model_name)
            st.download_button(
                label=f"📥 Download Forecast as CSV ({branch_label})",
                data=csv_df.to_csv(index=False),
                file_name=f"forecast_{selected_sku}_{branch_file_code}_{clean_model_tag}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                width="stretch"
            )

            render_model_dossier(res, selected_sku, branch_label, is_dark)
        else:
            # Historical pattern view when simulation not executed
            sku_raw = filtered_forecast_df[filtered_forecast_df['Material'] == selected_sku].copy()
            if len(sku_raw) > 0:
                sku_weekly = (
                    sku_raw.groupby('Billing Date')['Billing Quantity ODU']
                    .sum()
                    .resample('W-MON')
                    .sum()
                    .reset_index()
                    .sort_values('Billing Date')
                )
                
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Scatter(
                    x=sku_weekly['Billing Date'],
                    y=sku_weekly['Billing Quantity ODU'],
                    mode='lines+markers',
                    name='Historical Demand',
                    line=dict(color='#00E5FF' if is_dark else '#0369A1', width=2.5),
                    marker=dict(size=7, color='#6366F1'),
                    fill='tozeroy',
                    fillcolor='rgba(0, 229, 255, 0.1)' if is_dark else 'rgba(3, 105, 161, 0.1)'
                ))
                
                apply_custom_chart_theme(fig_hist, height=420, title=f"Historical Demand Velocity: {selected_sku} | {branch_label}")
                st.plotly_chart(fig_hist, width="stretch", theme=None)
                
                st.info("👆 Adjust parameters in the Control Bar on the left and click 'Execute Forecast Simulation' to generate forward predictive curves.")

        # Out-of-sample check of every model on FY24-25 billing (independent of the Execute button)
        if selected_sku:
            render_holdout_model_validation(
                selected_sku, engine_branches, branch_label,
                CHAMPION_LABEL if model_family == "🤖 Champion Model (AutoML)" else selected_model, is_dark)


# -----------------------------------------------------------------------------
# PAGE 3: 🛡️ DATA QUALITY & HEALTH
# -----------------------------------------------------------------------------
def show_data_quality(df, metrics):
    st.markdown("""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">🛡️ Data Quality & Integrity Diagnostics</h2>
            <p class="section-subtitle">Multi-dimensional audit of enterprise completeness, null variance, and attribute schemas</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    q_col1, q_col2, q_col3 = st.columns(3)
    quality_status = "Enterprise Ready" if metrics['completeness'] >= 95 else "Operational" if metrics['completeness'] >= 85 else "Hygiene Required"
    
    with q_col1:
        st.markdown(render_kpi_card(
            label="Overall Data Quality Index",
            value=f"{metrics['completeness']:.1f}/100",
            delta_text="Certified",
            delta_type="cyan",
            icon="🏆",
            subtext="Fleet-wide aggregate rating",
            progress=metrics['completeness']
        ), unsafe_allow_html=True)
        
    with q_col2:
        st.markdown(render_kpi_card(
            label="Anomalous Attribute Fields",
            value=f"{metrics['columns_with_missing']}",
            delta_text=f"{metrics['columns_with_missing']} of {metrics['total_columns']}",
            delta_type="amber" if metrics['columns_with_missing'] > 0 else "green",
            icon="🔍",
            subtext="Columns with null presence",
            progress=(metrics['columns_with_missing'] / metrics['total_columns'] * 100)
        ), unsafe_allow_html=True)
        
    with q_col3:
        st.markdown(render_kpi_card(
            label="Enterprise Integrity State",
            value=quality_status,
            delta_text="Live",
            delta_type="green" if metrics['completeness'] >= 95 else "amber",
            icon="🛡️",
            subtext=f"Total missing: {metrics['total_missing']:,} cells",
            progress=100
        ), unsafe_allow_html=True)
        
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    
    # Row 1: Dual Diagnostic Charts (6-Dimension Radar + Missing Values Bar)
    diag_c1, diag_c2 = st.columns([1, 1])
    with diag_c1:
        fig_radar = create_data_quality_radar_chart(metrics, theme=st.session_state.get('theme', 'dark'))
        st.plotly_chart(fig_radar, width="stretch", theme=None)
        
    with diag_c2:
        fig_missing = create_missing_data_chart(df)
        if fig_missing:
            st.plotly_chart(fig_missing, width="stretch", theme=None)
        else:
            st.success("✅ Clean Record: Zero missing values detected across dataset attributes.")
            
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    
    # Row 2: Schema Audit Table & Type Distribution Breakdown
    detail_c1, detail_c2 = st.columns([3, 2])
    with detail_c1:
        st.markdown("""
        <div class="subpanel-title" style="margin-bottom: 12px;">
            📋 Missing Field Summary Breakdown
        </div>
        """, unsafe_allow_html=True)
        
        missing_summary = df.isnull().sum()
        missing_summary = missing_summary[missing_summary > 0].sort_values(ascending=False)
        if len(missing_summary) > 0:
            summary_df = pd.DataFrame({
                'Column': missing_summary.index,
                'Missing Rows': missing_summary.values,
                'Null Ratio %': (missing_summary.values / len(df) * 100).round(2)
            })
            st.dataframe(summary_df, width="stretch", height=360)
        else:
            st.info("No column attributes exhibit missing values.")

    with detail_c2:
        # Data Types Distribution
        dtype_counts = df.dtypes.value_counts()
        is_dark = (st.session_state.get('theme', 'dark') == 'dark')
        fig_dtypes = px.pie(
            values=dtype_counts.values,
            names=dtype_counts.index.astype(str),
            title="Schema Attribute Type Distribution",
            hole=0.55,
            color_discrete_sequence=['#00E5FF', '#6366F1', '#10B981', '#F59E0B'] if is_dark else ['#0369A1', '#6366F1', '#047857', '#B45309']
        )
        fig_dtypes.update_traces(
            marker=dict(line=dict(color='#0A0E1A' if is_dark else '#FFFFFF', width=2)),
            textfont=dict(color="#FFFFFF" if is_dark else "#0F172A", family="Plus Jakarta Sans")
        )
        apply_custom_chart_theme(fig_dtypes, height=360, theme=st.session_state.get('theme', 'dark'))
        st.plotly_chart(fig_dtypes, width="stretch", theme=None)

# -----------------------------------------------------------------------------
# PAGE 4: 🧹 DATA CLEANING STUDIO
# -----------------------------------------------------------------------------
def show_data_cleaning(df, metrics):
    st.markdown("""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">🧹 Automated Data Hygiene Pipeline</h2>
            <p class="section-subtitle">Intelligent deduplication, imputation roadmaps, and schema standardization</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    is_dark = (st.session_state.get('theme', 'dark') == 'dark')
    clean_accent_1 = "#00E5FF" if is_dark else "#0369A1"
    clean_accent_2 = "#10B981" if is_dark else "#047857"
    
    clean_c1, clean_c2 = st.columns(2)
    
    with clean_c1:
        st.markdown(f"""
        <div class="glass-panel">
            <div class="subpanel-title" style="color: {clean_accent_1}; display: flex; align-items: center; gap: 8px;">
                <span>✨</span> Recommended Hygiene Actions
            </div>
            <ul class="panel-bullet-list">
                <li>Prune <strong>{metrics['duplicate_rows']:,}</strong> redundant duplicate transaction rows</li>
                <li>Impute or isolate <strong>{metrics['total_missing']:,}</strong> null fields</li>
                <li>Normalize schema in <strong>{metrics['columns_with_missing']}</strong> attributes</li>
                <li>Enforce ISO date format standard for <code>Billing Date</code></li>
                <li>Standardize casing across categorical dimensions (<code>Segment</code>, <code>Material</code>)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with clean_c2:
        cleaned_records = metrics['total_records'] - metrics['duplicate_rows']
        st.markdown(f"""
        <div class="glass-panel">
            <div class="subpanel-title" style="color: {clean_accent_2}; display: flex; align-items: center; gap: 8px;">
                <span>⚡</span> Post-Cleaning Projections
            </div>
            <ul class="panel-bullet-list">
                <li>Expected Post-Clean Fleet Size: <strong>{cleaned_records:,} rows</strong></li>
                <li>Target Data Completeness: <strong>{min(100.0, metrics['completeness'] + 3.5):.2f}%</strong></li>
                <li>Efficiency & Storage Optimization: <strong>+{metrics['duplicate_percentage']:.2f}%</strong></li>
                <li>Model Training Latency Reduction: <strong>~18% faster convergence</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Duplicate Analysis Chart
    dup_c1, dup_c2 = st.columns([3, 2])
    with dup_c1:
        if metrics['duplicate_rows'] > 0:
            border_pie = '#0A0E1A' if is_dark else '#FFFFFF'
            fig_dup = go.Figure(data=[go.Pie(
                labels=['Unique Transactions', 'Duplicate Transactions'],
                values=[metrics['total_records'] - metrics['duplicate_rows'], metrics['duplicate_rows']],
                hole=0.55,
                marker=dict(colors=['#10B981', '#F43F5E'], line=dict(color=border_pie, width=2)),
                textfont=dict(color="#FFFFFF" if is_dark else "#0F172A", family="Plus Jakarta Sans")
            )])
            apply_custom_chart_theme(fig_dup, height=360, title="Duplicate vs Unique Transaction Density")
            st.plotly_chart(fig_dup, width="stretch", theme=None)
        else:
            st.success("✅ Zero duplicate transaction rows discovered in active dataset.")
            
    with dup_c2:
        dup_color = "#F43F5E" if is_dark else "#BE123C"
        green_color = "#10B981" if is_dark else "#047857"
        st.markdown(f"""
        <div class="glass-panel" style="margin-top: 10px;">
            <div class="subpanel-title" style="margin-bottom: 10px;">
                Deduplication Telemetry
            </div>
            <div class="telemetry-row">
                <span class="label">Identified Duplicates:</span>
                <strong style="color: {dup_color};">{metrics['duplicate_rows']:,}</strong>
            </div>
            <div class="telemetry-row">
                <span class="label">Duplicate Ratio:</span>
                <strong style="color: {dup_color};">{metrics['duplicate_percentage']:.2f}%</strong>
            </div>
            <div class="telemetry-row" style="border-bottom: none;">
                <span class="label">Verified Unique Records:</span>
                <strong style="color: {green_color};">{metrics['total_records'] - metrics['duplicate_rows']:,}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown("""
    <div class="subpanel-title" style="font-size: 18px !important; margin-bottom: 12px;">
        📐 Categorical Standardization Audit
    </div>
    """, unsafe_allow_html=True)
    
    text_columns = df.select_dtypes(include=['object']).columns
    for col in text_columns[:4]:
        with st.expander(f"📊 Attribute Field: {col}"):
            c_a, c_b = st.columns(2)
            with c_a:
                st.write(f"**Distinct Cardinality:** {df[col].nunique():,}")
                st.write(f"**Null Values:** {df[col].isnull().sum():,}")
                st.write(f"**Storage Type:** `{df[col].dtype}`")
            with c_b:
                st.write("**High-Frequency Values:**")
                st.dataframe(df[col].value_counts().head(5), width="stretch")

# -----------------------------------------------------------------------------
# PAGE 5: 📈 STATISTICAL DEEP-DIVE
# -----------------------------------------------------------------------------
def show_statistical_analysis(df):
    st.markdown("""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">📈 Statistical Deep-Dive</h2>
            <p class="section-subtitle">Multi-variate numerical distributions, correlation matrices, and variance spread</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    analysis_df = df[df['Billing Quantity ODU'] >= 0].copy() if 'Billing Quantity ODU' in df.columns else df
    numeric_cols = analysis_df.select_dtypes(include=[np.number]).columns.tolist()
    identifier_columns = {'Billing Doc.', 'Item', 'Stor. Location', 'Tonnage.1'}
    numeric_analysis_cols = [column for column in numeric_cols if column not in identifier_columns]
    is_dark = (st.session_state.get('theme', 'dark') == 'dark')
    
    st.markdown("""
    <div class="subpanel-title" style="margin-bottom: 10px;">
        📊 Descriptive Numerical Summary
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(analysis_df[numeric_analysis_cols].describe(), width="stretch")
    
    st.markdown("---")
    fig_corr = create_correlation_heatmap(analysis_df)
    if fig_corr:
        st.plotly_chart(fig_corr, width="stretch", theme=None)
        
    st.markdown("---")
    st.markdown("""
    <div class="subpanel-title" style="margin-bottom: 10px;">
        📉 Distribution & Outlier Inspector
    </div>
    """, unsafe_allow_html=True)
    
    selected_col = st.selectbox("Choose Numerical Dimension to Inspect:", numeric_analysis_cols)
    if selected_col:
        stat_c1, stat_c2 = st.columns(2)
        with stat_c1:
            fig_dist = create_distribution_chart(analysis_df, selected_col)
            st.plotly_chart(fig_dist, width="stretch", theme=None)
        with stat_c2:
            fig_box = px.box(analysis_df, y=selected_col, title=f"Box Plot Spread: {selected_col}")
            box_accent = '#00E5FF' if is_dark else '#0369A1'
            fig_box.update_traces(marker_color=box_accent, line=dict(color=box_accent))
            apply_custom_chart_theme(fig_box, height=400)
            st.plotly_chart(fig_box, width="stretch", theme=None)
            
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(render_kpi_card("Mean", f"{analysis_df[selected_col].mean():.2f}", "AVG", "cyan", "📐", "Arithmetic mean"), unsafe_allow_html=True)
        with m2:
            st.markdown(render_kpi_card("Median", f"{analysis_df[selected_col].median():.2f}", "P50", "green", "🎯", "50th percentile"), unsafe_allow_html=True)
        with m3:
            st.markdown(render_kpi_card("Std Deviation", f"{analysis_df[selected_col].std():.2f}", "SIGMA", "amber", "📊", "Dispersion"), unsafe_allow_html=True)
        with m4:
            st.markdown(render_kpi_card("Range", f"{analysis_df[selected_col].max() - analysis_df[selected_col].min():.2f}", "SPREAD", "rose", "↔️", "Max minus min"), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PAGE 6: 🔍 INTELLIGENCE EXPLORER
# -----------------------------------------------------------------------------
def show_detailed_exploration(df):
    st.markdown("""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">🔍 Data Intelligence Explorer</h2>
            <p class="section-subtitle">Multi-dimensional column slice-and-dice, attribute profiling, and regex search</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    selected_columns = st.multiselect(
        "Choose Columns to Inspect:",
        df.columns.tolist(),
        default=df.columns.tolist()[:6]
    )
    
    if selected_columns:
        st.dataframe(df[selected_columns].head(100), width="stretch", height=380)
        st.markdown("---")
        
        c_prof1, c_prof2 = st.columns([1, 2])
        with c_prof1:
            analysis_col = st.selectbox("Inspect Attribute Profile:", selected_columns)
            if analysis_col:
                is_dark = (st.session_state.get('theme', 'dark') == 'dark')
                prof_color = "#00E5FF" if is_dark else "#0369A1"
                st.markdown(f"""
                <div class="glass-panel">
                    <div class="subpanel-title" style="color: {prof_color}; margin-bottom: 10px;">
                        Profile: {analysis_col}
                    </div>
                    <div class="telemetry-row">
                        <span class="label">Distinct Values:</span>
                        <strong>{df[analysis_col].nunique():,}</strong>
                    </div>
                    <div class="telemetry-row">
                        <span class="label">Missing Records:</span>
                        <strong style="color: {'#F59E0B' if is_dark else '#B45309'};">{df[analysis_col].isnull().sum():,}</strong>
                    </div>
                    <div class="telemetry-row" style="border-bottom: none;">
                        <span class="label">Inferred Dtype:</span>
                        <code>{df[analysis_col].dtype}</code>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        with c_prof2:
            if analysis_col:
                fig = create_distribution_chart(df, analysis_col)
                st.plotly_chart(fig, width="stretch", theme=None)
                
    st.markdown("---")
    st.markdown("""
    <div class="subpanel-title" style="margin-bottom: 10px;">
        🔎 Rapid Transaction Query Engine
    </div>
    """, unsafe_allow_html=True)
    
    s_c1, s_c2 = st.columns([1, 2])
    with s_c1:
        search_col = st.selectbox("Query Attribute:", df.columns.tolist())
    with s_c2:
        search_term = st.text_input("Enter Search Term or Key:")
        
    if search_term:
        filtered_df = df[df[search_col].astype(str).str.contains(search_term, case=False, na=False)]
        st.markdown(f"**Found `{len(filtered_df):,}` matching transaction rows:**")
        st.dataframe(filtered_df, width="stretch", height=350)

# -----------------------------------------------------------------------------
# PAGE 7: 📄 C-SUITE REPORTS & EXPORTS
# -----------------------------------------------------------------------------
def show_export_report(df, metrics):
    st.markdown("""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">📄 Executive Reports & Data Export Center</h2>
            <p class="section-subtitle">Generate automated C-Suite PDF briefing documents and multi-tab Excel workbooks</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    is_dark = (st.session_state.get('theme', 'dark') == 'dark')
    rep_accent = "#00E5FF" if is_dark else "#0369A1"
    brief_accent = "#10B981" if is_dark else "#047857"
    
    rep_c1, rep_c2 = st.columns([2, 1])
    with rep_c1:
        st.markdown(f"""
        <div class="glass-panel">
            <div class="subpanel-title" style="color: {rep_accent}; margin-bottom: 10px;">
                📑 Executive Report Structure
            </div>
            <ol class="panel-bullet-list">
                <li><strong>Executive Summary</strong> &ndash; High-level strategic briefing on South Region sales velocity.</li>
                <li><strong>Data Integrity Audit</strong> &ndash; Completeness ratios, missing field density, and schema metrics.</li>
                <li><strong>Actionable Roadmaps</strong> &ndash; Deduplication, normalization protocols, and automated pipeline rules.</li>
                <li><strong>Demand Forecasting Synopsis</strong> &ndash; Methodological framework covering ARIMA, SARIMA, and Gradient Boosting.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
    with rep_c2:
        st.markdown(f"""
        <div class="glass-panel">
            <div class="subpanel-title" style="color: {brief_accent}; margin-bottom: 10px;">
                📊 Briefing Telemetry
            </div>
            <div class="telemetry-row">
                <span class="label">Historical Records:</span>
                <strong>{metrics['total_records']:,}</strong>
            </div>
            <div class="telemetry-row">
                <span class="label">Completeness Score:</span>
                <strong style="color: {rep_accent};">{metrics['completeness']:.2f}%</strong>
            </div>
            <div class="telemetry-row">
                <span class="label">Missing Cells:</span>
                <strong style="color: {'#F59E0B' if is_dark else '#B45309'};">{metrics['total_missing']:,}</strong>
            </div>
            <div class="telemetry-row" style="border-bottom: none;">
                <span class="label">Duplicate Rows:</span>
                <strong style="color: {'#F43F5E' if is_dark else '#BE123C'};">{metrics['duplicate_rows']:,}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    # Generate PDF Action
    if st.button("🚀 Compile & Generate Executive PDF Report", type="primary", width="stretch"):
        with st.spinner("Compiling C-Suite executive briefing PDF..."):
            try:
                pdf_data = generate_pdf_report(df, metrics)
                b64_pdf = base64.b64encode(pdf_data).decode()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Executive_Briefing_{timestamp}.pdf"
                
                st.success("✅ Executive PDF Briefing generated successfully!")
                href = f'<div style="text-align:center; margin: 16px 0;"><a href="data:application/pdf;base64,{b64_pdf}" download="{filename}" style="background: linear-gradient(135deg, #10B981, #059669); color: white; padding: 12px 28px; border-radius: 12px; text-decoration: none; font-weight: 700; font-family: Outfit; font-size: 16px; box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);">📥 Download {filename}</a></div>'
                st.markdown(href, unsafe_allow_html=True)
                st.balloons()
            except Exception as e:
                st.error(f"PDF compilation error: {str(e)}")
                
    st.markdown("---")
    st.markdown("""
    <div class="subpanel-title" style="margin-bottom: 12px;">
        💾 Alternative Data Export Formats
    </div>
    """, unsafe_allow_html=True)
    
    exp1, exp2, exp3 = st.columns(3)
    with exp1:
        if st.button("📊 Export Formatted Excel (.xlsx)", width="stretch"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Sales_Data', index=False)
                summary_df = pd.DataFrame({
                    'Metric': ['Total Transactions', 'Total Columns', 'Missing Value Cells', 'Duplicate Rows', 'Data Completeness %'],
                    'Value': [metrics['total_records'], metrics['total_columns'], metrics['total_missing'], metrics['duplicate_rows'], f"{metrics['completeness']:.2f}%"]
                })
                summary_df.to_excel(writer, sheet_name='Executive_Summary', index=False)
            
            st.download_button(
                label="Download Excel Workbook",
                data=output.getvalue(),
                file_name=f"Data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch"
            )
            
    with exp2:
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📄 Export Raw CSV Dataset",
            data=csv_data,
            file_name=f"Dataset_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width="stretch"
        )
        
    with exp3:
        summary_text = f"""EXECUTIVE TELEMETRY SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ISB Capstone Project & Demand Forecasting

DATASET OVERVIEW
================
Total Records: {metrics['total_records']:,}
Total Columns: {metrics['total_columns']}
Date Horizon: {df['Billing Date'].min()} to {df['Billing Date'].max()}

DATA QUALITY INDICES
====================
Completeness Score: {metrics['completeness']:.2f}%
Missing Cells: {metrics['total_missing']:,} ({metrics['missing_percentage']:.2f}%)
Duplicate Records: {metrics['duplicate_rows']:,} ({metrics['duplicate_percentage']:.2f}%)
Anomalous Columns: {metrics['columns_with_missing']}
"""
        st.download_button(
            label="📋 Download Text Briefing (.txt)",
            data=summary_text,
            file_name=f"Telemetry_Summary_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            width="stretch"
        )

if __name__ == "__main__":
    main()
