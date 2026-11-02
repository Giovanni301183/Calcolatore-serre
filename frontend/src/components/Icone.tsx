// Icone semplici delle famiglie (SVG in linea, nessuna libreria)
const P = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }

const PATHS: Record<string, React.ReactNode> = {
  serra: <><path d="M4 30V18a7 7 0 0 1 14 0v12M18 30V18a7 7 0 0 1 14 0v12M2 30h32" {...P} /><path d="M11 30v-8M25 30v-8" {...P} /></>,
  capannone: <><path d="M3 30V15L18 6l15 9v15M2 30h32" {...P} /><path d="M13 30v-9h10v9" {...P} /></>,
  speciale: <><path d="M22 6a6 6 0 0 0-7.6 7.6L5 23l4 4 9.4-9.4A6 6 0 0 0 26 10l-3.5 3.5-3-3z" {...P} /></>,
  tunnel: <><path d="M4 30V20a14 12 0 0 1 28 0v10M2 30h32" {...P} /></>,
  ombraio: <><path d="M3 12h30M6 12v18M18 12v18M30 12v18M2 30h32M3 12l6-5h18l6 5" {...P} /></>,
  sole: <><circle cx="18" cy="18" r="6" {...P} /><path d="M18 4v4M18 28v4M4 18h4M28 18h4M8 8l3 3M25 25l3 3M28 8l-3 3M11 25l-3 3" {...P} /></>,
}

export default function Icona({ nome, className = 'h-9 w-9' }: { nome: string; className?: string }) {
  return <svg viewBox="0 0 36 36" className={className} aria-hidden>{PATHS[nome] ?? PATHS.speciale}</svg>
}
