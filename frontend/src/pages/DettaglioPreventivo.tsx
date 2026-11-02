import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api, data, eur, num, pct, type Stato } from '../api'
import BadgeStato, { STATI_MANUALI, etichettaStato } from '../components/Stato'
import PannelloPrezzo from '../components/PannelloPrezzo'

const IN_CORSO: Stato[] = ['in_coda', 'in_lavorazione']

const tipoFile = (n: string) => {
  const e = n.split('.').pop()?.toLowerCase()
  return e === 'pdf' ? 'PDF' : e === 'dwg' ? 'DWG' : e === 'dxf' ? 'DXF' : e === 'xls' || e === 'xlsx' ? 'Excel' : e === 'txt' ? 'Testo' : e?.toUpperCase()
}

export default function DettaglioPreventivo() {
  const { id = '' } = useParams()
  const qc = useQueryClient()
  const q = useQuery({
    queryKey: ['preventivo', id],
    queryFn: () => api.preventivo(id),
    refetchInterval: (query) => (query.state.data && IN_CORSO.includes(query.state.data.stato) ? 2000 : false),
  })
  const stato = useMutation({
    mutationFn: (s: Stato) => api.cambiaStato(id, s),
    onSuccess: (p) => { qc.setQueryData(['preventivo', id], p); qc.invalidateQueries({ queryKey: ['preventivi'] }) },
  })
  const cartella = useMutation({ mutationFn: () => api.apriCartella(id) })

  if (q.isError) return <p className="text-red-700">{q.error.message}</p>
  const p = q.data
  if (!p) return <p className="text-gray-500">Carico…</p>
  const inCorso = IN_CORSO.includes(p.stato)

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/" className="text-sm text-gray-600 hover:underline">← Home</Link>
        <h1 className="text-xl font-semibold">{p.cliente || 'Senza nome'}</h1>
        <BadgeStato stato={p.stato} />
        {p.con_calcolo && <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">Preliminare: soggetto a calcolo</span>}
        <span className="text-sm text-gray-500">N. {p.numero} · v{p.versione} · {data(p.creato_il)}</span>
        {p.famiglia === 'speciali' ? (
          <Link to={`/speciali/${p.id}`}
            className="ml-auto rounded-md border border-verde-600 px-3 py-1.5 text-sm font-medium text-verde-700 hover:bg-verde-50">
            Modifica voci
          </Link>
        ) : (
          <Link to={`/configura/${p.famiglia}?${p.con_calcolo ? 'calcolo=1&' : ''}da=${p.id}`}
            className="ml-auto rounded-md border border-verde-600 px-3 py-1.5 text-sm font-medium text-verde-700 hover:bg-verde-50">
            Duplica e modifica
          </Link>
        )}
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <p className="font-semibold">{p.titolo}</p>
        <p className="text-sm text-gray-600">{p.localita}</p>
        {p.descrizione && <p className="mt-1 whitespace-pre-line text-sm text-gray-700">{p.descrizione}</p>}

        {inCorso ? (
          <div className="mt-4 flex items-center gap-3 rounded-md bg-blue-50 p-4 text-sm text-blue-900">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-blue-300 border-t-blue-700" />
            {p.stato === 'in_coda' ? 'In coda…' : 'Excel compila il computo e AutoCAD crea DWG e PDF (circa 30 secondi)…'}
          </div>
        ) : p.stato === 'errore' ? (
          <pre className="mt-4 max-h-72 overflow-auto rounded-md bg-red-50 p-3 text-xs text-red-900">{p.errore}</pre>
        ) : (
          <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div><dt className="text-sm text-gray-500">Prezzo cliente</dt><dd className="text-2xl font-semibold tabular-nums">{eur(p.prezzo_finale ?? p.totale_eur)}</dd></div>
            <div><dt className="text-sm text-gray-500">Margine</dt><dd className="text-2xl font-semibold tabular-nums">{pct(p.margine_reale)}</dd></div>
            {p.famiglia !== 'speciali' && <>
              <div><dt className="text-sm text-gray-500">Peso struttura</dt><dd className="text-2xl font-semibold tabular-nums">{num(p.peso_kg)} kg</dd></div>
              <div><dt className="text-sm text-gray-500">Superficie</dt><dd className="text-2xl font-semibold tabular-nums">{num(p.area_m2)} m²</dd></div>
            </>}
          </dl>
        )}
      </div>

      {!inCorso && p.stato !== 'errore' && (p.costi?.length ? <PannelloPrezzo p={p} /> : p.famiglia !== 'speciali' && (
        <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-900">
          Questo preventivo è stato creato prima del motore prezzi: usa "Duplica e modifica" e rigenera per avere costi e margini.
        </p>
      ))}

      {!inCorso && p.file && p.file.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="mb-3 flex items-center">
            <h2 className="font-semibold">Documenti</h2>
            <button onClick={() => cartella.mutate()} className="ml-auto text-sm text-verde-700 hover:underline">Apri cartella</button>
          </div>
          <ul className="divide-y divide-gray-100">
            {p.file.map((f) => (
              <li key={f} className="flex items-center gap-3 py-2 text-sm">
                <span className="w-12 rounded bg-gray-100 px-1.5 py-0.5 text-center text-xs font-medium text-gray-700">{tipoFile(f)}</span>
                <a href={api.urlFile(p.id, f)} target="_blank" rel="noreferrer" className="text-verde-700 hover:underline">{f}</a>
              </li>
            ))}
          </ul>
          <p className="mt-2 truncate text-xs text-gray-500" title={p.cartella ?? ''}>{p.cartella}</p>
        </div>
      )}

      {!inCorso && p.stato !== 'errore' && (
        <div className="flex flex-wrap items-center gap-2 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <span className="mr-2 text-sm text-gray-600">Cambia stato:</span>
          {STATI_MANUALI.map((s) => (
            <button key={s} disabled={s === p.stato || stato.isPending} onClick={() => stato.mutate(s)}
              className={`rounded-md border px-3 py-1 text-sm ${s === p.stato ? 'border-verde-600 bg-verde-50 font-medium text-verde-800' : 'border-gray-300 hover:bg-gray-50'}`}>
              {etichettaStato(s)}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
