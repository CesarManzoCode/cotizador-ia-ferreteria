// Componente de logo y nombre del sistema en la barra superior.

export function Logo() {
  return (
    <div className="flex items-center gap-3">
      {/* Ícono minimalista estilo terminal */}
      <div className="w-7 h-7 rounded-md bg-accent/10 border border-accent/30 flex items-center justify-center">
        <span className="text-accent font-mono text-sm font-bold leading-none">$</span>
      </div>
      <div className="flex flex-col leading-none">
        <span className="text-text-primary font-mono text-sm font-semibold tracking-tight">
          cotizador<span className="text-accent">-ia</span>
        </span>
        <span className="text-text-muted font-mono text-[10px] mt-0.5">
          sistema de cotizaciones asistidas
        </span>
      </div>
    </div>
  )
}
