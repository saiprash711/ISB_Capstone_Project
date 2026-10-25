# Opens the generated report in Microsoft Word, refreshes the Table of Contents,
# List of Tables, List of Figures and caption numbers, saves, and exports a PDF.
param(
    [string]$Docx = "$PSScriptRoot\ISB_Capstone_Final_Report.docx",
    [string]$Pdf  = "$PSScriptRoot\ISB_Capstone_Final_Report.pdf"
)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Docx, $false, $false)
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
    foreach ($tof in $doc.TablesOfFigures) { $tof.Update() | Out-Null }
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.UpdatePageNumbers() | Out-Null }
    foreach ($tof in $doc.TablesOfFigures) { $tof.UpdatePageNumbers() | Out-Null }
    $doc.Save()
    # 17 = wdExportFormatPDF; requires the Save-as-PDF add-in on Word 2007
    $doc.ExportAsFixedFormat($Pdf, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1)
    "Pages: " + $doc.ComputeStatistics(2)
    $doc.Close()
} finally {
    try { $word.Quit() } catch { }   # Word sometimes exits before Quit is acknowledged
}
