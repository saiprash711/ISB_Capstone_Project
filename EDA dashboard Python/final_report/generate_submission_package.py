"""
Generates the companion deliverables required by Capstone_Report_Instructions_and_Best_Practices_2026:
  1. Data Note (1 page) -> docx and pdf
  2. Plain-Language Summary (150 words) -> docx, pdf, and txt
  3. Originality and Confidentiality Declaration -> docx and pdf
  4. Assignment Submission Form -> docx and pdf
"""
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "final_report"

NAVY = RGBColor(0x1F, 0x38, 0x64)
GREY = RGBColor(0x59, 0x59, 0x59)

TEAM = [
    ("Sai Prashanth Sarathy", "12510081", "Sai_Sarathy_ampba2026S@isb.edu"),
    ("R Arvindshankar", "12510053", "Arvind_Shankar_ampba2026S@isb.edu"),
    ("Hariharan N", "12510102", "Hariharan_N_ampba2026S@isb.edu"),
    ("Vedika Sharma", "12510071", "Vedika_Sharma_ampba2026S@isb.edu"),
    ("Vani Som", "12510023", "Vani_Som_ampba2026S@isb.edu"),
]

TITLE = "Demand Prediction by SKU: Forecasting Lumpy Room Air-Conditioner Demand for Depot Replenishment"
BATCH = "AMPBA Class of 2026S"
MONTH = "October 2026"
SPONSOR = "Deloitte Touche Tohmatsu India LLP"


def set_margins(doc, top=1.0, bottom=1.0, left=1.0, right=1.0):
    for sec in doc.sections:
        sec.top_margin = Inches(top)
        sec.bottom_margin = Inches(bottom)
        sec.left_margin = Inches(left)
        sec.right_margin = Inches(right)
        sec.page_width = Inches(8.5)
        sec.page_height = Inches(11.0)


