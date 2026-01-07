# set_adobe_pdf_env.ps1

Write-Host "Setting Adobe PDF Services environment variables..." -ForegroundColor Cyan

# Set for CURRENT PowerShell session
$env:PDF_SERVICES_CLIENT_ID = "PASTE_CLIENT_ID_HERE"
$env:PDF_SERVICES_CLIENT_SECRET = "PASTE_CLIENT_SECRET_HERE"
$env:PDF_SERVICES_ORG_ID = "PASTE_ORGANIZATION_ID_HERE"

# Persist for FUTURE sessions
setx PDF_SERVICES_CLIENT_ID     $env:PDF_SERVICES_CLIENT_ID
setx PDF_SERVICES_CLIENT_SECRET $env:PDF_SERVICES_CLIENT_SECRET
setx PDF_SERVICES_ORG_ID        $env:PDF_SERVICES_ORG_ID

Write-Host "`nEcho from inside script (current session):" -ForegroundColor Yellow
echo $env:PDF_SERVICES_CLIENT_ID
echo $env:PDF_SERVICES_CLIENT_SECRET
echo $env:PDF_SERVICES_ORG_ID

Write-Host "`n⚠️ Restart PowerShell / VS Code / Uvicorn after this" -ForegroundColor Red
Pause
