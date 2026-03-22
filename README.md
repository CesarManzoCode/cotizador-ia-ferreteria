# 🤖 Cotizador IA — Sistema de Cotizaciones Asistidas por IA

Sistema local para generar cotizaciones a partir de texto libre usando IA (Groq) y una lista de precios en Excel.

---

## ¿Qué hace el sistema?

1. El usuario escribe en lenguaje natural qué necesita cotizar
2. El LLM (Groq) extrae productos y cantidades
3. El sistema busca coincidencias en tu Excel de precios usando fuzzy matching
4. Genera advertencias para coincidencias dudosas y productos no encontrados
5. Produce un archivo Excel de cotización descargable

---

## Requisitos previos

| Herramienta | Versión mínima | Descarga |
|-------------|---------------|---------|
| Python | 3.11+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| npm | 9+ | incluido con Node.js |
| Git (opcional) | cualquiera | https://git-scm.com |

---

## Instalación paso a paso (Windows)

### 1. Instalar dependencias del backend

```cmd
cd cotizador-ia\backend
pip install -r requirements.txt
```

### 2. Instalar dependencias del frontend

```cmd
cd cotizador-ia\frontend
npm install
```

### 3. Configurar el archivo .env

```cmd
cd cotizador-ia\backend
copy .env.example .env
```

Luego abre `.env` con Notepad o VS Code y configura:

```env
# Tu API key de Groq (gratuita en https://console.groq.com)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# Ruta a tu Excel de lista de precios
EXCEL_RUTA=C:\Users\TuUsuario\Documentos\lista_precios.xlsx
```

### 4. Arrancar el sistema

```cmd
cd cotizador-ia
python app.py
```

El navegador se abrirá automáticamente en http://localhost:5173

---

## Variables de entorno (.env)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `GROQ_API_KEY` | **Obligatoria.** API key de Groq | `gsk_abc123...` |
| `GROQ_MODELO` | Modelo de Groq a usar | `llama-3.3-70b-versatile` |
| `GROQ_TEMPERATURA` | Temperatura del LLM (0-1) | `0.1` |
| `EXCEL_RUTA` | **Obligatoria.** Ruta al Excel de precios | `C:\precios\lista.xlsx` |
| `EXCEL_HOJA` | Nombre/índice de hoja del Excel | vacío = primera hoja |
| `EXCEL_FILA_ENCABEZADO` | Fila del encabezado (0-indexed) | `0` |
| `MATCHING_UMBRAL_ALTO` | Score mínimo para coincidencia automática | `75.0` |
| `MATCHING_UMBRAL_BAJO` | Score mínimo para coincidencia dudosa | `50.0` |
| `EXPORTAR_DIR_TEMPORAL` | Carpeta para Excel generados | `./temp_cotizaciones` |
| `DATABASE_URL` | URL de SQLite (no cambiar normalmente) | `sqlite+aiosqlite:///./cotizador.db` |

---

## Dónde configurar la ruta del Excel

**Archivo:** `backend/.env`  
**Variable:** `EXCEL_RUTA`

```env
# Windows — ruta absoluta (recomendada)
EXCEL_RUTA=C:\Users\Juan\Documentos\Ferreteria\lista_precios_2024.xlsx

# Windows — ruta relativa al directorio backend/
EXCEL_RUTA=..\datos\lista_precios.xlsx

# Con espacios en la ruta:
EXCEL_RUTA="C:\Mi Empresa\Precios\lista 2024.xlsx"
```

Después de cambiar la ruta, puedes recargar el catálogo sin reiniciar: presiona el botón **"recargar"** en la barra superior de la interfaz.

---

## Cómo cambiar el modelo de Groq

En `backend/.env`:

```env
# Mejor calidad (recomendado)
GROQ_MODELO=llama-3.3-70b-versatile

# Más rápido, menor calidad
GROQ_MODELO=llama-3.1-8b-instant

# Alternativa
GROQ_MODELO=mixtral-8x7b-32768
```

Consulta modelos disponibles en: https://console.groq.com/docs/models

---

## Cómo ajustar los umbrales de matching

En `backend/.env`:

```env
# Score >= 75: coincidencia automática (sin advertencia)
MATCHING_UMBRAL_ALTO=75.0

# Score entre 50 y 75: coincidencia dudosa (con advertencia)
MATCHING_UMBRAL_BAJO=50.0

# Score < 50: no encontrado (requiere cotización manual)
```

