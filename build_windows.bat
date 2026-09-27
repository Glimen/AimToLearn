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
REM --paths / --add-data : paquet du splash (sous-module) et sa police, que
REM PyInstaller ne trouverait pas seul. Sous-module requis : git submodule update --init
pyinstaller --noconfirm --clean --onefile --windowed --name AimToLearn --paths vendor\copper_tortoise_identity --add-data "vendor\copper_tortoise_identity\copper_tortoise_splash\fonts;copper_tortoise_splash/fonts" main.py || goto :error

echo.
echo Termine : dist\AimToLearn.exe
exit /b 0

:error
echo ECHEC de la construction (code %errorlevel%)
exit /b 1
