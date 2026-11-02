-- Schema dati del configuratore.
-- Scritto per SQLite (locale) ma compatibile con Postgres/Supabase:
--   TEXT id (uuid)        -> uuid primary key default gen_random_uuid()
--   INTEGER (0/1)         -> boolean
--   TEXT con JSON         -> jsonb
--   TEXT data ISO         -> timestamptz default now()

CREATE TABLE IF NOT EXISTS preventivi (
    id             TEXT PRIMARY KEY,
    creato_il      TEXT NOT NULL,
    aggiornato_il  TEXT NOT NULL,
    numero         TEXT,                          -- es. 2026/0001
    famiglia       TEXT NOT NULL,                 -- serre, capannoni, speciali...
    con_calcolo    INTEGER NOT NULL DEFAULT 0,    -- 1 = con calcolo strutturale
    cliente        TEXT,
    localita       TEXT,
    titolo         TEXT,
    descrizione    TEXT,                          -- descrizione libera (lavori speciali)
    configurazione TEXT NOT NULL,                 -- JSON con tutti i valori della maschera
    stato          TEXT NOT NULL,                 -- in_coda, in_lavorazione, bozza, da_verificare, inviato, accettato, perso, errore
    versione       INTEGER NOT NULL DEFAULT 1,
    origine_id     TEXT,                          -- preventivo da cui è stato duplicato
    area_m2        REAL,
    peso_kg        REAL,
    totale_eur     REAL,                          -- totale calcolato dal master Excel (riferimento)
    eur_m2         REAL,
    costi          TEXT,                          -- JSON: righe di costo [{categoria, voce, qta, unita, costo}]
    prezzi         TEXT,                          -- JSON: margini, extra, sconto, risultato
    prezzo_finale  REAL,                          -- prezzo al cliente calcolato con i margini
    margine_reale  REAL,
    cartella       TEXT,
    file           TEXT,                          -- JSON: elenco nomi file generati
    errore         TEXT
);

CREATE INDEX IF NOT EXISTS ix_preventivi_creato ON preventivi (creato_il);
CREATE INDEX IF NOT EXISTS ix_preventivi_cliente ON preventivi (cliente);

CREATE TABLE IF NOT EXISTS impostazioni (
    chiave TEXT PRIMARY KEY,
    valore TEXT NOT NULL                          -- JSON
);

CREATE TABLE IF NOT EXISTS listino (
    id            TEXT PRIMARY KEY,
    categoria     TEXT NOT NULL,                  -- struttura, pezzi_speciali, montaggio, trasporto, progettazione, altro
    voce          TEXT NOT NULL,
    unita         TEXT NOT NULL,                  -- kg, cad, m², viaggio, corpo...
    costo         REAL NOT NULL,                  -- costo unitario (non prezzo di vendita)
    fonte         TEXT,
    da_confermare INTEGER NOT NULL DEFAULT 0,
    aggiornato_il TEXT NOT NULL
);
