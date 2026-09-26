@echo off
REM Construit dist\AimToLearn.exe : un seul fichier, sans fenetre de console.
REM Prerequis : Windows, Python 3.10+ avec le lanceur "py", acces internet (pip).
REM A lancer depuis un dossier Windows (C:\...) et non depuis \\wsl$ :
REM cmd.exe ne sait pas se placer dans un chemin UNC.
setlocal
cd /d "%~dp0"

REM Environnement de build isole, cree au premier lancement seulement
if not exist .venv-win (
    py -3 -m venv .venv-win || goto :error
)
call .venv-win\Scripts\activate.bat || goto :error
python -m pip install --quiet --upgrade pip || goto :error
python -m pip install --quiet "pygame-ce>=2.5" pyinstaller || goto :error

REM --onefile : un seul .exe a distribuer ; --windowed : pas de console noire
pyinstaller --noconfirm --clean --onefile --windowed --name AimToLearn main.py || goto :error

echo.
echo Termine : dist\AimToLearn.exe
exit /b 0

:error
echo ECHEC de la construction (code %errorlevel%)
exit /b 1
