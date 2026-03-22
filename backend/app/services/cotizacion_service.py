"""
Servicio principal de cotización.
Orquesta el flujo completo: LLM → matching → exportación → respuesta.

Este es el núcleo del sistema. Coordina:
1. Extracción de productos con LLM
2. Matching contra el catálogo
3. Construcción de la respuesta
4. Generación del Excel de salida
5. Registro en base de datos
"""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.cotizacion import (
    NivelConfianza,
    ProductoEncontrado,
    ProductoSolicitado,
    RespuestaCotizacion,
    SolicitudCotizacion,
)
from app.services.llm_client import get_llm_client
from app.services.matching_service import MotorMatching
from app.services.exportar_service import ExportadorExcel
from app.models.cotizacion import Cotizacion

logger = logging.getLogger(__name__)


class CotizacionService:
    """
    Orquestador principal del proceso de cotización.
    
    FLUJO COMPLETO:
    1. Recibe texto libre del usuario
    2. LLM extrae lista de productos + cantidades
    3. Motor de matching busca en catálogo
    4. Se clasifican resultados (alto/dudoso/no encontrado)
    5. Se genera Excel de salida
    6. Se construye respuesta para el frontend
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
        self.motor_matching = MotorMatching(db)
        self.exportador = ExportadorExcel()

    async def procesar_solicitud(
        self,
        solicitud: SolicitudCotizacion,
    ) -> RespuestaCotizacion:
        """
        Procesa una solicitud de cotización completa.
        """
        logger.info(f"Procesando solicitud: '{solicitud.texto[:100]}...'")

        # ── Paso 1: Extraer productos con LLM ─────────────────────────────────
        productos_extraidos = await self._extraer_productos_con_llm(solicitud.texto)

        if not productos_extraidos:
            return RespuestaCotizacion(
                mensaje_asistente=(
                    "No pude identificar productos en tu solicitud. "
                    "Intenta describir los productos más claramente, por ejemplo: "
                    "'Necesito 50 tornillos de 1/4 pulgada y 20 taquetes de 3/8'."
                ),
                exito=False,
                error="No se identificaron productos en el texto",
            )

        # ── Paso 2: Buscar coincidencias en catálogo ───────────────────────────
        productos_solicitados = [
            ProductoSolicitado(
                nombre_original=p.get("nombre_normalizado") or p.get("nombre_original", ""),
                cantidad=float(p.get("cantidad", 1)),
                unidad_solicitada=p.get("unidad"),
                notas_adicionales=p.get("notas"),
            )
            for p in productos_extraidos
            if p.get("nombre_original") or p.get("nombre_normalizado")
        ]

        productos_encontrados = await self.motor_matching.buscar_multiples(
            productos_solicitados
        )

        # ── Paso 3: Clasificar resultados ──────────────────────────────────────
        productos_altos = [p for p in productos_encontrados if p.nivel_confianza == NivelConfianza.ALTO]
        productos_dudosos = [p for p in productos_encontrados if p.nivel_confianza == NivelConfianza.DUDOSO]
        productos_no_encontrados = [p for p in productos_encontrados if p.nivel_confianza == NivelConfianza.NO_ENCONTRADO]

        advertencias_dudosas = [p.advertencia for p in productos_dudosos if p.advertencia]
        advertencias_no_encontrados = [p.advertencia for p in productos_no_encontrados if p.advertencia]

        # ── Paso 4: Calcular totales ───────────────────────────────────────────
        subtotal = sum(
            p.subtotal or 0
            for p in productos_encontrados
            if p.nivel_confianza != NivelConfianza.NO_ENCONTRADO and p.subtotal
        )

        # ── Paso 5: Generar Excel ──────────────────────────────────────────────
        nombre_excel = None
        try:
            nombre_excel = self.exportador.generar_excel_cotizacion(
                productos=productos_encontrados,
                texto_solicitud=solicitud.texto,
            )
        except Exception as e:
            logger.error(f"Error al generar Excel: {e}")
            # No falla el proceso completo si el Excel falla

        # ── Paso 6: Registrar en base de datos ────────────────────────────────
        cotizacion_id = await self._registrar_cotizacion(
            texto=solicitud.texto,
            productos_encontrados=len(productos_altos),
            productos_dudosos=len(productos_dudosos),
            productos_no_encontrados=len(productos_no_encontrados),
            total=subtotal,
            nombre_excel=nombre_excel,
        )

        if nombre_excel:
            # Actualizar Excel con el ID de cotización
            try:
                nombre_excel = self.exportador.generar_excel_cotizacion(
                    productos=productos_encontrados,
                    texto_solicitud=solicitud.texto,
                    cotizacion_id=cotizacion_id,
                )
            except Exception:
                pass  # Usar el Excel sin ID si falla la regeneración

        # ── Paso 7: Construir mensaje del asistente ────────────────────────────
        mensaje = self._construir_mensaje_asistente(
            total_solicitados=len(productos_solicitados),
            total_encontrados=len(productos_altos),
            total_dudosos=len(productos_dudosos),
            total_no_encontrados=len(productos_no_encontrados),
            subtotal=subtotal,
        )

        return RespuestaCotizacion(
            cotizacion_id=cotizacion_id,
            mensaje_asistente=mensaje,
            productos=productos_encontrados,
            advertencias_dudosas=advertencias_dudosas,
            advertencias_no_encontrados=advertencias_no_encontrados,
            subtotal=subtotal,
            total=subtotal,
            archivo_excel_nombre=nombre_excel,
            exito=True,
        )

    async def _extraer_productos_con_llm(self, texto: str) -> Optional[List[dict]]:
        """
        Usa el LLM para extraer productos y cantidades del texto.
        Si el LLM falla, intenta extracción básica con heurísticas.
        """
        # Intentar con LLM primero
        productos = await self.llm.extraer_productos_json(texto)

        if productos is not None:
            logger.info(f"LLM extrajo {len(productos)} productos.")
            return productos

        # Fallback: extracción básica si el LLM no está disponible
        logger.warning("LLM no disponible. Usando extracción básica por heurísticas.")
        return self._extraccion_basica(texto)

    def _extraccion_basica(self, texto: str) -> List[dict]:
        """
        Extracción básica de productos cuando el LLM no está disponible.
        Divide el texto en partes por comas, "y", "más", etc.
        
        PUNTO DE DEBUGGING: Esta es una extracción de emergencia muy simple.
        Si el LLM falla frecuentemente, prioriza resolver la conexión a Groq.
        """
        import re

        # Dividir por delimitadores comunes
        partes = re.split(r"[,;]|\sy\s|\smas\s|\smás\s|\stambien\s", texto, flags=re.IGNORECASE)
        productos = []

        for parte in partes:
            parte = parte.strip()
            if len(parte) < 3:
                continue

            # Intentar extraer número al inicio
            match_num = re.match(r"^(\d+(?:\.\d+)?)\s+(.+)", parte)
            if match_num:
                cantidad = float(match_num.group(1))
                nombre = match_num.group(2).strip()
            else:
                cantidad = 1.0
                nombre = parte

            if nombre:
                productos.append({
                    "nombre_original": nombre,
                    "nombre_normalizado": nombre,
                    "cantidad": cantidad,
                    "unidad": None,
                    "notas": "Extraído por heurística (LLM no disponible)",
                })

        return productos

    def _construir_mensaje_asistente(
        self,
        total_solicitados: int,
        total_encontrados: int,
        total_dudosos: int,
        total_no_encontrados: int,
        subtotal: float,
    ) -> str:
        """Construye el mensaje de respuesta del asistente."""
        partes = [
            f"Procesé tu solicitud de {total_solicitados} producto(s).",
        ]

        if total_encontrados > 0:
            partes.append(f"✅ {total_encontrados} encontrado(s) con alta coincidencia.")

        if total_dudosos > 0:
            partes.append(
                f"⚠️ {total_dudosos} con coincidencia dudosa — revisa las advertencias antes de confirmar."
            )

        if total_no_encontrados > 0:
            partes.append(
                f"❌ {total_no_encontrados} no encontrado(s) en el catálogo — requieren cotización manual."
            )

        if subtotal > 0:
            partes.append(f"\n💰 Subtotal estimado: ${subtotal:,.2f} MXN")

        partes.append("\nEl archivo Excel con la cotización está listo para descargar.")

        return " ".join(partes[:3]) + "\n" + " ".join(partes[3:]) if len(partes) > 3 else " ".join(partes)

    async def _registrar_cotizacion(
        self,
        texto: str,
        productos_encontrados: int,
        productos_dudosos: int,
        productos_no_encontrados: int,
        total: float,
        nombre_excel: Optional[str],
    ) -> Optional[int]:
        """Registra un registro mínimo de la cotización en SQLite."""
        try:
            cotizacion = Cotizacion(
                texto_solicitud=texto[:1000],  # Limitar longitud
                productos_encontrados=productos_encontrados,
                productos_dudosos=productos_dudosos,
                productos_no_encontrados=productos_no_encontrados,
                total=total,
                archivo_excel=nombre_excel,
            )
            self.db.add(cotizacion)
            await self.db.flush()  # Para obtener el ID sin commit
            cotizacion_id = cotizacion.id
            await self.db.commit()
            return cotizacion_id
        except Exception as e:
            logger.error(f"Error al registrar cotización en BD: {e}")
            return None
