"""
Rutas de la API para gestión del catálogo de productos.
Permite recargar el catálogo y consultar su estado.
"""

from fastapi import APIRouter, HTTPException
from app.services.catalogo_service import CatalogoService
from app.schemas.cotizacion import EstadoCatalogo
from app.core.config import settings

router = APIRouter()


@router.get(
    "/estado",
    response_model=EstadoCatalogo,
    summary="Estado del catálogo",
)
async def obtener_estado_catalogo() -> EstadoCatalogo:
    """Retorna el estado actual del catálogo: total de productos y fuente."""
    servicio = CatalogoService()
    total = await servicio.obtener_total_productos()

    return EstadoCatalogo(
        total_productos=total,
        archivo_fuente=settings.EXCEL_RUTA,
        estado="cargado" if total > 0 else "vacio",
        mensaje=(
            f"{total} productos disponibles desde '{settings.EXCEL_RUTA}'"
            if total > 0
            else "Catálogo vacío. Verifica EXCEL_RUTA en el archivo .env"
        ),
    )


@router.post(
    "/recargar",
    summary="Recargar catálogo desde Excel",
    description="Vuelve a leer el Excel y recarga todos los productos en la base de datos.",
)
async def recargar_catalogo():
    """
    Fuerza una recarga del catálogo desde el Excel configurado.
    Útil cuando el archivo Excel fue actualizado sin reiniciar el servidor.
    """
    servicio = CatalogoService()
    try:
        cantidad = await servicio.cargar_catalogo_desde_excel()
        return {
            "exito": True,
            "mensaje": f"Catálogo recargado: {cantidad} productos disponibles.",
            "total_productos": cantidad,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al recargar catálogo: {str(e)}")
