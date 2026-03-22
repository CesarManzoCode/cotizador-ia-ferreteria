"""
╔══════════════════════════════════════════════════════════════════════╗
║           PUNTO DE ENTRADA PRINCIPAL - COTIZADOR IA                 ║
║                                                                      ║
║  Uso:                                                                ║
║    python app.py              ← Arranca backend + abre frontend      ║
║    python app.py --solo-api   ← Solo el backend FastAPI              ║
║                                                                      ║
║  Requisitos previos:                                                 ║
║    1. Instalar dependencias del backend:                             ║
║       cd backend && pip install -r requirements.txt                  ║
║    2. Instalar dependencias del frontend:                            ║
║       cd frontend && npm install                                     ║
║    3. Copiar y configurar el .env:                                   ║
║       cd backend && copy .env.example .env                           ║
║       (luego editar .env con tu GROQ_API_KEY y EXCEL_RUTA)           ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

# Directorio raíz del proyecto
RAIZ = Path(__file__).parent
BACKEND_DIR = RAIZ / "backend"
FRONTEND_DIR = RAIZ / "frontend"

# URLs del sistema
URL_BACKEND = "http://localhost:8000"
URL_FRONTEND = "http://localhost:5173"
URL_API_DOCS = "http://localhost:8000/api/docs"


def verificar_requisitos():
    """Verifica que los requisitos mínimos estén instalados."""
    print("🔍 Verificando requisitos...")

    # Verificar Python
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ requerido. Versión actual: {version.major}.{version.minor}")
        sys.exit(1)
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")

    # Verificar que existe el .env
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        ejemplo = BACKEND_DIR / ".env.example"
        print(f"\n⚠️  No se encontró el archivo .env en: {env_file}")
        print(f"   Copia el archivo de ejemplo y configúralo:")
        print(f"   cd backend && copy .env.example .env")
        print(f"   Luego edita .env con tu GROQ_API_KEY y EXCEL_RUTA\n")
        # No detener: el sistema puede arrancar sin .env (con valores por defecto)

    # Verificar node_modules del frontend
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print(f"\n⚠️  Dependencias del frontend no instaladas.")
        print(f"   Ejecuta: cd frontend && npm install\n")

    print()


def iniciar_backend():
    """Inicia el servidor FastAPI con uvicorn."""
    print("🚀 Iniciando backend FastAPI en http://localhost:8000 ...")

    # Cambiar al directorio del backend para que .env y las rutas relativas funcionen
    proceso = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",   # Recarga automática al cambiar código (desarrollo)
        ],
        cwd=str(BACKEND_DIR),
        # En Windows, CREATE_NEW_PROCESS_GROUP permite terminar el proceso limpiamente
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )
    return proceso


def iniciar_frontend():
    """Inicia el servidor de desarrollo de Vite (React)."""
    print("🎨 Iniciando frontend React en http://localhost:5173 ...")

    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"

    proceso = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(FRONTEND_DIR),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )
    return proceso


def esperar_y_abrir_navegador():
    """Espera a que el sistema arranque y abre el navegador."""
    print("\n⏳ Esperando que los servidores arranquen...")
    time.sleep(4)
    print(f"\n✅ Sistema listo!")
    print(f"   Frontend:  {URL_FRONTEND}")
    print(f"   Backend:   {URL_BACKEND}")
    print(f"   API Docs:  {URL_API_DOCS}")
    print(f"\n   Presiona Ctrl+C para detener el sistema.\n")
    webbrowser.open(URL_FRONTEND)


def main():
    """Punto de entrada principal."""
    solo_api = "--solo-api" in sys.argv

    print("=" * 60)
    print("  🤖 COTIZADOR IA — Sistema de Cotizaciones Asistidas")
    print("=" * 60)
    print()

    verificar_requisitos()

    procesos = []

    try:
        # Iniciar backend siempre
        proc_backend = iniciar_backend()
        procesos.append(proc_backend)

        if not solo_api:
            # Iniciar frontend
            proc_frontend = iniciar_frontend()
            procesos.append(proc_frontend)
            esperar_y_abrir_navegador()
        else:
            print(f"\n✅ Backend iniciado en {URL_BACKEND}")
            print(f"   API Docs: {URL_API_DOCS}")
            print(f"   Presiona Ctrl+C para detener.\n")

        # Mantener el script corriendo hasta Ctrl+C
        for proceso in procesos:
            proceso.wait()

    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo sistema...")
        for proceso in procesos:
            try:
                if os.name == "nt":
                    proceso.send_signal(subprocess.signal.CTRL_BREAK_EVENT)
                else:
                    proceso.terminate()
            except Exception:
                proceso.kill()
        print("✅ Sistema detenido correctamente.\n")


if __name__ == "__main__":
    main()
