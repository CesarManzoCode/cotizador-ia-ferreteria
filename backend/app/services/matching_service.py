"""
Motor de matching de productos.
Estrategia híbrida: normalización + fuzzy matching + heurísticas.

DECISIÓN DE ARQUITECTURA: No se usan embeddings vectoriales.
Razón: Para uso local con listas de precios de ferretería/construcción,
el fuzzy matching bien calibrado supera a embeddings en rendimiento práctico,
sin requerir modelos locales pesados ni infraestructura adicional.

El LLM se usa SOLO para normalización inicial del texto del usuario.
El matching real es determinista y basado en similitud textual.

PUNTOS DE DEBUGGING:
- Ajusta MATCHING_UMBRAL_ALTO y MATCHING_UMBRAL_BAJO en .env
- Si muchos productos legítimos caen en "dudoso", baja el umbral alto
- Si hay muchas coincidencias incorrectas, sube el umbral bajo
"""

import logging
import re
import unicodedata
from typing import Optional
from rapidfuzz import fuzz, process

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.producto import Producto
from app.schemas.cotizacion import (
    NivelConfianza,
    ProductoEncontrado,
    ProductoSolicitado,
)

logger = logging.getLogger(__name__)


def normalizar_texto(texto: str) -> str:
    """
    Normalización agresiva de texto para matching.
    Elimina tildes, convierte a minúsculas, limpia caracteres especiales.
    """
    if not texto:
        return ""

    # Minúsculas
    texto = texto.lower().strip()

    # Eliminar tildes
    nfkd = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in nfkd if not unicodedata.combining(c))

    # Normalizar separadores de medidas (1/4 -> 1 4, 3/8 -> 3 8)
    # Mantener la fracción como texto para que "1/4" y "cuarto" puedan coincidir
    texto = re.sub(r"(\d)/(\d)", r"\1/\2", texto)

    # Eliminar caracteres especiales excepto números, letras, espacios, /, .
    texto = re.sub(r"[^a-z0-9\s/\.\-]", " ", texto)

    # Colapsar espacios múltiples
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def _calcular_score_compuesto(query: str, candidato: str) -> float:
    """
    Calcula un score de similitud compuesto usando múltiples métricas de rapidfuzz.
    
    Combina:
    - token_sort_ratio: robusto ante palabras reordenadas
    - token_set_ratio: robusto ante palabras adicionales
    - partial_ratio: útil para descripciones parciales
    
    PUNTO DE DEBUGGING: Si el matching falla para tu lista de precios específica,
    ajusta los pesos (0.4, 0.4, 0.2) según el comportamiento observado.
    """
    q = normalizar_texto(query)
    c = normalizar_texto(candidato)

    if not q or not c:
        return 0.0

    # Métricas de similitud
    score_sort = fuzz.token_sort_ratio(q, c)
    score_set = fuzz.token_set_ratio(q, c)
    score_partial = fuzz.partial_ratio(q, c)

    # Ponderación: token_sort y token_set son más confiables para productos
    score_final = (score_sort * 0.4) + (score_set * 0.4) + (score_partial * 0.2)

    return round(score_final, 2)


def _determinar_nivel_confianza(score: float) -> NivelConfianza:
    """
    Determina el nivel de confianza basado en el score de matching.
    Los umbrales son configurables desde .env.
    """
    if score >= settings.MATCHING_UMBRAL_ALTO:
        return NivelConfianza.ALTO
    elif score >= settings.MATCHING_UMBRAL_BAJO:
        return NivelConfianza.DUDOSO
    else:
        return NivelConfianza.NO_ENCONTRADO


def _obtener_precio_principal(producto: Producto) -> Optional[float]:
    """
    Determina el precio a usar para la cotización.
    Prioridad: precio_publico_neto > precio_lista > precio_sugerido_con_iva
    
    PUNTO DE DEBUGGING: Si el precio que muestra el sistema no es el correcto
    para tu caso de uso, ajusta la prioridad aquí.
    """
    if producto.precio_publico_neto and producto.precio_publico_neto > 0:
        return producto.precio_publico_neto
    if producto.precio_lista and producto.precio_lista > 0:
        return producto.precio_lista
    if producto.precio_sugerido_con_iva and producto.precio_sugerido_con_iva > 0:
        return producto.precio_sugerido_con_iva
    if producto.precio_publico and producto.precio_publico > 0:
        return producto.precio_publico
    return None


