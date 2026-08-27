@echo off
echo ===================================================
echo [1/3] Setting Git Remote URL...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/george770131/sportsbet-odds-analysis.git

echo [2/3] Setting Main Branch...
git branch -M main

echo [3/3] Pushing Code to GitHub...
echo If a browser window pops up, please click Sign In / Authorize.
echo.
git push -u origin main

echo.
echo ===================================================
echo Finished! Press any key to exit.
echo ===================================================
pause
