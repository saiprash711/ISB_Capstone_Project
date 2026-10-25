"""
Update and generate the official ISB Capstone Individual Contribution Report.
This script:
1. Loads 'C:\\Users\\TC100\\Downloads\\Individual Contribution in Capstone Project.docx' (or backup)
2. Fills the header metadata:
   - Project Name: Demand Prediction by SKU - Sales Data Collection and EDA
   - Group No: (left blank for manual entry)
   - Sponsor: Deloitte
3. Reconfigures the table grid column widths (dxa) and cell widths so columns never awkwardly wrap:
   - Sno: 550 dxa
   - Name: 1650 dxa
   - Email Id: 1900 dxa
   - PGID: 950 dxa (with noWrap)
   - Percentage Contributed to the Project: 1200 dxa (with noWrap)
   - Tasks done: 3928 dxa
4. Populates all 5 students with their contact details, PGID, 20% parity share,
   and comprehensive bullet points of their contributions from the Capstone Dossier.
5. Calibrates typography and spacing so the entire document formats into a balanced 2-page document.
6. Exports to publication-grade PDF via Microsoft Word COM (SaveAs FileFormat=17).
7. Syncs the resulting PDF and DOCX files to Downloads, workspace root, and Your_capstone_reports.
"""

import os
import shutil
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

SRC_DOCX = r"C:\Users\TC100\Downloads\Individual Contribution in Capstone Project.docx"
BACKUP_DOCX = r"C:\Users\TC100\Downloads\Individual Contribution in Capstone Project_BACKUP.docx"
OUT_PDF_DOWNLOADS = r"C:\Users\TC100\Downloads\Individual Contribution in Capstone Project.pdf"

WORKSPACE_DIR = r"c:\ISB Capstone\EDA dashboard Python"
REPORTS_DIR = os.path.join(WORKSPACE_DIR, "Your_capstone_reports")

PROJECT_NAME = "Demand Prediction by SKU - Sales Data Collection and EDA"
GROUP_NO = ""  # Left blank for manual entry as requested
SPONSOR = "Deloitte"

# Column widths in dxa (1 inch = 1440 dxa)
# Page width A4 = 11906 dxa. Margins 0.6 in (864 dxa each side) -> printable width = 10178 dxa
COL_WIDTHS_DXA = [550, 1650, 1900, 950, 1200, 3928]

