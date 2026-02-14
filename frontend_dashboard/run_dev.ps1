# Roda o Next.js sem depender de npx/PATH. Execute dentro de frontend_dashboard.
Set-Location $PSScriptRoot
if (-not (Test-Path node_modules\next)) {
    Write-Host "Instalando dependencias (npm install)..."
    npm install
}
node node_modules\next\dist\bin\next dev
