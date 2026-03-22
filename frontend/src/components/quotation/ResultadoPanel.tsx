import { Download, CheckCircle, AlertTriangle, XCircle, TrendingUp, Hash, Tag, FileText } from 'lucide-react'
import type { RespuestaCotizacion, ProductoEncontrado, NivelConfianza } from '../../types'
import { obtenerUrlDescarga } from '../../api/cotizador'

interface Props {
  respuesta: RespuestaCotizacion
}

function formatearPrecio(valor: number | null | undefined): string {
  if (valor === null || valor === undefined) return '—'
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
  }).format(valor)
}

function BadgeConfianza({ nivel, score }: { nivel: NivelConfianza; score: number }) {
  if (nivel === 'alto')
    return <span className="badge-green"><CheckCircle size={10} />{score.toFixed(0)}%</span>
  if (nivel === 'dudoso')
    return <span className="badge-yellow"><AlertTriangle size={10} />{score.toFixed(0)}%</span>
  return <span className="badge-red"><XCircle size={10} />no encontrado</span>
}

function FilaProducto({ producto }: { producto: ProductoEncontrado }) {
  const esNoEncontrado = producto.nivel_confianza === 'no_encontrado'
  const esDudoso      = producto.nivel_confianza === 'dudoso'

  const bgClass = esNoEncontrado
    ? 'bg-warn-red-bg border-warn-red/20'
    : esDudoso
    ? 'bg-warn-yellow-bg border-warn-yellow/20'
    : 'bg-surface-2 border-surface-3'

  return (
    <div className={`rounded-lg border text-xs font-mono ${bgClass}`}>
      {/* ── Cabecera: solicitado + badge ── */}
      <div className="flex items-start justify-between gap-2 px-3 pt-3 pb-2">
        <div className="flex-1 min-w-0">
          <p className="text-text-muted text-[10px] uppercase tracking-wider mb-0.5">solicitado</p>
          <p className="text-text-secondary">{producto.nombre_solicitado}</p>
        </div>
        <BadgeConfianza nivel={producto.nivel_confianza} score={producto.score_similitud} />
      </div>

      {/* ── Datos del producto encontrado ── */}
      {!esNoEncontrado && producto.nombre_encontrado && (
        <div className="px-3 pb-2 space-y-1.5">

          {/* Nombre del producto */}
          <div>
            <p className="text-text-muted text-[10px] uppercase tracking-wider mb-0.5">
              <Tag size={9} className="inline mr-1" />producto
            </p>
            <p className="text-text-primary font-semibold leading-snug">
              {producto.nombre_encontrado}
            </p>
          </div>

          {/* Descripción */}
          {producto.descripcion && (
            <div>
              <p className="text-text-muted text-[10px] uppercase tracking-wider mb-0.5">
                <FileText size={9} className="inline mr-1" />descripción
              </p>
              <p className="text-text-secondary leading-snug line-clamp-2">
                {producto.descripcion}
              </p>
            </div>
          )}

          {/* Código FERROL */}
          {producto.codigo_ferrol && (
            <div className="flex items-center gap-1.5">
              <Hash size={10} className="text-accent flex-shrink-0" />
              <span className="text-text-muted text-[10px] uppercase tracking-wider">cód. ferrol:</span>
              <span className="code-tag text-accent">{producto.codigo_ferrol}</span>
            </div>
          )}
        </div>
      )}

      {/* ── Pie: cantidad + precio ── */}
      <div className={`flex items-center justify-between px-3 py-2 border-t ${
        esNoEncontrado ? 'border-warn-red/10' : esDudoso ? 'border-warn-yellow/10' : 'border-surface-3'
      }`}>
        <span className="text-text-muted">
          Cant: <span className="text-text-secondary">{producto.cantidad} {producto.unidad || 'pza'}</span>
        </span>
        <div className="text-right">
          {producto.precio_unitario != null && (
            <p className="text-text-muted text-[10px]">
              {formatearPrecio(producto.precio_unitario)} / {producto.unidad || 'pza'}
            </p>
          )}
          {producto.subtotal != null && (
            <p className={`font-bold text-sm ${esDudoso ? 'text-warn-yellow' : 'text-warn-green'}`}>
              {formatearPrecio(producto.subtotal)}
            </p>
          )}
        </div>
      </div>

      {/* ── Advertencia ── */}
      {producto.advertencia && (
        <div className={`px-3 py-1.5 border-t text-[10px] ${
          esNoEncontrado
            ? 'text-warn-red border-warn-red/10'
            : 'text-warn-yellow border-warn-yellow/10'
        }`}>
          ⚠ {producto.advertencia}
        </div>
      )}
    </div>
  )
}

export function ResultadoPanel({ respuesta }: Props) {
  const altos         = respuesta.productos.filter(p => p.nivel_confianza === 'alto')
  const dudosos       = respuesta.productos.filter(p => p.nivel_confianza === 'dudoso')
  const noEncontrados = respuesta.productos.filter(p => p.nivel_confianza === 'no_encontrado')

  return (
    <div className="flex flex-col gap-4 animate-slide-up">

      {/* ── Resumen totales ── */}
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
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 rounded bg-warn-green-bg border border-warn-green/20">
            <p className="text-warn-green font-mono text-lg font-bold">{altos.length}</p>
            <p className="text-text-muted font-mono text-[10px]">encontrados</p>
          </div>
          <div className="text-center p-2 rounded bg-warn-yellow-bg border border-warn-yellow/20">
            <p className="text-warn-yellow font-mono text-lg font-bold">{dudosos.length}</p>
            <p className="text-text-muted font-mono text-[10px]">dudosos</p>
          </div>
          <div className="text-center p-2 rounded bg-warn-red-bg border border-warn-red/20">
            <p className="text-warn-red font-mono text-lg font-bold">{noEncontrados.length}</p>
            <p className="text-text-muted font-mono text-[10px]">manuales</p>
          </div>
        </div>
      </div>

      {/* ── Descarga ── */}
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

      {/* ── Advertencias no encontrados ── */}
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
                <span className="text-warn-red flex-shrink-0">›</span>{adv}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Advertencias dudosas ── */}
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
                <span className="text-warn-yellow flex-shrink-0">›</span>{adv}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Lista de productos ── */}
      <div>
        <p className="text-text-muted font-mono text-[10px] uppercase tracking-widest mb-2">
          Detalle ({respuesta.productos.length} productos)
        </p>
        <div className="flex flex-col gap-2">
          {respuesta.productos.map((p, i) => (
            <FilaProducto key={i} producto={p} />
          ))}
        </div>
      </div>
    </div>
  )
}
