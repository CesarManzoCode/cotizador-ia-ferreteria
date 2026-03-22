// Hook personalizado para gestionar el estado del proceso de cotización.
// Encapsula toda la lógica de negocio del frontend.

import { useState, useCallback, useEffect } from 'react'
import {
  enviarSolicitudCotizacion,
  obtenerEstadoCatalogo,
  recargarCatalogo,
} from '../api/cotizador'
import type {
  EstadoApp,
  EstadoProceso,
  RespuestaCotizacion,
  EstadoCatalogo,
} from '../types'

export function useCotizacion() {
  const [proceso, setProceso] = useState<EstadoProceso>('idle')
  const [respuesta, setRespuesta] = useState<RespuestaCotizacion | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [catalogoInfo, setCatalogoInfo] = useState<EstadoCatalogo | null>(null)
  const [recargandoCatalogo, setRecargandoCatalogo] = useState(false)

  // Cargar estado del catálogo al montar el componente
  useEffect(() => {
    cargarEstadoCatalogo()
  }, [])

  const cargarEstadoCatalogo = useCallback(async () => {
    try {
      const estado = await obtenerEstadoCatalogo()
      setCatalogoInfo(estado)
    } catch {
      // Si el backend no está disponible, mostramos un estado de error silencioso
      setCatalogoInfo({
        total_productos: 0,
        archivo_fuente: '',
        estado: 'error',
        mensaje: 'No se pudo conectar al backend',
      })
    }
  }, [])

  const procesarCotizacion = useCallback(async (texto: string) => {
    if (!texto.trim() || proceso === 'cargando') return

    setProceso('cargando')
    setRespuesta(null)
    setError(null)

    try {
      const resultado = await enviarSolicitudCotizacion({ texto })
      setRespuesta(resultado)
      setProceso('exito')
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error inesperado'
      setError(mensaje)
      setProceso('error')
    }
  }, [proceso])

  const reiniciar = useCallback(() => {
    setProceso('idle')
    setRespuesta(null)
    setError(null)
  }, [])

  const forzarRecargaCatalogo = useCallback(async () => {
    setRecargandoCatalogo(true)
    try {
      await recargarCatalogo()
      await cargarEstadoCatalogo()
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al recargar catálogo'
      setError(mensaje)
    } finally {
      setRecargandoCatalogo(false)
    }
  }, [cargarEstadoCatalogo])

  const estado: EstadoApp = { proceso, respuesta, error, catalogoInfo }

  return {
    estado,
    procesarCotizacion,
    reiniciar,
    forzarRecargaCatalogo,
    recargandoCatalogo,
  }
}