MEMBERS_DATA = [
    {
        "sno": "1",
        "name": "Sai Prashanth Sarathy",
        "email": "Sai_Sarathy_ampba2026S@isb.edu",
        "pgid": "12510081",
        "share": "20%",
        "tasks": [
            ("Lead Platform Architecture & Vercel Deployment", "Architected serverless cloud deployment on Vercel with 100% localhost parity (commits 441fa1e, fe13e8d, e82675c), APICS replenishment smoothing telemetry, and automated routing."),
            ("End-to-End Data Pipeline & Ingestion", "Built canonical automated data pipeline (src/data/orchestrator.py, ingestion.py, cleaning.py), transforming 82,034 raw ERP records into the 8,951-row canonical weekly data mart."),
            ("System Architecture & Governance", "Structured the modular 7-layer decoupled software hierarchy and centralized YAML configuration governance (config/data_config.yaml, model_config.yaml, business_config.yaml)."),
            ("Documentation & Reporting", "Primary author of Weekly Reports Wk 02, Wk 03, and co-author of Wk 07; compiled system ARCHITECTURE.md and forensic audit documentation.")
        ]
    },
    {
        "sno": "2",
        "name": "R Arvindshankar",
        "email": "Arvind_Shankar_ampba2026S@isb.edu",
        "pgid": "12510053",
        "share": "20%",
        "tasks": [
            ("Multi-Echelon Network Modeling", "Structured the 3-echelon supply chain network (National → South Region → 5 Regional Depots → 154 SKUs) in src/hierarchy/aggregation.py."),
            ("Hierarchical Mathematical Reconciliation", "Implemented src/hierarchy/reconciliation.py containing Bottom-Up, Top-Down, and Minimum Trace (MinT) optimal combination reconciliation with Ledoit-Wolf shrinkage covariance estimation, guaranteeing zero reconciliation mismatches (+4.8% accuracy gain)."),
            ("Econometric Variance Decomposition", "Built classical additive time-series decomposition module analyzing Trend, Seasonality, and Residual variance shares across SKU tiers."),
            ("Reporting & Formulation Defense", "Co-author of Weekly Report Wk 07; drafted formal mathematical formulation proofs, structural summation matrices (S matrix), and mid-review defense guide.")
        ]
    },
    {
        "sno": "3",
        "name": "Hariharan N",
        "email": "Hariharan_N_ampba2026S@isb.edu",
        "pgid": "12510102",
        "share": "20%",
        "tasks": [
            ("Analytics Cockpit & UI/UX Architecture", "Designed and coded the 7-module interactive intelligence dashboard (dashboard.py, src/dashboard_intelligence.py), providing seamless navigation across Executive Overview, Data Quality Radar, Cleaning Studio, Deep-Dive Forecasting, Inventory Optimizer, and What-If Simulator."),
            ("Interactive Visualization Engine", "Built the dynamic Plotly charting suite featuring dual light/dark high-contrast theme responsiveness, confidence interval fan charts, and multi-dimensional hierarchy filtering across 154 SKUs and branches."),
            ("Initial Data Extraction & CRM Validation", "Spearheaded initial raw ERP data extraction from manufacturing sponsor, validating regional sales office codes, customer tier classifications, and dealer master records."),
            ("Reporting & Slide Deck Design", "Primary author of Weekly Report Wk 04; co-author of Wk 01; designed capstone presentation slide visual templates and UI style guide.")
        ]
    },
    {
        "sno": "4",
        "name": "Vedika Sharma",
        "email": "Vedika_Sharma_ampba2026S@isb.edu",
        "pgid": "12510071",
        "share": "20%",
        "tasks": [
            ("Causal Feature Engineering", "Developed src/features/engineering.py implementing strictly shifted autoregressive lags (1–52W), rolling demand momentum statistics, and Fourier cyclical features with zero temporal data leakage."),
            ("Machine Learning Tournament Engine", "Implemented recursive walk-forward forecasting (predict_recursive) for tree ensembles (Random Forest, Gradient Boosting, XGBoost, LightGBM) in src/forecasting/ml_models.py."),
            ("Walk-Forward Backtesting & Leakage Audit", "Engineered expanding-window chronological backtesting (src/validation/backtesting.py) and 4-tier automated leakage auditor (src/validation/leakage_audit.py), achieving 100% clean audit pass."),
            ("Reporting & Model Governance", "Primary author of Weekly Report Wk 05; compiled MODEL_CARD.md, LEAKAGE_AUDIT.md, and auditable Champion/Challenger model registry.")
        ]
    },
    {
        "sno": "5",
        "name": "Vani Som",
        "email": "Vani_Som_ampba2026S@isb.edu",
        "pgid": "12510023",
        "share": "20%",
        "tasks": [
            ("Probabilistic Inventory Engine", "Programmed src/inventory/inventory_engine.py converting forecast distributions into actionable replenishment policies: Lead Time Demand (LTD), Safety Stock (SS) with service level calibration (90–98%), dynamic Reorder Points (ROP), and Monte Carlo stockout simulations."),
            ("Conformal Prediction Intervals", "Engineered empirical P10, P50, and P90 uncertainty intervals in src/uncertainty/prediction_intervals.py."),
            ("Scenario Simulation & Operational Telemetry Radar", "Built What-If simulator (src/scenarios/simulator.py) and statistical drift monitor (src/monitoring/drift.py, alerts.py) utilizing Population Stability Index (PSI), KS tests, and APICS Tracking Signals."),
            ("Reporting & Business ROI", "Primary author of Weekly Report Wk 06; co-author of Wk 01; authored business impact, stockout risk reduction, and working capital optimization case studies.")
        ]
    }
]


def set_cell_properties(cell, width_dxa, top_pad=50, bottom_pad=50, left_pad=60, right_pad=60, bg_hex=None, nowrap=False):
    """Sets width, cell padding, background shading, and nowrap option."""
    tcPr = cell._tc.get_or_add_tcPr()
    
    # 1. Exact cell width
    tcW = tcPr.find(qn('w:tcW'))
    if tcW is None:
        tcW = OxmlElement('w:tcW')
        tcPr.append(tcW)
    tcW.set(qn('w:w'), str(width_dxa))
    tcW.set(qn('w:type'), 'dxa')

    # 2. Cell padding
    tcMar = tcPr.find(qn('w:tcMar'))
    if tcMar is None:
        tcMar = OxmlElement('w:tcMar')
        tcPr.append(tcMar)
    else:
        tcMar.clear()

    for m, val in [('top', top_pad), ('bottom', bottom_pad), ('left', left_pad), ('right', right_pad)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)

    # 3. Background shading
    if bg_hex:
        shd = tcPr.find(qn('w:shd'))
        if shd is not None:
            tcPr.remove(shd)
        tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_hex}"/>'))

    # 4. NoWrap
    if nowrap:
        nw = tcPr.find(qn('w:noWrap'))
        if nw is None:
            tcPr.append(parse_xml(f'<w:noWrap {nsdecls("w")}/>'))


