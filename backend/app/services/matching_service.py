"""
Motor de matching de productos — v2.
Estrategia mejorada: búsqueda multi-campo con prioridad por campo.

MEJORAS vs v1:
- Coincidencia exacta en campo 'producto' tiene prioridad absoluta
- Búsqueda separada por campo (producto, descripcion, codigo_ferrol)
- Score final combina el mejor resultado por campo con pesos distintos
- Normalización más agresiva para nombres con caracteres especiales
- Búsqueda por código FERROL exacto antes del fuzzy
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
    """Normalización agresiva para matching."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    # Eliminar tildes
    nfkd = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Normalizar fracciones: "1/4" → "1/4" (mantener)
    # Eliminar caracteres especiales excepto números, letras, espacios, /, ., -
    texto = re.sub(r"[^a-z0-9\s/\.\-]", " ", texto)
    # Colapsar espacios
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _score_exacto(query: str, candidato: str) -> float:
    """
    Chequea coincidencia exacta después de normalizar.
    Si son idénticos → 100. Si el candidato contiene el query completo → 95.
    """
    q = normalizar_texto(query)
    c = normalizar_texto(candidato)
    if not q or not c:
        return 0.0
    if q == c:
        return 100.0
    if q in c or c in q:
        return 95.0
    return 0.0


def _score_compuesto(query: str, candidato: str) -> float:
    """
    Score fuzzy compuesto con múltiples métricas de rapidfuzz.
    Penaliza diferencias grandes de longitud para evitar falsos positivos
    cuando el query es corto y el candidato es muy largo.
    """
    q = normalizar_texto(query)
    c = normalizar_texto(candidato)
    if not q or not c:
        return 0.0

    score_sort  = fuzz.token_sort_ratio(q, c)
    score_set   = fuzz.token_set_ratio(q, c)
    score_ratio = fuzz.ratio(q, c)
    score_partial = fuzz.partial_ratio(q, c)

    # Penalización por diferencia de longitud extrema
    # Si el candidato es más de 3x más largo que el query, penalizar
    len_ratio = min(len(q), len(c)) / max(len(q), len(c)) if max(len(q), len(c)) > 0 else 0
    penalizacion = 1.0 if len_ratio > 0.33 else 0.85

    score = (score_sort * 0.35 + score_set * 0.30 + score_ratio * 0.20 + score_partial * 0.15)
    return round(score * penalizacion, 2)


def _determinar_nivel_confianza(score: float) -> NivelConfianza:
    if score >= settings.MATCHING_UMBRAL_ALTO:
        return NivelConfianza.ALTO
    elif score >= settings.MATCHING_UMBRAL_BAJO:
        return NivelConfianza.DUDOSO
    else:
        return NivelConfianza.NO_ENCONTRADO


