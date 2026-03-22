@echo off
REM ══════════════════════════════════════════════════════════════════════
REM  COTIZADOR IA — Script de arranque para Windows
REM  Doble clic para arrancar el sistema completo.
REM ══════════════════════════════════════════════════════════════════════

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║       COTIZADOR IA — Iniciando sistema       ║
echo  ╚══════════════════════════════════════════════╝
echo.

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no encontrado. Instala Python 3.11+ desde https://python.org
    pause
    exit /b 1
)

REM Verificar que el .env existe
if not exist "backend\.env" (
    echo  AVISO: No se encontro backend\.env
    echo  Copia backend\.env.example a backend\.env y configura tus variables.
    echo.
    pause
)

REM Arrancar con Python
python app.py

pause
