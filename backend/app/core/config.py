"""
Configuración central del sistema.
Lee variables de entorno desde el archivo .env usando Pydantic Settings.
Todos los parámetros configurables del sistema están aquí.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Configuración principal de la aplicación.
    Todas las variables pueden sobreescribirse desde el archivo .env
    """

    # ── Información general ────────────────────────────────────────────────────
    APP_NOMBRE: str = "Cotizador IA"
    APP_VERSION: str = "1.0.0"

    # ── Base de datos ──────────────────────────────────────────────────────────
    # SQLite se crea automáticamente, no requiere instalación manual
    DATABASE_URL: str = "sqlite+aiosqlite:///./cotizador.db"

    # ── Excel de lista de precios ──────────────────────────────────────────────
    # IMPORTANTE: Pon aquí la ruta completa o relativa a tu archivo Excel.
    # Ejemplo en Windows: C:\Users\tu_usuario\precios\lista_precios.xlsx
    # Ejemplo relativo: ../listas/precios.xlsx
    # PUNTO DE DEBUGGING: Si el Excel no carga, verifica esta ruta primero.
    EXCEL_RUTA: str = "./lista_precios.xlsx"

    # Hoja del Excel que contiene el catálogo (primera hoja por defecto)
    EXCEL_HOJA: str = ""  # Vacío = primera hoja disponible

    # Fila donde comienzan los encabezados (0-indexed, normalmente 0)
    # PUNTO DE DEBUGGING: Si tu Excel tiene filas de encabezado extra, ajusta esto
    EXCEL_FILA_ENCABEZADO: int = 0

    # ── Groq (LLM) ────────────────────────────────────────────────────────────
    # Obtén tu API key gratuita en: https://console.groq.com
    GROQ_API_KEY: str = ""

    # Modelo de Groq a usar. Puedes cambiarlo sin modificar código.
    # Modelos disponibles en Groq: llama-3.3-70b-versatile, mixtral-8x7b-32768, etc.
    GROQ_MODELO: str = "llama-3.3-70b-versatile"

    # URL base de la API de Groq (no cambiar salvo que Groq cambie su endpoint)
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Temperatura del modelo (0 = determinista, 1 = creativo)
    # Para extracción de productos, valores bajos son más precisos
    GROQ_TEMPERATURA: float = 0.1

    # Máximo de tokens en la respuesta del LLM
    GROQ_MAX_TOKENS: int = 2000

    # ── Matching y umbrales ───────────────────────────────────────────────────
    # PUNTO DE DEBUGGING: Ajusta estos umbrales según el comportamiento real
    # del matching con tu lista de precios específica.

    # Umbral mínimo de similitud para considerar una coincidencia válida (0-100)
    # Por encima de este valor: coincidencia aceptada automáticamente
    MATCHING_UMBRAL_ALTO: float = 75.0

    # Entre UMBRAL_BAJO y UMBRAL_ALTO: coincidencia dudosa (genera advertencia)
    MATCHING_UMBRAL_BAJO: float = 50.0

    # Por debajo de UMBRAL_BAJO: producto no encontrado (cotización manual)

    # Número máximo de candidatos a evaluar por producto
    MATCHING_MAX_CANDIDATOS: int = 5

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Orígenes permitidos para el frontend React
    CORS_ORIGENES: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── Exportación ───────────────────────────────────────────────────────────
    # Directorio temporal donde se guardan los Excel generados
    EXPORTAR_DIR_TEMPORAL: str = "./temp_cotizaciones"

    # Nombre base del archivo de cotización generado
    EXPORTAR_NOMBRE_BASE: str = "cotizacion"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Permite variables de entorno case-insensitive
        case_sensitive = False


# Instancia global de configuración
# Importar desde aquí en todos los módulos: from app.core.config import settings
settings = Settings()