def _obtener_precio_principal(producto: Producto) -> Optional[float]:
    """Prioridad de precio: precio_publico_neto > precio_lista > precio_sugerido_con_iva"""
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
    Motor de matching v2 — búsqueda multi-campo con prioridad.

    Estrategia por orden de prioridad:
    1. Coincidencia exacta en campo 'producto' (normalizado)
    2. Coincidencia exacta en campo 'codigo_ferrol'
    3. Fuzzy sobre campo 'producto' únicamente (mayor peso)
    4. Fuzzy sobre 'descripcion'
    5. Fuzzy sobre texto_busqueda completo (fallback)
    Toma el mejor score entre todas las estrategias.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._catalogo_cache: Optional[list[Producto]] = None
        # Índices pre-calculados para búsqueda eficiente
        self._idx_producto: Optional[list[str]] = None
        self._idx_descripcion: Optional[list[str]] = None
        self._idx_codigo: Optional[dict[str, int]] = None
        self._idx_busqueda: Optional[list[str]] = None

    async def _obtener_catalogo(self) -> list[Producto]:
        if self._catalogo_cache is None:
            resultado = await self.db.execute(select(Producto))
            self._catalogo_cache = list(resultado.scalars().all())

            # Pre-calcular índices normalizados una sola vez
            self._idx_producto = [
                normalizar_texto(p.producto or "") for p in self._catalogo_cache
            ]
            self._idx_descripcion = [
                normalizar_texto(p.descripcion or "") for p in self._catalogo_cache
            ]
            self._idx_busqueda = [
                normalizar_texto(p.texto_busqueda or "") for p in self._catalogo_cache
            ]
            # Índice de código FERROL para búsqueda exacta O(1)
            self._idx_codigo = {
                normalizar_texto(p.codigo_ferrol or ""): i
                for i, p in enumerate(self._catalogo_cache)
                if p.codigo_ferrol
            }
            logger.info(f"Índices de matching construidos: {len(self._catalogo_cache)} productos")
        return self._catalogo_cache

    async def buscar_producto(self, producto_solicitado: ProductoSolicitado) -> ProductoEncontrado:
        catalogo = await self._obtener_catalogo()

        if not catalogo:
            return ProductoEncontrado(
                nombre_solicitado=producto_solicitado.nombre_original,
                cantidad=producto_solicitado.cantidad,
                nivel_confianza=NivelConfianza.NO_ENCONTRADO,
                score_similitud=0.0,
                advertencia="El catálogo está vacío. Verifica EXCEL_RUTA en .env",
            )

        query = producto_solicitado.nombre_original
        query_norm = normalizar_texto(query)

        mejor_idx = -1
        mejor_score = 0.0
        metodo_usado = "ninguno"

        # ── Estrategia 1: Exacto en campo 'producto' ──────────────────────────
        for i, texto_prod in enumerate(self._idx_producto):
            score = _score_exacto(query_norm, texto_prod)
            if score > mejor_score:
                mejor_score = score
                mejor_idx = i
                metodo_usado = "exacto_producto"
            if mejor_score == 100.0:
                break  # No hay nada mejor, salir inmediatamente

        # ── Estrategia 2: Exacto en código FERROL ────────────────────────────
        if mejor_score < 100.0:
            idx_codigo = self._idx_codigo.get(query_norm)
            if idx_codigo is not None:
                mejor_score = 100.0
                mejor_idx = idx_codigo
                metodo_usado = "exacto_codigo_ferrol"

        # ── Estrategia 3: Fuzzy sobre campo 'producto' (máximo peso) ─────────
        if mejor_score < 95.0:
            candidatos_prod = process.extract(
                query_norm,
                self._idx_producto,
                scorer=fuzz.token_sort_ratio,
                limit=settings.MATCHING_MAX_CANDIDATOS * 2,
            )
            for texto_cand, score_base, idx in candidatos_prod:
                # Calcular score compuesto más preciso para cada candidato
                score_comp = _score_compuesto(query_norm, texto_cand)
                # Campo 'producto' tiene bonus de 10 puntos
                score_final = min(score_comp + 10, 100.0)
                if score_final > mejor_score:
                    mejor_score = score_final
                    mejor_idx = idx
                    metodo_usado = "fuzzy_producto"

        # ── Estrategia 4: Fuzzy sobre 'descripcion' ───────────────────────────
        if mejor_score < 90.0:
            candidatos_desc = process.extract(
                query_norm,
                self._idx_descripcion,
                scorer=fuzz.token_set_ratio,
                limit=settings.MATCHING_MAX_CANDIDATOS,
            )
            for texto_cand, score_base, idx in candidatos_desc:
                score_comp = _score_compuesto(query_norm, texto_cand)
                # Descripción sin bonus adicional
                if score_comp > mejor_score:
                    mejor_score = score_comp
                    mejor_idx = idx
                    metodo_usado = "fuzzy_descripcion"

        # ── Estrategia 5: Fuzzy sobre texto_busqueda completo (fallback) ──────
        if mejor_score < 70.0:
            candidatos_full = process.extract(
                query_norm,
                self._idx_busqueda,
                scorer=fuzz.token_set_ratio,
                limit=settings.MATCHING_MAX_CANDIDATOS,
            )
            for texto_cand, score_base, idx in candidatos_full:
                score_comp = _score_compuesto(query_norm, texto_cand)
                # Penalizar fallback: -5 puntos
                score_pen = max(score_comp - 5, 0)
                if score_pen > mejor_score:
                    mejor_score = score_pen
                    mejor_idx = idx
                    metodo_usado = "fuzzy_texto_completo"

        logger.debug(f"Matching '{query}': score={mejor_score:.1f} método={metodo_usado} idx={mejor_idx}")

        # ── Construir resultado ───────────────────────────────────────────────
        if mejor_idx < 0 or mejor_score < settings.MATCHING_UMBRAL_BAJO:
            return ProductoEncontrado(
                nombre_solicitado=query,
                cantidad=producto_solicitado.cantidad,
                nivel_confianza=NivelConfianza.NO_ENCONTRADO,
                score_similitud=round(mejor_score, 1),
                advertencia=f"Producto no encontrado en catálogo: '{query}'. Requiere cotización manual.",
            )

        p = catalogo[mejor_idx]
        nivel = _determinar_nivel_confianza(mejor_score)
        precio = _obtener_precio_principal(p)
        subtotal = round(precio * producto_solicitado.cantidad, 2) if precio else None

        advertencia = None
        if nivel == NivelConfianza.DUDOSO:
            advertencia = (
                f"Coincidencia dudosa ({mejor_score:.0f}% vía {metodo_usado}): "
                f"'{query}' → '{p.producto}'. Verificar manualmente."
            )

        return ProductoEncontrado(
            nombre_solicitado=query,
            cantidad=producto_solicitado.cantidad,
            producto_id=p.id,
            nombre_encontrado=p.producto,
            descripcion=p.descripcion,
            marca=p.marca,
            unidad=p.unidad,
            codigo_ferrol=p.codigo_ferrol,
            precio_unitario=precio,
            subtotal=subtotal,
            nivel_confianza=nivel,
            score_similitud=round(mejor_score, 1),
            advertencia=advertencia,
        )

    async def buscar_multiples(self, productos: list[ProductoSolicitado]) -> list[ProductoEncontrado]:
        resultados = []
        for p in productos:
            resultados.append(await self.buscar_producto(p))
        return resultados
