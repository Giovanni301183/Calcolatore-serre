import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { api, data, eur, type Tessera } from '../api'
import Icona from '../components/Icone'
import BadgeStato from '../components/Stato'

function TesseraFamiglia({ t }: { t: Tessera }) {
  const nav = useNavigate()
  const vai = (calcolo: boolean) => nav(t.percorso ?? `/configura/${t.id}${calcolo ? '?calcolo=1' : ''}`)
  return (
    <div className={`flex flex-col rounded-xl border bg-white p-5 shadow-sm ${t.attiva ? 'border-gray-200' : 'border-dashed border-gray-300 opacity-60'}`}>
      <div className="flex items-start gap-3">
        <span className={`rounded-lg p-2 ${t.attiva ? 'bg-verde-50 text-verde-700' : 'bg-gray-100 text-gray-500'}`}>
          <Icona nome={t.icona} />
        </span>
        <div className="min-w-0">
          <h2 className="font-semibold uppercase tracking-wide">{t.nome}</h2>
          <p className="text-sm text-gray-600">{t.descrizione}</p>
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        {!t.attiva ? (
          <span className="rounded-md bg-gray-100 px-3 py-1.5 text-sm text-gray-600">{t.nota ?? 'In arrivo'}</span>
        ) : t.calcolo ? (
          <>
            <button onClick={() => vai(false)} className="rounded-md bg-verde-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-verde-700">
              Senza calcolo
            </button>
            <button onClick={() => vai(true)} className="rounded-md border border-verde-600 px-3 py-1.5 text-sm font-medium text-verde-700 hover:bg-verde-50">
              Con calcolo strutturale
            </button>
          </>
        ) : (
          <button onClick={() => vai(false)} className="rounded-md bg-verde-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-verde-700">
            Nuovo
          </button>
        )}
      </div>
    </div>
  )
}

export default function Home() {
  const [q, setQ] = useState('')
  const famiglie = useQuery({ queryKey: ['famiglie'], queryFn: api.famiglie })
  const prev = useQuery({ queryKey: ['preventivi', q], queryFn: () => api.preventivi(q) })

  return (
    <div className="space-y-8">
      <section>
        <h1 className="mb-4 text-xl font-semibold">Nuovo preventivo</h1>
        {famiglie.isError && <p className="text-red-700">Backend non raggiungibile: avvia il server (avvia.bat).</p>}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {famiglie.data?.map((t) => <TesseraFamiglia key={t.id} t={t} />)}
        </div>
      </section>

      <section>
        <div className="mb-3 flex flex-wrap items-center gap-3">
          <h2 className="text-lg font-semibold">Ultimi preventivi</h2>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Cerca cliente, località, misure…"
            className="ml-auto w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm sm:w-72"
          />
        </div>
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-600">
              <tr>
                <th className="px-4 py-2 font-medium">Data</th>
                <th className="px-4 py-2 font-medium">Cliente</th>
                <th className="px-4 py-2 font-medium">Descrizione</th>
                <th className="px-4 py-2 text-right font-medium">Totale</th>
                <th className="px-4 py-2 font-medium">Stato</th>
              </tr>
            </thead>
            <tbody>
              {prev.data?.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-500">Nessun preventivo ancora.</td></tr>
              )}
              {prev.data?.map((p) => (
                <tr key={p.id} className="border-t border-gray-100 hover:bg-verde-50/50">
                  <td className="px-4 py-2 whitespace-nowrap text-gray-600">{data(p.creato_il)}</td>
                  <td className="px-4 py-2"><Link to={`/preventivi/${p.id}`} className="font-medium text-verde-700 hover:underline">{p.cliente || 'senza nome'}</Link></td>
                  <td className="px-4 py-2 text-gray-700">
                    {p.titolo}
                    {p.con_calcolo && <span className="ml-2 rounded bg-amber-50 px-1.5 text-xs text-amber-700">con calcolo</span>}
                    {p.versione > 1 && <span className="ml-2 text-xs text-gray-500">v{p.versione}</span>}
                  </td>
                  <td className="px-4 py-2 text-right whitespace-nowrap tabular-nums">{eur(p.prezzo_finale ?? p.totale_eur)}</td>
                  <td className="px-4 py-2"><BadgeStato stato={p.stato} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
