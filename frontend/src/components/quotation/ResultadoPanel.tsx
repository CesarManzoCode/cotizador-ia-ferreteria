// Panel de resultados de la cotización.
// Muestra productos encontrados, advertencias y botón de descarga.

import { Download, CheckCircle, AlertTriangle, XCircle, TrendingUp } from 'lucide-react'
import type { RespuestaCotizacion, ProductoEncontrado, NivelConfianza } from '../../types'
import { obtenerUrlDescarga } from '../../api/cotizador'

interface Props {
  respuesta: RespuestaCotizacion
}

function formatearPrecio(valor: number | null): string {
  if (valor === null || valor === undefined) return '—'
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
  }).format(valor)
}

function BadgeConfianza({ nivel, score }: { nivel: NivelConfianza; score: number }) {
  if (nivel === 'alto') {
    return <span className="badge-green"><CheckCircle size={10} />{score.toFixed(0)}%</span>
  }
  if (nivel === 'dudoso') {
    return <span className="badge-yellow"><AlertTriangle size={10} />{score.toFixed(0)}%</span>
  }
  return <span className="badge-red"><XCircle size={10} />no encontrado</span>
}

function FilaProducto({ producto }: { producto: ProductoEncontrado }) {
  const esNoEncontrado = producto.nivel_confianza === 'no_encontrado'
  const esDudoso = producto.nivel_confianza === 'dudoso'

  return (
    <div className={`p-3 rounded-lg border text-xs font-mono transition-colors ${
      esNoEncontrado
        ? 'bg-warn-red-bg border-warn-red/20'
        : esDudoso
        ? 'bg-warn-yellow-bg border-warn-yellow/20'
        : 'bg-surface-2 border-surface-3'
    }`}>
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="flex-1 min-w-0">
          <p className="text-text-muted text-[10px] uppercase tracking-wider mb-0.5">solicitado</p>
          <p className="text-text-secondary truncate">{producto.nombre_solicitado}</p>
        </div>
        <BadgeConfianza nivel={producto.nivel_confianza} score={producto.score_similitud} />
      </div>

      {!esNoEncontrado && producto.nombre_encontrado && (
        <div className="mb-1.5">
          <p className="text-text-muted text-[10px] uppercase tracking-wider mb-0.5">encontrado</p>
          <p className="text-text-primary font-medium">{producto.nombre_encontrado}</p>
          {producto.marca && (
            <p className="text-text-muted text-[10px]">{producto.marca}</p>
          )}
        </div>
      )}

      <div className="flex items-center justify-between mt-2 pt-2 border-t border-surface-3/50">
        <div className="flex items-center gap-3">
          <span className="text-text-muted">
            Cant: <span className="text-text-secondary">{producto.cantidad} {producto.unidad || 'pza'}</span>
          </span>
          {producto.codigo_ferrol && (
            <span className="code-tag">{producto.codigo_ferrol}</span>
          )}
        </div>
        <div className="text-right">
          {producto.precio_unitario !== null && (
            <p className="text-text-muted text-[10px]">
              {formatearPrecio(producto.precio_unitario)} / {producto.unidad || 'pza'}
            </p>
          )}
          {producto.subtotal !== null && (
            <p className={`font-semibold ${esDudoso ? 'text-warn-yellow' : 'text-warn-green'}`}>
              {formatearPrecio(producto.subtotal)}
            </p>
          )}
        </div>
      </div>

      {producto.advertencia && (
        <p className={`mt-2 text-[10px] ${
          esNoEncontrado ? 'text-warn-red' : 'text-warn-yellow'
        }`}>
          ⚠ {producto.advertencia}
        </p>
      )}
    </div>
  )
}

