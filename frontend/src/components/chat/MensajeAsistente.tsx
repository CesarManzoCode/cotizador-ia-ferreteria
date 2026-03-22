// Burbuja de respuesta del asistente IA.

interface Props {
  mensaje: string
}

export function MensajeAsistente({ mensaje }: Props) {
  return (
    <div className="card-dark p-4 animate-fade-in">
      <div className="flex items-start gap-3">
        <div className="w-6 h-6 rounded-full bg-accent/10 border border-accent/30
                        flex items-center justify-center flex-shrink-0 mt-0.5">
          <span className="text-accent font-mono text-xs font-bold">AI</span>
        </div>
        <div className="flex-1">
          <span className="text-text-muted font-mono text-[10px] uppercase tracking-widest">
            asistente
          </span>
          <p className="text-text-primary font-mono text-xs mt-1 leading-relaxed whitespace-pre-line">
            {mensaje}
          </p>
        </div>
      </div>
    </div>
  )
}
