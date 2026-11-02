// Tipi e chiamate verso il backend FastAPI (/api, in sviluppo passa dal proxy di Vite)

export interface Porta {
  posizione: string
  campata: number
  distanza: number
  larghezza: number
  altezza: number
}

export interface FrontaleRiga {
  frontale: string
  campata: number
  montanti: number
  interasse: number
}

export type Valore = string | number | boolean | Porta[] | FrontaleRiga[]
export type Valori = Record<string, Valore>

export interface Tessera {
  id: string
  nome: string
  descrizione: string
  icona: string
  attiva: boolean
  calcolo: boolean
  nota?: string
  percorso?: string
}

export interface Campo {
  key: string
  label: string
  tipo: 'testo' | 'numero' | 'scelta' | 'si_no' | 'porte' | 'frontali'
  posizioni?: string[]
  frontali?: string[]
  default: Valore
  unita?: string
  min?: number
  max?: number
  step?: number
  opzioni?: Valore[]
  suggeriti?: number[]
  aiuto?: string
}

export interface Gruppo {
  id: string
  titolo: string
  campi: Campo[]
}

export interface Schema {
  id: string
  nome: string
  gruppi: Gruppo[]
  modelli: { id: string; nome: string; valori: Valori }[]
  default_interramento: Record<string, number>
}

export interface Avviso {
  livello: 'info' | 'attenzione'
  testo: string
}

export interface Risultato {
  titolo: string
  area_m2: number
  larghezza_totale: number
  archi_per_campata: number
  monconi: number
  h_colmo: number
  ml_aperture: { tendina: number; ghigliottina: number; fungo: number }
  quantita: { voce: string; qta: number; regola: string; affidabilita: string }[]
  avvisi: Avviso[]
}

export type Stato =
  | 'in_coda' | 'in_lavorazione' | 'bozza' | 'da_verificare' | 'inviato' | 'accettato' | 'perso' | 'errore'

export interface Preventivo {
  id: string
  creato_il: string
  aggiornato_il: string
  famiglia: string
  con_calcolo: boolean
  cliente: string
  localita: string
  titolo: string
  configurazione: Valori
  stato: Stato
  versione: number
  area_m2: number | null
  peso_kg: number | null
  totale_eur: number | null
  eur_m2: number | null
  cartella: string | null
  file: string[] | null
  errore: string | null
  numero: string | null
  descrizione: string | null
  costi: RigaCosto[] | null
  prezzi: { scelte: Scelte; risultato: RisultatoPrezzo; note_master?: string[]; approvato_da?: string | null } | null
  prezzo_finale: number | null
  margine_reale: number | null
}

export interface RigaCosto {
  categoria: string
  voce: string
  qta?: number
  unita?: string
  costo_unitario?: number
  costo: number
  listino_id?: string
}

export interface Scelte {
  margini?: Record<string, number>
  montaggio_eur_m2?: number
  trasporto_eur_viaggio?: number
  viaggi?: number | ''
  progettazione_eur?: number
  sconto_pct?: number
}

export interface RisultatoPrezzo {
  righe: RigaCosto[]
  categorie: { id: string; nome: string; costo: number; margine: number; prezzo: number; ricarico: number }[]
  costo_totale: number
  prezzo_listino: number
  sconto_pct: number
  sconto: number
  prezzo_finale: number
  margine_reale: number
  ricarico_equivalente: number
  eur_m2: number | null
  semaforo: 'verde' | 'giallo' | 'rosso'
  richiede_approvazione: boolean
  riferimento_master: number | null
  avvisi: string[]
}

export interface Categoria { id: string; nome: string; descrizione: string }

export interface Impostazioni {
  margini: Record<string, number>
  margine_minimo: number
  margine_attenzione: number
  sconto_max_commerciale: number
  montaggio_eur_m2: number
  trasporto_eur_viaggio: number
  kg_per_viaggio: number
  progettazione_eur: number
  validita_giorni: number
  condizioni_pagamento: string
  da_confermare: boolean
}

