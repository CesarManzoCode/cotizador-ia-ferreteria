"""
Modelo de base de datos para productos del catálogo.
Refleja las columnas del Excel de lista de precios.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.db.database import Base


class Producto(Base):
    """
    Tabla de productos importados desde el Excel.
    Se recarga desde el Excel al arrancar la aplicación.
    """
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)

    # ── Campos principales del Excel ───────────────────────────────────────────
    # PUNTO DE DEBUGGING: Si el Excel tiene nombres distintos, revisa
    # el importador en catalogo_service.py → MAPEO_COLUMNAS
    producto = Column(String(500), index=True, nullable=True)
    descripcion = Column(Text, nullable=True)
    marca = Column(String(200), nullable=True)
    categoria = Column(String(200), nullable=True)
    unidad = Column(String(50), nullable=True)
    multiplo = Column(String(50), nullable=True)
    master = Column(String(50), nullable=True)

    # ── Precios ────────────────────────────────────────────────────────────────
    precio_lista = Column(Float, nullable=True)
    promocion = Column(Float, nullable=True)
    vigencia = Column(String(100), nullable=True)
    costo_mas_iva = Column(Float, nullable=True)
    iva = Column(Float, nullable=True)
    precio_sugerido_con_iva = Column(Float, nullable=True)

    # ── Códigos ────────────────────────────────────────────────────────────────
    codigo_sat = Column(String(100), nullable=True)
    precio_publico_neto = Column(Float, nullable=True)
    codigo_ferrol = Column(String(200), nullable=True)
    espacio = Column(String(200), nullable=True)
    descripcion_ferrol = Column(Text, nullable=True)

    # ── Precios por descuento ──────────────────────────────────────────────────
    precio_20 = Column(Float, nullable=True)
    precio_85 = Column(Float, nullable=True)
    precio_12 = Column(Float, nullable=True)
    precio_publico = Column(Float, nullable=True)
    precio_publico_5_desc = Column(Float, nullable=True)

    # ── Campo de búsqueda normalizado ──────────────────────────────────────────
    # Texto combinado y normalizado para matching eficiente
    texto_busqueda = Column(Text, nullable=True, index=True)

    # ── Metadatos ──────────────────────────────────────────────────────────────
    fecha_carga = Column(DateTime, server_default=func.now())
    fila_excel = Column(Integer, nullable=True)  # Útil para debugging

    def __repr__(self):
        return f"<Producto(id={self.id}, producto='{self.producto}')>"
