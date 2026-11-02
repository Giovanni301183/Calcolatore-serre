"""API del configuratore. Avvio: avvia.bat (oppure: uvicorn app.main:app --port 8000 dalla cartella backend)."""
import datetime, os, re, sys, traceback
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "motore"))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import regole
from . import db, prezzi, offerta
from .famiglie import MODULI, TESSERE

app = FastAPI(title="Configuratore Terranova")
db.init()
if db.listino_vuoto() and os.path.exists(regole.MASTER):
    db.inserisci_listino(prezzi.listino_da_master(regole.MASTER))
# Excel e AutoCAD non reggono lavori in parallelo: una generazione alla volta
CODA = ThreadPoolExecutor(max_workers=1)
USCITA = os.path.join(regole.BASE, "04_preventivi")

STATI_MANUALI = {"bozza", "da_verificare", "inviato", "accettato", "perso"}


class Richiesta(BaseModel):
    valori: dict = {}
    con_calcolo: bool = False


class NuovoPreventivo(Richiesta):
    origine_id: str | None = None


class CambioStato(BaseModel):
    stato: str


class Prezzo(BaseModel):
    scelte: dict = {}
    salva: bool = False


class Offerta(BaseModel):
    approvato_da: str = ""


class Speciale(BaseModel):
    cliente: str = ""
    localita: str = ""
    titolo: str = ""
    descrizione: str = ""
    righe: list[dict] = []
    origine_id: str | None = None


class VoceListino(BaseModel):
    costo: float


def _modulo(fam):
    if fam not in MODULI:
        raise HTTPException(404, f"Famiglia '{fam}' non disponibile")
    return MODULI[fam]


def _imp():
    return prezzi.impostazioni(db.impostazioni())


def _calcola_prezzo(p, scelte):
    return prezzi.calcola(p.get("costi") or [], scelte, _imp(), area_m2=p.get("area_m2"), peso_kg=p.get("peso_kg"),
                          con_calcolo=p.get("con_calcolo"), riferimento_master=p.get("totale_eur"))


# ---------------- famiglie ----------------

@app.get("/api/famiglie")
def famiglie():
    return TESSERE


@app.get("/api/famiglie/{fam}/schema")
def schema(fam: str):
    return _modulo(fam).schema()


@app.post("/api/famiglie/{fam}/calcola")
def calcola(fam: str, r: Richiesta):
    try:
        return _modulo(fam).calcola(r.valori, r.con_calcolo)
    except (ValueError, ZeroDivisionError) as e:
        raise HTTPException(422, f"Dati non validi: {e}")


@app.post("/api/famiglie/{fam}/anteprima")
def anteprima(fam: str, r: Richiesta):
    try:
        return Response(_modulo(fam).anteprima_svg(r.valori), media_type="image/svg+xml")
    except (ValueError, ZeroDivisionError) as e:
        raise HTTPException(422, f"Dati non validi: {e}")


def _lavora(pid, fam, valori, con_calcolo):
    db.aggiorna(pid, stato="in_lavorazione")
    try:
        r = MODULI[fam].genera_documenti(valori, con_calcolo)
        t = r["totali"]
        file = sorted(f for f in os.listdir(r["cartella"]) if not f.startswith("_"))
        db.aggiorna(pid, cartella=r["cartella"], file=file, titolo=r["titolo"], area_m2=r["area_m2"], peso_kg=t.get("peso_kg"),
                    totale_eur=t.get("totale_eur"), eur_m2=t.get("eur_m2"), costi=r.get("costi") or [], errore=None)
        p = db.leggi(pid)
        ris = _calcola_prezzo(p, {})
        db.aggiorna(pid, prezzi={"scelte": {}, "risultato": ris, "note_master": r.get("note") or []},
                    prezzo_finale=ris["prezzo_finale"], margine_reale=ris["margine_reale"],
                    stato="da_verificare" if con_calcolo else "bozza")
    except Exception:
        db.aggiorna(pid, stato="errore", errore=traceback.format_exc()[-2000:])


