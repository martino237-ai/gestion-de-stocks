@echo off
title SVGS - Systeme de Vente et Gestion des Stocks
color 1F
echo ============================================
echo    SVGS - Lancement de l'application
echo    MBOLONG - PFE Informatique 2026
echo ============================================
echo.

:: Verifier si le venv existe et l'utiliser si possible
set "VENV_PY=%~dp0..\..\..\.venv\Scripts\python.exe"
if exist "%VENV_PY%" (
    set "PYTHON=%VENV_PY%"
) else (
    set "PYTHON=python"
)

:: Verifier Python
"%PYTHON%" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo Telechargez Python depuis https://python.org
    pause
    exit /b 1
)

:: Installer les dependances si necessaire
echo [INFO] Verification des dependances...
"%PYTHON%" -m pip install mysql-connector-python --quiet --break-system-packages 2>nul
"%PYTHON%" -m pip install mysql-connector-python --quiet 2>nul

:: Lancer l'application
echo [INFO] Demarrage de SVGS...
echo.
"%PYTHON%" "%~dp0main.py"

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] L'application s'est terminee avec une erreur.
    pause
)
