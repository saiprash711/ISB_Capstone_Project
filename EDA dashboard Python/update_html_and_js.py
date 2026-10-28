import os
import shutil

ROOT_DIR = r"C:\ISB Capstone"
INDEX_PATH = os.path.join(ROOT_DIR, "index.html")
PUBLIC_INDEX_PATH = os.path.join(ROOT_DIR, "public", "index.html")

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update quick-meta-strip to add Final Report badge
old_meta = """            <div class="meta-chip">
              <span>Completeness:</span>
              <strong style="color: #0284C7;">95.0%</strong>
            </div>
          </div>"""

new_meta = """            <div class="meta-chip">
              <span>Completeness:</span>
              <strong style="color: #0284C7;">95.0%</strong>
            </div>
            <div class="meta-chip" style="border: 1px solid rgba(99, 102, 241, 0.4); background: rgba(99, 102, 241, 0.1);">
              <span>Deliverable:</span>
              <a href="assets/ISB_Capstone_Final_Report.pdf" download="ISB_Capstone_Final_Report.pdf" style="color: #6366F1; font-weight: 700; text-decoration: none;">🎓 Final Report PDF</a>
            </div>
          </div>"""

if old_meta in html:
    html = html.replace(old_meta, new_meta, 1)
    print("Updated quick-meta-strip with Final Report link")

# 2. Update Top Nav bar button label
old_nav_btn = '<button type="button" class="top-segment-btn" data-target="reports">📄 C-Suite Reports</button>'
new_nav_btn = '<button type="button" class="top-segment-btn" data-target="reports">📄 Final Report &amp; Deliverables</button>'
if old_nav_btn in html:
    html = html.replace(old_nav_btn, new_nav_btn, 1)
    print("Updated top nav button label")

# 3. Update view-holdout download strip to include Final Report and add Operational Rolling table
old_holdout_strip = """            <a href="assets/verification.json" download="verification.json" class="btn btn-emerald">
              🛡️ Download Forensic Verification Audit (.json)
            </a>
            <a href="assets/ISB_Capstone_Final_Report.pdf" download="ISB_Capstone_Final_Report.pdf" class="btn btn-secondary" style="border: 1px solid #6366F1; color: #6366F1;">
              📕 Read Final Report Holdout Chapter (PDF)
            </a>
          </div>
        </div>"""

rolling_table_html = """        <!-- Operational Rolling Re-Forecast Leaderboard -->
        <div class="glass-panel" style="margin-top: 24px;">
          <div class="subpanel-title" style="color: #0284C7;">🔄 Operational Rolling Horizon Leaderboard (Re-Forecast Every 4 Weeks &bull; Next 4 Weeks Ahead)</div>
          <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 12px;">
            Simulating live production usage: every 4 weeks the engine is retrained on historical actuals to issue rolling replenishment forecasts.
          </p>
          <div class="table-scroll-container" style="max-height: 320px; overflow-y: auto;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Echelon Level</th>
                  <th>Engine Accuracy</th>
                  <th>Same Week Last Year</th>
                  <th>4-Week Moving Avg</th>
                  <th>Engine Bias</th>
                  <th>APICS Operational Verdict</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>South Region x Quarter</strong></td>
                  <td><strong style="color: #10B981;">71.8%</strong></td>
                  <td>68.2%</td>
                  <td>74.0%</td>
                  <td>+0.6%</td>
                  <td><span class="kpi-badge emerald">EXCELLENT</span></td>
                </tr>
                <tr>
                  <td><strong>South Region x Month</strong></td>
                  <td><strong style="color: #10B981;">65.6%</strong></td>
                  <td>65.6%</td>
                  <td>50.5%</td>
                  <td>+0.6%</td>
                  <td><span class="kpi-badge emerald">OPERATIONAL</span></td>
                </tr>
                <tr>
                  <td><strong>Branch Hub x Month</strong></td>
                  <td><strong style="color: #10B981;">63.4%</strong></td>
                  <td>58.8%</td>
                  <td>46.0%</td>
                  <td>+0.6%</td>
                  <td><span class="kpi-badge emerald">BEATS MOVING AVG (+17.4 pts)</span></td>
                </tr>
                <tr>
                  <td><strong>SKU x Month (South Region)</strong></td>
                  <td><strong style="color: #0284C7;">51.1%</strong></td>
                  <td>-36.9%</td>
                  <td>44.4%</td>
                  <td>+0.6%</td>
                  <td><span class="kpi-badge cyan">BEATS MOVING AVG (+6.7 pts)</span></td>
                </tr>
                <tr>
                  <td><strong>SKU x Branch x Month</strong></td>
                  <td><strong style="color: #0284C7;">38.5%</strong></td>
                  <td>-44.6%</td>
                  <td>35.6%</td>
                  <td>+0.6%</td>
                  <td><span class="kpi-badge cyan">BEATS NAIVE (+83.1 pts)</span></td>
                </tr>
                <tr>
                  <td><strong>SKU x Branch x Week</strong></td>
                  <td><strong style="color: #6366F1;">2.1%</strong></td>
                  <td>-61.2%</td>
                  <td>0.4%</td>
                  <td>+0.6%</td>
                  <td><span class="kpi-badge purple">POSITIVE AT HIGH LUMPINESS</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>"""