**Cuándo ajustar:**
- Muchos falsos positivos → sube `MATCHING_UMBRAL_ALTO` a 80 o 85
- El sistema no encuentra productos obvios → baja `MATCHING_UMBRAL_BAJO` a 40
- Muchos productos marcados como "dudosos" innecesariamente → baja `MATCHING_UMBRAL_ALTO` a 70

---

## Cómo modificar el formato del Excel de salida

Archivo: `backend/app/services/exportar_service.py`

**Cambiar colores:**
```python
COLOR_ENCABEZADO_FONDO = "1E293B"   # Color de encabezados
COLOR_DUDOSO_FONDO = "FEF9C3"       # Amarillo para dudosos
```

**Cambiar columnas:**
```python
COLUMNAS_COTIZACION = [
    ("Producto Solicitado", 30),
    ("Producto Encontrado", 35),
    # Agrega o quita columnas aquí
    # ("Mi Nueva Columna", 20),
]
```

**Agregar datos a las filas:** Modifica `_escribir_filas_productos()` en el mismo archivo.

---

## Mapeo de columnas del Excel de precios

Archivo: `backend/app/services/catalogo_service.py`  
Diccionario: `MAPEO_COLUMNAS`

Si tu Excel tiene nombres de columna diferentes, agrégalos al diccionario:

```python
MAPEO_COLUMNAS: dict[str, str] = {
    # "nombre en excel (normalizado)": "campo del modelo",
    "mi precio especial": "precio_lista",
    "clave producto": "codigo_ferrol",
    # ...
}
```

La normalización elimina tildes, espacios extra y convierte a minúsculas automáticamente. Solo necesitas agregar variantes con palabras distintas.

---

## Arquitectura del sistema

```
cotizador-ia/
├── app.py                     ← PUNTO DE ENTRADA PRINCIPAL
├── backend/
│   ├── app/
│   │   ├── main.py            ← FastAPI app + lifespan
│   │   ├── core/config.py     ← Configuración centralizada
│   │   ├── db/database.py     ← SQLite + sesiones async
│   │   ├── models/            ← Modelos SQLAlchemy
│   │   ├── schemas/           ← Schemas Pydantic (validación)
│   │   ├── services/
│   │   │   ├── llm_client.py       ← Abstracción del LLM (Groq)
│   │   │   ├── catalogo_service.py ← Importador de Excel
│   │   │   ├── matching_service.py ← Motor de búsqueda
│   │   │   ├── cotizacion_service.py ← Orquestador principal
│   │   │   └── exportar_service.py ← Generador de Excel de salida
│   │   └── api/routes/        ← Endpoints FastAPI
│   └── requirements.txt
└── frontend/
    └── src/
        ├── api/cotizador.ts   ← Cliente HTTP
        ├── hooks/useCotizacion.ts ← Estado de la app
        ├── types/index.ts     ← Tipos TypeScript
        └── components/        ← Componentes React
```

---

## Flujo completo de una cotización

```
Usuario escribe texto
        ↓
ChatPanel (frontend) → POST /api/cotizacion/
        ↓
CotizacionService.procesar_solicitud()
        ├─→ LLMClient.extraer_productos_json()   [Groq API]
        │           ↓
        │   Lista de {nombre, cantidad, unidad}
        ├─→ MotorMatching.buscar_multiples()
        │           ↓
        │   Fuzzy matching contra catálogo SQLite
        │   → nivel_confianza: alto/dudoso/no_encontrado
        ├─→ ExportadorExcel.generar_excel_cotizacion()
        │           ↓
        │   Archivo .xlsx en temp_cotizaciones/
        └─→ RespuestaCotizacion
                    ↓
        Frontend muestra productos + advertencias + descarga
```

---

## Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/cotizacion/` | Procesar solicitud de cotización |
| GET | `/api/catalogo/estado` | Estado del catálogo |
| POST | `/api/catalogo/recargar` | Recargar Excel |
| GET | `/api/exportar/descargar/{archivo}` | Descargar Excel |
| GET | `/api/health` | Health check |
| GET | `/api/docs` | Documentación Swagger |

---

## Debugging rápido

| Problema | Qué revisar |
|----------|-------------|
| Catálogo vacío | `EXCEL_RUTA` en `.env`, que el archivo exista y no esté abierto |
| LLM no responde | `GROQ_API_KEY` en `.env`, conexión a internet |
| Encabezados no mapeados | Logs del backend al arrancar — busca "Columna no mapeada" |
| Precios en cero | `_convertir_numero()` en `catalogo_service.py` |
| Excel no descarga | Que `temp_cotizaciones/` tenga permisos de escritura |
| CORS error | Que el frontend corra en puerto 5173 |