@app.post("/api/famiglie/{fam}/preventivi")
def nuovo_preventivo(fam: str, r: NuovoPreventivo):
    m = _modulo(fam)
    try:
        calc = m.calcola(r.valori, r.con_calcolo)
    except (ValueError, ZeroDivisionError) as e:
        raise HTTPException(422, f"Dati non validi: {e}")
    pid = db.crea(fam, r.con_calcolo, r.valori, cliente=r.valori.get("cliente", ""), localita=r.valori.get("localita", ""),
                  titolo=calc["titolo"], origine_id=r.origine_id, area_m2=calc["area_m2"])
    CODA.submit(_lavora, pid, fam, r.valori, r.con_calcolo)
    return db.leggi(pid)


# ---------------- lavori speciali (voci libere) ----------------

def _righe_speciali(righe):
    out = []
    for r in righe:
        q, cu = float(r.get("qta") or 0), float(r.get("costo_unitario") or 0)
        if not str(r.get("voce", "")).strip():
            continue
        cat = r.get("categoria") if r.get("categoria") in prezzi.NOMI else "altro"
        out.append({"categoria": cat, "voce": str(r["voce"]).strip(), "qta": q, "unita": r.get("unita") or "cad",
                    "costo_unitario": cu, "costo": round(q * cu, 2), "listino_id": r.get("listino_id")})
    return out


@app.post("/api/speciali/preventivi")
def nuovo_speciale(s: Speciale):
    righe = _righe_speciali(s.righe)
    pid = db.crea("speciali", False, {"righe": s.righe}, cliente=s.cliente, localita=s.localita, titolo=s.titolo or "Lavoro speciale",
                  stato="bozza", origine_id=s.origine_id, descrizione=s.descrizione, costi=righe)
    p = db.leggi(pid)
    ris = _calcola_prezzo(p, {})
    db.aggiorna(pid, prezzi={"scelte": {}, "risultato": ris}, prezzo_finale=ris["prezzo_finale"], margine_reale=ris["margine_reale"])
    return db.leggi(pid)


@app.put("/api/speciali/preventivi/{pid}")
def aggiorna_speciale(pid: str, s: Speciale):
    p = preventivo(pid)
    if p["famiglia"] != "speciali":
        raise HTTPException(422, "Non è un lavoro speciale")
    righe = _righe_speciali(s.righe)
    db.aggiorna(pid, cliente=s.cliente, localita=s.localita, titolo=s.titolo or "Lavoro speciale", descrizione=s.descrizione,
                configurazione={"righe": s.righe}, costi=righe)
    p = db.leggi(pid)
    scelte = (p.get("prezzi") or {}).get("scelte") or {}
    ris = _calcola_prezzo(p, scelte)
    db.aggiorna(pid, prezzi={**(p.get("prezzi") or {}), "scelte": scelte, "risultato": ris},
                prezzo_finale=ris["prezzo_finale"], margine_reale=ris["margine_reale"])
    return db.leggi(pid)


# ---------------- preventivi ----------------

@app.get("/api/preventivi")
def preventivi(q: str = "", limite: int = 50):
    return db.elenco(q, limite)


@app.get("/api/preventivi/{pid}")
def preventivo(pid: str):
    p = db.leggi(pid)
    if not p:
        raise HTTPException(404, "Preventivo non trovato")
    return p


@app.patch("/api/preventivi/{pid}")
def cambia_stato(pid: str, c: CambioStato):
    if c.stato not in STATI_MANUALI:
        raise HTTPException(422, f"Stato non ammesso: {c.stato}")
    preventivo(pid)
    db.aggiorna(pid, stato=c.stato)
    return db.leggi(pid)


