# Launch a FREE public HTTPS URL for ApexPulse AI (Zero AWS / Zero Cloud Cost!)
# Proxies your local React + FastAPI + 2.93 GB Trained Model + OpenCV + Companion AI over HTTPS.

$ErrorActionPreference = "Stop"

$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cf) {
    $defaultPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
    if (Test-Path $defaultPath) {
        $cf = $defaultPath
    } else {
        Write-Host "Installing Cloudflare Tunnel (cloudflared) via winget..." -ForegroundColor Cyan
        winget install --id Cloudflare.cloudflared -e --accept-package-agreements --accept-source-agreements
        $cf = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
    }
}

Write-Host "Starting FREE public HTTPS tunnel to http://localhost:5173 ..." -ForegroundColor Green
Write-Host "Share the generated https://*.trycloudflare.com link on any device!" -ForegroundColor Yellow
& $cf tunnel --url http://127.0.0.1:5173
