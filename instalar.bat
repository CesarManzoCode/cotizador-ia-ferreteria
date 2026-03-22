@echo off
REM ══════════════════════════════════════════════════════════════════════
REM  COTIZADOR IA — Script de instalación para Windows
REM  Ejecuta este script UNA VEZ antes de usar el sistema.
REM ══════════════════════════════════════════════════════════════════════

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║     COTIZADOR IA — Instalacion inicial       ║
echo  ╚══════════════════════════════════════════════╝
echo.

echo [1/4] Verificando Python...
python --version
if errorlevel 1 (
    echo  ERROR: Python no encontrado. Instala Python 3.11+ desde https://python.org
    pause
    exit /b 1
)

echo.
echo [2/4] Instalando dependencias del backend...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo  ERROR: Fallo la instalacion de dependencias del backend.
    pause
    exit /b 1
)
cd ..

echo.
echo [3/4] Instalando dependencias del frontend...
cd frontend
call npm install
if errorlevel 1 (
    echo  ERROR: Fallo la instalacion de dependencias del frontend.
    pause
    exit /b 1
)
cd ..

echo.
echo [4/4] Configurando archivo .env...
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env"
    echo  Archivo .env creado desde .env.example
    echo.
    echo  *** IMPORTANTE: Abre backend\.env y configura: ***
    echo      GROQ_API_KEY=tu_api_key_aqui
    echo      EXCEL_RUTA=ruta\a\tu\lista_precios.xlsx
    echo.
) else (
    echo  El archivo .env ya existe. No se sobreescribio.
)

echo.
echo  ══════════════════════════════════════════════
echo  Instalacion completada correctamente.
echo  Siguiente paso: edita backend\.env con tus datos
echo  Luego ejecuta: arrancar.bat
echo  ══════════════════════════════════════════════
echo.
pause