@app.post("/api/preventivi/{pid}/prezzo")
def prezzo(pid: str, r: Prezzo):
    """calcola il prezzo con le scelte (margini, montaggio, trasporto, sconto); con salva=true lo memorizza"""
    p = preventivo(pid)
    if not p.get("costi"):
        raise HTTPException(409, "Costi non disponibili: genera (o rigenera) il preventivo")
    ris = _calcola_prezzo(p, r.scelte)
    if r.salva:
        db.aggiorna(pid, prezzi={**(p.get("prezzi") or {}), "scelte": r.scelte, "risultato": ris},
                    prezzo_finale=ris["prezzo_finale"], margine_reale=ris["margine_reale"])
    return ris


def _cartella(p):
    if p.get("cartella") and os.path.isdir(p["cartella"]):
        return p["cartella"]
    nome = re.sub(r'[\\/:*?"<>|]+', "_", p.get("cliente") or "senza_nome").strip()[:40]
    d = os.path.join(USCITA, f"{datetime.date.today():%Y%m%d}_{nome}_SPECIALE")
    os.makedirs(d, exist_ok=True)
    return d


@app.post("/api/preventivi/{pid}/offerta")
def crea_offerta(pid: str, o: Offerta):
    p = preventivo(pid)
    pz = p.get("prezzi") or {}
    if not pz.get("risultato"):
        raise HTTPException(409, "Prima calcola e salva il prezzo")
    ris = _calcola_prezzo(p, pz.get("scelte") or {})          # sempre ricalcolato con listino e impostazioni attuali
    if ris["richiede_approvazione"] and not o.approvato_da.strip():
        raise HTTPException(409, "Margine sotto il minimo o sconto oltre il massimo: serve il nome di chi approva")
    d = _cartella(p)
    nome = offerta.nome_file(p)
    offerta.genera_pdf(p, ris, _imp(), os.path.join(d, nome))
    file = sorted(f for f in os.listdir(d) if not f.startswith("_"))
    db.aggiorna(pid, cartella=d, file=file, prezzi={**pz, "risultato": ris, "approvato_da": o.approvato_da.strip() or None},
                prezzo_finale=ris["prezzo_finale"], margine_reale=ris["margine_reale"])
    return db.leggi(pid)


@app.get("/api/preventivi/{pid}/file/{nome}")
def scarica(pid: str, nome: str):
    p = preventivo(pid)
    if nome not in (p.get("file") or []):          # solo i file registrati: niente percorsi arbitrari
        raise HTTPException(404, "File non trovato")
    path = os.path.join(p["cartella"], nome)
    if not os.path.exists(path):
        raise HTTPException(404, "File non più presente su disco")
    inline = nome.lower().endswith((".pdf", ".txt"))
    return FileResponse(path, filename=nome, content_disposition_type="inline" if inline else "attachment")


@app.post("/api/preventivi/{pid}/apri-cartella")
def apri_cartella(pid: str):
    p = preventivo(pid)
    if not p.get("cartella") or not os.path.isdir(p["cartella"]):
        raise HTTPException(404, "Cartella non disponibile")
    os.startfile(p["cartella"])                    # solo in locale: apre Esplora risorse sul PC che esegue il server
    return {"ok": True}


# ---------------- impostazioni e listino ----------------

@app.get("/api/impostazioni")
def leggi_impostazioni():
    return {"valori": _imp(), "categorie": prezzi.CATEGORIE}


@app.put("/api/impostazioni")
def salva_impostazioni(valori: dict):
    ammesse = set(prezzi.DEFAULT)
    db.salva_impostazioni({k: v for k, v in valori.items() if k in ammesse})
    return leggi_impostazioni()


@app.get("/api/listino")
def leggi_listino():
    return db.listino()


@app.patch("/api/listino/{lid}")
def modifica_listino(lid: str, v: VoceListino):
    r = db.aggiorna_listino(lid, v.costo)
    if not r:
        raise HTTPException(404, "Voce non trovata")
    return r


# in produzione FastAPI serve anche l'app React compilata (frontend/dist): un solo servizio
DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

    @app.get("/{percorso:path}")
    def spa(percorso: str):
        f = os.path.join(DIST, percorso)
        return FileResponse(f if percorso and os.path.isfile(f) else os.path.join(DIST, "index.html"))
