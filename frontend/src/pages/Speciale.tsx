import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, eur, type Categoria, type Preventivo, type RigaCosto, type VoceListino } from '../api'

const vuota = (): RigaCosto => ({ categoria: 'struttura', voce: '', qta: 1, unita: 'kg', costo_unitario: 0, costo: 0 })
const cell = 'w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-verde-600 focus:outline-none'

function Editor({ iniziale, categorie, listino }: { iniziale?: Preventivo; categorie: Categoria[]; listino: VoceListino[] }) {
  const nav = useNavigate()
  const [testa, setTesta] = useState({
    cliente: iniziale?.cliente ?? '', localita: iniziale?.localita ?? '',
    titolo: iniziale?.titolo ?? '', descrizione: iniziale?.descrizione ?? '',
  })
  const [righe, setRighe] = useState<RigaCosto[]>(
    (iniziale?.configurazione?.righe as unknown as RigaCosto[] | undefined) ?? [vuota()],
  )
  const perVoce = useMemo(() => new Map(listino.map((l) => [`${l.voce} (${l.unita})`, l])), [listino])

  const setRiga = (i: number, patch: Partial<RigaCosto>) =>
    setRighe((rs) => rs.map((r, j) => (j === i ? { ...r, ...patch } : r)))
  const sceltaVoce = (i: number, testo: string) => {
    const l = perVoce.get(testo)
    setRiga(i, l ? { voce: l.voce, unita: l.unita, costo_unitario: l.costo, categoria: l.categoria, listino_id: l.id } : { voce: testo, listino_id: undefined })
  }
  const totale = righe.reduce((s, r) => s + (Number(r.qta) || 0) * (Number(r.costo_unitario) || 0), 0)

  const salva = useMutation({
    mutationFn: () => {
      const body = { ...testa, righe }
      return iniziale ? api.aggiornaSpeciale(iniziale.id, body) : api.nuovoSpeciale(body)
    },
    onSuccess: (p) => nav(`/preventivi/${p.id}`),
  })

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/" className="text-sm text-gray-600 hover:underline">← Home</Link>
        <h1 className="text-xl font-semibold">Lavoro speciale</h1>
        {iniziale && <span className="text-sm text-gray-500">N. {iniziale.numero}</span>}
        <button onClick={() => salva.mutate()} disabled={salva.isPending || !righe.some((r) => r.voce.trim())}
          className="ml-auto rounded-md bg-verde-600 px-4 py-2 text-sm font-semibold text-white hover:bg-verde-700 disabled:opacity-50">
          {salva.isPending ? 'Salvo…' : 'Salva e calcola prezzo'}
        </button>
      </div>
      {salva.isError && <p className="rounded-md bg-red-50 p-3 text-sm text-red-800">{salva.error.message}</p>}

      <div className="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:grid-cols-3">
        {(['cliente', 'localita', 'titolo'] as const).map((k) => (
          <label key={k} className="text-xs font-medium text-gray-600">{k === 'localita' ? 'Località' : k === 'titolo' ? 'Oggetto (es. Tettoia 6 x 4)' : 'Cliente'}
            <input className={`${cell} mt-1`} value={testa[k]} onChange={(e) => setTesta({ ...testa, [k]: e.target.value })} /></label>
        ))}
        <label className="text-xs font-medium text-gray-600 sm:col-span-3">Descrizione tecnica (va nell'offerta)
          <textarea rows={3} className={`${cell} mt-1`} value={testa.descrizione} onChange={(e) => setTesta({ ...testa, descrizione: e.target.value })} /></label>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <div className="mb-2 flex items-center">
          <h2 className="font-semibold">Voci di costo</h2>
          <span className="ml-3 text-xs text-gray-500">Scrivi o scegli una voce del listino: unità e costo si compilano da soli</span>
        </div>
        <datalist id="listino">{listino.map((l) => <option key={l.id} value={`${l.voce} (${l.unita})`} />)}</datalist>
        <table className="w-full min-w-[760px] text-sm">
          <thead className="text-left text-xs text-gray-500"><tr>
            <th className="w-44 py-1 font-medium">Categoria</th><th className="py-1 font-medium">Voce</th>
            <th className="w-24 py-1 pr-4 text-right font-medium">Q.tà</th><th className="w-20 py-1 pl-1 font-medium">Unità</th>
            <th className="w-28 py-1 text-right font-medium">Costo unit. €</th><th className="w-28 py-1 text-right font-medium">Costo €</th><th className="w-8" />
          </tr></thead>
          <tbody>
            {righe.map((r, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="py-1.5 pr-2">
                  <select className={cell} value={r.categoria} onChange={(e) => setRiga(i, { categoria: e.target.value })}>
                    {categorie.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
                  </select>
                </td>
                <td className="py-1.5 pr-2"><input list="listino" className={cell} value={r.voce} onChange={(e) => sceltaVoce(i, e.target.value)} /></td>
                <td className="py-1.5 pr-2"><input type="number" step="any" className={`${cell} text-right`} value={r.qta ?? 0} onChange={(e) => setRiga(i, { qta: Number(e.target.value) })} /></td>
                <td className="py-1.5 pr-2"><input className={cell} value={r.unita ?? ''} onChange={(e) => setRiga(i, { unita: e.target.value })} /></td>
                <td className="py-1.5 pr-2"><input type="number" step="any" className={`${cell} text-right`} value={r.costo_unitario ?? 0} onChange={(e) => setRiga(i, { costo_unitario: Number(e.target.value) })} /></td>
                <td className="py-1.5 pr-2 text-right tabular-nums">{eur((Number(r.qta) || 0) * (Number(r.costo_unitario) || 0))}</td>
                <td><button title="Elimina riga" onClick={() => setRighe((rs) => rs.filter((_, j) => j !== i))} className="px-1 text-gray-400 hover:text-red-600">✕</button></td>
              </tr>
            ))}
          </tbody>
          <tfoot><tr className="border-t-2 border-gray-300 font-medium">
            <td colSpan={5} className="py-2"><button onClick={() => setRighe((rs) => [...rs, vuota()])} className="text-sm font-normal text-verde-700 hover:underline">+ Aggiungi voce</button></td>
            <td className="py-2 text-right tabular-nums">{eur(totale)}</td><td />
          </tr></tfoot>
        </table>
        <p className="mt-2 text-xs text-gray-500">Sono costi (non prezzi): margini, sconto e offerta si gestiscono nella pagina successiva.</p>
      </div>
    </div>
  )
}

export default function Speciale() {
  const { id } = useParams()
  const imp = useQuery({ queryKey: ['impostazioni'], queryFn: api.impostazioni })
  const lis = useQuery({ queryKey: ['listino'], queryFn: api.listino })
  const p = useQuery({ queryKey: ['preventivo', id], queryFn: () => api.preventivo(id!), enabled: !!id })
  if (!imp.data || !lis.data || (id && !p.data)) return <p className="text-gray-500">Carico…</p>
  return <Editor key={id ?? 'nuovo'} iniziale={p.data} categorie={imp.data.categorie} listino={lis.data} />
}