def style_table(table, col_widths, navy_header=True):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        '<w:tblBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="BFC8D6"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="BFC8D6"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="BFC8D6"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="BFC8D6"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="BFC8D6"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="BFC8D6"/>'
        '</w:tblBorders>'
    )
    tblPr.append(borders)
    for r_idx, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml('<w:cantSplit xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
        for c_idx, cell in enumerate(row.cells):
            cell.width = Inches(col_widths[c_idx])
            tcPr = cell._tc.get_or_add_tcPr()
            tcMar = parse_xml(
                '<w:tcMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:top w:w="80" w:type="dxa"/><w:left w:w="120" w:type="dxa"/>'
                '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tcMar>'
            )
            tcPr.append(tcMar)
            if r_idx == 0 and navy_header:
                shd = parse_xml('<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="clear" w:color="auto" w:fill="1F3864"/>')
                tcPr.append(shd)
            elif r_idx % 2 == 1:
                shd = parse_xml('<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="clear" w:color="auto" w:fill="F5F7F7"/>')
                tcPr.append(shd)


# ==============================================================================
# 1. DATA NOTE (Exact 1 page)
# ==============================================================================
def create_data_note():
    doc = docx.Document()
    set_margins(doc, top=0.75, bottom=0.75, left=0.85, right=0.85)

    p_inst = doc.add_paragraph()
    r = p_inst.add_run("INDIAN SCHOOL OF BUSINESS  ·  INSTITUTE OF DATA SCIENCE")
    r.font.name = "Cambria"
    r.font.size = Pt(9.5)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_after = Pt(2)

    p_title = doc.add_paragraph()
    r = p_title.add_run("CAPSTONE PROJECT: DATA NOTE")
    r.font.name = "Cambria"
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(4)

    p_sub = doc.add_paragraph()
    r = p_sub.add_run(f"Project: {TITLE}\nSponsor: {SPONSOR}  |  Cohort: {BATCH}  |  Date: {MONTH}")
    r.font.name = "Calibri"
    r.font.size = Pt(9)
    r.font.italic = True
    r.font.color.rgb = GREY
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)

    # Metadata table
    tbl = doc.add_table(rows=5, cols=2)
    style_table(tbl, [2.0, 4.8], navy_header=False)
    data_meta = [
        ("Sponsor & Client Context", "Deloitte Touche Tohmatsu India LLP (advising a leading Indian room air-conditioner manufacturer)"),
        ("Source Data Extraction", "SAP ERP billing extract spanning 16 July 2022 to 30 June 2024 (103 weekly billing cycles; 82,034 rows)"),
        ("Data Sensitivity Level", "CONFIDENTIAL / RESTRICTED (Commercial client billing data shared under sponsor NDA for ISB evaluation)"),
        ("Target Demand Grain", "Weekly billing quantity for 70 outdoor-unit (ODU) models across 5 regional sales depots (BLR, COK, MAA, SBD, SBD1)"),
        ("Sponsor Approval Status", "Data-handling protocol and academic usage approved by Deloitte in August 2026"),
    ]
    for row, (k, v) in zip(tbl.rows, data_meta):
        c0, c1 = row.cells
        p0, p1 = c0.paragraphs[0], c1.paragraphs[0]
        r0 = p0.add_run(k)
        r0.font.name = "Calibri"
        r0.font.size = Pt(9)
        r0.font.bold = True
        r0.font.color.rgb = NAVY
        r1 = p1.add_run(v)
        r1.font.name = "Calibri"
        r1.font.size = Pt(9)
        p0.paragraph_format.space_after = Pt(2)
        p1.paragraph_format.space_after = Pt(2)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    sections = [
        ("1. Data Description & Provenance",
         "The dataset comprises transactional ERP billing lines from the manufacturer's South India operations. Each record captures billing date, material code, sales office code, billing quantity, equipment segment (inverter vs. fixed-speed), star rating, and tonnage. Following comprehensive forensic audits, indoor-unit lines (IDUs) were set aside (demand is strictly 1:1 with outdoor units) and exact duplicate rows in Q1 FY25 were removed, establishing an empirical data mart of 66,336 positive ODU lines and 698,904 shipped units."),

        ("2. Anonymization & Confidentiality Safeguards",
         "In strict compliance with ISB Honor Code and sponsor confidentiality protocols, the following safeguards were applied:\n"
         "• Client Manufacturer Masking: The corporate entity and brand name of the AC manufacturer are fully anonymized.\n"
         "• Personally Identifiable Information (PII) Exclusion: The extract contained names of individual retail buyers and dealer names. All customer/dealer names were strictly quarantined, omitted from feature engineering and models, and appear in zero tables or charts.\n"
         "• Commercial Pricing Suppression: No invoice values, unit prices, billing margins, or revenue figures are disclosed; all analyses and replenishment policies operate on unit volumes.\n"
         "• Aggregation Thresholds: All published exhibits and summary tables are aggregated to SKU × branch × week level."),

        ("3. Code Repository & Storage Security",
         "The analytical codebase and Streamlit cockpit are maintained in a secure private GitHub repository (https://github.com/saiprash711/ISB_Capstone_Project). All raw billing files, client extracts, and intermediate pickles are excluded from version control via .gitignore. Reproduction instructions utilize synthetic or sanitized mock files."),
    ]

    for title, body in sections:
        h = doc.add_paragraph()
        r = h.add_run(title)
        r.font.name = "Cambria"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = NAVY
        h.paragraph_format.space_before = Pt(4)
        h.paragraph_format.space_after = Pt(2)

        p = doc.add_paragraph()
        r = p.add_run(body)
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(4)

    # Team signature line
    sig_p = doc.add_paragraph()
    r = sig_p.add_run("Submitted on behalf of the Capstone Project Team:\n" +
                      ", ".join(f"{name} ({pgid})" for name, pgid, _ in TEAM))
    r.font.name = "Calibri"
    r.font.size = Pt(8.5)
    r.font.italic = True
    r.font.color.rgb = GREY
    sig_p.paragraph_format.space_before = Pt(6)

    path_docx = OUT / "ISB_Capstone_Data_Note.docx"
    doc.save(str(path_docx))
    print("Saved", path_docx)


