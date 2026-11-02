# Configuratore Terranova — prima versione locale

Implementa la prima parte del PRD (`../PRD_configuratore_serre.md`).

## Come si usa

- **Uso normale:** doppio clic su `avvia.bat`. Il browser si apre su http://127.0.0.1:8000.
- **Dopo modifiche al frontend:** `compila_frontend.bat`.

## Cosa fa

| Pagina | Funzioni |
|---|---|
| **Home** | Tessere delle famiglie. *Serre ad arco* attiva con **Senza calcolo** / **Con calcolo strutturale**; le altre (capannoni, lavori speciali, tunnel…) sono visibili come "in arrivo". Sotto, gli ultimi preventivi con ricerca. |
| **Maschera Serre** | Modello standard o libero, 4 schede (Cliente, Struttura, Aperture, Fondazioni). A destra: **anteprima della tavola A3** (è lo stesso disegno del DWG), superficie, archi, H colmo, avvisi (larghezza fuori standard, lunghezza non multipla del passo, calcolo strutturale), quantità con regola e affidabilità. |
| **Genera** | Mette il lavoro in coda (uno alla volta): Excel compila il master 2026 ed ezdxf crea il disegno, che AutoCAD converte in DWG e PDF. I file vanno in `../04_preventivi/AAAAMMGG_Cliente_misure/` come prima. Circa 35 s. |
| **Dettaglio preventivo** | Totale, €/m², peso, link ai file, apri cartella, cambio stato (bozza / da verificare / inviato / accettato / perso), **Duplica e modifica** (crea la versione v2, v3…). |

"Con calcolo" → il preventivo nasce in stato **da verificare** e il Riepilogo porta la dicitura *PRELIMINARE — SOGGETTO A CALCOLO STRUTTURALE*.

### Prezzi e margini (prototipo fase 1)

| Pagina | Funzioni |
|---|---|
| **Prezzo e margini** (nel dettaglio preventivo) | Costi veri per voce, letti dal master 2026 (colonna X €/kg e foglio Pezzi Speciali). Margine per categoria, montaggio €/m², trasporto a viaggio, progettazione, sconto. Prezzo, margine reale, ricarico ed €/m² ricalcolati subito. Semaforo verde/giallo/rosso. Sotto la soglia minima o oltre lo sconto massimo serve il nome di chi approva. |
| **Offerta PDF** | PDF per il cliente con prezzi per categoria, senza costi né margini, con condizioni e filigrana "PRELIMINARE" se con calcolo. Creato con PyMuPDF, senza altri programmi. |
| **Lavori speciali** | Preventivo a voci libere: si scrive la voce o la si sceglie dal listino. Stessi margini e stessa offerta. |
| **Listino** | 41 voci di costo dal master 2026, modificabili. Quelle "da confermare" sono da verificare. |
| **Impostazioni** | Margini di default, soglie, sconto massimo, montaggio, trasporto, condizioni. Sono **valori di partenza da confermare**: struttura 37,5% = attuale ricarico ×1,6. |
| **Roadmap** | Come proseguiamo, fase per fase. |

⚠️ **Anomalia trovata nel master 2026:** nel totale i pezzi speciali entrano con un valore fisso (€ 676) invece della somma del foglio Pezzi Speciali (es. € 1.876,60 per una 3×9×50), e senza ricarico. Il prezzo calcolato dall'app usa il valore vero con il margine.

## Struttura

```
05_app/
├── avvia.bat, compila_frontend.bat
├── backend/                 FastAPI (Python)
│   ├── app/main.py          API + coda generazione + serve il frontend compilato
│   ├── app/db.py            accesso dati (SQLite ora, Supabase dopo: cambia solo questo file)
│   ├── app/schema.sql       tabella preventivi, compatibile Postgres
│   ├── app/famiglie/        una famiglia = un modulo (serre.py) + una riga in __init__.py
│   └── motore/              copia del prototipo 03_pilota/app (regole, disegno, genera, compila.vbs)
└── frontend/                React 18 + Vite + TypeScript + Tailwind + TanStack Query
    └── src/pages/           Home, Maschera, DettaglioPreventivo
```

## Sviluppo

```bat
:: terminale 1 - backend con ricarica automatica
cd backend
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

:: terminale 2 - frontend con ricarica a caldo (http://localhost:5173, /api inoltrato al backend)
cd frontend
npm run dev
```

## Limiti noti di questa versione

- **I costi delle serre arrivano solo dopo "Genera"**, perché le quantità e i €/kg li calcola ancora il master Excel. Dopo, margini e prezzo si ricalcolano all'istante. Prossimo passo: formule del master in Python, per avere il prezzo già nella maschera.
- Le serre usano i €/kg scritti nel master; il Listino oggi serve ai lavori speciali.
- L'anteprima impiega circa 5 secondi: parte 1,2 s dopo l'ultima modifica.
- Servono Excel e AutoCAD 2024 sul PC che esegue il server. Senza AutoCAD si ottengono solo Excel, DXF e Riepilogo.
- Nessun login: va bene in locale, ma va aggiunto prima di aprirlo alla rete o di passare a Supabase.
- "Apri cartella" apre Esplora risorse sul PC che esegue il server.

## Passaggio a Supabase (piano)

| Oggi (locale) | Su Supabase |
|---|---|
| SQLite `dati.sqlite` | Postgres: `schema.sql` con uuid / boolean / jsonb / timestamptz (vedi commenti nel file) |
| Nessun login | Supabase Auth (email aziendali) + ruoli (commerciale / tecnico / direzione) con Row Level Security |
| File in `04_preventivi` sul disco | Supabase Storage (bucket privato), con copia sul NAS per l'ufficio |
| `db.py` con sqlite3 | `db.py` con psycopg / supabase-py: le API e il frontend non cambiano |

⚠️ **Supabase non può eseguire la parte Python** (ezdxf, Excel, AutoCAD): ospita solo database, login e file. Il backend FastAPI resta su un PC o server dell'ufficio finché il motore dipende da Excel e AutoCAD. Quando il motore sarà tutto in Python (calcolo + ODA Converter + PDF con PyMuPDF), potrà girare anche su un servizio cloud.

Costi Supabase, da verificare sul sito al momento della scelta: il piano Free mette in pausa i progetti inattivi e ha limiti di spazio; il piano Pro costa circa 25 $/mese per progetto. Gli allegati DWG/PDF occupano spazio in Storage, quindi conviene tenere su Supabase solo gli ultimi e l'archivio storico sul NAS.
