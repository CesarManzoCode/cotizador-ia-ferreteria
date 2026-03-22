// ── Tipos principales del sistema de cotizaciones ────────────────────────────
// Deben mantenerse sincronizados con los schemas de Pydantic del backend.

export type NivelConfianza = 'alto' | 'dudoso' | 'no_encontrado'

export interface ProductoEncontrado {
  // Datos del producto solicitado
  nombre_solicitado: string
  cantidad: number

  // Datos del catálogo
  producto_id: number | null
  nombre_encontrado: string | null
  descripcion: string | null
  marca: string | null
  unidad: string | null
  codigo_ferrol: string | null

  // Precios
  precio_unitario: number | null
  subtotal: number | null

  // Matching
  nivel_confianza: NivelConfianza
  score_similitud: number
  advertencia: string | null
}

export interface RespuestaCotizacion {
  cotizacion_id: number | null
  mensaje_asistente: string
  productos: ProductoEncontrado[]
  advertencias_dudosas: string[]
  advertencias_no_encontrados: string[]
  subtotal: number
  total: number
  archivo_excel_nombre: string | null
  exito: boolean
  error: string | null
}

export interface SolicitudCotizacion {
  texto: string
}

export interface EstadoCatalogo {
  total_productos: number
  archivo_fuente: string
  estado: 'cargado' | 'vacio' | 'error'
  mensaje: string | null
}

// ── Estado interno del chat ───────────────────────────────────────────────────

export type EstadoProceso = 'idle' | 'cargando' | 'exito' | 'error'

export interface EstadoApp {
  proceso: EstadoProceso
  respuesta: RespuestaCotizacion | null
  error: string | null
  catalogoInfo: EstadoCatalogo | null
}
