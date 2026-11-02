import type { Porta } from '../api'

const cell = 'w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-verde-600 focus:outline-none'

/** Elenco porte: posizione (frontale A/B o laterale 1/2), campata o distanza, misure */
export default function EditorPorte({ porte, posizioni, campate, lunghezza, onChange }: {
  porte: Porta[]; posizioni: string[]; campate: number; lunghezza: number; onChange: (p: Porta[]) => void
}) {
  const set = (i: number, patch: Partial<Porta>) => onChange(porte.map((p, j) => (j === i ? { ...p, ...patch } : p)))
  const nuova = (): Porta => ({ posizione: 'Frontale A', campata: 0, distanza: 0, larghezza: 2.4, altezza: 2.3 })
  return (
    <div>
      <div className="mb-1 text-xs font-medium text-gray-600">Porte scorrevoli ({porte.length})</div>
      <div className="space-y-2">
        {porte.map((p, i) => {
          const frontale = p.posizione.startsWith('Frontale')
          return (
            <div key={i} className="grid grid-cols-2 gap-2 rounded-lg border border-gray-200 bg-gray-50 p-2.5 sm:grid-cols-[1.3fr_1fr_0.8fr_0.8fr_auto]">
              <label className="text-[11px] text-gray-500">Posizione
                <select className={cell} value={p.posizione} onChange={(e) => set(i, { posizione: e.target.value })}>
                  {posizioni.map((x) => <option key={x}>{x}</option>)}
                </select>
              </label>
              {frontale ? (
                <label className="text-[11px] text-gray-500">Campata
                  <select className={cell} value={p.campata} onChange={(e) => set(i, { campata: Number(e.target.value) })}>
                    <option value={0}>Centrale ({Math.ceil(campate / 2)})</option>
                    {Array.from({ length: campate }, (_, k) => <option key={k + 1} value={k + 1}>{k + 1}</option>)}
                  </select>
                </label>
              ) : (
                <label className="text-[11px] text-gray-500">Distanza dal frontale A (m)
                  <input type="number" step={0.5} min={0} max={lunghezza} className={cell} value={p.distanza || ''}
                    placeholder={`metà: ${lunghezza / 2}`} onChange={(e) => set(i, { distanza: Number(e.target.value) })} />
                </label>
              )}
              <label className="text-[11px] text-gray-500">Larghezza (m)
                <input type="number" step={0.1} min={1} className={cell} value={p.larghezza} onChange={(e) => set(i, { larghezza: Number(e.target.value) })} />
              </label>
              <label className="text-[11px] text-gray-500">Altezza (m)
                <input type="number" step={0.1} min={1.8} className={cell} value={p.altezza} onChange={(e) => set(i, { altezza: Number(e.target.value) })} />
              </label>
              <button title="Togli porta" onClick={() => onChange(porte.filter((_, j) => j !== i))}
                className="self-end px-2 py-1 text-gray-400 hover:text-red-600">✕</button>
            </div>
          )
        })}
      </div>
      <button onClick={() => onChange([...porte, nuova()])} className="mt-2 text-sm text-verde-700 hover:underline">+ Aggiungi porta</button>
    </div>
  )
}
