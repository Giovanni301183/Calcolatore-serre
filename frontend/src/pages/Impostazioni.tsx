import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, num, type Impostazioni as Imp } from '../api'

const inp = 'w-28 rounded-md border border-gray-300 px-2 py-1 text-right text-sm tabular-nums focus:border-verde-600 focus:outline-none'

export default function Impostazioni() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['impostazioni'], queryFn: api.impostazioni })
  const [v, setV] = useState<Imp | null>(null)
  useEffect(() => { if (q.data) setV(q.data.valori) }, [q.data])
  const salva = useMutation({
    mutationFn: (x: Imp) => api.salvaImpostazioni(x),
    onSuccess: (d) => qc.setQueryData(['impostazioni'], d),
  })
  if (!q.data || !v) return <p className="text-gray-500">Carico…</p>
  const n = (k: keyof Imp) => (e: React.ChangeEvent<HTMLInputElement>) => setV({ ...v, [k]: Number(e.target.value) })

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold">Impostazioni prezzi</h1>
        <button onClick={() => salva.mutate({ ...v, da_confermare: false })}
          className="ml-auto rounded-md bg-verde-600 px-4 py-2 text-sm font-semibold text-white hover:bg-verde-700">Salva e conferma</button>
      </div>
      {v.da_confermare && (
        <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-900">
          Valori di partenza proposti: struttura 37,5% = l'attuale ricarico ×1,6 del master. Gli altri sono ipotesi da decidere con la direzione.
        </p>
      )}
      {salva.isSuccess && <p className="text-sm text-green-700">Salvato.</p>}

      <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="mb-1 font-semibold">Margine di default per categoria</h2>
        <p className="mb-3 text-xs text-gray-500">Margine sul prezzo: prezzo = costo ÷ (1 − margine). Accanto, il ricarico equivalente sul costo.</p>
        <table className="w-full text-sm"><tbody>
          {q.data.categorie.map((c) => {
            const m = v.margini[c.id] ?? 0
            return (
              <tr key={c.id} className="border-t border-gray-100">
                <td className="py-2">{c.nome}<div className="text-xs text-gray-500">{c.descrizione}</div></td>
                <td className="py-2 text-right whitespace-nowrap">
                  <input type="number" step={0.5} className={inp} value={m}
                    onChange={(e) => setV({ ...v, margini: { ...v.margini, [c.id]: Number(e.target.value) } })} /> %
                </td>
                <td className="w-40 py-2 text-right text-xs text-gray-500">ricarico {num(m < 100 ? (1 / (1 - m / 100) - 1) * 100 : 0, 1)}%</td>
              </tr>
            )
          })}
        </tbody></table>
      </section>

      <section className="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 text-sm shadow-sm sm:grid-cols-2">
        <h2 className="font-semibold sm:col-span-2">Soglie e approvazioni</h2>
        <label className="flex items-center justify-between">Margine minimo (sotto = approvazione) <span><input type="number" className={inp} value={v.margine_minimo} onChange={n('margine_minimo')} /> %</span></label>
        <label className="flex items-center justify-between">Margine di attenzione (giallo) <span><input type="number" className={inp} value={v.margine_attenzione} onChange={n('margine_attenzione')} /> %</span></label>
        <label className="flex items-center justify-between">Sconto max commerciale <span><input type="number" className={inp} value={v.sconto_max_commerciale} onChange={n('sconto_max_commerciale')} /> %</span></label>
      </section>

      <section className="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 text-sm shadow-sm sm:grid-cols-2">
        <h2 className="font-semibold sm:col-span-2">Montaggio, trasporto, progettazione (costi di default)</h2>
        <label className="flex items-center justify-between">Montaggio € al m² <input type="number" className={inp} value={v.montaggio_eur_m2} onChange={n('montaggio_eur_m2')} /></label>
        <label className="flex items-center justify-between">Trasporto € a viaggio <input type="number" className={inp} value={v.trasporto_eur_viaggio} onChange={n('trasporto_eur_viaggio')} /></label>
        <label className="flex items-center justify-between">Kg per viaggio <input type="number" className={inp} value={v.kg_per_viaggio} onChange={n('kg_per_viaggio')} /></label>
        <label className="flex items-center justify-between">Progettazione € (con calcolo) <input type="number" className={inp} value={v.progettazione_eur} onChange={n('progettazione_eur')} /></label>
      </section>

      <section className="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 text-sm shadow-sm">
        <h2 className="font-semibold">Condizioni nell'offerta</h2>
        <label className="flex items-center justify-between">Validità (giorni) <input type="number" className={inp} value={v.validita_giorni} onChange={n('validita_giorni')} /></label>
        <label>Condizioni di pagamento
          <input className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1" value={v.condizioni_pagamento}
            onChange={(e) => setV({ ...v, condizioni_pagamento: e.target.value })} /></label>
      </section>
    </div>
  )
}
