Set-Location $PSScriptRoot

$git = "C:\Users\qazx5\AppData\Local\MinGit\cmd\git.exe"
if (-not (Test-Path $git)) {
    $git = "git"
}

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Syncing latest code to GitHub..." -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

& $git init
& $git config user.name "george770131"
& $git config user.email "george770131@users.noreply.github.com"
& $git remote remove origin 2>$null
& $git remote add origin https://github.com/george770131/sportsbet-odds-analysis.git

& $git add .
& $git commit -m "Fix handicap lines and dynamic team spread rendering"
& $git branch -M main

Write-Host "Pushing to GitHub..." -ForegroundColor Green
& $git push -f -u origin main

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Sync complete! Streamlit Cloud will update shortly." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
