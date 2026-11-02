import { useEffect, useState } from 'react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, eur, num, pct, type Preventivo, type Scelte } from '../api'
import { useDebounce } from '../useDebounce'

const SEMAFORO = {
  verde: 'bg-green-100 text-green-800 border-green-300',
  giallo: 'bg-amber-100 text-amber-900 border-amber-300',
  rosso: 'bg-red-100 text-red-800 border-red-300',
}

const inp = 'w-24 rounded-md border border-gray-300 px-2 py-1 text-right text-sm tabular-nums focus:border-verde-600 focus:outline-none'

/** Prezzo e margini: costi veri (master o voci libere) -> prezzo cliente con margini per categoria */
export default function PannelloPrezzo({ p }: { p: Preventivo }) {
  const qc = useQueryClient()
  const imp = useQuery({ queryKey: ['impostazioni'], queryFn: api.impostazioni })
  const [scelte, setScelte] = useState<Scelte>(p.prezzi?.scelte ?? {})
  const [approva, setApprova] = useState('')
  const [modificato, setModificato] = useState(false)
  useEffect(() => { setScelte(p.prezzi?.scelte ?? {}); setModificato(false) }, [p.id, p.prezzi?.scelte])

  const sDeb = useDebounce(scelte, 250)
  const ris = useQuery({
    queryKey: ['prezzo', p.id, sDeb, p.aggiornato_il],
    queryFn: () => api.prezzo(p.id, sDeb),
    placeholderData: keepPreviousData,
  })
  const salva = useMutation({
    mutationFn: () => api.prezzo(p.id, scelte, true),
    onSuccess: () => { setModificato(false); qc.invalidateQueries({ queryKey: ['preventivo', p.id] }); qc.invalidateQueries({ queryKey: ['preventivi'] }) },
  })
  const offerta = useMutation({
    mutationFn: async () => { if (modificato) await api.prezzo(p.id, scelte, true); return api.offerta(p.id, approva) },
    onSuccess: (np) => { setModificato(false); qc.setQueryData(['preventivo', p.id], np) },
  })

  const set = (patch: Scelte) => { setScelte((s) => ({ ...s, ...patch })); setModificato(true) }
  const setMargine = (cat: string, v: number) => set({ margini: { ...(scelte.margini ?? {}), [cat]: v } })

  const r = ris.data
  const v = imp.data?.valori
  if (!r || !v) return <div className="rounded-xl border border-gray-200 bg-white p-5 text-sm text-gray-500">Calcolo prezzo…</div>

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <h2 className="font-semibold">Prezzo e margini</h2>
        <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">solo uso interno: costi e margini non vanno nell'offerta</span>
        {modificato && <span className="text-xs text-amber-700">modifiche non salvate</span>}
        <div className="ml-auto flex gap-2">
          <button onClick={() => salva.mutate()} disabled={!modificato || salva.isPending}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-40">Salva</button>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        {/* tabella categorie */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-gray-500">
              <tr><th className="py-1.5 font-medium">Categoria</th><th className="py-1.5 text-right font-medium">Costo</th>
                <th className="py-1.5 text-right font-medium">Margine %</th><th className="py-1.5 text-right font-medium">Prezzo</th></tr>
            </thead>
            <tbody>
              {r.categorie.map((c) => (
                <tr key={c.id} className="border-t border-gray-100">
                  <td className="py-2">{c.nome}</td>
                  <td className="py-2 text-right tabular-nums text-gray-600">{eur(c.costo)}</td>
                  <td className="py-2 text-right">
                    <input type="number" step={0.5} min={0} max={90} className={inp}
                      value={scelte.margini?.[c.id] ?? c.margine} onChange={(e) => setMargine(c.id, Number(e.target.value))} />
                    <div className="text-[11px] text-gray-400">ricarico {num(c.ricarico, 1)}%</div>
                  </td>
                  <td className="py-2 text-right font-medium tabular-nums">{eur(c.prezzo)}</td>
                </tr>
              ))}
              <tr className="border-t-2 border-gray-300 font-medium">
                <td className="py-2">Totale listino</td><td className="py-2 text-right tabular-nums">{eur(r.costo_totale)}</td><td />
                <td className="py-2 text-right tabular-nums">{eur(r.prezzo_listino)}</td>
              </tr>
            </tbody>
          </table>

          {/* voci aggiuntive */}
          <div className="mt-4 grid gap-3 rounded-lg bg-gray-50 p-3 text-sm sm:grid-cols-2">
            {p.famiglia !== 'speciali' && (
              <>
                <label className="flex items-center justify-between gap-2">Montaggio €/m²
                  <input type="number" step={0.5} min={0} className={inp} value={scelte.montaggio_eur_m2 ?? v.montaggio_eur_m2}
                    onChange={(e) => set({ montaggio_eur_m2: Number(e.target.value) })} /></label>
                <label className="flex items-center justify-between gap-2">Trasporto € a viaggio
                  <input type="number" step={10} min={0} className={inp} value={scelte.trasporto_eur_viaggio ?? v.trasporto_eur_viaggio}
                    onChange={(e) => set({ trasporto_eur_viaggio: Number(e.target.value) })} /></label>
                <label className="flex items-center justify-between gap-2">N. viaggi <span className="text-xs text-gray-400">(vuoto = da peso)</span>
                  <input type="number" step={1} min={1} className={inp} value={scelte.viaggi ?? ''}
                    onChange={(e) => set({ viaggi: e.target.value === '' ? '' : Number(e.target.value) })} /></label>
                {p.con_calcolo && (
                  <label className="flex items-center justify-between gap-2">Progettazione €
                    <input type="number" step={50} min={0} className={inp} value={scelte.progettazione_eur ?? v.progettazione_eur}
                      onChange={(e) => set({ progettazione_eur: Number(e.target.value) })} /></label>
                )}
              </>
            )}
            <label className="flex items-center justify-between gap-2">Sconto %
              <input type="number" step={0.5} min={0} max={50} className={inp} value={scelte.sconto_pct ?? 0}
                onChange={(e) => set({ sconto_pct: Number(e.target.value) })} /></label>
          </div>
        </div>

        {/* riepilogo */}
        <div className="space-y-3">
          <div className={`rounded-lg border p-4 ${SEMAFORO[r.semaforo]}`}>
            <div className="text-sm">Prezzo al cliente (IVA esclusa)</div>
            <div className="text-3xl font-semibold tabular-nums">{eur(r.prezzo_finale)}</div>
            <div className="mt-1 text-sm">
              Margine reale <b>{pct(r.margine_reale)}</b> · ricarico {pct(r.ricarico_equivalente)}
              {r.eur_m2 != null && <> · {eur(r.eur_m2)}/m²</>}
            </div>
            {r.sconto > 0 && <div className="text-xs">Sconto {pct(r.sconto_pct)}: − {eur(r.sconto)}</div>}
            <div className="mt-1 text-xs opacity-80">Soglie: minimo {v.margine_minimo}% · attenzione {v.margine_attenzione}%</div>
          </div>
          {r.riferimento_master != null && (
            <p className="text-xs text-gray-600">Totale calcolato dal master Excel: {eur(r.riferimento_master)} (ricarico fisso ×1,6 sulla struttura).</p>
          )}
          {(p.prezzi?.note_master ?? []).map((n, i) => (
            <p key={i} className="rounded-md bg-orange-50 p-2.5 text-xs text-orange-900">⚠ {n}</p>
          ))}
          <ul className="space-y-1">
            {r.avvisi.map((a, i) => <li key={i} className="text-xs text-gray-700">• {a}</li>)}
          </ul>

          <div className="rounded-lg border border-gray-200 p-3">
            {r.richiede_approvazione && (
              <label className="mb-2 block text-sm">
                <span className="text-red-700">Serve l'approvazione della direzione.</span> Nome di chi approva:
                <input value={approva} onChange={(e) => setApprova(e.target.value)} className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1 text-sm" />
              </label>
            )}
            <button onClick={() => offerta.mutate()} disabled={offerta.isPending || (r.richiede_approvazione && !approva.trim())}
              className="w-full rounded-md bg-verde-600 px-4 py-2 text-sm font-semibold text-white hover:bg-verde-700 disabled:opacity-40">
              {offerta.isPending ? 'Creo il PDF…' : 'Genera offerta PDF per il cliente'}
            </button>
            {offerta.isError && <p className="mt-2 text-xs text-red-700">{offerta.error.message}</p>}
            {offerta.isSuccess && <p className="mt-2 text-xs text-green-700">Offerta creata: la trovi nei Documenti.</p>}
          </div>
        </div>
      </div>

      <details className="mt-4">
        <summary className="cursor-pointer text-sm font-medium text-verde-700">Dettaglio costi ({r.righe.length} righe)</summary>
        <table className="mt-2 w-full text-sm">
          <thead className="text-left text-xs text-gray-500"><tr>
            <th className="py-1 font-medium">Voce</th><th className="py-1 font-medium">Categoria</th>
            <th className="py-1 text-right font-medium">Q.tà</th><th className="py-1 text-right font-medium">Costo unit.</th><th className="py-1 text-right font-medium">Costo</th>
          </tr></thead>
          <tbody>
            {r.righe.map((x, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="py-1.5">{x.voce}</td>
                <td className="py-1.5 text-xs text-gray-500">{r.categorie.find((c) => c.id === x.categoria)?.nome ?? x.categoria}</td>
                <td className="py-1.5 text-right tabular-nums">{x.qta != null ? `${num(x.qta, x.unita === 'kg' ? 0 : 2)} ${x.unita ?? ''}` : ''}</td>
                <td className="py-1.5 text-right tabular-nums">{x.costo_unitario != null ? eur(x.costo_unitario) : ''}</td>
                <td className="py-1.5 text-right tabular-nums">{eur(x.costo)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  )
}
