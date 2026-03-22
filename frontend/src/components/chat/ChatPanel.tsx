// Panel principal de entrada de solicitudes.
// Contiene el textarea de chat, botón de envío y burbuja de respuesta del asistente.

import { useState, useRef, KeyboardEvent } from 'react'
import { Send, RotateCcw, AlertCircle, Loader2 } from 'lucide-react'
import type { EstadoProceso, RespuestaCotizacion } from '../../types'
import { MensajeAsistente } from './MensajeAsistente'

interface Props {
  proceso: EstadoProceso
  error: string | null
  respuesta: RespuestaCotizacion | null
  onEnviar: (texto: string) => void
  onNuevaCotizacion: () => void
}

// Ejemplos de solicitudes para guiar al usuario
const EJEMPLOS = [
  'Necesito 50 tornillos galvanizados de 1/4, 20 taquetes de 3/8 y 10 pijas para tablaroca',
  '100 metros de tubo conduit de 3/4, 5 cajas de contactos dobles y 2 rollos de cable 12',
  '30 piezas de varilla del 3/8, 10 sacos de cemento y 5 cubetas de impermeabilizante',
]

export function ChatPanel({ proceso, error, respuesta, onEnviar, onNuevaCotizacion }: Props) {
  const [texto, setTexto] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const cargando = proceso === 'cargando'
  const hayResultado = proceso === 'exito' || proceso === 'error'

  const manejarEnvio = () => {
    const textoLimpio = texto.trim()
    if (!textoLimpio || cargando) return
    onEnviar(textoLimpio)
  }

  const manejarTecla = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter o Cmd+Enter para enviar
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      manejarEnvio()
    }
  }

  const manejarEjemplo = (ejemplo: string) => {
    setTexto(ejemplo)
    textareaRef.current?.focus()
  }

  const manejarNueva = () => {
    setTexto('')
    onNuevaCotizacion()
    setTimeout(() => textareaRef.current?.focus(), 100)
  }

  return (
    <div className="flex flex-col gap-4">
      {/* ── Cabecera del panel ──────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-text-primary font-mono text-base font-semibold">
            Nueva cotización
          </h1>
          <p className="text-text-muted font-mono text-xs mt-0.5">
            Describe los productos que necesitas cotizar en lenguaje natural.
          </p>
        </div>
        {hayResultado && (
          <button
            onClick={manejarNueva}
            className="btn-secondary flex items-center gap-1.5"
          >
            <RotateCcw size={13} />
            Nueva
          </button>
        )}
      </div>

      {/* ── Área de entrada ─────────────────────────────────────────────────── */}
      <div className="card-dark p-1">
        {/* Barra de título estilo terminal */}
        <div className="flex items-center gap-1.5 px-3 py-2 border-b border-surface-3">
          <div className="w-2.5 h-2.5 rounded-full bg-warn-red/50" />
          <div className="w-2.5 h-2.5 rounded-full bg-warn-yellow/50" />
          <div className="w-2.5 h-2.5 rounded-full bg-warn-green/50" />
          <span className="ml-2 text-text-muted font-mono text-[10px]">solicitud.txt</span>
        </div>

        <div className="relative">
          <textarea
            ref={textareaRef}
            value={texto}
            onChange={e => setTexto(e.target.value)}
            onKeyDown={manejarTecla}
            disabled={cargando}
            rows={5}
            placeholder={
              'Escribe aquí lo que necesitas cotizar...\n\nEjemplo: "50 tornillos 1/4, 20 taquetes 3/8, 2 rollos de alambre galvanizado #18"'
            }
            className="w-full bg-transparent text-text-primary font-mono text-sm
                       placeholder-text-muted resize-none p-4
                       focus:outline-none disabled:opacity-50"
            autoFocus
          />

          {/* Contador de caracteres */}
          <div className="absolute bottom-2 right-3 text-text-muted font-mono text-[10px]">
            {texto.length}/5000
          </div>
        </div>

        {/* Pie del textarea: shortcuts y botón enviar */}
        <div className="flex items-center justify-between px-3 py-2 border-t border-surface-3">
          <span className="text-text-muted font-mono text-[10px]">
            <kbd className="code-tag">Ctrl+Enter</kbd> para enviar
          </span>

          <button
            onClick={manejarEnvio}
            disabled={!texto.trim() || cargando}
            className="btn-primary flex items-center gap-2"
          >
            {cargando ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Procesando...
              </>
            ) : (
              <>
                <Send size={14} />
                Cotizar
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Ejemplos rápidos (solo en estado idle) ──────────────────────────── */}
      {proceso === 'idle' && !texto && (
        <div className="animate-fade-in">
          <p className="text-text-muted font-mono text-xs mb-2">Ejemplos:</p>
          <div className="flex flex-col gap-1.5">
            {EJEMPLOS.map((ej, i) => (
              <button
                key={i}
                onClick={() => manejarEjemplo(ej)}
                className="text-left text-text-muted hover:text-text-secondary
                           font-mono text-xs px-3 py-2 rounded-lg
                           bg-surface-1 hover:bg-surface-2
                           border border-surface-3 hover:border-surface-3
                           transition-all duration-150 truncate"
              >
                <span className="text-accent mr-2">›</span>
                {ej}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Indicador de carga ───────────────────────────────────────────────── */}
      {cargando && (
        <div className="card-dark p-4 animate-fade-in">
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-accent/10 border border-accent/30
                            flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-accent font-mono text-xs">AI</span>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-text-secondary font-mono text-xs">Procesando solicitud</span>
                <Loader2 size={11} className="animate-spin text-accent" />
              </div>
              <div className="space-y-1.5">
                {['Extrayendo productos con IA...', 'Buscando en catálogo...', 'Generando cotización...'].map((paso, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <div className="w-1 h-1 rounded-full bg-accent animate-pulse-soft"
                         style={{ animationDelay: `${i * 0.4}s` }} />
                    <span className="text-text-muted font-mono text-[11px]">{paso}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Error ─────────────────────────────────────────────────────────────── */}
      {proceso === 'error' && error && (
        <div className="card-dark border-warn-red/30 p-4 animate-fade-in">
          <div className="flex items-start gap-3">
            <AlertCircle size={16} className="text-warn-red flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-warn-red font-mono text-xs font-medium mb-1">Error al procesar</p>
              <p className="text-text-muted font-mono text-xs">{error}</p>
              <p className="text-text-muted font-mono text-[10px] mt-2">
                Verifica que el backend esté corriendo y que GROQ_API_KEY esté configurada en .env
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── Respuesta del asistente ───────────────────────────────────────────── */}
      {proceso === 'exito' && respuesta && (
        <MensajeAsistente mensaje={respuesta.mensaje_asistente} />
      )}
    </div>
  )
}