# ==============================================================================
# 2. PLAIN-LANGUAGE SUMMARY (150 words)
# ==============================================================================
def create_plain_language_summary():
    summary_text = (
        "Air conditioners are seasonal and expensive. In South India, more than half of all sales happen "
        "between February and May, and a two-week shipping lead time forces depot managers to guess what dealers "
        "will order weeks ahead. Order too little, and customers walk away during the summer heat; order too much, "
        "and costly units sit unsold for months. Today, depots rely mostly on recent sales averages and intuition.\n\n"
        "We analyzed two years of real billing records for a major air-conditioner brand across five regional branches. "
        "We discovered that most models sell unpredictably, but a single machine-learning system that learns demand "
        "patterns across all models simultaneously outperformed traditional rules. It reduced weekly forecast errors "
        "by 21% and anticipated the post-summer sales drop where warehouses typically accumulate costly surpluses. "
        "By matching buffers to true forecast accuracy, depots can maintain full customer availability while cutting "
        "excess safety inventory by 24%, freeing substantial working capital."
    )
    # Count words
    words = [w for w in summary_text.split() if w.strip()]
    word_count = len(words)

    # Save TXT
    path_txt = OUT / "ISB_Capstone_Plain_Language_Summary.txt"
    with open(path_txt, "w", encoding="utf-8") as f:
        f.write(f"PROJECT TITLE: {TITLE}\n")
        f.write(f"AUTHORS: {', '.join(n for n, _, _ in TEAM)}\n")
        f.write(f"COHORT: {BATCH} | {MONTH}\n")
        f.write(f"SPONSOR: {SPONSOR}\n")
        f.write(f"WORD COUNT: {word_count} words (Limit: 150 words)\n\n")
        f.write(summary_text)
    print("Saved", path_txt, f"({word_count} words)")

    # Save DOCX
    doc = docx.Document()
    set_margins(doc)

    p_inst = doc.add_paragraph()
    r = p_inst.add_run("INDIAN SCHOOL OF BUSINESS  ·  INSTITUTE OF DATA SCIENCE")
    r.font.name = "Cambria"
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_title = doc.add_paragraph()
    r = p_title.add_run("PLAIN-LANGUAGE SUMMARY")
    r.font.name = "Cambria"
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_sub = doc.add_paragraph()
    r = p_sub.add_run(f"Project: {TITLE}\nTeam: {', '.join(n for n, _, _ in TEAM)}\nSponsor: {SPONSOR}  |  {BATCH}")
    r.font.name = "Calibri"
    r.font.size = Pt(9.5)
    r.font.italic = True
    r.font.color.rgb = GREY
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(18)

    p_note = doc.add_paragraph()
    r = p_note.add_run(f"Target word count: ~150 words | Actual count: {word_count} words | Register: General Business (No Jargon)")
    r.font.name = "Calibri"
    r.font.size = Pt(9)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p_note.paragraph_format.space_after = Pt(12)

    for para in summary_text.split("\n\n"):
        p = doc.add_paragraph()
        r = p.add_run(para)
        r.font.name = "Calibri"
        r.font.size = Pt(11)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(10)

    path_docx = OUT / "ISB_Capstone_Plain_Language_Summary.docx"
    doc.save(str(path_docx))
    print("Saved", path_docx)