def populate_docx():
    # Use clean backup if available
    if os.path.exists(BACKUP_DOCX):
        doc = docx.Document(BACKUP_DOCX)
    else:
        shutil.copyfile(SRC_DOCX, BACKUP_DOCX)
        doc = docx.Document(SRC_DOCX)

    # Setup section margins
    sec = doc.sections[0]
    sec.left_margin = Inches(0.60)
    sec.right_margin = Inches(0.60)
    sec.top_margin = Inches(0.55)
    sec.bottom_margin = Inches(0.55)

    # Remove empty paragraphs that push table down awkwardly
    for p in list(doc.paragraphs):
        if not p.text.strip():
            p._p.getparent().remove(p._p)

    # Paragraph 0: Document Title
    p0 = doc.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_before = Pt(0)
    p0.paragraph_format.space_after = Pt(6)
    p0.clear()
    r0 = p0.add_run("Individual Contribution in Capstone Project")
    r0.bold = True
    r0.font.size = Pt(17)
    r0.font.color.rgb = RGBColor(0, 112, 192) # #0070C0 ISB Blue

    p_proj = None
    p_grp = None
    p_sp = None

    for p in doc.paragraphs:
        txt = p.text.strip()
        if "Project Name:" in txt:
            p_proj = p
        elif "Group No:" in txt:
            p_grp = p
        elif "Sponsor:" in txt:
            p_sp = p

    if p_proj:
        p_proj.clear()
        p_proj.paragraph_format.space_before = Pt(1)
        p_proj.paragraph_format.space_after = Pt(1)
        r_label = p_proj.add_run("Project Name: ")
        r_label.bold = True
        r_label.font.size = Pt(10)
        r_val = p_proj.add_run(PROJECT_NAME)
        r_val.font.size = Pt(10)

    if p_grp:
        p_grp.clear()
        p_grp.paragraph_format.space_before = Pt(1)
        p_grp.paragraph_format.space_after = Pt(1)
        r_label = p_grp.add_run("Group No: ")
        r_label.bold = True
        r_label.font.size = Pt(10)
        r_val = p_grp.add_run(GROUP_NO) # Left blank for manual entry
        r_val.font.size = Pt(10)

    if p_sp:
        p_sp.clear()
        p_sp.paragraph_format.space_before = Pt(1)
        p_sp.paragraph_format.space_after = Pt(6)
        r_label = p_sp.add_run("Sponsor: ")
        r_label.bold = True
        r_label.font.size = Pt(10)
        r_val = p_sp.add_run(SPONSOR)
        r_val.font.size = Pt(10)

    # Configure Table
    t = doc.tables[0]
    t.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Update Table Grid (dxa)
    tblGrid = t._tbl.tblGrid
    tblGrid.clear()
    for w in COL_WIDTHS_DXA:
        col = OxmlElement('w:gridCol')
        col.set(qn('w:w'), str(w))
        tblGrid.append(col)

    # Header Row
    header_tr = t.rows[0]._tr.get_or_add_trPr()
    if header_tr.find(qn('w:tblHeader')) is None:
        header_tr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

    header_titles = [
        "Sno",
        "Name",
        "Email Id",
        "PGID",
        "Percentage\nContributed to\nthe Project",
        "Tasks done\n(Mention the tasks done by respective team member in the project)"
    ]

    header_row = t.rows[0]
    for c_idx, cell in enumerate(header_row.cells):
        set_cell_properties(cell, COL_WIDTHS_DXA[c_idx], top_pad=80, bottom_pad=80, left_pad=60, right_pad=60, bg_hex="EAEEF3")
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 3, 4] else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(header_titles[c_idx])
        r.bold = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(15, 23, 42)

    # Populate Members Rows (1 to 5)
    for idx, member in enumerate(MEMBERS_DATA):
        r_idx = idx + 1
        if r_idx < len(t.rows):
            row = t.rows[r_idx]
        else:
            row = t.add_row()

        # Prevent mid-row pagination break where possible
        trPr = row._tr.get_or_add_trPr()
        if trPr.find(qn('w:cantSplit')) is None:
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

        bg_hex = "FFFFFF" if idx % 2 == 0 else "F8FAFC"

        # Col 0: Sno
        cell_sno = row.cells[0]
        set_cell_properties(cell_sno, COL_WIDTHS_DXA[0], top_pad=50, bottom_pad=50, left_pad=40, right_pad=40, bg_hex=bg_hex, nowrap=True)
        cell_sno.text = ""
        p0 = cell_sno.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        r = p0.add_run(member["sno"])
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(30, 41, 59)

        # Col 1: Name
        cell_name = row.cells[1]
        set_cell_properties(cell_name, COL_WIDTHS_DXA[1], top_pad=50, bottom_pad=50, left_pad=50, right_pad=50, bg_hex=bg_hex)
        cell_name.text = ""
        p1 = cell_name.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        p1.paragraph_format.line_spacing = 1.0
        r = p1.add_run(member["name"])
        r.bold = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(15, 23, 42)

        # Col 2: Email Id
        cell_email = row.cells[2]
        set_cell_properties(cell_email, COL_WIDTHS_DXA[2], top_pad=50, bottom_pad=50, left_pad=50, right_pad=50, bg_hex=bg_hex)
        cell_email.text = ""
        p2 = cell_email.paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(0)
        p2.paragraph_format.line_spacing = 1.0
        r = p2.add_run(member["email"])
        r.font.size = Pt(8)
        r.font.color.rgb = RGBColor(51, 65, 85)

        # Col 3: PGID
        cell_pgid = row.cells[3]
        set_cell_properties(cell_pgid, COL_WIDTHS_DXA[3], top_pad=50, bottom_pad=50, left_pad=40, right_pad=40, bg_hex=bg_hex, nowrap=True)
        cell_pgid.text = ""
        p3 = cell_pgid.paragraphs[0]
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p3.paragraph_format.space_before = Pt(0)
        p3.paragraph_format.space_after = Pt(0)
        r = p3.add_run(member["pgid"])
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(30, 41, 59)

        # Col 4: Percentage
        cell_share = row.cells[4]
        set_cell_properties(cell_share, COL_WIDTHS_DXA[4], top_pad=50, bottom_pad=50, left_pad=40, right_pad=40, bg_hex=bg_hex, nowrap=True)
        cell_share.text = ""
        p4 = cell_share.paragraphs[0]
        p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p4.paragraph_format.space_before = Pt(0)
        p4.paragraph_format.space_after = Pt(0)
        r = p4.add_run(member["share"])
        r.bold = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(5, 150, 105) # Green 20%

        # Col 5: Tasks done
        cell_tasks = row.cells[5]
        set_cell_properties(cell_tasks, COL_WIDTHS_DXA[5], top_pad=40, bottom_pad=40, left_pad=60, right_pad=60, bg_hex=bg_hex)
        cell_tasks.text = ""

        for t_idx, (t_title, t_desc) in enumerate(member["tasks"]):
            if t_idx == 0:
                p_task = cell_tasks.paragraphs[0]
            else:
                p_task = cell_tasks.add_paragraph()

            p_task.paragraph_format.space_before = Pt(0.5)
            p_task.paragraph_format.space_after = Pt(1.5)
            p_task.paragraph_format.line_spacing = 1.0

            r_bullet = p_task.add_run("• ")
            r_bullet.bold = True
            r_bullet.font.size = Pt(8)
            r_bullet.font.color.rgb = RGBColor(0, 112, 192)

            r_title = p_task.add_run(f"{t_title}: ")
            r_title.bold = True
            r_title.font.size = Pt(8)
            r_title.font.color.rgb = RGBColor(15, 23, 42)

            r_desc = p_task.add_run(t_desc)
            r_desc.font.size = Pt(8)
            r_desc.font.color.rgb = RGBColor(51, 65, 85)

    doc.save(SRC_DOCX)
    print(f"[SUCCESS] Updated DOCX saved to: {SRC_DOCX}")

    repo_docx = os.path.join(REPORTS_DIR, "Individual Contribution in Capstone Project.docx")
    shutil.copyfile(SRC_DOCX, repo_docx)
    print(f"[SUCCESS] Saved copy in repo: {repo_docx}")


