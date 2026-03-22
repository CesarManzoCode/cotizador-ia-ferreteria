// Barra de estado que muestra info del catálogo y botón de recarga.

import { RefreshCw, Database, AlertTriangle } from 'lucide-react'
import type { EstadoCatalogo } from '../../types'

interface Props {
  catalogoInfo: EstadoCatalogo | null
  onRecargar: () => void
  recargando: boolean
}

export function BarraEstado({ catalogoInfo, onRecargar, recargando }: Props) {
  if (!catalogoInfo) {
    return (
      <div className="flex items-center gap-2 text-text-muted font-mono text-xs">
        <span className="animate-pulse-soft">Conectando...</span>
      </div>
    )
  }

  const sinCatalogo = catalogoInfo.estado !== 'cargado' || catalogoInfo.total_productos === 0

  return (
    <div className="flex items-center gap-3">
      {/* Indicador del catálogo */}
      <div className={`flex items-center gap-1.5 font-mono text-xs ${
        sinCatalogo ? 'text-warn-yellow' : 'text-warn-green'
      }`}>
        {sinCatalogo ? (
          <AlertTriangle size={13} />
        ) : (
          <Database size={13} />
        )}
        <span>
          {sinCatalogo
            ? 'catálogo vacío'
            : `${catalogoInfo.total_productos.toLocaleString()} productos`}
        </span>
      </div>

      {/* Botón de recarga */}
      <button
        onClick={onRecargar}
        disabled={recargando}
        title="Recargar catálogo desde Excel"
        className="flex items-center gap-1.5 text-text-muted hover:text-text-primary
                   font-mono text-xs transition-colors duration-200
                   disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <RefreshCw
          size={12}
          className={recargando ? 'animate-spin' : ''}
        />
        <span className="hidden sm:inline">
          {recargando ? 'recargando...' : 'recargar'}
        </span>
      </button>
    </div>
  )
}
