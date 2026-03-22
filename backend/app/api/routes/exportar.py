"""
Rutas de la API para exportación y descarga de archivos.
Sirve los archivos Excel generados para descarga desde el frontend.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.exportar_service import ExportadorExcel

router = APIRouter()


@router.get(
    "/descargar/{nombre_archivo}",
    summary="Descargar Excel de cotización",
    description="Descarga el archivo Excel de cotización generado.",
)
async def descargar_excel(nombre_archivo: str) -> FileResponse:
    """
    Endpoint para descargar un Excel de cotización por nombre de archivo.
    El nombre del archivo se obtiene de la respuesta del endpoint de cotización.
    
    PUNTO DE DEBUGGING: Si la descarga falla con 404, verifica que:
    1. El directorio EXPORTAR_DIR_TEMPORAL existe y tiene permisos de escritura
    2. El archivo fue generado correctamente (revisa logs del exportador)
    3. El nombre del archivo en la URL coincide exactamente con el generado
    """
    # Validación básica del nombre de archivo para seguridad
    if "/" in nombre_archivo or "\\" in nombre_archivo or ".." in nombre_archivo:
        raise HTTPException(
            status_code=400,
            detail="Nombre de archivo inválido."
        )

    if not nombre_archivo.endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden descargar archivos Excel (.xlsx)."
        )

    exportador = ExportadorExcel()

    if not exportador.archivo_existe(nombre_archivo):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Archivo '{nombre_archivo}' no encontrado. "
                "Puede haber expirado o hubo un error al generarlo."
            ),
        )

    ruta = exportador.obtener_ruta_archivo(nombre_archivo)

    return FileResponse(
        path=str(ruta),
        filename=nombre_archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={nombre_archivo}"
        },
    )
