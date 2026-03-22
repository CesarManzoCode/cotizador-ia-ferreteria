"""
Servicio de importación del catálogo desde Excel.
Este es uno de los módulos más críticos del sistema.

PUNTOS DE DEBUGGING PRINCIPALES:
1. Si los encabezados del Excel no se mapean correctamente → ver MAPEO_COLUMNAS
2. Si los precios vienen como texto con comas → ver _convertir_numero()
3. Si hay filas de encabezado extra → ver EXCEL_FILA_ENCABEZADO en .env
4. Si el Excel tiene la hoja en posición distinta → ver EXCEL_HOJA en .env
"""

import logging
import re
import unicodedata
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.models.producto import Producto

logger = logging.getLogger(__name__)


# ── Mapeo de columnas del Excel → campos del modelo ───────────────────────────
# PUNTO DE DEBUGGING PRINCIPAL:
# Si tu Excel real tiene nombres diferentes, agrega las variantes aquí.
# Las claves son variantes posibles del nombre en el Excel.
# Los valores son el nombre del campo en el modelo Python.
#
# El sistema normaliza automáticamente (quita tildes, espacios extra, minúsculas)
# antes de comparar, por lo que no necesitas agregar variantes de capitalización.
# Sí necesitas agregar variantes con palabras diferentes.

MAPEO_COLUMNAS: dict[str, str] = {
    # Columna Excel (normalizada) → campo en modelo Producto
    "producto": "producto",
    "descripcion": "descripcion",
    "descripción": "descripcion",
    "marca": "marca",
    "categoria": "categoria",
    "categoría": "categoria",
    "unidad": "unidad",
    "multiplo": "multiplo",
    "múltiplo": "multiplo",
    "master": "master",
    "precio lista": "precio_lista",
    "preciolista": "precio_lista",
    "promocion": "promocion",
    "promoción": "promocion",
    "vigencia": "vigencia",
    "costo + iva": "costo_mas_iva",
    "costo+iva": "costo_mas_iva",
    "costoiva": "costo_mas_iva",
    "costo mas iva": "costo_mas_iva",
    "iva": "iva",
    "precio sugerido de venta con iva": "precio_sugerido_con_iva",
    "precio sugerido con iva": "precio_sugerido_con_iva",
    "preciosugeridoconiva": "precio_sugerido_con_iva",
    "codigo sat": "codigo_sat",
    "código sat": "codigo_sat",
    "codigosat": "codigo_sat",
    "precio publico neto": "precio_publico_neto",
    "precio público neto": "precio_publico_neto",
    "preciopublicioneto": "precio_publico_neto",
    "codigo ferrol": "codigo_ferrol",
    "código ferrol": "codigo_ferrol",
    "codigoferrol": "codigo_ferrol",
    "espacio": "espacio",
    "descripcion ferrol": "descripcion_ferrol",
    "descripción ferrol": "descripcion_ferrol",
    "descripcionferrol": "descripcion_ferrol",
    "precio 20%": "precio_20",
    "precio20": "precio_20",
    "precio 8.5%": "precio_85",
    "precio85": "precio_85",
    "precio 12%": "precio_12",
    "precio12": "precio_12",
    "precio publico": "precio_publico",
    "precio público": "precio_publico",
    "preciopublico": "precio_publico",
    "precio publico con 5% descuento": "precio_publico_5_desc",
    "precio público con 5% descuento": "precio_publico_5_desc",
    "precio publico 5 descuento": "precio_publico_5_desc",
    "preciopublico5desc": "precio_publico_5_desc",
}


def _normalizar_encabezado(texto: str) -> str:
    """
    Normaliza un encabezado de columna para comparación robusta.
    - Convierte a minúsculas
    - Elimina tildes/acentos
    - Elimina espacios extra al inicio/fin
    - Colapsa espacios múltiples a uno solo
    
    PUNTO DE DEBUGGING: Si un encabezado no se mapea, agrega un print
    aquí para ver el valor normalizado y agrégalo a MAPEO_COLUMNAS.
    """
    if not isinstance(texto, str):
        texto = str(texto)

    # Eliminar espacios al inicio y fin
    texto = texto.strip()

    # Eliminar saltos de línea y tabs
    texto = re.sub(r"[\n\r\t]+", " ", texto)

    # Colapsar espacios múltiples
    texto = re.sub(r"\s+", " ", texto)

    # Convertir a minúsculas
    texto = texto.lower()

    # Eliminar tildes/acentos usando normalización Unicode NFD
    nfkd = unicodedata.normalize("NFKD", texto)
    texto_sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))

    return texto_sin_tildes


