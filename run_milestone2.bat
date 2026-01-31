@echo off
cd /d "%~dp0"
echo ========================================================
echo   SEG301 - MILESTONE 2: CORE SEARCH ENGINE SETUP
echo ========================================================

echo.
echo [1/3] Running SPIMI Indexer...
echo --------------------------------------------------------
python src/indexer/spimi.py
IF %ERRORLEVEL% NEQ 0 (
    echo Error running SPIMI Indexer!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Merging Blocks to Final Index...
echo --------------------------------------------------------
python src/indexer/merging.py
IF %ERRORLEVEL% NEQ 0 (
    echo Error running Merger!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] Starting Search Application...
echo --------------------------------------------------------
python src/search_app.py

pause
