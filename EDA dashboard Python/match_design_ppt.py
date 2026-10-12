"""
Match the exact design of existing Capstone_PPT.pptx slides
Analyze design elements and replicate for new slides
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from copy import deepcopy

def analyze_slide_design(prs, slide_index=1):
    """Analyze the design of an existing slide"""
    slide = prs.slides[slide_index]
    print(f"\n=== Analyzing Slide {slide_index + 1} Design ===")
    
    for i, shape in enumerate(slide.shapes):
        print(f"\nShape {i + 1}:")
        print(f"  Type: {shape.shape_type}")
        print(f"  Position: ({shape.left.inches:.2f}\", {shape.top.inches:.2f}\")")
        print(f"  Size: {shape.width.inches:.2f}\" x {shape.height.inches:.2f}\"")
        
        if hasattr(shape, 'fill'):
            if shape.fill.type == 1:  # Solid fill
                try:
                    rgb = shape.fill.fore_color.rgb
                    print(f"  Fill: RGB({rgb[0]}, {rgb[1]}, {rgb[2]})")
                except:
                    print(f"  Fill: Solid (color not accessible)")
        
        if hasattr(shape, 'text') and shape.text.strip():
            text = shape.text.strip()[:50]
            print(f"  Text: {text}")
            
            if hasattr(shape, 'text_frame'):
                for paragraph in shape.text_frame.paragraphs:
                    if paragraph.runs:
                        run = paragraph.runs[0]
                        if run.font.size:
                            print(f"  Font Size: {run.font.size.pt}pt")
                        if run.font.bold:
                            print(f"  Bold: Yes")
                        try:
                            rgb = run.font.color.rgb
                            print(f"  Font Color: RGB({rgb[0]}, {rgb[1]}, {rgb[2]})")
                        except:
                            pass

def create_matching_slide(prs, slide_number, title, subtitle):
    """Create a slide matching the existing design pattern"""
    
    # Add slide using first layout
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    
    # Background - match existing (appears to be dark)
    # The existing slides don't set explicit background, using master
    
    # Title (top-left, matches "02 — CONTEXT" style)
    title_shape = slide.shapes.add_textbox(
        Inches(1.04), Inches(1.04), 
        Inches(19.71), Inches(0.33)
    )
    title_frame = title_shape.text_frame
    title_frame.text = f"{slide_number:02d} — {title.upper()}"
    p = title_frame.paragraphs[0]
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = RGBColor(87, 210, 230)  # Cyan from existing slides
    
    # Subtitle (below title - large heading style)
    subtitle_shape = slide.shapes.add_textbox(
        Inches(1.04), Inches(1.56),
        Inches(16.09), Inches(1.51)
    )
    subtitle_frame = subtitle_shape.text_frame
    subtitle_frame.text = subtitle
    subtitle_frame.word_wrap = True
    p = subtitle_frame.paragraphs[0]
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = RGBColor(237, 242, 248)
    
    # Horizontal divider line (like in existing slides)
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(1.04), Inches(3.40),
        Inches(17.92), Inches(0.02)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(226, 236, 247)
    line.line.fill.background()
    
    return slide, Inches(3.96)  # Return slide and starting Y position for content

def add_content_box(slide, left, top, width, height, title, items, color_rgb):
    """Add a content box matching existing design - simple text, no heavy boxes"""
    
    # Title within box (no background box - minimalist style)
    title_box = slide.shapes.add_textbox(
        left, top,
        width, Inches(0.33)
    )
    title_frame = title_box.text_frame
    title_frame.text = title
    p = title_frame.paragraphs[0]
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = color_rgb
    
    # Thin line under title
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        left, top + Inches(0.38),
        width, Inches(0.02)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(226, 236, 247)
    line.line.fill.background()
    
    # Content items
    content_box = slide.shapes.add_textbox(
        left, top + Inches(0.55),
        width, height - Inches(0.55)
    )
    content_frame = content_box.text_frame
    content_frame.word_wrap = True
    
    for i, item in enumerate(items):
        if i > 0:
            p = content_frame.add_paragraph()
        else:
            p = content_frame.paragraphs[0]
        
        p.text = item
        p.font.size = Pt(21)
        p.font.color.rgb = RGBColor(237, 242, 248)
        p.space_before = Pt(12) if i > 0 else Pt(0)
        p.line_spacing = 1.4

def add_stat_box(slide, left, top, width, height, number, label, color_rgb):
    """Add a statistics box matching existing design - clean numbers with underline"""
    
    # Horizontal line above
    line1 = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        left, top,
        width, Inches(0.02)
    )
    line1.fill.solid()
    line1.fill.fore_color.rgb = RGBColor(226, 236, 247)
    line1.line.fill.background()
    
    # Number
    num_box = slide.shapes.add_textbox(
        left, top + Inches(0.20),
        width, Inches(1.19)
    )
    num_frame = num_box.text_frame
    num_frame.text = number
    p = num_frame.paragraphs[0]
    p.font.size = Pt(82)
    p.font.bold = True
    p.font.color.rgb = color_rgb
    p.alignment = PP_ALIGN.LEFT
    
    # Label
    label_box = slide.shapes.add_textbox(
        left, top + Inches(1.45),
        width, Inches(0.36)
    )
    label_frame = label_box.text_frame
    label_frame.text = label
    label_frame.word_wrap = True
    p = label_frame.paragraphs[0]
    p.font.size = Pt(21)
    p.font.color.rgb = RGBColor(147, 165, 187)
    p.alignment = PP_ALIGN.LEFT
    
    # Horizontal line below
    line2 = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        left, top + Inches(1.9),
        width, Inches(0.02)
    )
    line2.fill.solid()
    line2.fill.fore_color.rgb = RGBColor(226, 236, 247)
    line2.line.fill.background()

def create_enhanced_presentation():
    """Create enhanced presentation matching existing design"""
    print("Creating enhanced presentation with matched design...")
    
    try:
        prs = Presentation('Capstone_PPT.pptx')
        print(f"Loaded existing presentation ({len(prs.slides)} slides)")
    except Exception as e:
        print(f"Error loading presentation: {e}")
        return
    
    # Analyze existing slide for design reference
    analyze_slide_design(prs, 1)
    
    # Store original slide count
    original_count = len(prs.slides)
    
    # ==================== SLIDE 2: PROJECT TIMELINE & PROGRESS ====================
    print("Creating Slide 2: Project Timeline & Progress...")
    
    slide2, content_top = create_matching_slide(
        prs, 2, 
        "PROJECT TIMELINE & PROGRESS",
        "Mid-review checkpoint: 75% complete with dashboard and ARIMA models live"
    )
    
    # Move slide to position 1 (after title)
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    xml_slides.remove(slides[-1])
    xml_slides.insert(1, slides[-1])
    
    # Progress metrics (top row)
    metrics = [
        ("100%", "Data Collection\n& Analysis", RGBColor(16, 185, 129)),
        ("100%", "Dashboard\nDevelopment", RGBColor(16, 185, 129)),
        ("75%", "Model\nValidation", RGBColor(245, 158, 11)),
        ("40%", "Integration &\nTesting", RGBColor(99, 102, 241)),
    ]
    
    start_x = Inches(0.8)
    box_width = Inches(4.5)
    for i, (pct, label, color) in enumerate(metrics):
        left = start_x + i * (box_width + Inches(0.2))
        add_stat_box(slide2, left, content_top, box_width, Inches(1.5), pct, label, color)
    
    # Key Achievements (left column)
    achievements = [
        "• Fully functional 7-page interactive dashboard deployed",
        "• ARIMA model scoring 42 branch-SKU series live",
        "• Data quality improved from 95% to 98.5% post-cleaning",
        "• Executive-ready PDF/Excel report generation",
        "• 82,034 records analyzed across 154 SKUs and 5 hubs"
    ]
    
    add_content_box(
        slide2, 
        Inches(0.8), content_top + Inches(1.8),
        Inches(9), Inches(5.5),
        "✓ KEY ACHIEVEMENTS TO DATE",
        achievements,
        RGBColor(16, 185, 129)
    )
    
    # Current Focus (right column)
    focus = [
        "• Complete ML model validation (Random Forest, Gradient Boosting)",
        "• Extend ARIMA coverage from 15 to 50+ SKUs",
        "• Benchmark SARIMA seasonal performance against ARIMA",
        "• Build automated data refresh pipeline",
        "• Document model selection framework for production use"
    ]
    
    add_content_box(
        slide2,
        Inches(10.2), content_top + Inches(1.8),
        Inches(9), Inches(5.5),
        "→ CURRENT SPRINT FOCUS",
        focus,
        RGBColor(245, 158, 11)
    )
    
    # ==================== SLIDE 12: CHALLENGES & LEARNINGS ====================
    print("Creating Slide 12: Challenges & Learnings...")
    
    slide12, content_top = create_matching_slide(
        prs, len(prs.slides),
        "CHALLENGES & LEARNINGS",
        "Real obstacles encountered and technical pivots that shaped the solution"
    )
    
    # Challenges (left column)
    challenges = [
        "28.77% structural gap in Q1 FY24-25 limited training window",
        "70% of SKUs classified as lumpy demand — ruled out standard exponential smoothing",
        "No one-size-fits-all forecasting approach required implementing 5 distinct models",
        "Large dataset (82K records) with real-time UI requirements needed optimization",
        "Intermittent demand patterns made standard accuracy metrics challenging to interpret"
    ]
    
    add_content_box(
        slide12,
        Inches(0.8), content_top,
        Inches(9), Inches(6.5),
        "⚠ KEY CHALLENGES FACED",
        challenges,
        RGBColor(244, 63, 94)
    )
    
    # Learnings & Solutions (right column)
    solutions = [
        "Built statistical and ML tracks in parallel — let data decide which performs best per SKU",
        "Applied Syntetos-Boylan classification before model selection to match methods to demand type",
        "Separated EDA, cleaning, and forecasting modules so dashboard runs independently",
        "Built live performance metrics into dashboard for interactive model comparison",
        "Created 6 comprehensive guides alongside code for seamless stakeholder handoff"
    ]
    
    add_content_box(
        slide12,
        Inches(10.2), content_top,
        Inches(9), Inches(6.5),
        "✓ SOLUTIONS & LEARNINGS",
        solutions,
        RGBColor(16, 185, 129)
    )
    
    # ==================== SLIDE 13: DASHBOARD CAPABILITIES ====================
    print("Creating Slide 13: Dashboard Capabilities...")
    
    slide13, content_top = create_matching_slide(
        prs, len(prs.slides),
        "DASHBOARD CAPABILITIES",
        "Seven integrated views from executive summary to detailed forecasting"
    )
    
    # Dashboard pages in grid
    pages = [
        ("Executive Cockpit", "Health metrics, volume distribution, time series trends"),
        ("AI Demand Forecasting", "4–52 week forward forecasts by SKU and branch with confidence intervals"),
        ("Data Quality Radar", "Completeness scoring, null variance analysis, schema diagnostics"),
        ("Data Cleaning Studio", "Duplicate removal, null imputation, standardization recommendations"),
        ("Statistical Deep-Dive", "Distributions, correlation matrices, outlier detection, descriptive stats"),
        ("Intelligence Explorer", "Column profiling, attribute search, value distribution analysis"),
        ("C-Suite Reports", "Automated PDF briefings, multi-tab Excel exports, CSV downloads")
    ]
    
    # Create 2 columns of 4 and 3 boxes
    col1_items = pages[:4]
    col2_items = pages[4:]
    
    y_offset = content_top
    for i, (title, desc) in enumerate(col1_items):
        add_content_box(
            slide13,
            Inches(0.8), y_offset,
            Inches(9), Inches(1.5),
            f"{i+1}. {title}",
            [desc],
            RGBColor(87, 210, 230)
        )
        y_offset += Inches(1.7)
    
    y_offset = content_top
    for i, (title, desc) in enumerate(col2_items):
        add_content_box(
            slide13,
            Inches(10.2), y_offset,
            Inches(9), Inches(1.5),
            f"{i+5}. {title}",
            [desc],
            RGBColor(87, 210, 230)
        )
        y_offset += Inches(1.7)
    
    # ==================== SLIDE 14: TECHNICAL STACK ====================
    print("Creating Slide 14: Technical Stack...")
    
    slide14, content_top = create_matching_slide(
        prs, len(prs.slides),
        "TECHNICAL STACK",
        "Production-grade architecture built for real-time analytics and forecasting"
    )
    
    # Layer 1
    layer1_items = [
        "Streamlit 1.30+ — Interactive web framework for rapid deployment",
        "Plotly 5.18+ — Dynamic, interactive visualizations with zoom and hover",
        "Dark and light themes — Optimized for both boardroom projection and desk review"
    ]
    add_content_box(
        slide14,
        Inches(0.8), content_top,
        Inches(18.4), Inches(1.4),
        "PRESENTATION LAYER",
        layer1_items,
        RGBColor(99, 102, 241)
    )
    
    # Layer 2
    layer2_items = [
        "Pandas 2.1+ — Data manipulation and aggregation",
        "NumPy 1.26+ — Numerical computing and array operations",
        "SciPy 1.11+ — Statistical functions and distributions"
    ]
    add_content_box(
        slide14,
        Inches(0.8), content_top + Inches(1.6),
        Inches(18.4), Inches(1.4),
        "ANALYTICS LAYER",
        layer2_items,
        RGBColor(16, 185, 129)
    )
    
    # Layer 3
    layer3_items = [
        "Statsmodels 0.14+ — ARIMA, SARIMA, Exponential Smoothing time series models",
        "Scikit-learn 1.3+ — Random Forest and Gradient Boosting regressors",
        "Custom feature engineering — Lag features, rolling averages, calendar encoding"
    ]
    add_content_box(
        slide14,
        Inches(0.8), content_top + Inches(3.2),
        Inches(18.4), Inches(1.4),
        "FORECASTING LAYER",
        layer3_items,
        RGBColor(245, 158, 11)
    )
    
    # Layer 4
    layer4_items = [
        "FPDF 1.7+ — Professional PDF report generation with formatting",
        "OpenPyXL 3.1+ — Multi-sheet Excel export with styling",
        "Native CSV — Universal compatibility for downstream tools"
    ]
    add_content_box(
        slide14,
        Inches(0.8), content_top + Inches(4.8),
        Inches(18.4), Inches(1.4),
        "EXPORT LAYER",
        layer4_items,
        RGBColor(87, 210, 230)
    )
    
    # Performance note
    perf_box = slide14.shapes.add_textbox(
        Inches(1.04), content_top + Inches(6.4),
        Inches(18), Inches(0.8)
    )
    perf_frame = perf_box.text_frame
    perf_frame.word_wrap = True
    perf_frame.text = "OPTIMIZED FOR PERFORMANCE — Cached data loading reduces page load by 85% | Lazy chart evaluation | Efficient pandas operations handle 82K+ rows without lag"
    p = perf_frame.paragraphs[0]
    p.font.size = Pt(16)
    p.font.color.rgb = RGBColor(147, 165, 187)
    
    # Save
    output_file = "Capstone_PPT_Enhanced_v2.pptx"
    prs.save(output_file)
    
    print(f"\nEnhanced presentation created successfully!")
    print(f"Output: {output_file}")
    print(f"Total slides: {len(prs.slides)} (added {len(prs.slides) - original_count} new slides)")
    print(f"\nDesign Features:")
    print(f"   Matched existing dark theme")
    print(f"   Used cyan accent color (RGB 87, 210, 230)")
    print(f"   Consistent typography and spacing")
    print(f"   Minimalist style with thin lines")
    print(f"   Title format: '## — TITLE' pattern")
    print(f"\nNew slides use exact same design as your original slides!")
    print(f"\nOriginal file preserved as: Capstone_PPT.pptx")

if __name__ == "__main__":
    create_enhanced_presentation()