class MotorMatching:
    """
    Motor de matching de productos.
    Busca coincidencias en el catálogo para cada producto solicitado.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._catalogo_cache: Optional[list[Producto]] = None

    async def _obtener_catalogo(self) -> list[Producto]:
        """
        Carga el catálogo completo en memoria para matching eficiente.
        Se cachea en la instancia para evitar múltiples queries por solicitud.
        
        NOTA DE ESCALABILIDAD: Para catálogos > 50,000 productos considera
        índices de texto completo en SQLite o búsqueda por chunks.
        """
        if self._catalogo_cache is None:
            resultado = await self.db.execute(select(Producto))
            self._catalogo_cache = list(resultado.scalars().all())
            logger.debug(f"Catálogo cargado en memoria: {len(self._catalogo_cache)} productos")
        return self._catalogo_cache

    async def buscar_producto(
        self,
        producto_solicitado: ProductoSolicitado,
    ) -> ProductoEncontrado:
        """
        Busca el mejor match en el catálogo para un producto solicitado.
        
        Estrategia:
        1. Normalizar el texto de búsqueda
        2. Usar rapidfuzz para encontrar candidatos
        3. Calcular score compuesto
        4. Determinar nivel de confianza
        5. Generar advertencia si es necesario
        """
        catalogo = await self._obtener_catalogo()

        if not catalogo:
            # Catálogo vacío: no se puede hacer matching
            return ProductoEncontrado(
                nombre_solicitado=producto_solicitado.nombre_original,
                cantidad=producto_solicitado.cantidad,
                nivel_confianza=NivelConfianza.NO_ENCONTRADO,
                score_similitud=0.0,
                advertencia=(
                    "El catálogo está vacío. Verifica que el Excel esté configurado "
                    "correctamente en EXCEL_RUTA dentro del .env"
                ),
            )

        # Texto de consulta normalizado
        # Usar nombre_normalizado si está disponible (del LLM), sino el original
        texto_query = normalizar_texto(producto_solicitado.nombre_original)

        # Textos de búsqueda del catálogo
        textos_catalogo = [
            (p.texto_busqueda or "") for p in catalogo
        ]

        # Búsqueda fuzzy con rapidfuzz (muy eficiente)
        # Retorna los N mejores candidatos con sus scores
        candidatos_raw = process.extract(
            texto_query,
            textos_catalogo,
            scorer=fuzz.token_sort_ratio,
            limit=settings.MATCHING_MAX_CANDIDATOS,
        )

        if not candidatos_raw:
            return ProductoEncontrado(
                nombre_solicitado=producto_solicitado.nombre_original,
                cantidad=producto_solicitado.cantidad,
                nivel_confianza=NivelConfianza.NO_ENCONTRADO,
                score_similitud=0.0,
                advertencia=f"No se encontró '{producto_solicitado.nombre_original}' en el catálogo.",
            )

        # Tomar el mejor candidato
        # candidatos_raw = [(texto, score, índice), ...]
        mejor_texto, score_base, mejor_idx = candidatos_raw[0]
        mejor_producto = catalogo[mejor_idx]

        # Calcular score compuesto más preciso
        score_final = _calcular_score_compuesto(
            texto_query,
            mejor_producto.texto_busqueda or ""
        )

        nivel = _determinar_nivel_confianza(score_final)
        precio = _obtener_precio_principal(mejor_producto)

        # Construir advertencia según el nivel
        advertencia = None
        if nivel == NivelConfianza.DUDOSO:
            advertencia = (
                f"Coincidencia dudosa ({score_final:.0f}%): "
                f"'{producto_solicitado.nombre_original}' → '{mejor_producto.producto}'. "
                f"Verificar manualmente."
            )
        elif nivel == NivelConfianza.NO_ENCONTRADO:
            advertencia = (
                f"Producto no encontrado: '{producto_solicitado.nombre_original}'. "
                f"Debe cotizarse manualmente."
            )

        subtotal = None
        if precio is not None:
            subtotal = round(precio * producto_solicitado.cantidad, 2)

        return ProductoEncontrado(
            nombre_solicitado=producto_solicitado.nombre_original,
            cantidad=producto_solicitado.cantidad,
            producto_id=mejor_producto.id if nivel != NivelConfianza.NO_ENCONTRADO else None,
            nombre_encontrado=mejor_producto.producto if nivel != NivelConfianza.NO_ENCONTRADO else None,
            descripcion=mejor_producto.descripcion,
            marca=mejor_producto.marca,
            unidad=mejor_producto.unidad,
            codigo_ferrol=mejor_producto.codigo_ferrol,
            precio_unitario=precio if nivel != NivelConfianza.NO_ENCONTRADO else None,
            subtotal=subtotal if nivel != NivelConfianza.NO_ENCONTRADO else None,
            nivel_confianza=nivel,
            score_similitud=score_final,
            advertencia=advertencia,
        )

    async def buscar_multiples(
        self,
        productos_solicitados: list[ProductoSolicitado],
    ) -> list[ProductoEncontrado]:
        """
        Busca matches para múltiples productos solicitados.
        """
        resultados = []
        for producto in productos_solicitados:
            resultado = await self.buscar_producto(producto)
            resultados.append(resultado)
        return resultados
