"""Accesso ai dati. Tutto passa da qui, così il passaggio a Supabase/Postgres cambia solo questo file."""
import json, os, sqlite3, threading, uuid, datetime

DB_PATH = os.environ.get("SERRE_DB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dati.sqlite")
_lock = threading.Lock()
JSON_COLS = ("configurazione", "file", "costi", "prezzi")
# colonne aggiunte dopo la prima versione: create al volo sui database già esistenti
NUOVE_COLONNE = {"costi": "TEXT", "prezzi": "TEXT", "prezzo_finale": "REAL", "margine_reale": "REAL", "numero": "TEXT", "descrizione": "TEXT"}


def _conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql"), encoding="utf-8") as f:
        sql = f.read()
    with _lock, _conn() as c:
        c.executescript(sql)
        esistenti = {r["name"] for r in c.execute("PRAGMA table_info(preventivi)")}
        for col, tipo in NUOVE_COLONNE.items():
            if col not in esistenti:
                c.execute(f"ALTER TABLE preventivi ADD COLUMN {col} {tipo}")


def _ora():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _riga(r):
    if r is None:
        return None
    d = dict(r)
    for k in JSON_COLS:
        if d.get(k):
            d[k] = json.loads(d[k])
    d["con_calcolo"] = bool(d["con_calcolo"])
    return d


# ---------------- preventivi ----------------

def crea(famiglia, con_calcolo, configurazione, cliente="", localita="", titolo="", stato="in_coda", origine_id=None, **altri):
    pid, ora = str(uuid.uuid4()), _ora()
    versione = 1
    with _lock, _conn() as c:
        if origine_id:
            r = c.execute("SELECT versione FROM preventivi WHERE id=?", (origine_id,)).fetchone()
            versione = (r["versione"] + 1) if r else 1
        anno = datetime.date.today().year
        n = c.execute("SELECT COUNT(*) FROM preventivi WHERE creato_il LIKE ?", (f"{anno}%",)).fetchone()[0] + 1
        c.execute("""INSERT INTO preventivi (id, creato_il, aggiornato_il, famiglia, con_calcolo, cliente, localita, titolo,
                     configurazione, stato, versione, origine_id, numero) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (pid, ora, ora, famiglia, int(con_calcolo), cliente, localita, titolo,
                   json.dumps(configurazione, ensure_ascii=False), stato, versione, origine_id, f"{anno}/{n:04d}"))
    if altri:
        aggiorna(pid, **altri)
    return pid


def aggiorna(pid, **campi):
    if not campi:
        return
    for k in JSON_COLS:
        if k in campi and campi[k] is not None and not isinstance(campi[k], str):
            campi[k] = json.dumps(campi[k], ensure_ascii=False)
    campi["aggiornato_il"] = _ora()
    sets = ", ".join(f"{k}=?" for k in campi)
    with _lock, _conn() as c:
        c.execute(f"UPDATE preventivi SET {sets} WHERE id=?", (*campi.values(), pid))


def leggi(pid):
    with _conn() as c:
        return _riga(c.execute("SELECT * FROM preventivi WHERE id=?", (pid,)).fetchone())


def elenco(q="", limite=50):
    with _conn() as c:
        if q:
            like = f"%{q}%"
            rows = c.execute("""SELECT * FROM preventivi WHERE cliente LIKE ? OR titolo LIKE ? OR localita LIKE ? OR numero LIKE ?
                                ORDER BY creato_il DESC LIMIT ?""", (like, like, like, like, limite)).fetchall()
        else:
            rows = c.execute("SELECT * FROM preventivi ORDER BY creato_il DESC LIMIT ?", (limite,)).fetchall()
    return [_riga(r) for r in rows]


# ---------------- impostazioni (margini, soglie) ----------------

def impostazioni():
    with _conn() as c:
        return {r["chiave"]: json.loads(r["valore"]) for r in c.execute("SELECT chiave, valore FROM impostazioni")}


def salva_impostazioni(valori: dict):
    with _lock, _conn() as c:
        for k, v in valori.items():
            c.execute("INSERT INTO impostazioni (chiave, valore) VALUES (?, ?) ON CONFLICT(chiave) DO UPDATE SET valore=excluded.valore",
                      (k, json.dumps(v, ensure_ascii=False)))


# ---------------- listino costi ----------------

def listino():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM listino ORDER BY categoria, voce")]


def listino_vuoto():
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM listino").fetchone()[0] == 0


def inserisci_listino(righe):
    ora = _ora()
    with _lock, _conn() as c:
        for r in righe:
            c.execute("""INSERT INTO listino (id, categoria, voce, unita, costo, fonte, da_confermare, aggiornato_il)
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (str(uuid.uuid4()), r["categoria"], r["voce"], r["unita"], r["costo"], r.get("fonte", ""),
                       int(r.get("da_confermare", False)), ora))


def aggiorna_listino(lid, costo):
    with _lock, _conn() as c:
        c.execute("UPDATE listino SET costo=?, da_confermare=0, aggiornato_il=? WHERE id=?", (costo, _ora(), lid))
        return dict(c.execute("SELECT * FROM listino WHERE id=?", (lid,)).fetchone() or {})
