"""
Generate Executive QC Story (8-Step A3 One-Slider) Presentation
Matches the user's uploaded QC STORY format exactly:
- Header: QC STORY / SMALL STEPS BIG IMPACT / Metadata / Quote
- Step 1: THEME / PROBLEM STATEMENT (with vector bullseye)
- Step 2: CURRENT SITUATION (AS-IS) (with mini seasonal demand chart)
- Step 3: TARGET (GOAL) (with target icon and goal callout)
- Step 4: ROOT CAUSE ANALYSIS (with authentic vector Fishbone diagram + Verification table)
- Step 5: COUNTERMEASURE (Structured table + Checklist)
- Step 6: IMPLEMENTATION (Before vs After visual comparison)
- Step 7: RESULTS & IMPACT (Comparison table + 71.8% Impact badge)
- Step 8: STANDARDIZATION, FUTURE SCOPE & HORIZONTAL DEPLOYMENT with:
    * FUTURE SCOPE 1: Dynamic Stock Transfer-In & Transfer-Out Optimization (Inter-Branch Balancing)
    * FUTURE SCOPE 2: Local News & Real-Time AI Market Intelligence Integration
- Footer: Continuous Supply Chain Intelligence banner
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# ==============================================================================
# COLOR PALETTE (Matching the uploaded QC Story template)
# ==============================================================================
C_BG_SLIDE       = RGBColor(248, 250, 252) # Crisp off-white background
C_CARD_BG        = RGBColor(255, 255, 255) # Pure white card containers
C_CARD_BORDER    = RGBColor(203, 213, 225) # Crisp light slate border
C_NAVY_HEADER    = RGBColor(30, 58, 95)    # QC Story deep navy banner
C_NAVY_TEXT      = RGBColor(15, 23, 42)    # Dark slate primary text
C_MUTED_TEXT     = RGBColor(71, 85, 105)   # Muted gray body text
C_WHITE          = RGBColor(255, 255, 255)

# Step Header Colors (Matching uploaded picture)
C_STEP1_BLUE     = RGBColor(43, 76, 126)   # 1 Theme / Problem Statement
C_STEP2_GREEN    = RGBColor(46, 105, 48)   # 2 Current Situation (As-Is)
C_STEP3_AMBER    = RGBColor(217, 119, 6)   # 3 Target (Goal)
C_STEP4_RED      = RGBColor(197, 48, 48)   # 4 Root Cause Analysis
C_STEP5_PURPLE   = RGBColor(107, 70, 193)  # 5 Countermeasure
C_STEP6_TEAL     = RGBColor(13, 148, 136)  # 6 Implementation
C_STEP7_LEAF     = RGBColor(22, 163, 74)   # 7 Results
C_STEP8_SLATE    = RGBColor(59, 89, 152)   # 8 Standardization & Deployment

# Future Scope Highlights
C_FUTURE_CYAN    = RGBColor(2, 132, 199)   # Transfer In / Transfer Out
C_FUTURE_PURPLE  = RGBColor(124, 58, 237)  # Local News AI Integration
C_ACCENT_BG_CYAN = RGBColor(240, 249, 255)
C_ACCENT_BG_PURP = RGBColor(245, 243, 255)

def create_qc_story_presentation():
    prs = Presentation()
    prs.slide_width = Inches(20.0)
    prs.slide_height = Inches(11.25)
    slide = prs.slides.add_slide(prs.slide_layouts[6]) # blank layout

    # Background
    bg = slide.background
    bg_fill = bg.fill
    bg_fill.solid()
    bg_fill.fore_color.rgb = C_BG_SLIDE

    # ==========================================================================
    # HELPER FUNCTIONS
    # ==========================================================================
    def add_card(left, top, width, height, bg_color=C_CARD_BG, border_color=C_CARD_BORDER, border_w=1.0):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(border_w)
        return shape

    def add_step_header(left, top, width, height, step_num, title, color):
        hdr = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        hdr.fill.solid()
        hdr.fill.fore_color.rgb = color
        hdr.line.fill.background()
        tf = hdr.text_frame
        tf.word_wrap = False
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = Inches(0.12)
        tf.margin_top = Inches(0.0)
        tf.margin_right = Inches(0.05)
        tf.margin_bottom = Inches(0.0)
        p = tf.paragraphs[0]
        p.text = f"{step_num}   {title.upper()}"
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.color.rgb = C_WHITE
        p.alignment = PP_ALIGN.LEFT
        return hdr

    def add_styled_text(left, top, width, height, margin=0.06):
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(margin)
        tf.margin_top = Inches(margin)
        tf.margin_right = Inches(margin)
        tf.margin_bottom = Inches(margin)
        return tf

    def draw_bullseye(cx, cy, r_outer=0.32):
        # Outer ring
        c1 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r_outer), Inches(cy - r_outer), Inches(r_outer * 2), Inches(r_outer * 2))
        c1.fill.solid(); c1.fill.fore_color.rgb = RGBColor(220, 38, 38); c1.line.fill.background()
        # White ring
        r2 = r_outer * 0.72
        c2 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r2), Inches(cy - r2), Inches(r2 * 2), Inches(r2 * 2))
        c2.fill.solid(); c2.fill.fore_color.rgb = C_WHITE; c2.line.fill.background()
        # Middle ring
        r3 = r_outer * 0.46
        c3 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r3), Inches(cy - r3), Inches(r3 * 2), Inches(r3 * 2))
        c3.fill.solid(); c3.fill.fore_color.rgb = RGBColor(220, 38, 38); c3.line.fill.background()
        # Center dot
        r4 = r_outer * 0.22
        c4 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r4), Inches(cy - r4), Inches(r4 * 2), Inches(r4 * 2))
        c4.fill.solid(); c4.fill.fore_color.rgb = C_WHITE; c4.line.fill.background()

    # ==========================================================================
    # TOP HEADER AREA (QC STORY Banner + Quote + Metadata)
    # ==========================================================================
    hdr_top = 0.30
    hdr_height = 1.05

    # 1. Left QC STORY Brand Banner
    add_card(0.40, hdr_top, 8.80, hdr_height, bg_color=C_NAVY_HEADER, border_color=C_NAVY_HEADER)
    tf_qc = add_styled_text(0.55, hdr_top + 0.05, 8.50, 0.95)
    
    p = tf_qc.paragraphs[0]
    p.text = "QC STORY"
    p.font.size = Pt(30)
    p.font.bold = True
    p.font.color.rgb = C_WHITE

    p2 = tf_qc.add_paragraph()
    r1 = p2.add_run()
    r1.text = "SMALL STEPS, BIG IMPACT  •  "
    r1.font.size = Pt(11.5)
    r1.font.bold = True
    r1.font.color.rgb = RGBColor(56, 189, 248) # Cyan

    r2 = p2.add_run()
    r2.text = "AI Demand Forecasting & Dynamic Inventory Optimization"
    r2.font.size = Pt(11.5)
    r2.font.color.rgb = RGBColor(224, 231, 255)

    # 2. Middle Quote Box
    add_card(9.35, hdr_top, 4.80, hdr_height, bg_color=RGBColor(240, 249, 255), border_color=RGBColor(186, 230, 253))
    tf_q = add_styled_text(9.45, hdr_top + 0.08, 4.60, 0.90)
    pq = tf_q.paragraphs[0]
    pq.text = '"Predictive Precision Today, Resilient Supply Chain Tomorrow"'
    pq.font.size = Pt(10.5)
    pq.font.italic = True
    pq.font.bold = True
    pq.font.color.rgb = RGBColor(2, 132, 199)
    pq.alignment = PP_ALIGN.CENTER

    pq2 = tf_q.add_paragraph()
    pq2.text = "ISB AMPBA Capstone Project with Deloitte  |  Commercial Air Conditioning"
    pq2.font.size = Pt(8.5)
    pq2.font.color.rgb = RGBColor(71, 85, 105)
    pq2.alignment = PP_ALIGN.CENTER

    # Mini Trend graphic inside quote box
    bar_x = 11.2
    bar_y = hdr_top + 0.65
    bar_colors = [RGBColor(147, 197, 253), RGBColor(96, 165, 250), RGBColor(59, 130, 246), RGBColor(37, 99, 235)]
    for idx, h in enumerate([0.12, 0.18, 0.24, 0.30]):
        b = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(bar_x + idx * 0.12), Inches(bar_y + (0.30 - h)), Inches(0.08), Inches(h))
        b.fill.solid()
        b.fill.fore_color.rgb = bar_colors[idx]
        b.line.fill.background()

    # 3. Far-right Metadata Box
    add_card(14.30, hdr_top, 5.30, hdr_height, bg_color=RGBColor(255, 255, 255), border_color=C_CARD_BORDER)
    tf_m = add_styled_text(14.45, hdr_top + 0.05, 5.00, 0.95)
    
    pm1 = tf_m.paragraphs[0]
    r = pm1.add_run(); r.text = "Team Name  : "; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = C_NAVY_TEXT
    r = pm1.add_run(); r.text = "ISB Capstone Team (Sai Prashanth, Arvind, Hariharan, Vani, Vedika)"; r.font.size = Pt(9.0); r.font.color.rgb = C_MUTED_TEXT

    pm2 = tf_m.add_paragraph()
    r = pm2.add_run(); r.text = "Sponsor      : "; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = C_NAVY_TEXT
    r = pm2.add_run(); r.text = "Deloitte  |  Department: Supply Chain & Analytics"; r.font.size = Pt(9.0); r.font.color.rgb = C_MUTED_TEXT

    pm3 = tf_m.add_paragraph()
    r = pm3.add_run(); r.text = "Evaluation   : "; r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = C_NAVY_TEXT
    r = pm3.add_run(); r.text = "FY24-25 Holdout Validated (444K units) | 14/14 Audits Passed"; r.font.size = Pt(9.0); r.font.color.rgb = RGBColor(16, 185, 129); r.font.bold = True

    # ==========================================================================
    # ROW 1: STEPS 1, 2, 3
    # ==========================================================================
    r1_top = 1.45
    r1_h = 2.40

    # --------------------------------------------------------------------------
    # STEP 1: THEME / PROBLEM STATEMENT
    # --------------------------------------------------------------------------
    s1_left, s1_w = 0.40, 5.60
    add_card(s1_left, r1_top, s1_w, r1_h)
    add_step_header(s1_left, r1_top, s1_w, 0.32, "1", "THEME / PROBLEM STATEMENT", C_STEP1_BLUE)

    # Bullseye Target Vector Icon
    draw_bullseye(s1_left + 0.50, r1_top + 0.82, r_outer=0.32)

    tf_s1 = add_styled_text(s1_left + 0.95, r1_top + 0.36, s1_w - 1.05, r1_h - 0.40)
    
    def add_field(tf, label, val, is_bold=False, color=C_MUTED_TEXT):
        p = tf.add_paragraph() if len(tf.paragraphs[0].text) > 0 else tf.paragraphs[0]
        r1 = p.add_run(); r1.text = label + " : "; r1.font.bold = True; r1.font.size = Pt(9.0); r1.font.color.rgb = C_NAVY_TEXT
        r2 = p.add_run(); r2.text = val; r2.font.bold = is_bold; r2.font.size = Pt(9.0); r2.font.color.rgb = color

    add_field(tf_s1, "Title", "AI SKU Demand Forecasting & Safety Stock Sizing", is_bold=True, color=C_STEP1_BLUE)
    add_field(tf_s1, "Process/Line", "Commercial Room AC (RA-ODU) Supply Chain — 5 South Hubs")
    add_field(tf_s1, "Problem", "97.1% volatile/lumpy demand & acute Q4 summer surge cause severe stockouts and massive post-season dead-stock under legacy 8-wk moving average.")
    add_field(tf_s1, "Period", "Jul 2021 – Jun 2024 (Training) to FY25 (Holdout Validation)", color=RGBColor(30, 64, 175))

    # --------------------------------------------------------------------------
    # STEP 2: CURRENT SITUATION (AS-IS)
    # --------------------------------------------------------------------------
    s2_left, s2_w = 6.15, 7.50
    add_card(s2_left, r1_top, s2_w, r1_h)
    add_step_header(s2_left, r1_top, s2_w, 0.32, "2", "CURRENT SITUATION (AS-IS)", C_STEP2_GREEN)

    # Bullet observations
    tf_s2_obs = add_styled_text(s2_left + 0.10, r1_top + 0.35, s2_w - 0.20, 0.70)
    p = tf_s2_obs.paragraphs[0]
    p.text = "• What is happening? Acute demand lumpiness (45% annual sales in 10 summer weeks); legacy MA ignores seasonality."
    p.font.size = Pt(8.5); p.font.color.rgb = C_NAVY_TEXT
    
    p2 = tf_s2_obs.add_paragraph()
    p2.text = "• Where is it occurring? 5 South Hubs: Chennai (MAA 36.7%), Hyderabad (SBD/SBD1 43.4%), Cochin (COK 10%), Bangalore (BLR 9.9%)."
    p2.font.size = Pt(8.5); p2.font.color.rgb = C_NAVY_TEXT

    p3 = tf_s2_obs.add_paragraph()
    p3.text = "• Scale: 99,395 real billing transactions across 240 active ODU SKUs and 1,038 billing days analyzed."
    p3.font.size = Pt(8.5); p3.font.color.rgb = C_NAVY_TEXT

    # Table: Current Status
    tbl_s2 = slide.shapes.add_table(4, 2, Inches(s2_left + 0.15), Inches(r1_top + 1.12), Inches(4.70), Inches(1.15)).table
    tbl_s2.columns[0].width = Inches(1.50)
    tbl_s2.columns[1].width = Inches(3.20)

    rows_s2 = [
        ("Demand Pattern", "97.1% Volatile (62.3% Erratic, 34.8% Lumpy by Syntetos-Boylan)"),
        ("Legacy Forecast", "Static 8-week Moving Average (~50% weekly WAPE error)"),
        ("Working Capital", "Excess safety stocks tying up ~20% unneeded buffer capital"),
        ("Stockout Risk", "Recurrent peak stockouts on fast-moving 1.5T/2.0T high-margin SKUs")
    ]
    for r_idx, (it, st) in enumerate(rows_s2):
        cell_0 = tbl_s2.cell(r_idx, 0)
        cell_1 = tbl_s2.cell(r_idx, 1)
        cell_0.text = it; cell_1.text = st
        cell_0.fill.solid(); cell_0.fill.fore_color.rgb = RGBColor(241, 245, 249) if r_idx % 2 == 0 else C_WHITE
        cell_1.fill.solid(); cell_1.fill.fore_color.rgb = RGBColor(241, 245, 249) if r_idx % 2 == 0 else C_WHITE
        
        for c in (cell_0, cell_1):
            c.margin_left = Inches(0.06); c.margin_right = Inches(0.06)
            c.margin_top = Inches(0.02); c.margin_bottom = Inches(0.02)
        p0 = cell_0.text_frame.paragraphs[0]; p0.font.bold = True; p0.font.size = Pt(8.0); p0.font.color.rgb = C_NAVY_TEXT
        p1 = cell_1.text_frame.paragraphs[0]; p1.font.size = Pt(8.0); p1.font.color.rgb = C_MUTED_TEXT

    # Mini As-Is Visual Graph Box with custom vector bars
    g_left, g_top, g_w, g_h = s2_left + 5.00, r1_top + 1.12, 2.35, 1.15
    add_card(g_left, g_top, g_w, g_h, bg_color=RGBColor(248, 250, 252), border_color=RGBColor(203, 213, 225))
    
    tf_ghead = add_styled_text(g_left + 0.05, g_top + 0.04, g_w - 0.10, 0.25)
    p = tf_ghead.paragraphs[0]
    p.text = "Summer Peak Surge (As-Is)"
    p.font.bold = True; p.font.size = Pt(8.0); p.font.color.rgb = C_STEP2_GREEN; p.alignment = PP_ALIGN.CENTER

    # Draw 4 quarterly bars
    q_bars = [
        ("Q1 (Off)", 0.20, RGBColor(148, 163, 184)),
        ("Q2 (Low)", 0.25, RGBColor(148, 163, 184)),
        ("Q3 (Pre)", 0.38, RGBColor(251, 146, 60)),
        ("Q4 (Peak)", 0.75, RGBColor(220, 38, 38))
    ]
    bar_base_y = g_top + 0.95
    b_w = 0.36
    for b_idx, (q_lbl, q_h, q_col) in enumerate(q_bars):
        bx = g_left + 0.25 + b_idx * 0.48
        by = bar_base_y - q_h
        b_shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(bx), Inches(by), Inches(b_w), Inches(q_h))
        b_shp.fill.solid(); b_shp.fill.fore_color.rgb = q_col
        b_shp.line.fill.background()
        
        lbl_box = slide.shapes.add_textbox(Inches(bx - 0.08), Inches(bar_base_y + 0.02), Inches(b_w + 0.16), Inches(0.18))
        tf_lbl = lbl_box.text_frame
        tf_lbl.margin_left = tf_lbl.margin_right = tf_lbl.margin_top = tf_lbl.margin_bottom = 0
        p = tf_lbl.paragraphs[0]
        p.text = q_lbl.split()[0]
        p.font.size = Pt(6.5); p.font.color.rgb = C_NAVY_TEXT; p.alignment = PP_ALIGN.CENTER

    # --------------------------------------------------------------------------
    # STEP 3: TARGET (GOAL)
    # --------------------------------------------------------------------------
    s3_left, s3_w = 13.80, 5.80
    add_card(s3_left, r1_top, s3_w, r1_h)
    add_step_header(s3_left, r1_top, s3_w, 0.32, "3", "TARGET (GOAL)", C_STEP3_AMBER)

    tf_s3 = add_styled_text(s3_left + 0.15, r1_top + 0.38, 3.40, r1_h - 0.45)
    p = tf_s3.paragraphs[0]
    p.text = "Target Statement:"
    p.font.bold = True; p.font.size = Pt(9.5); p.font.color.rgb = C_NAVY_TEXT

    p = tf_s3.add_paragraph()
    p.text = "Deploy multi-model AI forecasting engine to minimize forecast error and optimize safety stock buffers."
    p.font.size = Pt(8.5); p.font.color.rgb = C_MUTED_TEXT

    add_field(tf_s3, "Reduce", "WAPE Forecast Error & Excess Buffer")
    add_field(tf_s3, "From", "Legacy MA (~50-60% weekly error)")
    add_field(tf_s3, "To", "Monthly WAPE <=34.4% (Acc >=65.6%), Qtr Acc >=71.8%", is_bold=True, color=RGBColor(180, 83, 9))
    add_field(tf_s3, "By Date", "FY25 Holdout Deployment", is_bold=True, color=C_NAVY_TEXT)

    # Goal Callout Badge
    add_card(s3_left + 3.70, r1_top + 0.45, 1.95, 1.80, bg_color=RGBColor(254, 243, 199), border_color=RGBColor(245, 158, 11), border_w=1.5)
    tf_goal = add_styled_text(s3_left + 3.75, r1_top + 0.50, 1.85, 1.70)
    p = tf_goal.paragraphs[0]
    p.text = "🎯 GOAL"
    p.font.bold = True; p.font.size = Pt(13); p.font.color.rgb = RGBColor(180, 83, 9); p.alignment = PP_ALIGN.CENTER
    
    p = tf_goal.add_paragraph()
    p.text = "Leaner Inventory\nZero Stockouts\nHappier Customers"
    p.font.bold = True; p.font.size = Pt(9.5); p.font.color.rgb = C_NAVY_TEXT; p.alignment = PP_ALIGN.CENTER

    p = tf_goal.add_paragraph()
    p.text = "\n✓ 71.8% Regional Acc\n✓ ~20% Buffer Cut\n✓ >=95% OTIF Fill"
    p.font.bold = True; p.font.size = Pt(8.0); p.font.color.rgb = RGBColor(4, 120, 87); p.alignment = PP_ALIGN.CENTER

    # ==========================================================================
    # ROW 2: STEPS 4, 5
    # ==========================================================================
    r2_top = 3.98
    r2_h = 2.42

    # --------------------------------------------------------------------------
    # STEP 4: ROOT CAUSE ANALYSIS (Fishbone + Verification)
    # --------------------------------------------------------------------------
    s4_left, s4_w = 0.40, 8.80
    add_card(s4_left, r2_top, s4_w, r2_h)
    add_step_header(s4_left, r2_top, s4_w, 0.32, "4", "ROOT CAUSE ANALYSIS  (Why-Why / Fishbone)", C_STEP4_RED)

    # Authentic Fishbone Diagram (Left Half)
    fb_cx = s4_left + 0.20
    fb_cy = r2_top + 0.38
    
    # 1. Main horizontal spine
    spine = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(fb_cx + 0.10), Inches(fb_cy + 0.70), Inches(2.95), Inches(0.04))
    spine.fill.solid(); spine.fill.fore_color.rgb = C_STEP4_RED; spine.line.fill.background()

    # Problem Box at right end of spine
    prob_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(fb_cx + 3.05), Inches(fb_cy + 0.48), Inches(1.30), Inches(0.48))
    prob_box.fill.solid(); prob_box.fill.fore_color.rgb = RGBColor(254, 226, 226)
    prob_box.line.color.rgb = C_STEP4_RED; prob_box.line.width = Pt(1.5)
    tf_pb = prob_box.text_frame
    tf_pb.word_wrap = True
    tf_pb.margin_left = tf_pb.margin_right = tf_pb.margin_top = tf_pb.margin_bottom = Inches(0.02)
    p = tf_pb.paragraphs[0]
    p.text = "Inaccurate Demand & Stock Imbalance"
    p.font.bold = True; p.font.size = Pt(7.5); p.font.color.rgb = C_STEP4_RED; p.alignment = PP_ALIGN.CENTER

    # Upper Ribs (Method, Machine, Measurement)
    upper_bones = [
        ("Method", 0.30),
        ("Machine", 1.30),
        ("Measurement", 2.30)
    ]
    for lbl, x_top in upper_bones:
        b_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(fb_cx + x_top + 0.25), Inches(fb_cy + 0.36), Inches(0.35), Inches(0.02))
        b_line.fill.solid(); b_line.fill.fore_color.rgb = RGBColor(239, 68, 68); b_line.line.fill.background()
        b_line.rotation = 45

        cat_b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(fb_cx + x_top - 0.15), Inches(fb_cy + 0.05), Inches(0.85), Inches(0.28))
        cat_b.fill.solid(); cat_b.fill.fore_color.rgb = RGBColor(241, 245, 249)
        cat_b.line.color.rgb = RGBColor(203, 213, 225); cat_b.line.width = Pt(1.0)
        tf_cb = cat_b.text_frame; tf_cb.word_wrap = True; tf_cb.margin_left = tf_cb.margin_right = tf_cb.margin_top = tf_cb.margin_bottom = 0
        p = tf_cb.paragraphs[0]; p.text = lbl; p.font.bold = True; p.font.size = Pt(7.0); p.font.color.rgb = C_NAVY_TEXT; p.alignment = PP_ALIGN.CENTER

    # Lower Ribs (Material, Environment, Management)
    lower_bones = [
        ("Material", 0.30),
        ("Environment", 1.30),
        ("Management", 2.30)
    ]
    for lbl, x_top in lower_bones:
        b_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(fb_cx + x_top + 0.25), Inches(fb_cy + 1.05), Inches(0.35), Inches(0.02))
        b_line.fill.solid(); b_line.fill.fore_color.rgb = RGBColor(239, 68, 68); b_line.line.fill.background()
        b_line.rotation = 135

        cat_b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(fb_cx + x_top - 0.15), Inches(fb_cy + 1.15), Inches(0.85), Inches(0.28))
        cat_b.fill.solid(); cat_b.fill.fore_color.rgb = RGBColor(241, 245, 249)
        cat_b.line.color.rgb = RGBColor(203, 213, 225); cat_b.line.width = Pt(1.0)
        tf_cb = cat_b.text_frame; tf_cb.word_wrap = True; tf_cb.margin_left = tf_cb.margin_right = tf_cb.margin_top = tf_cb.margin_bottom = 0
        p = tf_cb.paragraphs[0]; p.text = lbl; p.font.bold = True; p.font.size = Pt(7.0); p.font.color.rgb = C_NAVY_TEXT; p.alignment = PP_ALIGN.CENTER

    # Right: Verification Table
    tbl_s4 = slide.shapes.add_table(4, 3, Inches(s4_left + 4.60), Inches(r2_top + 0.38), Inches(4.05), Inches(1.45)).table
    tbl_s4.columns[0].width = Inches(1.85)
    tbl_s4.columns[1].width = Inches(1.45)
    tbl_s4.columns[2].width = Inches(0.75)

    headers_s4 = [("Potential Cause", "Verification", "Root Cause")]
    rows_s4 = [
        ("Static Moving Average", "52-wk holdout backtest", "YES (Y)"),
        ("No Demand Profiling", "Syntetos-Boylan test", "YES (Y)"),
        ("Isolated Single Series", "LightGBM cross-learning", "YES (Y)")
    ]
    for c_i, h_txt in enumerate(headers_s4[0]):
        cell = tbl_s4.cell(0, c_i)
        cell.text = h_txt
        cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(254, 226, 226)
        cell.margin_left = Inches(0.04); cell.margin_right = Inches(0.04)
        p = cell.text_frame.paragraphs[0]; p.font.bold = True; p.font.size = Pt(7.5); p.font.color.rgb = C_STEP4_RED

    for r_i, (c_pot, c_ver, c_rc) in enumerate(rows_s4):
        for c_i, val in enumerate((c_pot, c_ver, c_rc)):
            cell = tbl_s4.cell(r_i + 1, c_i)
            cell.text = val
            cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if r_i % 2 == 0 else C_WHITE
            cell.margin_left = Inches(0.04); cell.margin_right = Inches(0.04)
            p = cell.text_frame.paragraphs[0]; p.font.size = Pt(7.5); p.font.color.rgb = C_NAVY_TEXT
            if c_i == 2:
                p.font.bold = True; p.font.color.rgb = C_STEP4_RED; p.alignment = PP_ALIGN.CENTER

    # Identified Root Cause Footer Box
    add_card(s4_left + 0.12, r2_top + 1.90, s4_w - 0.24, 0.44, bg_color=RGBColor(254, 242, 242), border_color=RGBColor(252, 165, 165))
    tf_rc = add_styled_text(s4_left + 0.18, r2_top + 1.92, s4_w - 0.36, 0.40)
    p = tf_rc.paragraphs[0]
    r1 = p.add_run(); r1.text = "Root Cause Identified: "; r1.font.bold = True; r1.font.size = Pt(8.5); r1.font.color.rgb = C_STEP4_RED
    r2 = p.add_run(); r2.text = "Isolated single-series statistical rules cannot learn cross-SKU dynamics or adapt to extreme lumpy intermittency without machine learning and demand quadrant segmentation."; r2.font.size = Pt(8.0); r2.font.color.rgb = C_NAVY_TEXT

    # --------------------------------------------------------------------------
    # STEP 5: COUNTERMEASURE
    # --------------------------------------------------------------------------
    s5_left, s5_w = 9.35, 10.25
    add_card(s5_left, r2_top, s5_w, r2_h)
    add_step_header(s5_left, r2_top, s5_w, 0.32, "5", "COUNTERMEASURE", C_STEP5_PURPLE)

    # Countermeasure Table
    tbl_s5 = slide.shapes.add_table(5, 4, Inches(s5_left + 0.15), Inches(r2_top + 0.38), Inches(8.10), Inches(1.92)).table
    tbl_s5.columns[0].width = Inches(2.20)
    tbl_s5.columns[1].width = Inches(3.70)
    tbl_s5.columns[2].width = Inches(1.10)
    tbl_s5.columns[3].width = Inches(1.10)

    hdr_s5 = ("Root Cause", "Action Planned / Countermeasure", "Responsibility", "Due / Status")
    for c_i, h_txt in enumerate(hdr_s5):
        cell = tbl_s5.cell(0, c_i)
        cell.text = h_txt
        cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(243, 232, 255)
        cell.margin_left = Inches(0.05); cell.margin_right = Inches(0.05)
        p = cell.text_frame.paragraphs[0]; p.font.bold = True; p.font.size = Pt(8.0); p.font.color.rgb = C_STEP5_PURPLE

    rows_s5 = [
        ("Lumpy Intermittency", "Syntetos-Boylan demand quadrant classification (Smooth, Erratic, Lumpy, Intermittent)", "Data Science", "Completed"),
        ("Single-Series Limits", "17-Model Tournament: Global LightGBM cross-learning, SARIMA, ETS, Croston/TSB/SBA", "ML Team", "Completed"),
        ("Overfitting Risk", "Strict 52-week rolling-origin holdout backtesting; zero lookahead data leakage", "Validation Lead", "14/14 Passed"),
        ("Planner Operational Gap", "7-Page Interactive Streamlit Cockpit with live forecasting, P10/P90 & report exports", "Product Lead", "Live Deployed")
    ]
    for r_i, row in enumerate(rows_s5):
        for c_i, val in enumerate(row):
            cell = tbl_s5.cell(r_i + 1, c_i)
            cell.text = val
            cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if r_i % 2 == 0 else C_WHITE
            cell.margin_left = Inches(0.05); cell.margin_right = Inches(0.05)
            p = cell.text_frame.paragraphs[0]; p.font.size = Pt(7.5); p.font.color.rgb = C_NAVY_TEXT
            if c_i == 3:
                p.font.bold = True; p.font.color.rgb = RGBColor(16, 185, 129); p.alignment = PP_ALIGN.CENTER

    # Right Checklist Badge
    add_card(s5_left + 8.40, r2_top + 0.45, 1.70, 1.80, bg_color=RGBColor(245, 243, 255), border_color=RGBColor(196, 181, 253))
    tf_chk = add_styled_text(s5_left + 8.45, r2_top + 0.50, 1.60, 1.70)
    p = tf_chk.paragraphs[0]
    p.text = "📋 CHECKLIST"
    p.font.bold = True; p.font.size = Pt(10.5); p.font.color.rgb = C_STEP5_PURPLE; p.alignment = PP_ALIGN.CENTER

    items_chk = [
        ("☑ Eliminate", "Blind factory push & static Excel models"),
        ("☑ Prevent", "Peak summer stockouts & post-season dead stock"),
        ("☑ Sustain", "Automated drift audit & continuous retraining")
    ]
    for title, desc in items_chk:
        p = tf_chk.add_paragraph()
        r1 = p.add_run(); r1.text = title + "\n"; r1.font.bold = True; r1.font.size = Pt(8.0); r1.font.color.rgb = RGBColor(109, 40, 217)
        r2 = p.add_run(); r2.text = desc; r2.font.size = Pt(7.0); r2.font.color.rgb = C_MUTED_TEXT

    # ==========================================================================
    # ROW 3: STEPS 6, 7
    # ==========================================================================
    r3_top = 6.48
    r3_h = 2.08

    # --------------------------------------------------------------------------
    # STEP 6: IMPLEMENTATION (Actions Completed + Before vs After)
    # --------------------------------------------------------------------------
    s6_left, s6_w = 0.40, 8.80
    add_card(s6_left, r3_top, s6_w, r3_h)
    add_step_header(s6_left, r3_top, s6_w, 0.32, "6", "IMPLEMENTATION", C_STEP6_TEAL)

    # Left: Actions Completed
    tf_act = add_styled_text(s6_left + 0.12, r3_top + 0.36, 4.30, 1.65)
    p = tf_act.paragraphs[0]
    p.text = "Actions Completed:"
    p.font.bold = True; p.font.size = Pt(8.5); p.font.color.rgb = C_STEP6_TEAL

    acts = [
        ("1. Data Pipeline & Cleaning", "Cleaned 99,395 transactions, isolated synthetic sheets, audited 14/14 zero-leakage validation checks."),
        ("2. Multi-Model Architecture", "Built global LightGBM cross-learning model pooling 273 series with lag, rolling & seasonal index features."),
        ("3. Interactive Streamlit Cockpit", "Shipped 7-module dashboard: Executive Cockpit, Forecast Visualizer, Inventory Optimizer, Report Generators.")
    ]
    for act_title, act_desc in acts:
        p = tf_act.add_paragraph()
        r1 = p.add_run(); r1.text = act_title + ": "; r1.font.bold = True; r1.font.size = Pt(7.5); r1.font.color.rgb = C_NAVY_TEXT
        r2 = p.add_run(); r2.text = act_desc; r2.font.size = Pt(7.0); r2.font.color.rgb = C_MUTED_TEXT

    # Right: Before vs After visual boxes
    add_card(s6_left + 4.55, r3_top + 0.45, 1.85, 1.48, bg_color=RGBColor(241, 245, 249), border_color=RGBColor(203, 213, 225))
    tf_bef = add_styled_text(s6_left + 4.60, r3_top + 0.50, 1.75, 1.38)
    p = tf_bef.paragraphs[0]
    p.text = "BEFORE (As-Is)"
    p.font.bold = True; p.font.size = Pt(8.0); p.font.color.rgb = RGBColor(100, 116, 139); p.alignment = PP_ALIGN.CENTER
    p = tf_bef.add_paragraph()
    p.text = "• Static 8-wk Moving Avg\n• Sub-50% weekly accuracy\n• Reactive factory push\n• Frequent peak stockouts\n• ~20% excess safety stock"
    p.font.size = Pt(7.0); p.font.color.rgb = C_MUTED_TEXT

    # Arrow
    arrow_box = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(s6_left + 6.45), Inches(r3_top + 1.05), Inches(0.35), Inches(0.25))
    arrow_box.fill.solid(); arrow_box.fill.fore_color.rgb = C_STEP6_TEAL
    arrow_box.line.fill.background()

    # After box
    add_card(s6_left + 6.85, r3_top + 0.45, 1.85, 1.48, bg_color=RGBColor(240, 253, 250), border_color=C_STEP6_TEAL)
    tf_aft = add_styled_text(s6_left + 6.90, r3_top + 0.50, 1.75, 1.38)
    p = tf_aft.paragraphs[0]
    p.text = "AFTER (AI Cockpit)"
    p.font.bold = True; p.font.size = Pt(8.0); p.font.color.rgb = C_STEP6_TEAL; p.alignment = PP_ALIGN.CENTER
    p = tf_aft.add_paragraph()
    p.text = "• Global LightGBM cross-learn\n• 71.8% Regional Qtr Acc\n• 65.6% Monthly Acc\n• ~20% leaner safety stock\n• Live 7-page interactive UI"
    p.font.size = Pt(7.0); p.font.color.rgb = C_NAVY_TEXT

    # --------------------------------------------------------------------------
    # STEP 7: RESULTS
    # --------------------------------------------------------------------------
    s7_left, s7_w = 9.35, 10.25
    add_card(s7_left, r3_top, s7_w, r3_h)
    add_step_header(s7_left, r3_top, s7_w, 0.32, "7", "RESULTS & BUSINESS IMPACT", C_STEP7_LEAF)

    # Results Table
    tbl_s7 = slide.shapes.add_table(5, 4, Inches(s7_left + 0.15), Inches(r3_top + 0.38), Inches(7.80), Inches(1.60)).table
    tbl_s7.columns[0].width = Inches(2.20)
    tbl_s7.columns[1].width = Inches(1.80)
    tbl_s7.columns[2].width = Inches(1.80)
    tbl_s7.columns[3].width = Inches(2.00)

    hdr_s7 = ("Parameter / Metric", "Before (Legacy MA)", "After (AI Engine)", "Improvement / Impact")
    for c_i, h_txt in enumerate(hdr_s7):
        cell = tbl_s7.cell(0, c_i)
        cell.text = h_txt
        cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(220, 252, 231)
        cell.margin_left = Inches(0.05); cell.margin_right = Inches(0.05)
        p = cell.text_frame.paragraphs[0]; p.font.bold = True; p.font.size = Pt(8.0); p.font.color.rgb = C_STEP7_LEAF

    rows_s7 = [
        ("Regional Monthly WAPE", "50.5% (MA4 baseline)", "34.4% (Rolling LightGBM)", "+31.9% Error Reduction"),
        ("Regional Quarterly Accuracy", "55.0% - 60.0%", "71.8% Accuracy", "+16.8% Higher Precision"),
        ("Model Forecast Bias", "-22.6% (Severe Under-forecast)", "+0.6% (Near-Zero Bias)", "Eliminates Peak Shortages"),
        ("Safety Stock Buffer", "High excess holding", "~20% Excess Buffer Cut", "Massive Working Capital Freed")
    ]
    for r_i, row in enumerate(rows_s7):
        for c_i, val in enumerate(row):
            cell = tbl_s7.cell(r_i + 1, c_i)
            cell.text = val
            cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if r_i % 2 == 0 else C_WHITE
            cell.margin_left = Inches(0.05); cell.margin_right = Inches(0.05)
            p = cell.text_frame.paragraphs[0]; p.font.size = Pt(7.5); p.font.color.rgb = C_NAVY_TEXT
            if c_i == 3:
                p.font.bold = True; p.font.color.rgb = RGBColor(4, 120, 87)

    # Right Achievement % Callout Badge
    add_card(s7_left + 8.10, r3_top + 0.45, 2.00, 1.50, bg_color=RGBColor(240, 253, 244), border_color=RGBColor(134, 239, 172))
    tf_ach = add_styled_text(s7_left + 8.15, r3_top + 0.48, 1.90, 1.42)
    p = tf_ach.paragraphs[0]
    p.text = "🏆 IMPACT"
    p.font.bold = True; p.font.size = Pt(11); p.font.color.rgb = C_STEP7_LEAF; p.alignment = PP_ALIGN.CENTER
    
    p = tf_ach.add_paragraph()
    p.text = "71.8%"
    p.font.bold = True; p.font.size = Pt(20); p.font.color.rgb = RGBColor(4, 120, 87); p.alignment = PP_ALIGN.CENTER

    p = tf_ach.add_paragraph()
    p.text = "Regional Qtr Accuracy\n~20% Buffer Reduction\n>=95% OTIF Fill Rate"
    p.font.bold = True; p.font.size = Pt(7.5); p.font.color.rgb = C_NAVY_TEXT; p.alignment = PP_ALIGN.CENTER

    # ==========================================================================
    # ROW 4: STEP 8 — STANDARDIZATION & FUTURE SCOPE (FULL WIDTH)
    # The centerpiece specifically requested by the user:
    # 1) Transfer In and Transfer Out
    # 2) Local News AI Integration
    # ==========================================================================
    r4_top = 8.64
    r4_h = 2.18
    s8_left, s8_w = 0.40, 19.20

    add_card(s8_left, r4_top, s8_w, r4_h)
    add_step_header(s8_left, r4_top, s8_w, 0.32, "8", "STANDARDIZATION, FUTURE SCOPE & HORIZONTAL DEPLOYMENT", C_STEP8_SLATE)

    # Sub-Block 8A: Governance & Operational Standardization (Left)
    col_a_w = 4.10
    add_card(s8_left + 0.12, r4_top + 0.38, col_a_w, r4_h - 0.46, bg_color=RGBColor(248, 250, 252), border_color=RGBColor(203, 213, 225))
    tf_8a = add_styled_text(s8_left + 0.20, r4_top + 0.42, col_a_w - 0.16, r4_h - 0.52)
    
    p = tf_8a.paragraphs[0]
    p.text = "Standardization & Governance:"
    p.font.bold = True; p.font.size = Pt(8.5); p.font.color.rgb = C_STEP8_SLATE

    chk_lines = [
        "SOP updated:             ☑ Yes    ☐ No",
        "Training completed:     ☑ Yes    ☐ No",
        "Control plan updated:   ☑ Yes    ☐ No"
    ]
    for chk in chk_lines:
        p = tf_8a.add_paragraph()
        p.text = chk; p.font.bold = True; p.font.size = Pt(7.5); p.font.color.rgb = C_NAVY_TEXT

    p = tf_8a.add_paragraph()
    p.text = "\nHorizontal Scaling Roadmap:"
    p.font.bold = True; p.font.size = Pt(8.0); p.font.color.rgb = C_NAVY_TEXT

    p = tf_8a.add_paragraph()
    p.text = "• Expand model from South Hubs to North, West, and East depots.\n• Hierarchical MinT reconciliation for coherent SKU-to-Factory roll-up."
    p.font.size = Pt(7.2); p.font.color.rgb = C_MUTED_TEXT

    # --------------------------------------------------------------------------
    # Sub-Block 8B: FUTURE SCOPE 1 — TRANSFER-IN & TRANSFER-OUT OPTIMIZATION
    # --------------------------------------------------------------------------
    col_b_left = s8_left + 0.12 + col_a_w + 0.15
    col_b_w = 7.30
    add_card(col_b_left, r4_top + 0.38, col_b_w, r4_h - 0.46, bg_color=C_ACCENT_BG_CYAN, border_color=C_FUTURE_CYAN, border_w=1.5)
    tf_8b = add_styled_text(col_b_left + 0.12, r4_top + 0.42, col_b_w - 0.24, r4_h - 0.52)

    p = tf_8b.paragraphs[0]
    r1 = p.add_run(); r1.text = "🚀 FUTURE SCOPE 1: "; r1.font.bold = True; r1.font.size = Pt(9.0); r1.font.color.rgb = C_FUTURE_CYAN
    r2 = p.add_run(); r2.text = "Dynamic Stock Transfer-In & Transfer-Out Optimization"; r2.font.bold = True; r2.font.size = Pt(9.0); r2.font.color.rgb = C_NAVY_TEXT

    b_bullets = [
        ("Inter-Branch Network Balancing", "Automated MILP optimization calculating optimal lateral Transfer-In (deficit depots) and Transfer-Out (surplus depots) across the 5 South distribution hubs."),
        ("Zero-Lead-Time Stockout Mitigation", "When local heatwaves surge demand in one branch (e.g. Chennai MAA), lateral transfer from a neighboring hub (e.g. Bangalore BLR) resolves shortages in 24–48 hours instead of 4–6 week factory lead times."),
        ("Freight Cost vs. Margin Balancing", "Mathematical algorithm balances secondary transfer freight and transit times against lost margin penalties, reducing total regional network safety stock by 12–15% through virtual pooling.")
    ]
    for b_title, b_desc in b_bullets:
        p = tf_8b.add_paragraph()
        r1 = p.add_run(); r1.text = "• " + b_title + ": "; r1.font.bold = True; r1.font.size = Pt(7.5); r1.font.color.rgb = C_NAVY_TEXT
        r2 = p.add_run(); r2.text = b_desc; r2.font.size = Pt(7.2); r2.font.color.rgb = C_MUTED_TEXT

    # --------------------------------------------------------------------------
    # Sub-Block 8C: FUTURE SCOPE 2 — LOCAL NEWS & REAL-TIME AI INTEGRATION
    # --------------------------------------------------------------------------
    col_c_left = col_b_left + col_b_w + 0.15
    col_c_w = s8_w - (col_c_left - s8_left) - 0.12
    add_card(col_c_left, r4_top + 0.38, col_c_w, r4_h - 0.46, bg_color=C_ACCENT_BG_PURP, border_color=C_FUTURE_PURPLE, border_w=1.5)
    tf_8c = add_styled_text(col_c_left + 0.12, r4_top + 0.42, col_c_w - 0.24, r4_h - 0.52)

    p = tf_8c.paragraphs[0]
    r1 = p.add_run(); r1.text = "🤖 FUTURE SCOPE 2: "; r1.font.bold = True; r1.font.size = Pt(9.0); r1.font.color.rgb = C_FUTURE_PURPLE
    r2 = p.add_run(); r2.text = "Local News & Real-Time AI Market Intelligence Integration"; r2.font.bold = True; r2.font.size = Pt(9.0); r2.font.color.rgb = C_NAVY_TEXT

    c_bullets = [
        ("GenAI External Signal Crawlers", "Autonomous LLM pipelines ingesting regional news headlines, IMD meteorological heatwave warnings, local commercial real-estate starts, and dealer conference feedback."),
        ("NLP Demand Shock Multipliers", "Translates unstructured regional news and municipal policy shifts into quantitative demand elasticity multipliers—converting forecasting from backward-looking to proactive leading sensing."),
        ("Conversational Supply Chain Copilot", "In-cockpit GenAI agent providing causal explanations for demand surges (e.g. 'Chennai demand surged +22% due to announced tech corridor project and heatwave alert').")
    ]
    for c_title, c_desc in c_bullets:
        p = tf_8c.add_paragraph()
        r1 = p.add_run(); r1.text = "• " + c_title + ": "; r1.font.bold = True; r1.font.size = Pt(7.5); r1.font.color.rgb = C_NAVY_TEXT
        r2 = p.add_run(); r2.text = c_desc; r2.font.size = Pt(7.2); r2.font.color.rgb = C_MUTED_TEXT

    # ==========================================================================
    # BOTTOM FOOTER BANNER
    # ==========================================================================
    ftr_top = 10.88
    ftr_h = 0.28
    ftr = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.40), Inches(ftr_top), Inches(19.20), Inches(ftr_h))
    ftr.fill.solid()
    ftr.fill.fore_color.rgb = C_NAVY_HEADER
    ftr.line.fill.background()
    
    tf_ftr = ftr.text_frame
    tf_ftr.word_wrap = False
    tf_ftr.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf_ftr.paragraphs[0]
    p.text = "Continuous Supply Chain Intelligence & Quality Excellence  |  ISB AMPBA Capstone Project with Deloitte (Room AC Demand Prediction & Optimization Engine)"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER

    # Save presentations
    output_pptx = os.path.abspath("ISB_Deloitte_QC_Story_Executive_One_Slider.pptx")
    prs.save(output_pptx)
    print(f"Presentation saved successfully to: {output_pptx}")

    copy_pptx = os.path.abspath("Capstone_Executive_QC_Story.pptx")
    try:
        prs.save(copy_pptx)
        print(f"Presentation copy saved to: {copy_pptx}")
    except Exception as e:
        print(f"Copy save warning: {e}")

    return output_pptx

def export_to_pdf_and_png(pptx_path):
    """Export the presentation to PDF via PowerPoint COM and high-res PNG via PyMuPDF"""
    pdf_path = pptx_path.replace(".pptx", ".pdf")
    png_path = pptx_path.replace(".pptx", ".png")
    
    try:
        import win32com.client
        ppt = win32com.client.Dispatch("PowerPoint.Application")
        presentation = ppt.Presentations.Open(pptx_path, WithWindow=False)
        presentation.SaveAs(pdf_path, 32) # 32 = ppSaveAsPDF
        presentation.Close()
        ppt.Quit()
        print(f"PDF exported successfully to: {pdf_path}")
    except Exception as e:
        print(f"PowerPoint COM export warning: {e}")

    try:
        import fitz
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=200)
        pix.save(png_path)
        print(f"High-res PNG preview exported to: {png_path} ({pix.width}x{pix.height})")
    except Exception as e:
        print(f"PyMuPDF rendering warning: {e}")

    return pdf_path, png_path

if __name__ == "__main__":
    pptx_file = create_qc_story_presentation()
    pdf_file, png_file = export_to_pdf_and_png(pptx_file)