---

## Escalabilidad futura (arquitectura preparada)

La arquitectura está pensada para agregar sin romper lo existente:

- **Nuevos canales de entrada** (correo, WhatsApp): crear nuevo servicio que llame a `CotizacionService.procesar_solicitud()`
- **Nuevo proveedor LLM**: implementar nueva clase con método `extraer_productos_json()` y reemplazar en `llm_client.py`
- **Nuevas fuentes de precios**: crear nuevo importador en `services/` siguiendo el patrón de `catalogo_service.py`
- **Cola de revisión**: agregar tabla `revisiones` en modelos y endpoint de revisión
- **Múltiples listas de precios**: el modelo `Producto` puede recibir campo `fuente`

---

## PARTES QUE DEBES DEBUGGEAR MANUALMENTE

### 1. Mapeo de encabezados del Excel ⚠️ ALTA PRIORIDAD
**Archivo:** `backend/app/services/catalogo_service.py` → `MAPEO_COLUMNAS`

Tu Excel real casi con certeza tendrá variaciones en los nombres de columna. Al arrancar el sistema por primera vez, revisa los logs y busca líneas como:
```
✗ Columna no mapeada: 'PRECIO NETO PUBLICO' (normalizada: 'precio neto publico')
```
Agrega esa variante al diccionario `MAPEO_COLUMNAS`.

### 2. Formato de precios en el Excel ⚠️ ALTA PRIORIDAD
**Archivo:** `backend/app/services/catalogo_service.py` → `_convertir_numero()`

Si los precios vienen como `$1,234.56`, `1234,56` (coma decimal) o con otros formatos especiales, la función `_convertir_numero()` puede fallar silenciosamente (devuelve `None`). Verifica que los precios se carguen correctamente consultando `/api/catalogo/estado` y revisando un producto en la base de datos.

### 3. Hoja del Excel
Si tu Excel tiene múltiples hojas o el catálogo no está en la primera, configura `EXCEL_HOJA=NombreDeLaHoja` en `.env`. Si la hoja tiene nombre en español con tildes, puede requerir ajuste manual.

### 4. Fila de encabezado
Si el Excel tiene filas de título antes del encabezado real, ajusta `EXCEL_FILA_ENCABEZADO=1` (o el número correspondiente) en `.env`.

### 5. Umbrales de matching ⚠️ REQUIERE CALIBRACIÓN
Los umbrales por defecto (75/50) son un punto de partida razonable, pero tu lista de precios puede tener descripciones muy técnicas, abreviaciones propias o terminología regional. Necesitarás hacer pruebas con solicitudes reales y ajustar los umbrales hasta que el comportamiento sea el deseado.

### 6. Interpretación del LLM
El LLM puede ocasionalmente:
- No extraer correctamente medidas en fracciones (`1/4`, `3/8`)
- Confundir unidades (`metros` vs `rollos`)
- Generar JSON malformado (el sistema hace fallback a extracción básica)

Si el LLM falla frecuentemente, revisa los logs del backend y considera cambiar `GROQ_MODELO` a uno más capaz.

### 7. Rutas en Windows con espacios o caracteres especiales
Si tu ruta al Excel contiene acentos, ñ o espacios, ponla entre comillas en `.env`:
```env
EXCEL_RUTA="C:\Ferretería Güeréndaros\Lista de Precios 2024.xlsx"
```

### 8. Precio a usar en la cotización
El sistema prioriza: `precio_publico_neto` → `precio_lista` → `precio_sugerido_con_iva`. Si el precio que debe mostrarse es otro (por ejemplo `precio_20` o `precio_publico`), modifica `_obtener_precio_principal()` en `matching_service.py`.

### 9. Rendimiento con catálogos grandes
Para catálogos de más de 10,000 productos, la carga inicial en memoria puede tomar algunos segundos. Para más de 50,000, considera implementar búsqueda por chunks o un índice FTS en SQLite (comentado en `matching_service.py`).

### 10. Caracteres especiales en nombres de productos
Productos con ®, ™, º, °, comillas tipográficas o caracteres no-ASCII pueden causar problemas en el matching. La normalización Unicode cubre la mayoría, pero casos extremos requieren revisión manual.
