"""
Rutas de la API para el proceso de cotización.
Punto de entrada HTTP para solicitudes de cotización desde el frontend.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.cotizacion import SolicitudCotizacion, RespuestaCotizacion
from app.services.cotizacion_service import CotizacionService

router = APIRouter()


@router.post(
    "/",
    response_model=RespuestaCotizacion,
    summary="Procesar solicitud de cotización",
    description=(
        "Recibe un texto libre del usuario, extrae productos usando IA, "
        "busca coincidencias en el catálogo y devuelve la cotización completa."
    ),
)
async def procesar_cotizacion(
    solicitud: SolicitudCotizacion,
    db: AsyncSession = Depends(get_db),
) -> RespuestaCotizacion:
    """
    Endpoint principal del sistema de cotizaciones.
    
    El frontend envía el texto del usuario y recibe la cotización completa
    con productos, advertencias y referencia al Excel generado.
    """
    try:
        servicio = CotizacionService(db)
        respuesta = await servicio.procesar_solicitud(solicitud)
        return respuesta
    except Exception as e:
        # PUNTO DE DEBUGGING: Si hay errores inesperados, aparecerán aquí
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la cotización: {str(e)}"
        )