def _normalizar_texto_busqueda(producto: Producto) -> str:
    """
    Genera un texto combinado y normalizado para búsqueda eficiente.
    Combina producto, descripción, marca y categoría.
    Este texto se usa en el motor de matching.
    """
    partes = []

    for campo in ["producto", "descripcion", "marca", "categoria",
                  "descripcion_ferrol", "codigo_ferrol"]:
        valor = getattr(producto, campo, None)
        if valor and isinstance(valor, str):
            partes.append(valor.strip())

    texto_completo = " ".join(partes)
    return _normalizar_encabezado(texto_completo)


def _convertir_numero(valor) -> Optional[float]:
    """
    Convierte un valor del Excel a float de forma robusta.
    Maneja: None, strings con comas, strings con $, NaN, etc.
    
    PUNTO DE DEBUGGING: Si los precios vienen como texto (ej: "$1,234.56"),
    esta función los convierte automáticamente. Si fallan, revisa aquí.
    """
    if valor is None:
        return None

    import math
    if isinstance(valor, float) and math.isnan(valor):
        return None

    if isinstance(valor, (int, float)):
        return float(valor)

    if isinstance(valor, str):
        # Limpiar símbolos de moneda y espacios
        limpio = valor.strip()
        limpio = limpio.replace("$", "").replace(",", "").replace(" ", "")

        # Manejar valores con paréntesis (negativos en contabilidad)
        if limpio.startswith("(") and limpio.endswith(")"):
            limpio = "-" + limpio[1:-1]

        try:
            return float(limpio)
        except ValueError:
            return None

    return None


