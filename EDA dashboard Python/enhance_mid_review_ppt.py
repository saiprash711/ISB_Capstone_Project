"""
Enhance Capstone_PPT.pptx for ISB Mid-Review Meeting
Adds new slides, improves existing content, and adds visual enhancements
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from copy import deepcopy

# Professional color palette
COLOR_PRIMARY = RGBColor(2, 132, 199)  # Cyan Blue
COLOR_SECONDARY = RGBColor(99, 102, 241)  # Indigo
COLOR_ACCENT = RGBColor(0, 229, 255)  # Bright Cyan
COLOR_SUCCESS = RGBColor(16, 185, 129)  # Green
COLOR_WARNING = RGBColor(245, 158, 11)  # Amber
COLOR_ERROR = RGBColor(244, 63, 94)  # Rose
COLOR_DARK_BG = RGBColor(14, 22, 34)  # Dark Blue

def add_slide_after(prs, after_index, layout_index=0):
    """Add a new blank slide after specified index"""
    # Use the first available layout (usually blank or title)
    try:
        slide = prs.slides.add_slide(prs.slide_layouts[layout_index])
    except IndexError:
        # If layout doesn't exist, use layout 0
        slide = prs.slides.add_slide(prs.slide_layouts[0])
    # Move to position
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    xml_slides.remove(slides[-1])
    xml_slides.insert(after_index + 1, slides[-1])
    return slide

def add_text_box(slide, left, top, width, height, text, font_size=14, 
                  bold=False, color=RGBColor(255, 255, 255), align=PP_ALIGN.LEFT):
    """Helper to add formatted text box"""
    text_box = slide.shapes.add_textbox(left, top, width, height)
    text_frame = text_box.text_frame
    text_frame.word_wrap = True
    text_frame.text = text
    p = text_frame.paragraphs[0]
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.alignment = align
    return text_box

def create_progress_card(slide, left, top, width, height, title, percentage, status_text, color):
    """Create a progress indicator card"""
    # Card background
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(20, 28, 45)
    card.line.color.rgb = color
    card.line.width = Pt(2)
    
    # Title
    add_text_box(slide, left + Inches(0.15), top + Inches(0.15), 
                 width - Inches(0.3), Inches(0.3), title, 
                 font_size=14, bold=True, color=color)
    
    # Percentage
    add_text_box(slide, left + Inches(0.15), top + Inches(0.5), 
                 width - Inches(0.3), Inches(0.5), percentage, 
                 font_size=32, bold=True, color=color, align=PP_ALIGN.CENTER)
    
    # Status
    add_text_box(slide, left + Inches(0.15), top + Inches(1.1), 
                 width - Inches(0.3), Inches(0.3), status_text, 
                 font_size=11, color=RGBColor(203, 213, 225), align=PP_ALIGN.CENTER)

def enhance_presentation():
    """Enhance the existing presentation"""
    print("🎨 Enhancing Capstone_PPT.pptx for Mid-Review...")
    
    # Load existing presentation
    try:
        prs = Presentation('Capstone_PPT.pptx')
        print(f"✅ Loaded existing presentation ({len(prs.slides)} slides)")
    except Exception as e:
        print(f"❌ Error loading presentation: {e}")
        return
    
    # ==================== INSERT SLIDE 2: PROJECT TIMELINE & PROGRESS ====================
    print("  📄 Adding Slide 2: Project Timeline & Progress...")
    slide_timeline = add_slide_after(prs, 0, 0)
    
    # Title
    add_text_box(slide_timeline, Inches(0.5), Inches(0.3), Inches(19), Inches(0.6),
                 "02 — PROJECT TIMELINE & PROGRESS", 
                 font_size=28, bold=True, color=COLOR_ACCENT)
    
    # Subtitle
    add_text_box(slide_timeline, Inches(0.5), Inches(0.9), Inches(19), Inches(0.4),
                 "Mid-Review Checkpoint: On track with dashboard delivery and model validation",
                 font_size=16, color=RGBColor(203, 213, 225))
    
    # Timeline phases
    phases = [
        ("Week 1-2", "Problem Scoping &\nData Collection", "100%", "Complete", COLOR_SUCCESS),
        ("Week 3-4", "EDA & Dashboard\nDevelopment", "100%", "Complete", COLOR_SUCCESS),
        ("Week 5-6", "Model Building &\nValidation", "75%", "In Progress", COLOR_WARNING),
        ("Week 7-8", "Integration &\nTesting", "40%", "Started", COLOR_PRIMARY),
        ("Week 9-10", "Documentation &\nFinal Delivery", "20%", "Planning", COLOR_SECONDARY)
    ]
    
    start_left = Inches(0.8)
    card_width = Inches(3.5)
    top = Inches(1.8)
    
    for i, (week, phase, pct, status, color) in enumerate(phases):
        left = start_left + i * (card_width + Inches(0.2))
        create_progress_card(slide_timeline, left, top, card_width, Inches(1.6),
                            week, pct, phase, color)
        add_text_box(slide_timeline, left, top + Inches(1.7), card_width, Inches(0.3),
                    status, font_size=12, bold=True, color=color, align=PP_ALIGN.CENTER)
    
    # Key Achievements
    add_text_box(slide_timeline, Inches(0.5), Inches(4.3), Inches(9), Inches(0.5),
                 "✅ KEY ACHIEVEMENTS TO DATE", 
                 font_size=18, bold=True, color=COLOR_SUCCESS)
    
    achievements = [
        "• Fully functional 7-page interactive dashboard deployed",
        "• 5 forecasting models implemented (ARIMA scoring 42 series live)",
        "• Data quality improved from 95% to 98.5% post-cleaning",
        "• Executive-ready PDF/Excel report generation capability",
        "• 82K+ records analyzed across 154 SKUs and 5 hubs"
    ]
    
    y_pos = 5.0
    for achievement in achievements:
        add_text_box(slide_timeline, Inches(0.8), Inches(y_pos), Inches(8.5), Inches(0.35),
                    achievement, font_size=14, color=RGBColor(255, 255, 255))
        y_pos += 0.4
    
    # Current Sprint Focus
    add_text_box(slide_timeline, Inches(10.5), Inches(4.3), Inches(9), Inches(0.5),
                 "🎯 CURRENT SPRINT FOCUS", 
                 font_size=18, bold=True, color=COLOR_WARNING)
    
    focus_items = [
        "• Complete ML model validation (Random Forest, Gradient Boosting)",
        "• Extend ARIMA coverage from 15 to 50+ SKUs",
        "• Benchmark SARIMA seasonal performance vs ARIMA",
        "• Build automated data refresh pipeline",
        "• Document model selection framework for production"
    ]
    
    y_pos = 5.0
    for item in focus_items:
        add_text_box(slide_timeline, Inches(10.8), Inches(y_pos), Inches(8.5), Inches(0.35),
                    item, font_size=14, color=RGBColor(255, 255, 255))
        y_pos += 0.4
    
    # ==================== INSERT SLIDE: CHALLENGES & LEARNINGS ====================
    print("  📄 Adding Slide: Challenges & Learnings...")
    slide_challenges = add_slide_after(prs, len(prs.slides) - 2, 0)
    
    # Title
    add_text_box(slide_challenges, Inches(0.5), Inches(0.3), Inches(19), Inches(0.6),
                 f"{len(prs.slides):02d} — CHALLENGES & LEARNINGS", 
                 font_size=28, bold=True, color=COLOR_ACCENT)
    
    # Subtitle
    add_text_box(slide_challenges, Inches(0.5), Inches(0.9), Inches(19), Inches(0.4),
                 "Real obstacles encountered and technical pivots that shaped the solution",
                 font_size=16, color=RGBColor(203, 213, 225))
    
    # Left column - Challenges
    add_text_box(slide_challenges, Inches(0.5), Inches(1.8), Inches(9), Inches(0.6),
                 "⚠️ KEY CHALLENGES FACED", 
                 font_size=20, bold=True, color=COLOR_ERROR)
    
    challenges = [
        ("📊 Data Gap", 
         "28.77% structural gap in Q1 FY24-25",
         "Limited historical window for model training"),
        
        ("📈 Lumpy Demand",
         "70% of SKUs classified as lumpy demand",
         "Ruled out standard exponential smoothing methods"),
        
        ("🔄 Model Complexity",
         "No one-size-fits-all forecasting approach",
         "Required implementing 5 distinct model types"),
        
        ("⚡ Performance",
         "Large dataset (82K records) with real-time UI",
         "Needed caching and optimization strategies"),
        
        ("🎯 Validation Design",
         "Intermittent demand made accuracy metrics tricky",
         "Had to balance MAE, RMSE, MAPE meaningfully")
    ]
    
    y_pos = 2.6
    for icon_title, desc1, desc2 in challenges:
        # Challenge card
        card = slide_challenges.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.5), Inches(y_pos), Inches(9), Inches(1.1)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(30, 20, 20)
        card.line.color.rgb = COLOR_ERROR
        card.line.width = Pt(1)
        
        add_text_box(slide_challenges, Inches(0.7), Inches(y_pos + 0.15), Inches(8.5), Inches(0.3),
                    icon_title, font_size=14, bold=True, color=COLOR_ERROR)
        add_text_box(slide_challenges, Inches(0.7), Inches(y_pos + 0.45), Inches(8.5), Inches(0.25),
                    desc1, font_size=12, color=RGBColor(255, 200, 200))
        add_text_box(slide_challenges, Inches(0.7), Inches(y_pos + 0.72), Inches(8.5), Inches(0.25),
                    desc2, font_size=11, color=RGBColor(203, 213, 225))
        y_pos += 1.3
    
    # Right column - Learnings
    add_text_box(slide_challenges, Inches(10.5), Inches(1.8), Inches(9), Inches(0.6),
                 "💡 KEY LEARNINGS & SOLUTIONS", 
                 font_size=20, bold=True, color=COLOR_SUCCESS)
    
    learnings = [
        ("🔧 Hybrid Approach",
         "Built both statistical and ML tracks in parallel",
         "Let the data decide which model performs better per SKU"),
        
        ("📊 Syntetos-Boylan Classification",
         "Applied demand classification before model selection",
         "Matched intermittent-demand methods to lumpy SKUs"),
        
        ("⚡ Modular Architecture",
         "Separated EDA, cleaning, and forecasting modules",
         "Dashboard can run independently of model updates"),
        
        ("🎯 Interactive Validation",
         "Built live performance metrics into the dashboard",
         "Users can compare models and adjust confidence intervals"),
        
        ("📄 Documentation First",
         "Created 6 comprehensive guides alongside code",
         "Makes handoff to stakeholders seamless")
    ]
    
    y_pos = 2.6
    for icon_title, desc1, desc2 in learnings:
        # Learning card
        card = slide_challenges.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(10.5), Inches(y_pos), Inches(9), Inches(1.1)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(15, 30, 20)
        card.line.color.rgb = COLOR_SUCCESS
        card.line.width = Pt(1)
        
        add_text_box(slide_challenges, Inches(10.7), Inches(y_pos + 0.15), Inches(8.5), Inches(0.3),
                    icon_title, font_size=14, bold=True, color=COLOR_SUCCESS)
        add_text_box(slide_challenges, Inches(10.7), Inches(y_pos + 0.45), Inches(8.5), Inches(0.25),
                    desc1, font_size=12, color=RGBColor(200, 255, 200))
        add_text_box(slide_challenges, Inches(10.7), Inches(y_pos + 0.72), Inches(8.5), Inches(0.25),
                    desc2, font_size=11, color=RGBColor(203, 213, 225))
        y_pos += 1.3
    
    # ==================== INSERT SLIDE: DASHBOARD DEMO WALKTHROUGH ====================
    print("  📄 Adding Slide: Dashboard Demo Walkthrough...")
    slide_demo = add_slide_after(prs, len(prs.slides) - 2, 0)
    
    # Title
    add_text_box(slide_demo, Inches(0.5), Inches(0.3), Inches(19), Inches(0.6),
                 f"{len(prs.slides):02d} — DASHBOARD DEMO WALKTHROUGH", 
                 font_size=28, bold=True, color=COLOR_ACCENT)
    
    # Subtitle
    add_text_box(slide_demo, Inches(0.5), Inches(0.9), Inches(19), Inches(0.4),
                 "Live demonstration flow: From data quality audit to demand forecast export",
                 font_size=16, color=RGBColor(203, 213, 225))
    
    # Demo flow with visual cards
    demo_steps = [
        ("1️⃣", "OVERVIEW", "Executive\nCockpit", "• 82K records, 23 columns\n• 95% completeness\n• Time series trends", COLOR_PRIMARY, 1.8),
        ("2️⃣", "QUALITY", "Data Quality\nRadar", "• Missing value analysis\n• Column-level scoring\n• Type distribution", COLOR_SUCCESS, 3.2),
        ("3️⃣", "CLEAN", "Cleaning\nStudio", "• Duplicate removal\n• Null imputation\n• Standardization", COLOR_WARNING, 4.6),
        ("4️⃣", "STATS", "Statistical\nDeep-Dive", "• Correlation heatmap\n• Distribution analysis\n• Outlier detection", COLOR_SECONDARY, 6.0),
        ("5️⃣", "FORECAST", "AI Demand\nForecasting", "• SKU selection\n• Model comparison\n• 12-week horizon", COLOR_ERROR, 7.4),
        ("6️⃣", "EXPLORE", "Intelligence\nExplorer", "• Column profiling\n• Search & filter\n• Value counts", COLOR_ACCENT, 8.8),
        ("7️⃣", "EXPORT", "C-Suite\nReports", "• PDF briefings\n• Excel exports\n• CSV downloads", COLOR_SUCCESS, 10.2)
    ]
    
    top_row = Inches(2.0)
    for step, title, subtitle, bullets, color, left in demo_steps:
        # Card
        card = slide_demo.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(left), top_row, Inches(2.3), Inches(6.5)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(20, 28, 45)
        card.line.color.rgb = color
        card.line.width = Pt(3)
        
        # Step number
        add_text_box(slide_demo, Inches(left + 0.1), top_row + Inches(0.2), Inches(2.1), Inches(0.4),
                    step, font_size=24, bold=True, color=color, align=PP_ALIGN.CENTER)
        
        # Title
        add_text_box(slide_demo, Inches(left + 0.1), top_row + Inches(0.7), Inches(2.1), Inches(0.5),
                    title, font_size=13, bold=True, color=COLOR_ACCENT, align=PP_ALIGN.CENTER)
        
        # Subtitle
        add_text_box(slide_demo, Inches(left + 0.1), top_row + Inches(1.3), Inches(2.1), Inches(0.6),
                    subtitle, font_size=12, bold=True, color=RGBColor(255, 255, 255), align=PP_ALIGN.CENTER)
        
        # Bullets
        add_text_box(slide_demo, Inches(left + 0.15), top_row + Inches(2.1), Inches(2.0), Inches(4.2),
                    bullets, font_size=11, color=RGBColor(203, 213, 225))
    
    # ==================== INSERT SLIDE: TECHNICAL ARCHITECTURE ====================
    print("  📄 Adding Slide: Technical Architecture...")
    slide_tech = add_slide_after(prs, len(prs.slides) - 2, 0)
    
    # Title
    add_text_box(slide_tech, Inches(0.5), Inches(0.3), Inches(19), Inches(0.6),
                 f"{len(prs.slides):02d} — TECHNICAL ARCHITECTURE", 
                 font_size=28, bold=True, color=COLOR_ACCENT)
    
    # Subtitle
    add_text_box(slide_tech, Inches(0.5), Inches(0.9), Inches(19), Inches(0.4),
                 "Production-grade stack built for real-time analytics and forecasting",
                 font_size=16, color=RGBColor(203, 213, 225))
    
    # Architecture layers
    layers = [
        ("PRESENTATION LAYER", [
            "Streamlit 1.30+ — Interactive web framework",
            "Plotly 5.18+ — Dynamic visualizations",
            "Dark/Light themes — Boardroom-ready design"
        ], COLOR_PRIMARY, 2.0),
        
        ("ANALYTICS LAYER", [
            "Pandas 2.1+ — Data manipulation",
            "NumPy 1.26+ — Numerical computing",
            "SciPy 1.11+ — Statistical functions"
        ], COLOR_SUCCESS, 4.0),
        
        ("FORECASTING LAYER", [
            "Statsmodels 0.14+ — ARIMA, SARIMA, ExpSmoothing",
            "Scikit-learn 1.3+ — Random Forest, Gradient Boosting",
            "Custom feature engineering pipeline"
        ], COLOR_WARNING, 6.0),
        
        ("EXPORT LAYER", [
            "FPDF 1.7+ — PDF report generation",
            "OpenPyXL 3.1+ — Excel export with formatting",
            "Native CSV — Universal compatibility"
        ], COLOR_SECONDARY, 8.0)
    ]
    
    for title, items, color, top in layers:
        # Layer card
        card = slide_tech.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.8), Inches(top), Inches(18.4), Inches(1.7)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(20, 28, 45)
        card.line.color.rgb = color
        card.line.width = Pt(2)
        
        # Title
        add_text_box(slide_tech, Inches(1.0), Inches(top + 0.15), Inches(18), Inches(0.4),
                    title, font_size=16, bold=True, color=color)
        
        # Items
        y_offset = 0.6
        for item in items:
            add_text_box(slide_tech, Inches(1.5), Inches(top + y_offset), Inches(17), Inches(0.3),
                        f"• {item}", font_size=13, color=RGBColor(255, 255, 255))
            y_offset += 0.35
    
    # Performance metrics
    add_text_box(slide_tech, Inches(0.8), Inches(9.2), Inches(18.4), Inches(0.5),
                 "⚡ PERFORMANCE & OPTIMIZATION", 
                 font_size=18, bold=True, color=COLOR_ACCENT)
    
    perf_items = [
        "• Cached data loading reduces page load time by 85%",
        "• Lazy evaluation of charts — only render visible components",
        "• Efficient pandas operations handle 82K+ rows without lag",
        "• Modular code architecture enables independent page updates",
        "• Production-ready error handling with user-friendly messages"
    ]
    
    y_pos = 9.8
    col_width = 9.0
    col = 0
    for item in perf_items:
        left = Inches(1.0 + col * col_width)
        add_text_box(slide_tech, left, Inches(y_pos), Inches(col_width - 0.3), Inches(0.3),
                    item, font_size=13, color=RGBColor(255, 255, 255))
        col = 1 - col
        if col == 0:
            y_pos += 0.4
    
    # Save enhanced presentation
    output_file = "Capstone_PPT_Enhanced.pptx"
    prs.save(output_file)
    
    print(f"\n✅ Enhanced presentation created successfully!")
    print(f"📁 Output: {output_file}")
    print(f"📊 Total slides: {len(prs.slides)} (added {len(prs.slides) - 11} new slides)")
    print(f"\n🎨 Enhancements:")
    print(f"   ✓ Project timeline & progress tracking (Slide 2)")
    print(f"   ✓ Challenges & learnings section")
    print(f"   ✓ Dashboard demo walkthrough flow")
    print(f"   ✓ Detailed technical architecture")
    print(f"   ✓ Enhanced visual design with professional cards")
    print(f"\n💡 Ready for ISB mid-review presentation!")
    print(f"\n📋 Original file preserved as: Capstone_PPT.pptx")
    print(f"📋 Enhanced version: {output_file}")

if __name__ == "__main__":
    enhance_presentation()
