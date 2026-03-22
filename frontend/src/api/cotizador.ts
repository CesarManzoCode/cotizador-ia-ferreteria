// Cliente HTTP para comunicación con el backend FastAPI.
// Centraliza todas las llamadas a la API en un solo lugar.

import type {
  RespuestaCotizacion,
  SolicitudCotizacion,
  EstadoCatalogo,
} from '../types'

// URL base del backend. En desarrollo usa el proxy de Vite.
// En producción apuntaría al servidor real.
const API_BASE = '/api'

// Timeout máximo de espera (ms) — el LLM puede tardar varios segundos
const TIMEOUT_MS = 60_000

/**
 * Función auxiliar para fetch con timeout y manejo de errores consistente.
 */
async function fetchConTimeout(
  url: string,
  opciones: RequestInit = {},
  timeoutMs = TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const respuesta = await fetch(url, {
      ...opciones,
      signal: controller.signal,
    })
    return respuesta
  } finally {
    clearTimeout(timer)
  }
}

/**
 * Envía una solicitud de cotización al backend.
 * El backend procesa el texto, busca en el catálogo y devuelve la cotización.
 */
export async function enviarSolicitudCotizacion(
  solicitud: SolicitudCotizacion,
): Promise<RespuestaCotizacion> {
  const respuesta = await fetchConTimeout(`${API_BASE}/cotizacion/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(solicitud),
  })

  if (!respuesta.ok) {
    const detalle = await respuesta.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(detalle.detail || `Error ${respuesta.status}`)
  }

  return respuesta.json()
}

/**
 * Obtiene el estado del catálogo cargado en el backend.
 */
export async function obtenerEstadoCatalogo(): Promise<EstadoCatalogo> {
  const respuesta = await fetchConTimeout(`${API_BASE}/catalogo/estado`)
  if (!respuesta.ok) throw new Error('No se pudo obtener el estado del catálogo')
  return respuesta.json()
}

/**
 * Fuerza una recarga del catálogo desde el Excel configurado.
 */
export async function recargarCatalogo(): Promise<{ mensaje: string; total_productos: number }> {
  const respuesta = await fetchConTimeout(`${API_BASE}/catalogo/recargar`, {
    method: 'POST',
  })
  if (!respuesta.ok) {
    const detalle = await respuesta.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(detalle.detail || `Error ${respuesta.status}`)
  }
  return respuesta.json()
}

/**
 * Construye la URL de descarga para un archivo Excel generado.
 */
export function obtenerUrlDescarga(nombreArchivo: string): string {
  return `${API_BASE}/exportar/descargar/${encodeURIComponent(nombreArchivo)}`
}

/**
 * Verifica si el backend está disponible.
 */
export async function verificarSaludBackend(): Promise<boolean> {
  try {
    const respuesta = await fetchConTimeout(`${API_BASE}/health`, {}, 5000)
    return respuesta.ok
  } catch {
    return false
  }
}
