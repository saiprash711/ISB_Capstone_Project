$files = @(
    'ISB_Capstone_Plain_Language_Summary',
    'ISB_Capstone_Originality_and_Confidentiality_Declaration',
    'ISB_Capstone_Assignment_Submission_Form'
)
foreach ($f in $files) {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    try {
        $docxPath = (Resolve-Path "$PSScriptRoot\$f.docx").Path
        $pdfPath  = [System.IO.Path]::ChangeExtension($docxPath, '.pdf')
        $doc = $word.Documents.Open($docxPath, $false, $true)
        $doc.ExportAsFixedFormat($pdfPath, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1)
        $pages = $doc.ComputeStatistics(2)
        $doc.Close()
        Write-Host "Exported $f.pdf - Pages: $pages"
    } finally {
        try { $word.Quit() } catch { }
    }
}