export interface VoceListino {
  id: string
  categoria: string
  voce: string
  unita: string
  costo: number
  fonte: string
  da_confermare: number
  aggiornato_il: string
}

export interface Speciale {
  cliente: string
  localita: string
  titolo: string
  descrizione: string
  righe: RigaCosto[]
  origine_id?: string
}

async function richiesta<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!r.ok) {
    let msg = `${r.status}`
    try { msg = (await r.json()).detail ?? msg } catch { /* risposta non JSON */ }
    throw new Error(msg)
  }
  return r.json()
}

const post = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) })

export const api = {
  famiglie: () => richiesta<Tessera[]>('/api/famiglie'),
  schema: (fam: string) => richiesta<Schema>(`/api/famiglie/${fam}/schema`),
  calcola: (fam: string, valori: Valori, con_calcolo: boolean) =>
    richiesta<Risultato>(`/api/famiglie/${fam}/calcola`, post({ valori, con_calcolo })),
  anteprima: async (fam: string, valori: Valori) => {
    const r = await fetch(`/api/famiglie/${fam}/anteprima`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ valori }),
    })
    if (!r.ok) throw new Error(`${r.status}`)
    return URL.createObjectURL(await r.blob())
  },
  nuovoPreventivo: (fam: string, valori: Valori, con_calcolo: boolean, origine_id?: string) =>
    richiesta<Preventivo>(`/api/famiglie/${fam}/preventivi`, post({ valori, con_calcolo, origine_id })),
  preventivi: (q = '') => richiesta<Preventivo[]>(`/api/preventivi?q=${encodeURIComponent(q)}`),
  preventivo: (id: string) => richiesta<Preventivo>(`/api/preventivi/${id}`),
  cambiaStato: (id: string, stato: Stato) =>
    richiesta<Preventivo>(`/api/preventivi/${id}`, { method: 'PATCH', body: JSON.stringify({ stato }) }),
  apriCartella: (id: string) => richiesta<{ ok: boolean }>(`/api/preventivi/${id}/apri-cartella`, { method: 'POST' }),
  prezzo: (id: string, scelte: Scelte, salva = false) =>
    richiesta<RisultatoPrezzo>(`/api/preventivi/${id}/prezzo`, post({ scelte, salva })),
  offerta: (id: string, approvato_da = '') => richiesta<Preventivo>(`/api/preventivi/${id}/offerta`, post({ approvato_da })),
  impostazioni: () => richiesta<{ valori: Impostazioni; categorie: Categoria[] }>('/api/impostazioni'),
  salvaImpostazioni: (v: Partial<Impostazioni>) =>
    richiesta<{ valori: Impostazioni; categorie: Categoria[] }>('/api/impostazioni', { method: 'PUT', body: JSON.stringify(v) }),
  listino: () => richiesta<VoceListino[]>('/api/listino'),
  modificaListino: (id: string, costo: number) =>
    richiesta<VoceListino>(`/api/listino/${id}`, { method: 'PATCH', body: JSON.stringify({ costo }) }),
  nuovoSpeciale: (s: Speciale) => richiesta<Preventivo>('/api/speciali/preventivi', post(s)),
  aggiornaSpeciale: (id: string, s: Speciale) =>
    richiesta<Preventivo>(`/api/speciali/preventivi/${id}`, { method: 'PUT', body: JSON.stringify(s) }),
  urlFile: (id: string, nome: string) => `/api/preventivi/${id}/file/${encodeURIComponent(nome)}`,
}

// formattazione all'italiana
export const eur = (v: number | null | undefined) =>
  v == null ? '—' : v.toLocaleString('it-IT', { style: 'currency', currency: 'EUR' })
export const num = (v: number | null | undefined, dec = 0) =>
  v == null ? '—' : v.toLocaleString('it-IT', { minimumFractionDigits: dec, maximumFractionDigits: dec })
export const pct = (v: number | null | undefined) => (v == null ? '—' : `${num(v, 1)}%`)
export const data = (iso: string) =>
  new Date(iso).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: '2-digit' })
