import { useEffect, useMemo, useState } from 'react'
import { keepPreviousData, useMutation, useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api, num, type FrontaleRiga, type Porta, type Schema, type Valore, type Valori } from '../api'
import CampoInput from '../components/CampoInput'
import EditorFrontali from '../components/EditorFrontali'
import EditorPorte from '../components/EditorPorte'
import { useDebounce } from '../useDebounce'

const defaults = (s: Schema): Valori =>
  Object.fromEntries(s.gruppi.flatMap((g) => g.campi.map((c) => [c.key, c.default])))

function Form({ schema, iniziali, conCalcolo, origineId }: { schema: Schema; iniziali: Valori; conCalcolo: boolean; origineId?: string }) {
  const fam = schema.id
  const nav = useNavigate()
  const [valori, setValori] = useState<Valori>(iniziali)
  const [tab, setTab] = useState(schema.gruppi[0].id)
  const [modello, setModello] = useState('')

  const set = (k: string, v: Valore) =>
    setValori((old) => {
      const n = { ...old, [k]: v }
      if (k === 'fondazione' && typeof v === 'string' && v in schema.default_interramento) n.interramento = schema.default_interramento[v]
      return n
    })
  const applicaModello = (id: string) => {
    setModello(id)
    const m = schema.modelli.find((x) => x.id === id)
    if (m) setValori((old) => ({ ...old, ...m.valori }))
  }

  const vCalc = useDebounce(valori, 300)
  const vDis = useDebounce(valori, 1200)
  const calc = useQuery({
    queryKey: ['calcola', fam, vCalc, conCalcolo],
    queryFn: () => api.calcola(fam, vCalc, conCalcolo),
    placeholderData: keepPreviousData,
  })
  const ant = useQuery({
    queryKey: ['anteprima', fam, vDis],
    queryFn: () => api.anteprima(fam, vDis),
    placeholderData: keepPreviousData,
    staleTime: Infinity,
    gcTime: 30_000,
  })
  useEffect(() => () => { if (ant.data) URL.revokeObjectURL(ant.data) }, [ant.data])

  const genera = useMutation({
    mutationFn: () => api.nuovoPreventivo(fam, valori, conCalcolo, origineId),
    onSuccess: (p) => nav(`/preventivi/${p.id}`),
  })

  const gruppo = schema.gruppi.find((g) => g.id === tab)!
  const r = calc.data

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/" className="text-sm text-gray-600 hover:underline">← Home</Link>
        <h1 className="text-xl font-semibold">{schema.nome}</h1>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${conCalcolo ? 'bg-amber-100 text-amber-800' : 'bg-verde-100 text-verde-800'}`}>
          {conCalcolo ? 'Con calcolo strutturale' : 'Senza calcolo'}
        </span>
        {origineId && <span className="text-xs text-gray-500">nuova versione di un preventivo esistente</span>}
        <button
          onClick={() => genera.mutate()}
          disabled={genera.isPending || calc.isError}
          className="ml-auto rounded-md bg-verde-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-verde-700 disabled:opacity-50"
        >
          {genera.isPending ? 'Invio…' : 'Genera disegno + computo'}
        </button>
      </div>
      {genera.isError && <p className="rounded-md bg-red-50 p-3 text-sm text-red-800">{String(genera.error.message)}</p>}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        {/* colonna dati */}
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-100 p-4">
            <label className="mb-1 block text-xs font-medium text-gray-600">Modello standard</label>
            <select value={modello} onChange={(e) => applicaModello(e.target.value)}
              className="w-full rounded-md border border-gray-300 bg-white px-2.5 py-1.5 text-sm">
              <option value="">Libero</option>
              {schema.modelli.map((m) => <option key={m.id} value={m.id}>{m.nome}</option>)}
            </select>
          </div>
          <nav className="flex overflow-x-auto border-b border-gray-100 px-2">
            {schema.gruppi.map((g, i) => (
              <button key={g.id} onClick={() => setTab(g.id)}
                className={`whitespace-nowrap border-b-2 px-3 py-2.5 text-sm ${tab === g.id ? 'border-verde-600 font-semibold text-verde-700' : 'border-transparent text-gray-600 hover:text-gray-900'}`}>
                {i + 1}. {g.titolo}
              </button>
            ))}
          </nav>
          <div className="grid gap-3 p-4 sm:grid-cols-2">
            {gruppo.campi.map((c) => (
              <div key={c.key} className={c.tipo === 'si_no' || c.tipo === 'porte' || c.tipo === 'frontali' ? 'sm:col-span-2' : ''}>
                {c.tipo === 'frontali' ? (
                  <>
                    <EditorFrontali righe={Array.isArray(valori[c.key]) ? (valori[c.key] as FrontaleRiga[]) : []}
                      frontali={c.frontali ?? []} opzioni={(c.opzioni ?? []).map(Number)} campate={Number(valori.campate) || 1}
                      onChange={(r) => set(c.key, r)} />
                    {c.aiuto && <p className="mt-1 text-xs text-gray-500">{c.aiuto}</p>}
                  </>
                ) : c.tipo === 'porte' ? (
                  <>
                    <EditorPorte porte={Array.isArray(valori[c.key]) ? (valori[c.key] as Porta[]) : (c.default as Porta[])}
                      posizioni={c.posizioni ?? []} campate={Number(valori.campate) || 1} lunghezza={Number(valori.lunghezza) || 0}
                      onChange={(p) => set(c.key, p)} />
                    {c.aiuto && <p className="mt-1 text-xs text-gray-500">{c.aiuto}</p>}
                  </>
                ) : (
                  <CampoInput campo={c} valore={valori[c.key] ?? c.default} onChange={(v) => set(c.key, v)} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* colonna risultato */}
        <div className="space-y-4">
          <div className="relative overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            {ant.data ? (
              <img src={ant.data} alt="Anteprima tavola A3" className="aspect-[420/297] w-full bg-white" />
            ) : (
              <div className="flex aspect-[420/297] items-center justify-center text-sm text-gray-500">
                {ant.isError ? 'Anteprima non disponibile con questi dati' : 'Preparo l’anteprima…'}
              </div>
            )}
            {ant.isFetching && ant.data && (
              <span className="absolute right-2 top-2 rounded bg-white/90 px-2 py-0.5 text-xs text-gray-600 shadow">aggiorno…</span>
            )}
          </div>

          {calc.isError && <p className="rounded-md bg-red-50 p-3 text-sm text-red-800">{calc.error.message}</p>}
          {r && (
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <p className="font-semibold">{r.titolo}</p>
              <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-5">
                <div><dt className="text-gray-500">Superficie</dt><dd className="font-medium tabular-nums">{num(r.area_m2)} m²</dd></div>
                <div><dt className="text-gray-500">Archi per campata</dt><dd className="font-medium tabular-nums">{r.archi_per_campata}</dd></div>
                <div><dt className="text-gray-500">H colmo</dt><dd className="font-medium tabular-nums">{num(r.h_colmo, 2)} m</dd></div>
                <div><dt className="text-gray-500">ml tendina</dt><dd className="font-medium tabular-nums">{num(r.ml_aperture.tendina)}</dd></div>
                <div><dt className="text-gray-500">Monconi per capriata</dt><dd className="font-medium tabular-nums">{r.monconi}</dd></div>
              </dl>
              <p className="mt-3 rounded-md bg-gray-50 p-2.5 text-xs text-gray-600">
                Peso, prezzo e €/m² vengono calcolati alla generazione con il master Excel 2026.
                Prossimo passo: motore prezzi in Python con margini, per averli qui in tempo reale.
              </p>

              {r.avvisi.length > 0 && (
                <ul className="mt-3 space-y-1.5">
                  {r.avvisi.map((a, i) => (
                    <li key={i} className={`rounded-md px-3 py-2 text-sm ${a.livello === 'attenzione' ? 'bg-amber-50 text-amber-900' : 'bg-sky-50 text-sky-900'}`}>
                      {a.livello === 'attenzione' ? '⚠ ' : 'ℹ '}{a.testo}
                    </li>
                  ))}
                </ul>
              )}

              <details className="mt-3">
                <summary className="cursor-pointer text-sm font-medium text-verde-700">Quantità inserite dalle regole ({r.quantita.length})</summary>
                <table className="mt-2 w-full text-sm">
                  <tbody>
                    {r.quantita.map((q) => (
                      <tr key={q.voce} className="border-t border-gray-100">
                        <td className="py-1.5 pr-2">{q.voce}</td>
                        <td className="py-1.5 pr-2 text-right font-medium tabular-nums">{q.qta}</td>
                        <td className="py-1.5 text-xs text-gray-500">{q.regola} · <span className={q.affidabilita.startsWith('bassa') ? 'text-red-700' : ''}>{q.affidabilita}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Maschera() {
  const { famiglia = '' } = useParams()
  const [sp] = useSearchParams()
  const conCalcolo = sp.get('calcolo') === '1'
  const da = sp.get('da') ?? undefined
  const schema = useQuery({ queryKey: ['schema', famiglia], queryFn: () => api.schema(famiglia) })
  const origine = useQuery({ queryKey: ['preventivo', da], queryFn: () => api.preventivo(da!), enabled: !!da })

  const iniziali = useMemo(
    () => (schema.data ? { ...defaults(schema.data), ...(origine.data?.configurazione ?? {}) } : null),
    [schema.data, origine.data],
  )

  if (schema.isError) return <p className="text-red-700">Famiglia non disponibile: {schema.error.message}</p>
  if (!schema.data || !iniziali || (da && !origine.data)) return <p className="text-gray-500">Carico…</p>
  return <Form key={`${famiglia}-${da}`} schema={schema.data} iniziali={iniziali} conCalcolo={conCalcolo} origineId={da} />
}
