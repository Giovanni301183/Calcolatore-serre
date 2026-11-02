import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, data, type VoceListino } from '../api'

function Costo({ v }: { v: VoceListino }) {
  const qc = useQueryClient()
  const [val, setVal] = useState(String(v.costo))
  const m = useMutation({
    mutationFn: (c: number) => api.modificaListino(v.id, c),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['listino'] }),
  })
  const salva = () => { const c = Number(val.replace(',', '.')); if (!Number.isNaN(c) && c !== v.costo) m.mutate(c) }
  return (
    <input value={val} onChange={(e) => setVal(e.target.value)} onBlur={salva} onKeyDown={(e) => e.key === 'Enter' && salva()}
      className={`w-24 rounded border px-2 py-1 text-right text-sm tabular-nums ${m.isSuccess ? 'border-green-400' : 'border-gray-300'}`} />
  )
}

export default function Listino() {
  const lis = useQuery({ queryKey: ['listino'], queryFn: api.listino })
  const imp = useQuery({ queryKey: ['impostazioni'], queryFn: api.impostazioni })
  const [q, setQ] = useState('')
  if (!lis.data || !imp.data) return <p className="text-gray-500">Carico…</p>
  const righe = lis.data.filter((l) => l.voce.toLowerCase().includes(q.toLowerCase()))
  const daConf = lis.data.filter((l) => l.da_confermare).length

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">Listino costi</h1>
        <span className="text-sm text-gray-500">{lis.data.length} voci · {daConf} da confermare</span>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cerca voce…"
          className="ml-auto w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm sm:w-64" />
      </div>
      <p className="rounded-md bg-sky-50 p-3 text-sm text-sky-900">
        Costi unitari (non prezzi di vendita), presi dal master 2026. Una modifica vale per i nuovi calcoli dei lavori speciali.
        Le serre per ora usano ancora i €/kg scritti nel master Excel: quando il motore sarà in Python useranno questo listino.
      </p>
      {imp.data.categorie.map((c) => {
        const voci = righe.filter((l) => l.categoria === c.id)
        if (!voci.length) return null
        return (
          <div key={c.id} className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
            <h2 className="border-b border-gray-100 px-4 py-2.5 font-semibold">{c.nome}</h2>
            <table className="w-full text-sm">
              <tbody>
                {voci.map((v) => (
                  <tr key={v.id} className="border-t border-gray-50">
                    <td className="px-4 py-1.5">{v.voce}{v.da_confermare ? <span className="ml-2 rounded bg-amber-50 px-1.5 text-xs text-amber-700">da confermare</span> : null}</td>
                    <td className="px-2 py-1.5 text-xs text-gray-500">{v.fonte}</td>
                    <td className="px-2 py-1.5 text-right whitespace-nowrap">€ <Costo v={v} /> / {v.unita}</td>
                    <td className="px-4 py-1.5 text-right text-xs whitespace-nowrap text-gray-400">{data(v.aggiornato_il)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      })}
    </div>
  )
}