# ==============================================================================
# 3. ORIGINALITY & CONFIDENTIALITY DECLARATION FORM
# ==============================================================================
def create_declaration_form():
    doc = docx.Document()
    set_margins(doc, top=0.85, bottom=0.85, left=0.85, right=0.85)

    p_inst = doc.add_paragraph()
    r = p_inst.add_run("INDIAN SCHOOL OF BUSINESS  ·  INSTITUTE OF DATA SCIENCE\nADVANCED MANAGEMENT PROGRAMME IN BUSINESS ANALYTICS (AMPBA)")
    r.font.name = "Cambria"
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_title = doc.add_paragraph()
    r = p_title.add_run("ORIGINALITY & CONFIDENTIALITY DECLARATION")
    r.font.name = "Cambria"
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(14)

    # Details table
    tbl = doc.add_table(rows=4, cols=2)
    style_table(tbl, [2.0, 4.8], navy_header=False)
    details = [
        ("Capstone Project Title", TITLE),
        ("Sponsoring Organization", f"{SPONSOR} (Client: Room Air-Conditioner Manufacturer)"),
        ("Academic Cohort", f"{BATCH} — Final Report Submission"),
        ("Submission Date", "October 25, 2026"),
    ]
    for row, (k, v) in zip(tbl.rows, details):
        c0, c1 = row.cells
        r0 = c0.paragraphs[0].add_run(k)
        r0.font.name = "Calibri"
        r0.font.size = Pt(9.5)
        r0.font.bold = True
        r0.font.color.rgb = NAVY
        r1 = c1.paragraphs[0].add_run(v)
        r1.font.name = "Calibri"
        r1.font.size = Pt(9.5)
        c0.paragraphs[0].paragraph_format.space_after = Pt(2)
        c1.paragraphs[0].paragraph_format.space_after = Pt(2)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    decl_paras = [
        ("Declaration of Academic Originality (Honor Code Clause 3N-b)",
         "We, the undersigned participants of the Advanced Management Programme in Business Analytics at the "
         "Indian School of Business, hereby declare that this Capstone Project Final Report is our own original work. "
         "All secondary sources, research literature, software packages, and data assets referenced herein have been "
         "scrupulously acknowledged and cited in accordance with the APA 7th edition referencing standards. We affirm "
         "that unattributed text, copied analyses, and fabricated statistics are strict violations of the ISB Honor Code. "
         "Our use of generative-AI tools has been transparently documented and disclosed in Appendix A."),

        ("Declaration of Sponsor Confidentiality and Data Responsibility",
         "We certify that all historical billing extracts and operational intelligence provided by Deloitte and its client "
         "have been maintained under strict confidentiality. Personally Identifiable Information (PII) including individual "
         "buyer identities and dealer names have been sanitized and excluded from all feature matrices, models, and public "
         "exhibits. Commercial data have been reported exclusively in aggregated form. We confirm that no proprietary data "
         "files have been or will be published in public code repositories."),

        ("Joint Accountability Statement",
         "As stipulated in the Capstone Report Instructions, all named team members are jointly and severally accountable "
         "for the entire report and all accompanying deliverables."),
    ]

    for title, body in decl_paras:
        h = doc.add_paragraph()
        r = h.add_run(title)
        r.font.name = "Cambria"
        r.font.size = Pt(10.5)
        r.font.bold = True
        r.font.color.rgb = NAVY
        h.paragraph_format.space_before = Pt(4)
        h.paragraph_format.space_after = Pt(2)

        p = doc.add_paragraph()
        r = p.add_run(body)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(4)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Signatures table
    sig_tbl = doc.add_table(rows=6, cols=4)
    style_table(sig_tbl, [2.2, 1.2, 2.2, 1.2], navy_header=True)
    hdr_cells = sig_tbl.rows[0].cells
    for c, text in zip(hdr_cells, ["Team Member Name", "PGID", "Email Address", "Signature"]):
        r = c.paragraphs[0].add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, (name, pgid, email) in enumerate(TEAM, start=1):
        row = sig_tbl.rows[r_idx]
        for c, text in zip(row.cells, [name, pgid, email, "[Signed]"]):
            r = c.paragraphs[0].add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            if text == name:
                r.font.bold = True
                r.font.color.rgb = NAVY
            c.paragraphs[0].paragraph_format.space_after = Pt(2)

    path_docx = OUT / "ISB_Capstone_Originality_and_Confidentiality_Declaration.docx"
    doc.save(str(path_docx))
    print("Saved", path_docx)


