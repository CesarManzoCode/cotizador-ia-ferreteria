"""
Modelo de base de datos para cotizaciones generadas.
Almacena un registro básico de cada cotización para trazabilidad mínima.
No almacena historial de conversación.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func
from app.db.database import Base


class Cotizacion(Base):
    """
    Registro mínimo de cada cotización generada.
    Solo para trazabilidad y referencia futura.
    No se almacena el historial del chat.
    """
    __tablename__ = "cotizaciones"

    id = Column(Integer, primary_key=True, index=True)

    # Texto original recibido del usuario
    texto_solicitud = Column(Text, nullable=False)

    # Número de productos encontrados y no encontrados
    productos_encontrados = Column(Integer, default=0)
    productos_dudosos = Column(Integer, default=0)
    productos_no_encontrados = Column(Integer, default=0)

    # Total calculado de la cotización
    total = Column(Float, default=0.0)

    # Nombre del archivo Excel generado (para descarga)
    archivo_excel = Column(String(500), nullable=True)

    # Estado: generada, descargada, cancelada
    estado = Column(String(50), default="generada")

    fecha_creacion = Column(DateTime, server_default=func.now())