new_holdout_strip = old_holdout_strip + "\n\n" + rolling_table_html

if "Operational Rolling Horizon Leaderboard" not in html and old_holdout_strip in html:
    html = html.replace(old_holdout_strip, new_holdout_strip, 1)
    print("Added Operational Rolling Horizon Leaderboard table")


# 4. Update view-reports to add the Final Report Package
old_reports_section = """      <!-- ===================================================================
           VIEW 7: 📄 C-SUITE REPORTS
      ==================================================================== -->
      <section class="view-content" id="view-reports" style="display: none;">
        <div class="section-title-wrap">
          <h2 class="section-title">📄 Executive Reports &amp; Data Export Center</h2>
          <p class="section-subtitle">Generate automated C-Suite PDF briefing documents and presentation slide decks</p>
        </div>

        <div class="charts-row-equal">
          <div class="glass-panel">
            <div class="subpanel-title" style="color: var(--primary-color);">📑 Executive Report Structure</div>
            <ol class="panel-bullet-list" style="margin-left: 10px;">
              <li><strong>1. Executive Summary:</strong> High-level strategic briefing on South Region sales velocity.</li>
              <li><strong>2. Data Integrity Audit:</strong> Completeness ratios, missing field density, and schema metrics.</li>
              <li><strong>3. Predictive Modeling:</strong> ARIMA &amp; Machine Learning 180-day forecast outputs.</li>
              <li><strong>4. Strategic Directives:</strong> Actionable inventory buffers and branch allocations.</li>
            </ol>
          </div>

          <div class="glass-panel">
            <div class="subpanel-title" style="color: #10B981;">📥 Executive Deliverables (1-Click Downloads)</div>
            <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 10px;">
              <a href="assets/Capstone_Weekly_Report_26.10.26.pdf" download="Capstone_Weekly_Report_26.10.26.pdf" class="btn btn-primary" style="background: linear-gradient(135deg, #0284C7, #0369A1);">
                📄 Download Latest Capstone Weekly Report (26.10.2026 &bull; PDF)
              </a>
              <a href="assets/Capstone_Weekly_Report_25.10.26.pdf" download="Capstone_Weekly_Report_25.10.26.pdf" class="btn btn-secondary">
                📄 Download Capstone Weekly Report (25.10.2026 &bull; PDF)
              </a>
              <a href="assets/holdout_validation_FY24-25.xlsx" download="holdout_validation_FY24-25.xlsx" class="btn btn-emerald">
                📊 Download FY24-25 Holdout Validation Workbook (.xlsx)
              </a>

              <a href="assets/Executive_Report.pdf" download="Executive_Report.pdf" class="btn btn-primary">
                📄 Download Executive Report (.pdf &bull; 528 KB)
              </a>
              <a href="assets/Presentation_Deck.pptx" download="Presentation_Deck.pptx" class="btn btn-secondary">
                📊 Download Presentation Deck (.pptx &bull; 830 KB)
              </a>
              <a href="assets/ARIMA_Forecast_Results.csv" download="ARIMA_Forecast_Results.csv" class="btn btn-emerald">
                📈 Download ARIMA Forecast Dataset (.csv &bull; 17 KB)
              </a>
            </div>
          </div>
        </div>
      </section>"""

