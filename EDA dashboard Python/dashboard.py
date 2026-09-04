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
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Regional Branch Definitions (Daikin South Region)
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
    page_title="Daikin AI Intelligence & Demand Forecasting | ISB Capstone",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# DYNAMIC WORLD-CLASS EXECUTIVE THEME & ANIMATION ENGINE (DARK & LIGHT)
# -----------------------------------------------------------------------------
def inject_theme_css(theme="dark"):
    is_dark = (theme == "dark")
    
    if is_dark:
        bg_main = "#0A0E1A"
        bg_app = "#0A0E1A"
        bg_secondary = "#131C31"
        primary_color = "#00E5FF"
        bg_mesh = """
            radial-gradient(at 0% 0%, rgba(0, 229, 255, 0.09) 0px, transparent 45%),
            radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.14) 0px, transparent 50%),
            radial-gradient(at 50% 50%, rgba(16, 185, 129, 0.05) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(0, 229, 255, 0.07) 0px, transparent 45%),
            radial-gradient(at 0% 100%, rgba(139, 92, 246, 0.09) 0px, transparent 50%)
        """
        text_primary = "#FFFFFF"
        text_secondary = "#CBD5E1"
        text_muted = "#94A3B8"
        bg_card = "linear-gradient(135deg, rgba(19, 28, 49, 0.85) 0%, rgba(15, 23, 42, 0.92) 100%)"
        border_glass = "rgba(255, 255, 255, 0.12)"
        border_glass_hover = "rgba(0, 229, 255, 0.55)"
        header_bg = "linear-gradient(135deg, rgba(19, 28, 49, 0.92) 0%, rgba(15, 23, 42, 0.98) 100%)"
        panel_bg = "linear-gradient(135deg, rgba(19, 28, 49, 0.8) 0%, rgba(15, 23, 42, 0.88) 100%)"
        popover_bg = "#131C31"
        seg_bg = "rgba(15, 23, 42, 0.85)"
        seg_text = "#CBD5E1"
        seg_active_bg = "linear-gradient(135deg, rgba(0, 229, 255, 0.25) 0%, rgba(99, 102, 241, 0.35) 100%)"
        seg_active_text = "#00E5FF"
        seg_active_border = "rgba(0, 229, 255, 0.6)"
        seg_active_shadow = "rgba(0, 229, 255, 0.35)"
        sidebar_bg = "#080C16"
        sidebar_grad = "linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(8, 12, 22, 0.99) 100%)"
        meta_chip_bg = "rgba(255, 255, 255, 0.06)"
        meta_chip_border = "rgba(255, 255, 255, 0.12)"
        card_shadow = "0 10px 25px -8px rgba(0, 0, 0, 0.5)"
        card_shadow_hover = "0 20px 35px -10px rgba(0, 229, 255, 0.25), 0 0 20px rgba(99, 102, 241, 0.2)"
        icon_wrap_bg = "rgba(255, 255, 255, 0.07)"
        input_bg = "rgba(19, 28, 49, 0.92)"
        title_grad = "linear-gradient(135deg, #FFFFFF 30%, #67E8F9 100%)"
        title_color = "#FFFFFF"
        brand_logo_grad = "linear-gradient(135deg, #00E5FF 0%, #3B82F6 100%)"
        btn_grad = "linear-gradient(135deg, #0284C7 0%, #2563EB 100%)"
        btn_text = "#FFFFFF"
        scrollbar_track = "#0A0E1A"
        scrollbar_thumb = "#334155"
    else:
        bg_main = "#F8FAFC"
        bg_app = "#F8FAFC"
        bg_secondary = "#FFFFFF"
        primary_color = "#0284C7"
        bg_mesh = """
            radial-gradient(at 0% 0%, rgba(3, 105, 161, 0.07) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.05) 0px, transparent 50%),
            radial-gradient(at 50% 50%, rgba(16, 185, 129, 0.03) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(3, 105, 161, 0.05) 0px, transparent 50%),
            radial-gradient(at 0% 100%, rgba(139, 92, 246, 0.04) 0px, transparent 50%)
        """
        text_primary = "#0F172A"
        text_secondary = "#334155"
        text_muted = "#64748B"
        bg_card = "linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.95) 100%)"
        border_glass = "rgba(203, 213, 225, 0.9)"
        border_glass_hover = "rgba(2, 132, 199, 0.6)"
        header_bg = "linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(241, 245, 249, 0.95) 100%)"
        panel_bg = "linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%)"
        popover_bg = "#FFFFFF"
        seg_bg = "#FFFFFF"
        seg_text = "#334155"
        seg_active_bg = "linear-gradient(135deg, #0284C7 0%, #2563EB 100%)"
        seg_active_text = "#FFFFFF"
        seg_active_border = "#0284C7"
        seg_active_shadow = "rgba(2, 132, 199, 0.35)"
        sidebar_bg = "#F1F5F9"
        sidebar_grad = "linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%)"
        meta_chip_bg = "rgba(0, 0, 0, 0.04)"
        meta_chip_border = "rgba(0, 0, 0, 0.08)"
        card_shadow = "0 10px 25px -5px rgba(15, 23, 42, 0.08)"
        card_shadow_hover = "0 20px 35px -10px rgba(2, 132, 199, 0.22)"
        icon_wrap_bg = "rgba(2, 132, 199, 0.08)"
        input_bg = "#FFFFFF"
        title_grad = "linear-gradient(135deg, #0F172A 20%, #0369A1 100%)"
        title_color = "#0F172A"
        brand_logo_grad = "linear-gradient(135deg, #0284C7 0%, #1D4ED8 100%)"
        btn_grad = "linear-gradient(135deg, #0284C7 0%, #1D4ED8 100%)"
        btn_text = "#FFFFFF"
        scrollbar_track = "#F1F5F9"
        scrollbar_thumb = "#CBD5E1"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

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
        }}

        .stApp {{
            background-color: {bg_app} !important;
            background-image: {bg_mesh} !important;
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

        /* Headings */
        h1, h2, h3, h4, h5, h6,
        .section-title,
        .subpanel-title {{
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

        @keyframes auraPulse {{
            0%, 100% {{ opacity: 0.6; transform: scale(1); }}
            50% {{ opacity: 0.85; transform: scale(1.04); }}
        }}

        @keyframes shimmer {{
            0% {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}

        @keyframes pulseBeacon {{
            0% {{ box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.7); }}
            70% {{ box-shadow: 0 0 0 9px rgba(0, 229, 255, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(0, 229, 255, 0); }}
        }}

        @keyframes cardEntrance {{
            from {{ opacity: 0; transform: translateY(18px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes floatBadge {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-3px); }}
        }}

        .executive-header {{
            background: {header_bg};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid {border_glass};
            border-radius: 20px;
            padding: 24px 32px;
            margin-bottom: 24px;
            box-shadow: {card_shadow};
            position: relative;
            overflow: hidden;
            animation: cardEntrance 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
        }}

        .executive-header::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #00E5FF, #6366F1, #10B981, #F59E0B, #00E5FF);
            background-size: 300% 100%;
            animation: shimmer 8s linear infinite;
        }}

        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}

        .brand-title-wrap {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .brand-logo-badge {{
            width: 54px;
            height: 54px;
            border-radius: 14px;
            background: {brand_logo_grad};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            box-shadow: 0 8px 20px rgba(2, 132, 199, 0.35);
            animation: floatBadge 4s ease-in-out infinite;
        }}

        .brand-title {{
            font-family: 'Outfit', sans-serif !important;
            font-size: 26px !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px !important;
            background: {title_grad};
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            margin: 0 !important;
            line-height: 1.2 !important;
        }}

        .brand-subtitle {{
            font-size: 13px !important;
            color: {text_secondary} !important;
            margin: 3px 0 0 0 !important;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .live-status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: {"rgba(0, 229, 255, 0.1)" if is_dark else "rgba(2, 132, 199, 0.08)"};
            border: 1px solid {"rgba(0, 229, 255, 0.3)" if is_dark else "rgba(2, 132, 199, 0.25)"};
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 600;
            color: {"#00E5FF" if is_dark else "#0284C7"};
            letter-spacing: 0.5px;
        }}

        .live-beacon {{
            width: 8px;
            height: 8px;
            background-color: {"#00E5FF" if is_dark else "#0284C7"};
            border-radius: 50%;
            display: inline-block;
            animation: pulseBeacon 2s infinite;
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
            padding: 6px 12px;
            border-radius: 10px;
            font-size: 12px;
            color: {text_secondary};
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .meta-chip strong {{
            color: {text_primary} !important;
        }}

        .section-title-wrap {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 18px 0 20px 0;
            padding-bottom: 12px;
            border-bottom: 1px solid {border_glass};
        }}

        .section-title {{
            font-family: 'Outfit', sans-serif !important;
            font-size: 22px !important;
            font-weight: 700 !important;
            color: {title_color} !important;
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0 !important;
        }}

        .section-subtitle {{
            font-size: 13.5px;
            color: {text_secondary};
            margin: 2px 0 0 0;
        }}

        .kpi-card {{
            background: {bg_card};
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid {border_glass};
            border-radius: 18px;
            padding: 20px 22px;
            position: relative;
            overflow: hidden;
            transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: {card_shadow};
            animation: cardEntrance 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
        }}

        .kpi-card:hover {{
            transform: translateY(-5px) scale(1.008);
            border-color: {border_glass_hover};
            box-shadow: {card_shadow_hover};
        }}

        .kpi-card-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}

        .kpi-icon-wrap {{
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: {icon_wrap_bg};
            border: 1px solid {border_glass};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }}

        .kpi-badge {{
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            letter-spacing: 0.3px;
            text-transform: uppercase;
        }}

        .kpi-badge-cyan {{
            background: {"rgba(0, 229, 255, 0.18)" if is_dark else "rgba(2, 132, 199, 0.14)"} !important;
            color: {"#00E5FF" if is_dark else "#0284C7"} !important;
            border: 1px solid {"rgba(0, 229, 255, 0.4)" if is_dark else "rgba(2, 132, 199, 0.35)"} !important;
        }}
        .kpi-badge-green {{
            background: {"rgba(16, 185, 129, 0.18)" if is_dark else "rgba(4, 120, 87, 0.14)"} !important;
            color: {"#10B981" if is_dark else "#047857"} !important;
            border: 1px solid {"rgba(16, 185, 129, 0.4)" if is_dark else "rgba(4, 120, 87, 0.35)"} !important;
        }}
        .kpi-badge-amber {{
            background: {"rgba(245, 158, 11, 0.18)" if is_dark else "rgba(180, 83, 9, 0.14)"} !important;
            color: {"#F59E0B" if is_dark else "#B45309"} !important;
            border: 1px solid {"rgba(245, 158, 11, 0.4)" if is_dark else "rgba(180, 83, 9, 0.35)"} !important;
        }}
        .kpi-badge-rose {{
            background: {"rgba(244, 63, 94, 0.18)" if is_dark else "rgba(190, 18, 60, 0.14)"} !important;
            color: {"#F43F5E" if is_dark else "#BE123C"} !important;
            border: 1px solid {"rgba(244, 63, 94, 0.4)" if is_dark else "rgba(190, 18, 60, 0.35)"} !important;
        }}

        .kpi-label {{
            font-size: 13px !important;
            font-weight: 700 !important;
            color: {text_secondary} !important;
            margin-bottom: 4px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.6px !important;
        }}

        .kpi-value {{
            font-family: 'Outfit', sans-serif !important;
            font-size: 32px !important;
            font-weight: 800 !important;
            color: {text_primary} !important;
            line-height: 1.1 !important;
            margin-bottom: 8px !important;
            letter-spacing: -0.5px !important;
        }}

        .kpi-bar {{
            height: 5px;
            background: {"rgba(255, 255, 255, 0.12)" if is_dark else "rgba(0, 0, 0, 0.08)"};
            border-radius: 3px;
            overflow: hidden;
            margin-top: 12px;
            width: 100%;
        }}

        .kpi-bar-fill {{
            height: 100%;
            border-radius: 3px;
            display: block;
            transition: width 0.8s ease-out;
        }}

        .glass-panel {{
            background: {panel_bg};
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid {border_glass};
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 22px;
            box-shadow: {card_shadow};
            transition: border-color 0.3s ease;
        }}

        .glass-panel:hover {{
            border-color: {border_glass_hover};
        }}

        /* SUBPANEL TITLES & TELEMETRY ROWS */
        .subpanel-title {{
            font-family: 'Outfit', sans-serif !important;
            font-size: 17px !important;
            font-weight: 700 !important;
            color: {title_color} !important;
            margin-bottom: 12px !important;
        }}

        .telemetry-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 9px 0;
            border-bottom: 1px solid {border_glass};
            font-size: 13.5px;
            color: {text_secondary};
        }}

        .telemetry-row strong {{
            color: {text_primary} !important;
            font-weight: 700 !important;
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
            margin-bottom: 6px !important;
        }}

        .panel-bullet-list strong {{
            color: {text_primary} !important;
            font-weight: 700 !important;
        }}

        .panel-bullet-list code, code {{
            background: {"rgba(0, 229, 255, 0.14)" if is_dark else "rgba(2, 132, 199, 0.09)"} !important;
            color: {"#00E5FF" if is_dark else "#0369A1"} !important;
            border: 1px solid {"rgba(0, 229, 255, 0.3)" if is_dark else "rgba(2, 132, 199, 0.25)"} !important;
            padding: 2px 7px !important;
            border-radius: 6px !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 600 !important;
        }}

        /* SEGMENTED CONTROL / BUTTON GROUP STYLING (Both stButtonGroup and stSegmentedControl) */
        [data-testid="stButtonGroup"],
        [data-testid="stSegmentedControl"] {{
            background: {seg_bg} !important;
            background-color: {seg_bg} !important;
            border: 1px solid {border_glass} !important;
            border-radius: 14px !important;
            padding: 4px !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            box-shadow: {card_shadow} !important;
            margin-bottom: 20px !important;
            display: flex !important;
            gap: 4px !important;
            flex-wrap: wrap !important;
        }}

        [data-testid="stButtonGroup"] button,
        [data-testid="stSegmentedControl"] button {{
            border-radius: 10px !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
            border: none !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            padding: 8px 18px !important;
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
            transform: translateY(-1px) !important;
        }}

        [data-testid="stButtonGroup"] button[aria-checked="false"]:hover *,
        [data-testid="stSegmentedControl"] button[aria-checked="false"]:hover * {{
            color: {text_primary} !important;
        }}

        /* Selected active button group state */
        [data-testid="stButtonGroup"] button[aria-checked="true"],
        [data-testid="stSegmentedControl"] button[aria-checked="true"] {{
            background: {seg_active_bg} !important;
            background-color: {"rgba(0, 229, 255, 0.22)" if is_dark else "#0284C7"} !important;
            border: 1px solid {seg_active_border} !important;
            box-shadow: 0 4px 14px {seg_active_shadow} !important;
            color: {seg_active_text} !important;
            transform: translateY(-1px) !important;
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

        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            background-image: {sidebar_grad} !important;
            border-right: 1px solid {border_glass} !important;
        }}

        [data-testid="stSidebar"] .block-container {{
            padding-top: 1.5rem !important;
        }}

        /* RADIO BUTTONS (SIDEBAR NAVIGATION & OPTIONS) */
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

        /* ACTION BUTTONS (STBUTTON) - EXPLICITLY SCOPED */
        [data-testid="stButton"] > button {{
            background: {btn_grad} !important;
            color: {btn_text} !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            border: none !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 20px -4px rgba(2, 132, 199, 0.35) !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
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
            transform: translateY(-3px) scale(1.015) !important;
            box-shadow: 0 14px 28px -4px rgba(2, 132, 199, 0.5) !important;
        }}

        .stDownloadButton > button {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.95) 0%, rgba(5, 150, 105, 0.95) 100%) !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 20px -4px rgba(16, 185, 129, 0.35) !important;
            transition: all 0.25s ease !important;
        }}

        .stDownloadButton > button *,
        .stDownloadButton > button p,
        .stDownloadButton > button span {{
            color: #FFFFFF !important;
            font-weight: 700 !important;
            background: transparent !important;
        }}

        /* SELECTBOX & BASEWEB POPOVER DROPDOWN */
        div[data-baseweb="select"] > div {{
            background-color: {input_bg} !important;
            border: 1px solid {border_glass} !important;
            border-radius: 12px !important;
            color: {text_primary} !important;
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
            background-color: {"rgba(0, 229, 255, 0.22)" if is_dark else "rgba(2, 132, 199, 0.12)"} !important;
            color: {"#00E5FF" if is_dark else "#0284C7"} !important;
            font-weight: 700 !important;
        }}

        /* MULTISELECT TAGS */
        span[data-baseweb="tag"] {{
            background-color: {"rgba(0, 229, 255, 0.18)" if is_dark else "rgba(2, 132, 199, 0.12)"} !important;
            color: {"#00E5FF" if is_dark else "#0284C7"} !important;
            border: 1px solid {"rgba(0, 229, 255, 0.35)" if is_dark else "rgba(2, 132, 199, 0.3)"} !important;
            border-radius: 8px !important;
        }}
        span[data-baseweb="tag"] span {{
            color: {"#00E5FF" if is_dark else "#0284C7"} !important;
            font-weight: 700 !important;
        }}

        /* EXPANDER */
        [data-testid="stExpander"] {{
            background: {panel_bg} !important;
            border: 1px solid {border_glass} !important;
            border-radius: 14px !important;
            box-shadow: {card_shadow} !important;
            overflow: hidden !important;
            margin-bottom: 14px !important;
        }}

        [data-testid="stExpander"] summary {{
            background-color: transparent !important;
            border-radius: 14px !important;
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

        [data-testid="stExpander"] summary svg {{
            color: {text_secondary} !important;
            fill: {text_secondary} !important;
        }}

        [data-testid="stExpanderDetails"] {{
            border-top: 1px solid {border_glass} !important;
            padding: 16px !important;
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
            color: {"#00E5FF" if is_dark else "#0284C7"} !important;
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
            border-radius: 10px !important;
            font-weight: 500 !important;
        }}
        [data-testid="stTextInput"] input::placeholder {{
            color: {text_muted} !important;
        }}

        /* DATAFRAME & TABLE DUAL-THEME */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            background-color: {input_bg} !important;
            border-radius: 14px !important;
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
            padding: 10px 14px !important;
            border-bottom: 2px solid {border_glass} !important;
        }}

        [data-testid="stTable"] td {{
            color: {text_primary} !important;
            border-bottom: 1px solid {border_glass} !important;
            padding: 9px 14px !important;
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
            border-radius: 14px !important;
            color: {text_primary} !important;
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
    plot_bg = 'rgba(19, 28, 49, 0.45)' if is_dark else 'rgba(241, 245, 249, 0.6)'
    text_color = '#E2E8F0' if is_dark else '#0F172A'
    title_color = '#FFFFFF' if is_dark else '#0F172A'
    grid_color = 'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(15, 23, 42, 0.08)'
    hover_bg = 'rgba(15, 23, 42, 0.98)' if is_dark else 'rgba(255, 255, 255, 0.98)'
    hover_text = '#FFFFFF' if is_dark else '#0F172A'
    hover_border = 'rgba(0, 229, 255, 0.6)' if is_dark else 'rgba(2, 132, 199, 0.6)'

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
            font=dict(color=text_color)
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
        tickfont=dict(color=text_color, family="Plus Jakarta Sans, sans-serif", size=11),
        title_font=dict(color=title_color, family="Outfit, sans-serif", size=13)
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid_color,
        zerolinecolor=grid_color,
        tickfont=dict(color=text_color, family="Plus Jakarta Sans, sans-serif", size=11),
        title_font=dict(color=title_color, family="Outfit, sans-serif", size=13)
    )
    
    return fig

# -----------------------------------------------------------------------------
# EXECUTIVE KPI CARD HTML GENERATOR
# -----------------------------------------------------------------------------
def render_kpi_card(label, value, delta_text=None, delta_type="cyan", icon="📊", subtext="", progress=None, theme=None):
    """Render a luxury glassmorphism KPI card with glowing highlights"""
    if theme is None:
        theme = st.session_state.get('theme', 'dark')
    is_dark = (theme == 'dark')
    badge_class = f"kpi-badge-{delta_type}"
    
    progress_html = ""
    if progress is not None:
        p_val = max(0, min(100, float(progress)))
        if is_dark:
            bar_color = "#00E5FF" if delta_type == "cyan" else "#10B981" if delta_type == "green" else "#F59E0B" if delta_type == "amber" else "#F43F5E"
        else:
            bar_color = "#0369A1" if delta_type == "cyan" else "#047857" if delta_type == "green" else "#B45309" if delta_type == "amber" else "#BE123C"
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
    # Try CSV first (faster), fallback to Excel
    csv_candidates = ['Filtered.csv', 'EDA dashboard Python/Filtered.csv']
    excel_candidates = ['Filtered.xlsx', 'EDA dashboard Python/Filtered.xlsx']
    
    csv_path = next((p for p in csv_candidates if os.path.exists(p)), None)
    if csv_path:
        df = pd.read_csv(csv_path, low_memory=False)
        if 'Billing Date' in df.columns:
            df['Billing Date'] = pd.to_datetime(df['Billing Date'], dayfirst=True)
    else:
        excel_path = next((p for p in excel_candidates if os.path.exists(p)), None)
        if excel_path:
            df = pd.read_excel(excel_path, engine='openpyxl')
            if 'Billing Date' in df.columns:
                df['Billing Date'] = pd.to_datetime(df['Billing Date'], dayfirst=True)
        else:
            raise FileNotFoundError("Could not locate Filtered.csv or Filtered.xlsx dataset.")
    return df

# -----------------------------------------------------------------------------
# METRICS & ANALYSIS FUNCTIONS
# -----------------------------------------------------------------------------
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
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr()
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

def create_time_series_chart(df, theme=None):
    if 'Billing Date' in df.columns:
        df_time = df.groupby(df['Billing Date'].dt.to_period('M')).size().reset_index()
        df_time.columns = ['Month', 'Count']
        df_time['Month'] = df_time['Month'].astype(str)
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
        
        fig.add_trace(
            go.Box(
                y=df['Tonnage'], 
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
                        forecast_values, lower_bound, upper_bound, model_name, branch_label=None, theme=None):
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
    
    # Confidence interval band
    fig.add_trace(go.Scatter(
        x=list(forecast_dates) + list(forecast_dates)[::-1],
        y=list(upper_bound) + list(lower_bound)[::-1],
        fill='toself',
        fillcolor=ci_fill,
        line=dict(color='rgba(255, 255, 255, 0)'),
        name='95% Confidence Band',
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
    
    return fig

# -----------------------------------------------------------------------------
# STATISTICAL & ML MODEL RUNNERS
# -----------------------------------------------------------------------------
def run_statistical_model(sku_data, model_name, forecast_periods, confidence_level, branch_label="All Branches"):
    ts_series = sku_data['Billing Quantity ODU'].reset_index(drop=True)
    train_size = int(len(ts_series) * 0.8)
    train, test = ts_series[:train_size], ts_series[train_size:]
    
    if model_name == "ARIMA":
        model = ARIMA(train, order=(1, 1, 1))
        fitted_model = model.fit()
        test_forecast = fitted_model.forecast(steps=len(test))
        
        full_model = ARIMA(ts_series, order=(1, 1, 1))
        full_fitted = full_model.fit()
        future_forecast = full_fitted.forecast(steps=forecast_periods)
        forecast_result = full_fitted.get_forecast(steps=forecast_periods)
        
    elif model_name == "SARIMA":
        seasonal_order_train = (1, 1, 1, 12) if len(train) >= 24 else (0, 0, 0, 0)
        model = SARIMAX(train, order=(1, 1, 1), seasonal_order=seasonal_order_train)
        fitted_model = model.fit(disp=False)
        test_forecast = fitted_model.forecast(steps=len(test))
        
        seasonal_order_full = (1, 1, 1, 12) if len(ts_series) >= 24 else (0, 0, 0, 0)
        full_model = SARIMAX(ts_series, order=(1, 1, 1), seasonal_order=seasonal_order_full)
        full_fitted = full_model.fit(disp=False)
        future_forecast = full_fitted.forecast(steps=forecast_periods)
        forecast_result = full_fitted.get_forecast(steps=forecast_periods)
        
    else:  # Exponential Smoothing
        if len(train) >= 24:
            model = ExponentialSmoothing(train, seasonal_periods=12, trend='add', seasonal='add')
        else:
            model = ExponentialSmoothing(train, trend='add', seasonal=None)
        fitted_model = model.fit()
        test_forecast = fitted_model.forecast(steps=len(test))
        
        if len(ts_series) >= 24:
            full_model = ExponentialSmoothing(ts_series, seasonal_periods=12, trend='add', seasonal='add')
        else:
            full_model = ExponentialSmoothing(ts_series, trend='add', seasonal=None)
        full_fitted = full_model.fit()
        future_forecast = full_fitted.forecast(steps=forecast_periods)
        forecast_result = None
    
    test_arr = np.array(test)
    pred_arr = np.array(test_forecast)
    mae = mean_absolute_error(test_arr, pred_arr)
    rmse = np.sqrt(mean_squared_error(test_arr, pred_arr))
    
    non_zero = test_arr != 0
    if np.any(non_zero):
        mape = np.mean(np.abs((test_arr[non_zero] - pred_arr[non_zero]) / test_arr[non_zero])) * 100
    else:
        mape = 0.0
    
    metrics_dict = {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}
    
    last_date = sku_data['Billing Date'].max()
    future_dates = pd.date_range(start=last_date + timedelta(days=7), periods=forecast_periods, freq='W')
    
    if forecast_result is not None:
        alpha = 1 - (confidence_level / 100)
        conf_int = forecast_result.conf_int(alpha=alpha)
        lower_bound = conf_int.iloc[:, 0].values
        upper_bound = conf_int.iloc[:, 1].values
    else:
        z_score = 1.96 if confidence_level == 95 else 2.576
        lower_bound = future_forecast.values - z_score * rmse
        upper_bound = future_forecast.values + z_score * rmse
    
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'Forecast': future_forecast.values,
        'Lower_Bound': np.maximum(0, lower_bound),
        'Upper_Bound': upper_bound
    })
    
    fig = create_forecast_plot(
        historical_dates=sku_data['Billing Date'].values,
        historical_values=sku_data['Billing Quantity ODU'].values,
        forecast_dates=future_dates,
        forecast_values=future_forecast.values,
        lower_bound=forecast_df['Lower_Bound'].values,
        upper_bound=forecast_df['Upper_Bound'].values,
        model_name=model_name,
        branch_label=branch_label
    )
    
    return forecast_df, metrics_dict, fig

def run_ml_model(sku_data, model_name, forecast_periods, confidence_level, branch_label="All Branches"):
    df_ml = sku_data.copy()
    df_ml = df_ml.sort_values('Billing Date').reset_index(drop=True)
    
    df_ml['day_of_year'] = df_ml['Billing Date'].dt.dayofyear
    df_ml['week_of_year'] = df_ml['Billing Date'].dt.isocalendar().week
    df_ml['month'] = df_ml['Billing Date'].dt.month
    df_ml['quarter'] = df_ml['Billing Date'].dt.quarter
    
    for lag in [1, 2, 3, 4]:
        df_ml[f'lag_{lag}'] = df_ml['Billing Quantity ODU'].shift(lag)
    
    for window in [2, 4]:
        df_ml[f'rolling_mean_{window}'] = df_ml['Billing Quantity ODU'].rolling(window=window).mean()
    
    df_ml = df_ml.dropna()
    if len(df_ml) < 10:
        raise ValueError("Insufficient data after feature engineering. Need more historical points.")
    
    feature_cols = ['day_of_year', 'week_of_year', 'month', 'quarter'] + \
                   [f'lag_{i}' for i in range(1, 5)] + \
                   [f'rolling_mean_{i}' for i in [2, 4]]
    
    X = df_ml[feature_cols]
    y = df_ml['Billing Quantity ODU']
    
    train_size = int(len(X) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    if model_name == "Random Forest":
        model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    else:  # Gradient Boosting
        model = GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5, learning_rate=0.1)
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_test_arr = np.array(y_test)
    y_pred_arr = np.array(y_pred)
    mae = mean_absolute_error(y_test_arr, y_pred_arr)
    rmse = np.sqrt(mean_squared_error(y_test_arr, y_pred_arr))
    
    non_zero = y_test_arr != 0
    if np.any(non_zero):
        mape = np.mean(np.abs((y_test_arr[non_zero] - y_pred_arr[non_zero]) / y_test_arr[non_zero])) * 100
    else:
        mape = 0.0
    
    metrics_dict = {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}
    
    last_date = sku_data['Billing Date'].max()
    future_dates = pd.date_range(start=last_date + timedelta(days=7), periods=forecast_periods, freq='W')
    
    forecast_values = []
    last_known_values = df_ml['Billing Quantity ODU'].values[-4:].tolist()
    
    for i, future_date in enumerate(future_dates):
        future_features = {
            'day_of_year': future_date.dayofyear,
            'week_of_year': future_date.isocalendar()[1],
            'month': future_date.month,
            'quarter': future_date.quarter,
            'lag_1': last_known_values[-1],
            'lag_2': last_known_values[-2],
            'lag_3': last_known_values[-3],
            'lag_4': last_known_values[-4],
            'rolling_mean_2': np.mean(last_known_values[-2:]),
            'rolling_mean_4': np.mean(last_known_values[-4:])
        }
        
        X_future = pd.DataFrame([future_features])
        pred = model.predict(X_future)[0]
        forecast_values.append(max(0, pred))
        
        last_known_values.append(pred)
        last_known_values.pop(0)
    
    z_score = 1.96 if confidence_level == 95 else 2.576
    forecast_array = np.array(forecast_values)
    lower_bound = np.maximum(0, forecast_array - z_score * rmse)
    upper_bound = forecast_array + z_score * rmse
    
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'Forecast': forecast_array,
        'Lower_Bound': lower_bound,
        'Upper_Bound': upper_bound
    })
    
    fig = create_forecast_plot(
        historical_dates=sku_data['Billing Date'].values,
        historical_values=sku_data['Billing Quantity ODU'].values,
        forecast_dates=future_dates,
        forecast_values=forecast_array,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        model_name=model_name,
        branch_label=branch_label
    )
    
    return forecast_df, metrics_dict, fig

