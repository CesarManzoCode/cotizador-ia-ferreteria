// Componente raíz de la aplicación.
// Orquesta el layout principal y conecta los componentes.

import { useCotizacion } from './hooks/useCotizacion'
import { ChatPanel } from './components/chat/ChatPanel'
import { ResultadoPanel } from './components/quotation/ResultadoPanel'
import { BarraEstado } from './components/ui/BarraEstado'
import { Logo } from './components/ui/Logo'

export default function App() {
  const {
    estado,
    procesarCotizacion,
    reiniciar,
    forzarRecargaCatalogo,
    recargandoCatalogo,
  } = useCotizacion()

  const hayResultado = estado.proceso === 'exito' || estado.proceso === 'error'

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      {/* ── Barra superior ────────────────────────────────────────────────── */}
      <header className="border-b border-surface-3 bg-surface-1">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Logo />
          <BarraEstado
            catalogoInfo={estado.catalogoInfo}
            onRecargar={forzarRecargaCatalogo}
            recargando={recargandoCatalogo}
          />
        </div>
      </header>

      {/* ── Contenido principal ───────────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <div className={`grid gap-6 ${hayResultado ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
          {/* Panel de chat / entrada */}
          <div className={hayResultado ? '' : 'max-w-2xl mx-auto w-full'}>
            <ChatPanel
              proceso={estado.proceso}
              error={estado.error}
              respuesta={estado.respuesta}
              onEnviar={procesarCotizacion}
              onNuevaCotizacion={reiniciar}
            />
          </div>

          {/* Panel de resultado — solo visible cuando hay respuesta */}
          {hayResultado && estado.respuesta && (
            <div className="animate-slide-up">
              <ResultadoPanel respuesta={estado.respuesta} />
            </div>
          )}
        </div>
      </main>

      {/* ── Pie de página mínimo ──────────────────────────────────────────── */}
      <footer className="border-t border-surface-3 py-3 text-center">
        <span className="text-text-muted font-mono text-xs">
          cotizador-ia v1.0 · sistema local · sin autenticación
        </span>
      </footer>
    </div>
  )
}
