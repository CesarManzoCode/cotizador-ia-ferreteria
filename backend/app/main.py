"""
Punto de entrada principal de la API FastAPI.
Este módulo configura la aplicación, middlewares, CORS y rutas principales.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from app.core.config import settings
from app.db.database import inicializar_base_de_datos
from app.api.routes import cotizacion, catalogo, exportar
from app.services.catalogo_service import CatalogoService

# Configuración básica de logging (útil para desarrollo, sin complejidad)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación.
    Se ejecuta al arrancar y al cerrar.
    - Inicializa la base de datos SQLite automáticamente.
    - Carga el catálogo de productos desde el Excel configurado.
    """
    logger.info("=== Iniciando sistema de cotizaciones ===")

    # Crear tablas SQLite si no existen
    await inicializar_base_de_datos()
    logger.info("Base de datos SQLite inicializada correctamente.")

    # Cargar catálogo desde Excel (ruta configurada en .env)
    catalogo_service = CatalogoService()
    try:
        cantidad = await catalogo_service.cargar_catalogo_desde_excel()
        logger.info(f"Catálogo cargado: {cantidad} productos disponibles.")
    except Exception as e:
        # PUNTO DE DEBUGGING: Si el Excel no existe o tiene formato incorrecto,
        # el sistema arranca pero sin catálogo. Revisa EXCEL_RUTA en .env
        logger.warning(f"No se pudo cargar el catálogo: {e}")
        logger.warning("El sistema funcionará sin catálogo hasta que se configure correctamente.")

    yield  # La app corre aquí

    logger.info("=== Sistema de cotizaciones detenido ===")


# Creación de la aplicación FastAPI
app = FastAPI(
    title=settings.APP_NOMBRE,
    version=settings.APP_VERSION,
    description="Sistema local de cotizaciones asistidas por IA",
    lifespan=lifespan,
    # En producción real, considera deshabilitar docs o protegerlos
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Permite que el frontend React (puerto 5173) se comunique con el backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGENES,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── RUTAS DE LA API ────────────────────────────────────────────────────────────
app.include_router(
    cotizacion.router,
    prefix="/api/cotizacion",
    tags=["Cotización"],
)
app.include_router(
    catalogo.router,
    prefix="/api/catalogo",
    tags=["Catálogo"],
)
app.include_router(
    exportar.router,
    prefix="/api/exportar",
    tags=["Exportar"],
)


@app.get("/api/health", tags=["Sistema"])
async def health_check():
    """Endpoint de verificación de salud del sistema."""
    return {
        "estado": "ok",
        "sistema": settings.APP_NOMBRE,
        "version": settings.APP_VERSION,
    }
