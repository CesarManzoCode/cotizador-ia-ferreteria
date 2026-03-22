"""
Schemas Pydantic para validación de entrada/salida de la API.
Separan la capa de validación de los modelos de base de datos.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# ── Enumeraciones ──────────────────────────────────────────────────────────────

class NivelConfianza(str, Enum):
    """Nivel de confianza del matching de productos."""
    ALTO = "alto"        # Coincidencia clara, se cotiza automáticamente
    DUDOSO = "dudoso"    # Coincidencia ambigua, requiere revisión
    NO_ENCONTRADO = "no_encontrado"  # Sin coincidencia, cotización manual


# ── Schemas de entrada ─────────────────────────────────────────────────────────

class SolicitudCotizacion(BaseModel):
    """
    Solicitud de cotización enviada desde el frontend.
    El usuario escribe un texto libre describiendo lo que necesita.
    """
    texto: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Descripción libre de los productos a cotizar",
        examples=["Necesito 50 tornillos de 1/4 y 20 taquetes de 3/8"]
    )


# ── Schemas de productos en cotización ────────────────────────────────────────

class ProductoSolicitado(BaseModel):
    """Producto extraído del texto del usuario por el LLM."""
    nombre_original: str
    cantidad: float = 1.0
    unidad_solicitada: Optional[str] = None
    notas_adicionales: Optional[str] = None


class ProductoEncontrado(BaseModel):
    """Resultado del matching para un producto solicitado."""
    # Datos del producto solicitado
    nombre_solicitado: str
    cantidad: float

    # Datos del producto encontrado en catálogo
    producto_id: Optional[int] = None
    nombre_encontrado: Optional[str] = None
    descripcion: Optional[str] = None
    marca: Optional[str] = None
    unidad: Optional[str] = None
    codigo_ferrol: Optional[str] = None

    # Precios
    precio_unitario: Optional[float] = None
    subtotal: Optional[float] = None

    # Matching
    nivel_confianza: NivelConfianza
    score_similitud: float = 0.0
    advertencia: Optional[str] = None


# ── Schema de respuesta completa ───────────────────────────────────────────────

class RespuestaCotizacion(BaseModel):
    """
    Respuesta completa del sistema al frontend.
    Contiene todo lo necesario para mostrar la cotización.
    """
    # ID único de esta cotización (para descarga del Excel)
    cotizacion_id: Optional[int] = None

    # Mensaje del asistente (explicación/confirmación)
    mensaje_asistente: str

    # Productos cotizados (coincidencia alta o dudosa)
    productos: List[ProductoEncontrado] = []

    # Advertencias específicas
    advertencias_dudosas: List[str] = []       # Coincidencias sospechosas
    advertencias_no_encontrados: List[str] = []  # Sin coincidencia

    # Totales
    subtotal: float = 0.0
    total: float = 0.0

    # URL/nombre del Excel generado
    archivo_excel_nombre: Optional[str] = None

    # Estado del proceso
    exito: bool = True
    error: Optional[str] = None


# ── Schemas del catálogo ───────────────────────────────────────────────────────

class ProductoCatalogo(BaseModel):
    """Schema de un producto del catálogo para respuestas de API."""
    id: int
    producto: Optional[str] = None
    descripcion: Optional[str] = None
    marca: Optional[str] = None
    categoria: Optional[str] = None
    unidad: Optional[str] = None
    precio_lista: Optional[float] = None
    precio_publico_neto: Optional[float] = None
    codigo_ferrol: Optional[str] = None

    class Config:
        from_attributes = True


class EstadoCatalogo(BaseModel):
    """Estado actual del catálogo cargado."""
    total_productos: int
    archivo_fuente: str
    estado: str  # "cargado", "vacio", "error"
    mensaje: Optional[str] = None
