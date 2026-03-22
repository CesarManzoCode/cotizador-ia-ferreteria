"""Modelos de base de datos — importados aquí para que SQLAlchemy los registre."""
from app.models.producto import Producto
from app.models.cotizacion import Cotizacion

__all__ = ["Producto", "Cotizacion"]
