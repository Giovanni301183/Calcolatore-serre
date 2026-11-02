import type { Stato } from '../api'

const STILE: Record<Stato, [string, string]> = {
  in_coda: ['In coda', 'bg-gray-100 text-gray-700'],
  in_lavorazione: ['In lavorazione…', 'bg-blue-100 text-blue-800'],
  bozza: ['Bozza', 'bg-gray-100 text-gray-800'],
  da_verificare: ['Da verificare', 'bg-amber-100 text-amber-800'],
  inviato: ['Inviato', 'bg-sky-100 text-sky-800'],
  accettato: ['Accettato', 'bg-green-100 text-green-800'],
  perso: ['Perso', 'bg-rose-100 text-rose-800'],
  errore: ['Errore', 'bg-red-100 text-red-800'],
}

export const STATI_MANUALI: Stato[] = ['bozza', 'da_verificare', 'inviato', 'accettato', 'perso']
export const etichettaStato = (s: Stato) => STILE[s][0]

export default function BadgeStato({ stato }: { stato: Stato }) {
  const [testo, cls] = STILE[stato] ?? [stato, 'bg-gray-100']
  return <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>{testo}</span>
}