export function ResultadoPanel({ respuesta }: Props) {
  const productosAltos = respuesta.productos.filter(p => p.nivel_confianza === 'alto')
  const productosDudosos = respuesta.productos.filter(p => p.nivel_confianza === 'dudoso')
  const productosNoEncontrados = respuesta.productos.filter(p => p.nivel_confianza === 'no_encontrado')

  return (
    <div className="flex flex-col gap-4 animate-slide-up">
      {/* ── Cabecera con total ───────────────────────────────────────────────── */}
      <div className="card-dark p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <TrendingUp size={15} className="text-accent" />
            <h2 className="text-text-primary font-mono text-sm font-semibold">
              Cotización #{respuesta.cotizacion_id || 'borrador'}
            </h2>
          </div>
          <div className="text-right">
            <p className="text-text-muted font-mono text-[10px]">subtotal</p>
            <p className="text-warn-green font-mono text-lg font-bold">
              {formatearPrecio(respuesta.total)}
            </p>
          </div>
        </div>

        {/* Resumen de conteos */}
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 rounded bg-warn-green-bg border border-warn-green/20">
            <p className="text-warn-green font-mono text-lg font-bold">{productosAltos.length}</p>
            <p className="text-text-muted font-mono text-[10px]">encontrados</p>
          </div>
          <div className="text-center p-2 rounded bg-warn-yellow-bg border border-warn-yellow/20">
            <p className="text-warn-yellow font-mono text-lg font-bold">{productosDudosos.length}</p>
            <p className="text-text-muted font-mono text-[10px]">dudosos</p>
          </div>
          <div className="text-center p-2 rounded bg-warn-red-bg border border-warn-red/20">
            <p className="text-warn-red font-mono text-lg font-bold">{productosNoEncontrados.length}</p>
            <p className="text-text-muted font-mono text-[10px]">manuales</p>
          </div>
        </div>
      </div>

      {/* ── Botón de descarga ────────────────────────────────────────────────── */}
      {respuesta.archivo_excel_nombre && (
        <a
          href={obtenerUrlDescarga(respuesta.archivo_excel_nombre)}
          download={respuesta.archivo_excel_nombre}
          className="btn-primary flex items-center justify-center gap-2 w-full py-3 glow-blue"
        >
          <Download size={15} />
          Descargar Excel de cotización
        </a>
      )}

      {/* ── Advertencias críticas ────────────────────────────────────────────── */}
      {respuesta.advertencias_no_encontrados.length > 0 && (
        <div className="card-dark border-warn-red/30 p-3">
          <div className="flex items-center gap-2 mb-2">
            <XCircle size={13} className="text-warn-red" />
            <p className="text-warn-red font-mono text-xs font-medium">
              Requieren cotización manual ({respuesta.advertencias_no_encontrados.length})
            </p>
          </div>
          <ul className="space-y-1">
            {respuesta.advertencias_no_encontrados.map((adv, i) => (
              <li key={i} className="text-text-muted font-mono text-[11px] flex gap-1.5">
                <span className="text-warn-red flex-shrink-0">›</span>
                {adv}
              </li>
            ))}
          </ul>
        </div>
      )}

      {respuesta.advertencias_dudosas.length > 0 && (
        <div className="card-dark border-warn-yellow/30 p-3">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={13} className="text-warn-yellow" />
            <p className="text-warn-yellow font-mono text-xs font-medium">
              Coincidencias dudosas — verificar ({respuesta.advertencias_dudosas.length})
            </p>
          </div>
          <ul className="space-y-1">
            {respuesta.advertencias_dudosas.map((adv, i) => (
              <li key={i} className="text-text-muted font-mono text-[11px] flex gap-1.5">
                <span className="text-warn-yellow flex-shrink-0">›</span>
                {adv}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Lista de productos ───────────────────────────────────────────────── */}
      <div>
        <p className="text-text-muted font-mono text-[10px] uppercase tracking-widest mb-2">
          Detalle de productos ({respuesta.productos.length})
        </p>
        <div className="flex flex-col gap-2">
          {respuesta.productos.map((producto, i) => (
            <FilaProducto key={i} producto={producto} />
          ))}
        </div>
      </div>
    </div>
  )
}
