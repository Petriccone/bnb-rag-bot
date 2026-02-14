# Inicia o ngrok na porta 8000 (backend). Use em um terminal separado.
# A URL HTTPS que aparecer deve ser colocada no .env como TELEGRAM_WEBHOOK_BASE_URL
$ngrok = "C:\Users\rsp88\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
if (-not (Test-Path $ngrok)) {
    Write-Host "ngrok nao encontrado. Instale com: winget install ngrok.ngrok" -ForegroundColor Red
    exit 1
}
& $ngrok http 8000
