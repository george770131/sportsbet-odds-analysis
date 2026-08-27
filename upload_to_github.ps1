git remote remove origin 2>$null
git remote add origin https://github.com/george770131/sportsbet-odds-analysis.git
git branch -M main
Write-Host "正在上傳代碼至 GitHub，請稍候..." -ForegroundColor Green
git push -u origin main
Write-Host "上傳完成！按任意鍵關閉視窗..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
