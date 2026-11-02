import type { FrontaleRiga } from '../api'

const cell = 'w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-verde-600 focus:outline-none'

/** Montanti per frontale e campata: ogni riga cambia il valore generale sul frontale e sulla campata scelti.
 *  Le righe dopo valgono sulle precedenti (es. "A e B, Tutte, 4" e poi "Frontale B, campata 3, 0"). */
export default function EditorFrontali({ righe, frontali, opzioni, campate, onChange }: {
  righe: FrontaleRiga[]; frontali: string[]; opzioni: number[]; campate: number; onChange: (r: FrontaleRiga[]) => void
}) {
  const set = (i: number, patch: Partial<FrontaleRiga>) => onChange(righe.map((r, j) => (j === i ? { ...r, ...patch } : r)))
  const nuova = (): FrontaleRiga => ({ frontale: 'A e B', campata: 0, montanti: 4, interasse: 0 })
  return (
    <div>
      <div className="mb-1 text-xs font-medium text-gray-600">Montanti diversi per frontale / campata ({righe.length})</div>
      <div className="space-y-2">
        {righe.map((r, i) => (
          <div key={i} className="grid grid-cols-2 gap-2 rounded-lg border border-gray-200 bg-gray-50 p-2.5 sm:grid-cols-[1.2fr_1fr_0.8fr_0.9fr_auto]">
            <label className="text-[11px] text-gray-500">Frontale
              <select className={cell} value={r.frontale} onChange={(e) => set(i, { frontale: e.target.value })}>
                {frontali.map((x) => <option key={x}>{x}</option>)}
              </select>
            </label>
            <label className="text-[11px] text-gray-500">Campata
              <select className={cell} value={r.campata} onChange={(e) => set(i, { campata: Number(e.target.value) })}>
                <option value={0}>Tutte</option>
                {Array.from({ length: campate }, (_, k) => <option key={k + 1} value={k + 1}>{k + 1}</option>)}
                {r.campata > campate && <option value={r.campata}>{r.campata} (non esiste)</option>}
              </select>
            </label>
            <label className="text-[11px] text-gray-500">Montanti
              <select className={cell} value={r.montanti} onChange={(e) => set(i, { montanti: Number(e.target.value) })}>
                {opzioni.map((x) => <option key={x} value={x}>{x}</option>)}
              </select>
            </label>
            <label className="text-[11px] text-gray-500">Interasse (m)
              <input type="number" step={0.05} min={0} className={cell} value={r.interasse || ''} placeholder="generale"
                onChange={(e) => set(i, { interasse: Number(e.target.value) })} />
            </label>
            <button title="Togli riga" onClick={() => onChange(righe.filter((_, j) => j !== i))}
              className="self-end px-2 py-1 text-gray-400 hover:text-red-600">✕</button>
          </div>
        ))}
      </div>
      <button onClick={() => onChange([...righe, nuova()])} className="mt-2 text-sm text-verde-700 hover:underline">+ Aggiungi riga</button>
    </div>
  )
}