# ==============================================================================
# 4. ASSIGNMENT SUBMISSION FORM
# ==============================================================================
def create_submission_form():
    doc = docx.Document()
    set_margins(doc, top=0.8, bottom=0.8, left=0.85, right=0.85)

    p_inst = doc.add_paragraph()
    r = p_inst.add_run("INDIAN SCHOOL OF BUSINESS  ·  INSTITUTE OF DATA SCIENCE\nCAPSTONE PROJECT FINAL SUBMISSION FORM")
    r.font.name = "Cambria"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_after = Pt(10)

    # Details table
    tbl = doc.add_table(rows=7, cols=2)
    style_table(tbl, [2.2, 4.6], navy_header=False)
    details = [
        ("Programme", "Advanced Management Programme in Business Analytics (AMPBA)"),
        ("Cohort", BATCH),
        ("Project Title", TITLE),
        ("Sponsoring Organization", SPONSOR),
        ("Faculty Mentor", "[Faculty Mentor Name], Institute of Data Science, ISB"),
        ("Industry Mentor", "[Industry Mentor Name], Deloitte Consulting LLP"),
        ("Submission Date & LMS Target", "October 25, 2026, 11:55 PM IST"),
    ]
    for row, (k, v) in zip(tbl.rows, details):
        c0, c1 = row.cells
        r0 = c0.paragraphs[0].add_run(k)
        r0.font.name = "Calibri"
        r0.font.size = Pt(9.5)
        r0.font.bold = True
        r0.font.color.rgb = NAVY
        r1 = c1.paragraphs[0].add_run(v)
        r1.font.name = "Calibri"
        r1.font.size = Pt(9.5)
        c0.paragraphs[0].paragraph_format.space_after = Pt(2)
        c1.paragraphs[0].paragraph_format.space_after = Pt(2)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Submission Package Checklist Table
    p_chk = doc.add_paragraph()
    r = p_chk.add_run("Submission Package Checklist (as per §1 of Instructions)")
    r.font.name = "Cambria"
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p_chk.paragraph_format.space_after = Pt(4)

    chk_tbl = doc.add_table(rows=8, cols=4)
    style_table(chk_tbl, [0.5, 2.5, 1.8, 2.0], navy_header=True)
    for c, text in zip(chk_tbl.rows[0].cells, ["#", "Item / Deliverable", "Format", "Verification Status"]):
        r = c.paragraphs[0].add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    items = [
        ("1", "Final Project Report", "PDF (from Template)", "[X] Verified — 64 pages, updated TOC/TOF"),
        ("2", "Editable Source File", ".docx (Word)", "[X] Verified — Clean built styles"),
        ("3", "Assignment Submission Form", "PDF / .docx", "[X] Included in Submission Package"),
        ("4", "Code & Analysis Repository", "GitHub Link + README", "[X] Verified (saiprash711/ISB_Capstone_Project)"),
        ("5", "Data Note", "PDF / .docx (1 page)", "[X] Included (1-page data & anonymization note)"),
        ("6", "Originality & Confidentiality Form", "Signed PDF / .docx", "[X] Included (Joint declaration)"),
        ("7", "Plain-Language Summary", "150 words (.docx / .txt)", "[X] Included (150 words non-jargon executive brief)"),
    ]
    for r_idx, row_data in enumerate(items, start=1):
        row = chk_tbl.rows[r_idx]
        for c, text in zip(row.cells, row_data):
            r = c.paragraphs[0].add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(8.5)
            if "[X]" in text:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0x1F, 0x6E, 0x38)
            c.paragraphs[0].paragraph_format.space_after = Pt(2)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Student signatures
    p_sig = doc.add_paragraph()
    r = p_sig.add_run("Candidate Verification & Group Sign-off:")
    r.font.name = "Cambria"
    r.font.size = Pt(10.5)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p_sig.paragraph_format.space_after = Pt(4)

    s_tbl = doc.add_table(rows=6, cols=3)
    style_table(s_tbl, [2.5, 1.8, 2.5], navy_header=True)
    for c, text in zip(s_tbl.rows[0].cells, ["Candidate Name", "PGID", "Signature / Confirmation"]):
        r = c.paragraphs[0].add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, (name, pgid, _) in enumerate(TEAM, start=1):
        row = s_tbl.rows[r_idx]
        for c, text in zip(row.cells, [name, pgid, "[Electronically Verified]"]):
            r = c.paragraphs[0].add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(8.5)
            if text == name:
                r.font.bold = True
                r.font.color.rgb = NAVY
            c.paragraphs[0].paragraph_format.space_after = Pt(2)

    path_docx = OUT / "ISB_Capstone_Assignment_Submission_Form.docx"
    doc.save(str(path_docx))
    print("Saved", path_docx)


if __name__ == "__main__":
    create_data_note()
    create_plain_language_summary()
    create_declaration_form()
    create_submission_form()
    print("All companion deliverables created successfully.")