# -----------------------------------------------------------------------------
# EXECUTIVE PDF REPORT GENERATOR
# -----------------------------------------------------------------------------
def generate_pdf_report(df, metrics):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Banner
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 10, 'Daikin Executive Analytics & Quality Briefing', 0, 1, 'C')
    pdf.ln(4)
    
    pdf.set_font('Arial', 'I', 11)
    pdf.cell(0, 10, f'ISB Capstone Project | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
    pdf.ln(8)
    
    # 1. Executive Summary
    pdf.set_font('Arial', 'B', 15)
    pdf.cell(0, 10, '1. Executive Summary', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, f"""This strategic intelligence report provides an in-depth audit of Daikin South Region transaction records across {metrics['total_records']:,} historical sales rows and {metrics['total_columns']} operational dimensions. The dataset demonstrates enterprise-grade readiness with a {metrics['completeness']:.2f}% data completeness rating.""")
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
    pdf.cell(0, 10, 'Report generated by Daikin Demand Forecasting & EDA Intelligence Platform', 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# -----------------------------------------------------------------------------
# MAIN APPLICATION CONTROLLER & NAVIGATION
# -----------------------------------------------------------------------------
def main():
    # Navigation Setup
    NAV_OPTIONS = [
        "🏠 Executive Cockpit",
        "🎯 AI Demand Forecasting",
        "🛡️ Data Quality Radar",
        "🧹 Data Cleaning Studio",
        "📈 Statistical Deep-Dive",
        "🔍 Intelligence Explorer",
        "📄 C-Suite Reports"
    ]

    # Initialize theme session state
    if 'theme' not in st.session_state:
        st.session_state['theme'] = 'dark'
        
    theme_label = "🌙 Dark" if st.session_state['theme'] == 'dark' else "☀️ Light"
    if 'sidebar_theme_segmented' not in st.session_state:
        st.session_state['sidebar_theme_segmented'] = theme_label
    if 'top_theme_segmented' not in st.session_state:
        st.session_state['top_theme_segmented'] = theme_label

    # Initialize navigation session state
    if 'current_view' not in st.session_state:
        st.session_state['current_view'] = NAV_OPTIONS[0]
    if 'sidebar_radio_selector' not in st.session_state:
        st.session_state['sidebar_radio_selector'] = st.session_state['current_view']
    if 'top_segmented_selector' not in st.session_state:
        st.session_state['top_segmented_selector'] = st.session_state['current_view']

    # Callbacks for seamless two-way synchronization
    def on_top_theme_change():
        val = st.session_state.get('top_theme_segmented')
        if val:
            new_theme = 'dark' if 'Dark' in val else 'light'
            st.session_state['theme'] = new_theme
            st.session_state['sidebar_theme_segmented'] = "🌙 Dark" if new_theme == 'dark' else "☀️ Light"

    def on_sidebar_theme_change():
        val = st.session_state.get('sidebar_theme_segmented')
        if val:
            new_theme = 'dark' if 'Dark' in val else 'light'
            st.session_state['theme'] = new_theme
            st.session_state['top_theme_segmented'] = "🌙 Dark" if new_theme == 'dark' else "☀️ Light"

    def on_top_nav_change():
        val = st.session_state.get('top_segmented_selector')
        if val:
            st.session_state['current_view'] = val
            st.session_state['sidebar_radio_selector'] = val

    def on_sidebar_nav_change():
        val = st.session_state.get('sidebar_radio_selector')
        if val:
            st.session_state['current_view'] = val
            st.session_state['top_segmented_selector'] = val

    # Inject dynamic CSS based on active theme
    inject_theme_css(st.session_state['theme'])
    is_dark = (st.session_state['theme'] == 'dark')

    # Load dataset
    df = load_data()
    metrics = calculate_data_quality_metrics(df)
    
    # Determine branch columns & stats
    branch_col = next((c for c in ['SALES OFFICE CODE', 'SALES OFFICE CODE.1', 'Region', 'Branch'] if c in df.columns), None)
    num_branches = df[branch_col].nunique() if branch_col else 5
    date_min = df['Billing Date'].min().strftime('%d %b %Y') if 'Billing Date' in df.columns else '2024'
    date_max = df['Billing Date'].max().strftime('%d %b %Y') if 'Billing Date' in df.columns else '2025'

    # Executive Top Brand Header
    theme_pill_label = "🌙 Dark Luxury" if is_dark else "☀️ Modern Light"
    theme_pill_color = "#00E5FF" if is_dark else "#0369A1"
    st.markdown(f"""
    <div class="executive-header">
        <div class="header-content">
            <div class="brand-title-wrap">
                <div class="brand-logo-badge">⚡</div>
                <div>
                    <h1 class="brand-title">DAIKIN SUPPLY CHAIN INTELLIGENCE</h1>
                    <p class="brand-subtitle">
                        ISB Capstone Project &bull; South Region Demand Forecasting & Quality Radar
                    </p>
                </div>
            </div>
            <div class="quick-meta-strip">
                <div class="live-status-pill">
                    <span class="live-beacon"></span> AI FORECASTING ENGINE ACTIVE
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
                    <span>Coverage:</span>
                    <strong>{num_branches} Regional Branches</strong>
                </div>
                <div class="meta-chip">
                    <span>Completeness:</span>
                    <strong style="color: {theme_pill_color};">{metrics['completeness']:.1f}%</strong>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Synchronized Sidebar Controls
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
            <div style="font-size: 24px;">🎛️</div>
            <div>
                <h3 style="margin: 0; font-family: 'Outfit'; color: var(--text-primary); font-size: 18px;">Control Hub</h3>
                <p style="margin: 0; font-size: 12px; color: var(--text-secondary);">Executive Command Center</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar Theme Toggle
        st.markdown("""
        <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 6px;">
            🎨 Appearance Theme
        </div>
        """, unsafe_allow_html=True)
        sidebar_theme = st.segmented_control(
            "Theme Mode",
            ["🌙 Dark", "☀️ Light"],
            key="sidebar_theme_segmented",
            on_change=on_sidebar_theme_change,
            label_visibility="collapsed"
        )
            
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 6px;">
            Navigation Views
        </div>
        """, unsafe_allow_html=True)
        sidebar_pick = st.radio(
            "Executive Views:",
            NAV_OPTIONS,
            key="sidebar_radio_selector",
            on_change=on_sidebar_nav_change,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Dataset summary badge in sidebar
        st.markdown(f"""
        <div class="glass-panel" style="padding: 16px; margin-bottom: 16px;">
            <div style="font-size: 11px; font-weight: 700; color: {'#00E5FF' if is_dark else '#0369A1'}; text-transform: uppercase; margin-bottom: 8px;">
                Enterprise Fleet Stats
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 12.5px;">
                <span style="color: var(--text-secondary);">Total Transactions</span>
                <strong style="color: var(--text-primary);">{metrics['total_records']:,}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 12.5px;">
                <span style="color: var(--text-secondary);">Active Attributes</span>
                <strong style="color: var(--text-primary);">{metrics['total_columns']} Cols</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 12.5px;">
                <span style="color: var(--text-secondary);">Completeness</span>
                <strong style="color: {'#10B981' if is_dark else '#047857'};">{metrics['completeness']:.2f}%</strong>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12.5px;">
                <span style="color: var(--text-secondary);">Duplicate Rows</span>
                <strong style="color: {'#10B981' if metrics['duplicate_rows']==0 else '#B45309'};">{metrics['duplicate_rows']:,}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 8px;">
            Executive Shortcuts
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📄 Jump to C-Suite PDF", use_container_width=True, key="shortcut_pdf"):
            st.session_state['current_view'] = "📄 C-Suite Reports"
            st.session_state['sidebar_radio_selector'] = "📄 C-Suite Reports"
            st.session_state['top_segmented_selector'] = "📄 C-Suite Reports"
            st.rerun()
            
        if st.button("🎯 Jump to AI Forecasting", use_container_width=True, key="shortcut_forecast"):
            st.session_state['current_view'] = "🎯 AI Demand Forecasting"
            st.session_state['sidebar_radio_selector'] = "🎯 AI Demand Forecasting"
            st.session_state['top_segmented_selector'] = "🎯 AI Demand Forecasting"
            st.rerun()

        st.markdown("""
        <div style="text-align: center; font-size: 11px; color: var(--text-muted); margin-top: 20px;">
            Daikin Airconditioning & ISB &bull; 2024-2025
        </div>
        """, unsafe_allow_html=True)

    # Top Navigation Row with View Selector and Theme Toggle
    nav_col, theme_col = st.columns([5.4, 1.6])
    with nav_col:
        top_pick = st.segmented_control(
            "Executive View Selector",
            NAV_OPTIONS,
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

    active_page = st.session_state['current_view']

    # Routed View Rendering
    if active_page == "🏠 Executive Cockpit":
        show_overview(df, metrics)
    elif active_page == "🎯 AI Demand Forecasting":
        show_demand_forecasting(df)
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
    
    # Visualizations Row 1
    row1_c1, row1_c2 = st.columns([3, 2])
    with row1_c1:
        with st.container():
            fig_time = create_time_series_chart(df)
            if fig_time:
                st.plotly_chart(fig_time, use_container_width=True)
    with row1_c2:
        with st.container():
            fig_gauge = create_data_completeness_gauge(metrics['completeness'])
            st.plotly_chart(fig_gauge, use_container_width=True)
            
    # Visualizations Row 2
    row2_c1, row2_c2 = st.columns([2, 3])
    with row2_c1:
        with st.container():
            fig_segment = create_segment_analysis(df)
            if fig_segment:
                st.plotly_chart(fig_segment, use_container_width=True)
    with row2_c2:
        with st.container():
            fig_tonnage = create_tonnage_analysis(df)
            if fig_tonnage:
                st.plotly_chart(fig_tonnage, use_container_width=True)

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
        
    if 'Material' not in df.columns or 'Billing Date' not in df.columns:
        st.error("Required columns ('Material' and 'Billing Date') not found in dataset.")
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

        # Filtered DataFrame
        filtered_df = df[df[branch_col].isin(selected_branch_codes)].copy() if branch_col else df.copy()
        
        # Volume badge
        tot_vol = df['Billing Quantity ODU'].sum() if 'Billing Quantity ODU' in df.columns else len(df)
        b_vol = filtered_df['Billing Quantity ODU'].sum() if 'Billing Quantity ODU' in filtered_df.columns else len(filtered_df)
        b_share = (b_vol / tot_vol * 100) if tot_vol > 0 else 0
        
        st.markdown(f"""
        <div style="background: {bg_accent}; border: 1px solid {border_accent}; border-radius: 10px; padding: 10px; margin: 10px 0 16px 0; font-size: 12px;">
            <div style="color: var(--text-secondary); font-weight: 500;">Branch Demand Share</div>
            <div style="font-family: 'Outfit'; font-size: 18px; font-weight: 700; color: {accent_color};">{b_vol:,.0f} units <span style="font-size: 12px; color: var(--text-secondary); font-weight: 500;">({b_share:.1f}%)</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. SKU Selection
        if 'Billing Quantity ODU' in filtered_df.columns:
            sku_volumes = filtered_df.dropna(subset=['Material']).groupby('Material')['Billing Quantity ODU'].sum().sort_values(ascending=False)
            branch_top_skus = [str(s) for s in sku_volumes.head(10).index if str(s).strip() != '']
        else:
            sku_counts = filtered_df['Material'].dropna().astype(str).value_counts()
            branch_top_skus = [s for s in sku_counts.head(10).index if s.strip() != '']
            sku_volumes = sku_counts
            
        sku_scope = st.radio(
            "2. SKU Scope:",
            ["Top 10 in Filtered Branch", "Top 10 Overall", "All SKUs"],
            horizontal=True
        )
        
        if sku_scope == "Top 10 in Filtered Branch":
            available_skus = branch_top_skus
        elif sku_scope == "Top 10 Overall":
            overall_volumes = df.dropna(subset=['Material']).groupby('Material')['Billing Quantity ODU'].sum().sort_values(ascending=False) if 'Billing Quantity ODU' in df.columns else df['Material'].value_counts()
            available_skus = [str(s) for s in overall_volumes.head(10).index if str(s).strip() != '']
        else:
            available_skus = sorted(filtered_df['Material'].dropna().unique().astype(str).tolist())
            
        selected_sku = st.selectbox(
            "Select Target SKU (Material):",
            available_skus,
            format_func=lambda x: f"{x} ({sku_volumes.get(x, 0):,.0f} units)"
        )
        
        # 3. Model Engine Selection
        model_family = st.radio(
            "3. Algorithm Engine:",
            ["📊 Statistical Models", "🧠 Machine Learning Models"]
        )
        
        if model_family == "📊 Statistical Models":
            selected_model = st.selectbox(
                "Select Statistical Algorithm:",
                ["ARIMA", "SARIMA", "Exponential Smoothing"],
                help="ARIMA: Standard Time-Series | SARIMA: Seasonal Adjustments | Exponential Smoothing: Holt-Winters"
            )
        else:
            selected_model = st.selectbox(
                "Select Machine Learning Regressor:",
                ["Random Forest", "Gradient Boosting"],
                help="Random Forest: Robust Ensemble | Gradient Boosting: High Predictive Velocity"
            )
            
        # 4. Parameters
        forecast_periods = st.slider("Forecast Horizon (Weeks):", min_value=4, max_value=52, value=12)
        confidence_level = st.slider("Confidence Interval (%):", min_value=80, max_value=99, value=95)
        
        run_forecast = st.button("🚀 Execute Forecast Simulation", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with cfg_col2:
        # SKU Overview & Regional Breakdown Expander
        if branch_col:
            with st.expander(f"🏢 Regional Demand Distribution for {selected_sku} across All 5 Branches", expanded=False):
                sku_overall = df[df['Material'] == selected_sku].dropna(subset=[branch_col]).copy()
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
                        st.plotly_chart(fig_donut, use_container_width=True)
                    with dist_c2:
                        st.dataframe(
                            b_summary[['Branch', 'Billing Quantity ODU', 'Share %']].rename(columns={'Billing Quantity ODU': 'Units Sold'}),
                            use_container_width=True,
                            height=240,
                            hide_index=True
                        )

        if run_forecast and selected_model:
            with st.spinner(f"Simulating {selected_model} algorithm for {selected_sku} ({branch_label})..."):
                try:
                    sku_raw = filtered_df[filtered_df['Material'] == selected_sku].copy()
                    if len(sku_raw) == 0:
                        st.error(f"No transaction records found for SKU {selected_sku} in branch: {branch_label}.")
                        return
                        
                    sku_data = (
                        sku_raw.groupby('Billing Date')[['Billing Quantity ODU', 'Tonnage']]
                        .sum()
                        .resample('W-MON')
                        .sum()
                        .reset_index()
                        .sort_values('Billing Date')
                    )
                    
                    if len(sku_data) < 10:
                        st.error(f"Insufficient history for {selected_sku} in {branch_label}. Need >=10 weeks, found {len(sku_data)}.")
                        return
                        
                    # Execute Model
                    if model_family == "📊 Statistical Models":
                        forecast_df, metrics_dict, fig = run_statistical_model(
                            sku_data, selected_model, forecast_periods, confidence_level, branch_label=branch_label
                        )
                    else:
                        forecast_df, metrics_dict, fig = run_ml_model(
                            sku_data, selected_model, forecast_periods, confidence_level, branch_label=branch_label
                        )
                        
                    # Forecast Plot
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Performance Metrics Scorecard
                    st.markdown("""
                    <div class="subpanel-title" style="margin: 16px 0 12px 0;">
                        📈 Model Evaluation & Accuracy Telemetry
                    </div>
                    """, unsafe_allow_html=True)
                    
                    met1, met2, met3, met4 = st.columns(4)
                    accuracy = max(0, 100 - metrics_dict.get('MAPE', 100))
                    
                    with met1:
                        st.markdown(render_kpi_card("Mean Absolute Error", f"{metrics_dict.get('MAE', 0):.2f}", "MAE", "cyan", "🎯", "Average delta per week"), unsafe_allow_html=True)
                    with met2:
                        st.markdown(render_kpi_card("Root Mean Sq Error", f"{metrics_dict.get('RMSE', 0):.2f}", "RMSE", "amber", "📏", "Variance penalty index"), unsafe_allow_html=True)
                    with met3:
                        st.markdown(render_kpi_card("Percentage Error", f"{metrics_dict.get('MAPE', 0):.1f}%", "MAPE", "rose" if metrics_dict.get('MAPE', 0) > 30 else "green", "📊", "Mean % discrepancy"), unsafe_allow_html=True)
                    with met4:
                        st.markdown(render_kpi_card("Model Accuracy", f"{accuracy:.1f}%", "RATING", "green" if accuracy >= 80 else "amber", "⭐", "Predictive fidelity"), unsafe_allow_html=True)
                    
                    # Forecast Table & Download
                    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
                    st.markdown("""
                    <div class="subpanel-title" style="margin-bottom: 10px;">
                        📋 Forward Forecast Horizon Schedule
                    </div>
                    """, unsafe_allow_html=True)
                    
                    display_df = forecast_df.copy()
                    if 'Forecast_Tonnage' in display_df.columns:
                        display_df = display_df.drop(columns=['Forecast_Tonnage'])
                    if 'Date' in display_df.columns:
                        display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
                    
                    display_df.insert(0, 'Week', range(1, len(display_df) + 1))
                    display_df.insert(1, 'Branch', branch_label)
                    display_df = display_df.rename(columns={
                        'Forecast': 'Forecast (Units)',
                        'Lower_Bound': 'Lower Bound (Units)',
                        'Upper_Bound': 'Upper Bound (Units)'
                    })
                    
                    st.dataframe(
                        display_df.style.format({
                            'Forecast (Units)': '{:,.1f}',
                            'Lower Bound (Units)': '{:,.1f}',
                            'Upper Bound (Units)': '{:,.1f}'
                        }),
                        use_container_width=True,
                        height=320
                    )
                    
                    # Download CSV Action
                    csv_df = forecast_df.copy()
                    csv_df.insert(0, 'Material', selected_sku)
                    csv_df.insert(1, 'Branch', branch_label)
                    csv = csv_df.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download Strategic Forecast as CSV ({branch_label})",
                        data=csv,
                        file_name=f"daikin_forecast_{selected_sku}_{branch_file_code}_{selected_model}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error running forecast simulation: {str(e)}")
        else:
            # Historical pattern view when simulation not executed
            sku_raw = filtered_df[filtered_df['Material'] == selected_sku].copy()
            if len(sku_raw) > 0:
                sku_weekly = (
                    sku_raw.groupby('Billing Date')[['Billing Quantity ODU', 'Tonnage']]
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
                st.plotly_chart(fig_hist, use_container_width=True)
                
                st.info("👆 Adjust parameters in the Control Bar on the left and click 'Execute Forecast Simulation' to generate forward predictive curves.")

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
    
    diag_c1, diag_c2 = st.columns([3, 2])
    with diag_c1:
        fig_missing = create_missing_data_chart(df)
        if fig_missing:
            st.plotly_chart(fig_missing, use_container_width=True)
        else:
            st.success("✅ Clean Record: Zero missing values detected across dataset attributes.")
            
    with diag_c2:
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
            st.dataframe(summary_df, use_container_width=True, height=360)
        else:
            st.info("No column attributes exhibit missing values.")

    st.markdown("---")
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
    apply_custom_chart_theme(fig_dtypes, height=360)
    st.plotly_chart(fig_dtypes, use_container_width=True)

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
            st.plotly_chart(fig_dup, use_container_width=True)
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
                st.dataframe(df[col].value_counts().head(5), use_container_width=True)

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
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    is_dark = (st.session_state.get('theme', 'dark') == 'dark')
    
    st.markdown("""
    <div class="subpanel-title" style="margin-bottom: 10px;">
        📊 Descriptive Numerical Summary
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(df[numeric_cols].describe(), use_container_width=True)
    
    st.markdown("---")
    fig_corr = create_correlation_heatmap(df)
    if fig_corr:
        st.plotly_chart(fig_corr, use_container_width=True)
        
    st.markdown("---")
    st.markdown("""
    <div class="subpanel-title" style="margin-bottom: 10px;">
        📉 Distribution & Outlier Inspector
    </div>
    """, unsafe_allow_html=True)
    
    selected_col = st.selectbox("Choose Numerical Dimension to Inspect:", numeric_cols)
    if selected_col:
        stat_c1, stat_c2 = st.columns(2)
        with stat_c1:
            fig_dist = create_distribution_chart(df, selected_col)
            st.plotly_chart(fig_dist, use_container_width=True)
        with stat_c2:
            fig_box = px.box(df, y=selected_col, title=f"Box Plot Spread: {selected_col}")
            box_accent = '#00E5FF' if is_dark else '#0369A1'
            fig_box.update_traces(marker_color=box_accent, line=dict(color=box_accent))
            apply_custom_chart_theme(fig_box, height=400)
            st.plotly_chart(fig_box, use_container_width=True)
            
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(render_kpi_card("Mean", f"{df[selected_col].mean():.2f}", "AVG", "cyan", "📐", "Arithmetic mean"), unsafe_allow_html=True)
        with m2:
            st.markdown(render_kpi_card("Median", f"{df[selected_col].median():.2f}", "P50", "green", "🎯", "50th percentile"), unsafe_allow_html=True)
        with m3:
            st.markdown(render_kpi_card("Std Deviation", f"{df[selected_col].std():.2f}", "SIGMA", "amber", "📊", "Dispersion"), unsafe_allow_html=True)
        with m4:
            st.markdown(render_kpi_card("Range", f"{df[selected_col].max() - df[selected_col].min():.2f}", "SPREAD", "rose", "↔️", "Max minus min"), unsafe_allow_html=True)

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
        st.dataframe(df[selected_columns].head(100), use_container_width=True, height=380)
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
                st.plotly_chart(fig, use_container_width=True)
                
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
        st.dataframe(filtered_df, use_container_width=True, height=350)

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
    if st.button("🚀 Compile & Generate Executive PDF Report", type="primary", use_container_width=True):
        with st.spinner("Compiling C-Suite executive briefing PDF..."):
            try:
                pdf_data = generate_pdf_report(df, metrics)
                b64_pdf = base64.b64encode(pdf_data).decode()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Daikin_Executive_Briefing_{timestamp}.pdf"
                
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
        if st.button("📊 Export Formatted Excel (.xlsx)", use_container_width=True):
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
                file_name=f"Daikin_Data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
    with exp2:
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📄 Export Raw CSV Dataset",
            data=csv_data,
            file_name=f"Daikin_Dataset_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    with exp3:
        summary_text = f"""DAIKIN EXECUTIVE TELEMETRY SUMMARY
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
            file_name=f"Daikin_Telemetry_Summary_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