class CatalogoService:
    """
    Servicio principal para gestión del catálogo de productos.
    Importa desde Excel y mantiene los productos en SQLite.
    """

    async def cargar_catalogo_desde_excel(self) -> int:
        """
        Lee el Excel configurado en EXCEL_RUTA y carga los productos en SQLite.
        Limpia y reemplaza los datos existentes en cada carga.
        
        Returns:
            Número de productos cargados exitosamente.
        
        Raises:
            FileNotFoundError: Si el Excel no existe en la ruta configurada.
            Exception: Si el Excel no puede leerse o no tiene el formato esperado.
        """
        ruta_excel = Path(settings.EXCEL_RUTA)

        # Verificar que el archivo existe
        if not ruta_excel.exists():
            raise FileNotFoundError(
                f"Excel no encontrado: {ruta_excel.absolute()}\n"
                f"Configura la ruta correcta en EXCEL_RUTA dentro del archivo .env"
            )

        logger.info(f"Leyendo Excel: {ruta_excel.absolute()}")

        # Leer el Excel
        # PUNTO DE DEBUGGING: Si el Excel tiene múltiples hojas, ajusta EXCEL_HOJA en .env
        try:
            hoja = settings.EXCEL_HOJA if settings.EXCEL_HOJA else 0
            df = pd.read_excel(
                ruta_excel,
                sheet_name=hoja,
                header=settings.EXCEL_FILA_ENCABEZADO,
                dtype=str,  # Leer todo como string para normalizar manualmente
                engine="openpyxl",
            )
        except Exception as e:
            raise Exception(
                f"Error al leer el Excel '{ruta_excel}': {e}\n"
                f"Verifica que el archivo no esté abierto en otro programa."
            )

        logger.info(f"Excel leído: {len(df)} filas, {len(df.columns)} columnas.")
        logger.info(f"Columnas encontradas: {list(df.columns)}")

        # Mapear columnas del Excel a campos del modelo
        mapeo_aplicado = self._mapear_columnas(df)
        logger.info(f"Columnas mapeadas: {mapeo_aplicado}")

        # Cargar productos en base de datos
        cantidad = await self._guardar_productos(df, mapeo_aplicado)
        return cantidad

    def _mapear_columnas(self, df: pd.DataFrame) -> dict[str, str]:
        """
        Mapea los nombres de columnas del Excel a los campos del modelo.
        Usa normalización para tolerar variaciones en nombres.
        
        PUNTO DE DEBUGGING: Si una columna del Excel no se mapea correctamente,
        ejecuta el sistema y revisa los logs "Columna no mapeada: ...".
        Luego agrega el nombre normalizado a MAPEO_COLUMNAS arriba.
        
        Returns:
            Dict {nombre_columna_original: campo_modelo}
        """
        mapeo_resultado = {}

        for col_original in df.columns:
            col_normalizada = _normalizar_encabezado(str(col_original))

            if col_normalizada in MAPEO_COLUMNAS:
                campo_modelo = MAPEO_COLUMNAS[col_normalizada]
                mapeo_resultado[col_original] = campo_modelo
                logger.debug(f"  ✓ '{col_original}' → {campo_modelo}")
            else:
                # PUNTO DE DEBUGGING: Estas columnas no se están usando
                logger.warning(f"  ✗ Columna no mapeada: '{col_original}' (normalizada: '{col_normalizada}')")

        return mapeo_resultado

    async def _guardar_productos(
        self,
        df: pd.DataFrame,
        mapeo: dict[str, str]
    ) -> int:
        """
        Guarda los productos en SQLite.
        Limpia la tabla antes de cargar (recarga completa).
        """
        async with AsyncSessionLocal() as db:
            # Limpiar tabla de productos antes de cargar
            await db.execute(text("DELETE FROM productos"))
            await db.commit()
            logger.info("Tabla de productos limpiada. Iniciando carga...")

            productos_cargados = 0
            productos_omitidos = 0

            for idx, fila in df.iterrows():
                # Omitir filas completamente vacías
                if fila.dropna().empty:
                    continue

                producto = Producto()
                producto.fila_excel = int(idx) + settings.EXCEL_FILA_ENCABEZADO + 2  # 1-indexed para debugging

                # Mapear cada columna al campo correspondiente
                for col_excel, campo_modelo in mapeo.items():
                    valor_raw = fila.get(col_excel)

                    # Determinar si el campo es numérico
                    campos_numericos = {
                        "precio_lista", "promocion", "costo_mas_iva", "iva",
                        "precio_sugerido_con_iva", "precio_publico_neto",
                        "precio_20", "precio_85", "precio_12",
                        "precio_publico", "precio_publico_5_desc",
                    }

                    if campo_modelo in campos_numericos:
                        setattr(producto, campo_modelo, _convertir_numero(valor_raw))
                    else:
                        # Campo de texto
                        if valor_raw is not None and str(valor_raw).strip() not in ("", "nan", "None"):
                            setattr(producto, campo_modelo, str(valor_raw).strip())
                        else:
                            setattr(producto, campo_modelo, None)

                # Verificar que tenga al menos nombre o descripción
                if not producto.producto and not producto.descripcion:
                    productos_omitidos += 1
                    continue

                # Generar texto de búsqueda normalizado
                producto.texto_busqueda = _normalizar_texto_busqueda(producto)

                db.add(producto)
                productos_cargados += 1

                # Commit cada 500 registros para no saturar memoria
                if productos_cargados % 500 == 0:
                    await db.commit()
                    logger.info(f"  ... {productos_cargados} productos cargados")

            await db.commit()
            logger.info(
                f"Carga completa: {productos_cargados} productos guardados, "
                f"{productos_omitidos} filas omitidas."
            )
            return productos_cargados

    async def obtener_total_productos(self) -> int:
        """Retorna el número total de productos en el catálogo."""
        from sqlalchemy import select, func
        async with AsyncSessionLocal() as db:
            resultado = await db.execute(select(func.count(Producto.id)))
            return resultado.scalar() or 0