def convert_docx_to_pdf():
    import win32com.client
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False

    try:
        abs_docx = os.path.abspath(SRC_DOCX)
        abs_pdf = os.path.abspath(OUT_PDF_DOWNLOADS)
        
        doc = word.Documents.Open(abs_docx)
        # 17 = wdExportFormatPDF
        doc.SaveAs(abs_pdf, FileFormat=17)
        doc.Close(SaveChanges=0)
        print(f"[SUCCESS] Converted DOCX to PDF: {abs_pdf} ({os.path.getsize(abs_pdf):,} bytes)")

        destinations = [
            os.path.join(WORKSPACE_DIR, "ISB_Deloitte_Capstone_Individual_Contribution_and_Work_Allocation.pdf"),
            os.path.join(REPORTS_DIR, "ISB_Deloitte_Capstone_Individual_Contribution_and_Work_Allocation.pdf"),
            os.path.join(REPORTS_DIR, "Individual Contribution in Capstone Project.pdf"),
        ]
        for dest in destinations:
            shutil.copyfile(abs_pdf, dest)
            print(f"[SUCCESS] Synced PDF to: {dest}")

    finally:
        try:
            word.Quit()
        except Exception:
            pass


if __name__ == "__main__":
    populate_docx()
    convert_docx_to_pdf()