new_reports_section = """      <!-- ===================================================================
           VIEW 7: 📄 C-SUITE REPORTS & FINAL DELIVERABLES
      ==================================================================== -->
      <section class="view-content" id="view-reports" style="display: none;">
        <div class="section-title-wrap">
          <h2 class="section-title">📄 Executive Reports &amp; Final Deliverables Center</h2>
          <p class="section-subtitle">Official ISB Capstone Final Report, Academic Submission Package, and Executive C-Suite Briefings</p>
        </div>

        <!-- Official Final Capstone Submission Package -->
        <div class="glass-panel" style="margin-bottom: 24px; border: 1px solid rgba(99, 102, 241, 0.4); background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(16, 185, 129, 0.05));">
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
            <div>
              <div class="subpanel-title" style="color: #6366F1; font-size: 1.15rem; margin-bottom: 4px;">🎓 Official ISB Capstone Final Report Package (October 2026)</div>
              <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 0;">
                Demand Prediction by SKU: Forecasting Lumpy Room Air-Conditioner Demand for Depot Replenishment &bull; Deloitte Touche Tohmatsu India LLP &bull; AMPBA Class of 2026S
              </p>
            </div>
            <span class="kpi-badge emerald" style="font-size: 0.85rem; padding: 6px 12px;">✅ SUBMISSION READY</span>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-top: 14px;">
            <a href="assets/ISB_Capstone_Final_Report.pdf" download="ISB_Capstone_Final_Report.pdf" class="btn btn-primary" style="background: linear-gradient(135deg, #4F46E5, #6366F1); justify-content: center;">
              📕 Download Final Report (.pdf &bull; 1.7 MB)
            </a>
            <a href="assets/ISB_Capstone_Final_Report.docx" download="ISB_Capstone_Final_Report.docx" class="btn btn-secondary" style="justify-content: center;">
              📘 Download Final Report (.docx &bull; 1.4 MB)
            </a>
            <a href="assets/ISB_Capstone_Assignment_Submission_Form.pdf" download="ISB_Capstone_Assignment_Submission_Form.pdf" class="btn btn-emerald" style="justify-content: center;">
              📋 Assignment Submission Form (.pdf)
            </a>
            <a href="assets/ISB_Capstone_Data_Note.pdf" download="ISB_Capstone_Data_Note.pdf" class="btn btn-emerald" style="justify-content: center;">
              📊 Data Note (1-Page Methodology) (.pdf)
            </a>
            <a href="assets/ISB_Capstone_Originality_and_Confidentiality_Declaration.pdf" download="ISB_Capstone_Originality_and_Confidentiality_Declaration.pdf" class="btn btn-secondary" style="justify-content: center;">
              🛡️ Originality &amp; Confidentiality Declaration (.pdf)
            </a>
            <a href="assets/ISB_Capstone_Plain_Language_Summary.pdf" download="ISB_Capstone_Plain_Language_Summary.pdf" class="btn btn-primary" style="background: linear-gradient(135deg, #059669, #10B981); justify-content: center;">
              📝 Plain-Language Summary (.pdf)
            </a>
          </div>
        </div>

        <div class="charts-row-equal">
          <div class="glass-panel">
            <div class="subpanel-title" style="color: var(--primary-color);">📑 Executive Report Structure &amp; Methodology</div>
            <ol class="panel-bullet-list" style="margin-left: 10px;">
              <li><strong>1. Executive Summary &amp; Business Context:</strong> RAC supply chain replenishment dynamics across South Region hubs.</li>
              <li><strong>2. Forensic Data Integrity &amp; Leakage Audit:</strong> 14/14 automated audit checks, strict chronological train/test separation.</li>
              <li><strong>3. Multi-Model Time Series &amp; ML Architecture:</strong> 18 candidate algorithms, hierarchical reconciliation &amp; APICS smoothing.</li>
              <li><strong>4. Out-of-Sample FY24-25 Holdout Validation:</strong> 444,274 units evaluated across 154 SKUs and 5 regional branches.</li>
              <li><strong>5. Strategic Replenishment Directives:</strong> Buffer stock calibrations, service level guarantees, and deployment roadmap.</li>
            </ol>
          </div>

          <div class="glass-panel">
            <div class="subpanel-title" style="color: #10B981;">📥 Weekly Updates &amp; Supporting Deliverables</div>
            <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 10px;">
              <a href="assets/Capstone_Weekly_Report_26.10.26.pdf" download="Capstone_Weekly_Report_26.10.26.pdf" class="btn btn-primary" style="background: linear-gradient(135deg, #0284C7, #0369A1);">
                📄 Download Latest Capstone Weekly Report (26.10.2026 &bull; PDF)
              </a>
              <a href="assets/Capstone_Weekly_Report_25.10.26.pdf" download="Capstone_Weekly_Report_25.10.26.pdf" class="btn btn-secondary">
                📄 Download Capstone Weekly Report (25.10.2026 &bull; PDF)
              </a>
              <a href="assets/holdout_validation_FY24-25.xlsx" download="holdout_validation_FY24-25.xlsx" class="btn btn-emerald">
                📊 Download FY24-25 Holdout Validation Workbook (.xlsx)
              </a>
              <a href="assets/Executive_Report.pdf" download="Executive_Report.pdf" class="btn btn-primary">
                📄 Download Executive Report (.pdf &bull; 528 KB)
              </a>
              <a href="assets/Presentation_Deck.pptx" download="Presentation_Deck.pptx" class="btn btn-secondary">
                📊 Download Presentation Deck (.pptx &bull; 830 KB)
              </a>
              <a href="assets/ARIMA_Forecast_Results.csv" download="ARIMA_Forecast_Results.csv" class="btn btn-emerald">
                📈 Download ARIMA Forecast Dataset (.csv &bull; 17 KB)
              </a>
            </div>
          </div>
        </div>
      </section>"""

if old_reports_section in html:
    html = html.replace(old_reports_section, new_reports_section, 1)
    print("Updated view-reports section with Final Report Package")
else:
    print("Warning: old_reports_section not found verbatim")

# Write updated index.html
with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Written: {INDEX_PATH}")

# Copy to public/index.html
shutil.copy2(INDEX_PATH, PUBLIC_INDEX_PATH)
print(f"Copied to: {PUBLIC_INDEX_PATH}")
