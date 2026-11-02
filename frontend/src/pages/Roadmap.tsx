type St = 'fatto' | 'prototipo' | 'prossimo' | 'dopo'

const STILE: Record<St, [string, string]> = {
  fatto: ['Fatto', 'bg-green-100 text-green-800'],
  prototipo: ['Prototipo', 'bg-sky-100 text-sky-800'],
  prossimo: ['Prossimo', 'bg-amber-100 text-amber-900'],
  dopo: ['Dopo', 'bg-gray-100 text-gray-600'],
}

const FASI: { titolo: string; obiettivo: string; voci: [St, string][] }[] = [
  {
    titolo: 'Fase 0 — Analisi e prototipo', obiettivo: 'Capire 15 anni di archivio e dimostrare che si può automatizzare',
    voci: [
      ['fatto', 'Catalogo 4.506 computi + 3.280 DWG, varianti e combinazioni standard'],
      ['fatto', 'Regole quantità da 333 computi 2024-2026 (con affidabilità)'],
      ['fatto', 'Disegno A3 automatico sul cartiglio Terranova (DXF → DWG → PDF)'],
      ['fatto', 'App React + Vite: home a tessere, maschera Serre con anteprima, archivio preventivi'],
    ],
  },
  {
    titolo: 'Fase 1 — Prezzi e margini', obiettivo: 'Ogni preventivo con costo vero, margine controllato e offerta PDF',
    voci: [
      ['prototipo', 'Costi per voce letti dal master 2026 (€/kg struttura, pezzi speciali)'],
      ['prototipo', 'Margini per categoria, sconto, semaforo, soglia minima con approvazione'],
      ['prototipo', 'Offerta PDF al cliente (senza costi e margini), filigrana "preliminare" se con calcolo'],
      ['prototipo', 'Lavori speciali a voci libere dal listino'],
      ['prototipo', 'Listino costi e impostazioni modificabili'],
      ['prossimo', 'Decidere con la direzione: margini, soglie, montaggio €/m², trasporto, pagamenti'],
      ['prossimo', 'Correggere i pezzi speciali del master (oggi entrano nel totale con un valore fisso, senza ricarico)'],
    ],
  },
  {
    titolo: 'Fase 2 — Motore in Python (via Excel)', obiettivo: 'Prezzo istantaneo nella maschera, niente Excel sul server',
    voci: [
      ['prossimo', 'Portare le formule del master 2026 in Python, voce per voce'],
      ['prossimo', 'Test su 30+ commesse reali: scostamento kg e € entro ±3%'],
      ['prossimo', 'Prezzo e margine in tempo reale mentre si compila la maschera'],
      ['dopo', 'Listino unico usato da serre e speciali, prezzi con data di validità'],
    ],
  },
  {
    titolo: 'Fase 3 — Documenti senza AutoCAD', obiettivo: 'Generazione in < 15 s, nessuna licenza dedicata',
    voci: [
      ['dopo', 'DXF → DWG con ODA File Converter (AutoCAD solo di riserva)'],
      ['dopo', 'PDF del disegno con PyMuPDF'],
      ['dopo', 'Computo in .xlsx con openpyxl, stesso layout del computo analitico'],
    ],
  },
  {
    titolo: 'Fase 4 — Multiutente e Supabase', obiettivo: "Tutto l'ufficio, con ruoli",
    voci: [
      ['dopo', 'Login (Supabase Auth): commerciale, tecnico, direzione — costi visibili solo a chi può'],
      ['dopo', 'Database su Supabase Postgres (cambia solo db.py) e file su Storage + copia NAS'],
      ['dopo', 'Backend Python su PC/server ufficio finché serve Excel/AutoCAD, poi anche in cloud'],
    ],
  },
  {
    titolo: 'Fase 5 — Nuove famiglie', obiettivo: 'Coprire il resto dell’archivio',
    voci: [
      ['dopo', 'Tunnel e avanserre (stesso motore delle serre)'],
      ['dopo', 'Capannoni e tettoie IPE/HEA (analisi dei 588 computi IND)'],
      ['dopo', 'Ombrai, fotovoltaico, bancali/vasche'],
      ['dopo', 'AI opzionale: leggere la richiesta del cliente (email) e precompilare la maschera'],
    ],
  },
]

export default function Roadmap() {
  return (
    <div className="max-w-4xl space-y-4">
      <h1 className="text-xl font-semibold">Come proseguiamo</h1>
      <p className="text-sm text-gray-600">Ordine pensato per avere prima i <b>prezzi giusti</b>, poi la velocità, poi l'uso da parte di tutto l'ufficio.</p>
      <ol className="space-y-3">
        {FASI.map((f) => (
          <li key={f.titolo} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <h2 className="font-semibold">{f.titolo}</h2>
            <p className="mb-2 text-sm text-gray-600">{f.obiettivo}</p>
            <ul className="space-y-1.5">
              {f.voci.map(([s, t]) => (
                <li key={t} className="flex items-start gap-2 text-sm">
                  <span className={`mt-0.5 w-20 shrink-0 rounded-full px-2 py-0.5 text-center text-xs font-medium ${STILE[s][1]}`}>{STILE[s][0]}</span>
                  {t}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </div>
  )
}
