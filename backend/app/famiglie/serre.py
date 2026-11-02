"""Famiglia SERRE AD ARCO: campi della maschera, calcolo live, anteprima e generazione documenti.
Usa il motore del prototipo (motore/regole.py, disegno.py, genera.py)."""
import os, tempfile
import regole, disegno, genera
from .. import prezzi

ID = "serre"

MODELLI = [  # combinazioni più frequenti in archivio (varianti.xlsx, foglio "Proposta configuratore")
    {"id": "mc8n", "nome": "Multicampata 8 m nylon tendina", "valori": {"campate": 3, "larghezza": 8, "copertura": "Nylon", "finestra": "Tendina"}},
    {"id": "mc9n", "nome": "Multicampata 9 m nylon tendina", "valori": {"campate": 3, "larghezza": 9, "copertura": "Nylon", "finestra": "Tendina"}},
    {"id": "mc10r", "nome": "Multicampata 10 m rigida ghigliottina", "valori": {"campate": 2, "larghezza": 10, "copertura": "Rigida (ondulato)", "finestra": "Ghigliottina"}},
    {"id": "sc8n", "nome": "Monocampata 8 m nylon tendina", "valori": {"campate": 1, "larghezza": 8, "copertura": "Nylon", "finestra": "Tendina"}},
    {"id": "sc6r", "nome": "Monocampata 6 m rigida tendina", "valori": {"campate": 1, "larghezza": 6, "copertura": "Rigida (ondulato)", "finestra": "Tendina"}},
]

LARGHEZZE_STD = sorted(disegno.ARCO)
MONTANTI_OPZ = [2, 4, 3, 1, 0, 5, 6]
FRONTALI = ["A e B", "Frontale A", "Frontale B"]

GRUPPI = [
    {"id": "cliente", "titolo": "Cliente", "campi": [
        {"key": "cliente", "label": "Cliente", "tipo": "testo", "default": ""},
        {"key": "localita", "label": "Località", "tipo": "testo", "default": ""},
        {"key": "numero", "label": "N. disegno / documento", "tipo": "testo", "default": ""},
    ]},
    {"id": "struttura", "titolo": "Struttura", "campi": [
        {"key": "campate", "label": "N. campate", "tipo": "numero", "default": 3, "min": 1, "max": 40, "step": 1},
        {"key": "larghezza", "label": "Larghezza campata", "tipo": "numero", "unita": "m", "default": 8, "min": 3, "max": 16, "step": 0.5,
         "suggeriti": LARGHEZZE_STD},
        {"key": "lunghezza", "label": "Lunghezza", "tipo": "numero", "unita": "m", "default": 50, "min": 5, "max": 300, "step": 0.5},
        {"key": "passo", "label": "Passo archi", "tipo": "scelta", "unita": "m", "default": 2.5, "opzioni": [2, 2.25, 2.5, 3]},
        {"key": "h_gronda", "label": "H gronda", "tipo": "numero", "unita": "m", "default": 3.0, "min": 2, "max": 7, "step": 0.1},
        {"key": "copertura", "label": "Copertura", "tipo": "scelta", "default": "Nylon", "opzioni": ["Nylon", "Rigida (ondulato)", "Policarbonato"]},
        {"key": "pilastri", "label": "Pilastri", "tipo": "scelta", "default": "Zincati (Z.C.)", "opzioni": ["Zincati (Z.C.)", "Neri da zincare", "Scatolari"]},
        {"key": "magnelis", "label": "Grondaie Magnelis", "tipo": "si_no", "default": False},
    ]},
    {"id": "aperture", "titolo": "Aperture", "campi": [
        {"key": "finestra", "label": "Finestre laterali", "tipo": "scelta", "default": "Tendina", "opzioni": ["Tendina", "Ghigliottina", "Nessuna"]},
        {"key": "n_frontali", "label": "Tendina/ghigliottina sui frontali", "tipo": "scelta", "default": 2, "opzioni": [2, 1, 0]},
        {"key": "laterali_aperti", "label": "Laterali aperti (senza chiusura)", "tipo": "si_no", "default": False},
        {"key": "fungo", "label": "Finestra a fungo (colmo)", "tipo": "si_no", "default": False},
        {"key": "ali_gabbiano", "label": "Ali di gabbiano", "tipo": "si_no", "default": False},
    ]},
    {"id": "frontali", "titolo": "Capriata, frontali e porte", "campi": [
        {"key": "monconi", "label": "Monconi per capriata", "tipo": "scelta", "default": "Automatico",
         "opzioni": ["Automatico", 1, 3, 5, 7], "aiuto": "Automatico = come il master: 1 fino a 8 m, 3 per 9 e 10 m. I laterali sono a zig-zag (rinforzi a M): scendono dal nodo del rinforzo V fino al tirante, come nei disegni 23129 e 23138"},
        {"key": "rinforzi_v", "label": "Rinforzi a V", "tipo": "si_no", "default": True},
        {"key": "montanti_campata", "label": "Montanti frontali per campata (generale)", "tipo": "scelta", "default": 2, "opzioni": MONTANTI_OPZ},
        {"key": "interasse_montanti", "label": "Interasse montanti centrali (generale)", "tipo": "numero", "unita": "m", "default": 0, "min": 0, "max": 6, "step": 0.05,
         "aiuto": "0 = automatico: 2,40 fino a 8 m, larghezza/3 da 9 m (3,00 - 3,33). Nella campata con la porta i montanti fanno da stipiti"},
        {"key": "frontali_campate", "label": "Montanti diversi per frontale / campata", "tipo": "frontali", "default": [],
         "frontali": FRONTALI, "opzioni": MONTANTI_OPZ,
         "aiuto": "Vale il generale; ogni riga lo cambia sul frontale e sulla campata scelti (Tutte = tutte le campate). "
                  "Le righe sotto valgono sulle precedenti. Interasse 0 = come il generale"},
        {"key": "porte", "label": "Porte scorrevoli", "tipo": "porte", "default": [
            {"posizione": "Frontale A", "campata": 0, "distanza": 0, "larghezza": 2.4, "altezza": 2.3}],
         "posizioni": ["Frontale A", "Frontale B", "Laterale 1", "Laterale 2"],
         "aiuto": "Campata 0 = centrale. Per i laterali indica la distanza dal frontale A (0 = metà serra)"},
    ]},
    {"id": "fondazioni", "titolo": "Fondazioni", "campi": [
        {"key": "fondazione", "label": "Tipo fondazione", "tipo": "scelta", "default": "Tubo PVC Ø160 con cls", "opzioni": list(regole.FONDAZIONI)},
        {"key": "interramento", "label": "Pilastro interrato", "tipo": "numero", "unita": "m", "default": 0.5, "min": 0, "max": 2, "step": 0.05,
         "aiuto": "Si aggiorna in automatico quando cambi fondazione"},
    ]},
]

DEFAULT_INTERRAMENTO = {k: v["interr"] for k, v in regole.FONDAZIONI.items()}


def schema():
    return {"id": ID, "nome": "Serre ad arco", "gruppi": GRUPPI, "modelli": MODELLI,
            "default_interramento": DEFAULT_INTERRAMENTO}


def _valori(v):
    """unisce i valori ricevuti con i default"""
    out = {c["key"]: c["default"] for g in GRUPPI for c in g["campi"]}
    out.update({k: val for k, val in (v or {}).items() if val is not None and val != ""})
    return out


def porte_da_valori(v, c, L):
    """normalizza l'elenco porte (accetta anche il vecchio formato: numero porte + porta_l/porta_h)"""
    raw = v.get("porte")
    if not isinstance(raw, list):
        n = int(float(str(raw or 0).replace(",", ".")))
        raw = [{"posizione": "Frontale A", "campata": 0, "larghezza": v.get("porta_l", 2.4), "altezza": v.get("porta_h", 2.3)}] * n
    out = []
    for d in raw:
        f = lambda k, dflt: float(str(d.get(k, dflt) if d.get(k, dflt) not in ("", None) else dflt).replace(",", "."))
        pos = d.get("posizione") if d.get("posizione") in ("Frontale A", "Frontale B", "Laterale 1", "Laterale 2") else "Frontale A"
        camp = int(f("campata", 0)) or (c + 1) // 2
        out.append({"posizione": pos, "campata": min(max(camp, 1), c), "distanza": f("distanza", 0) or L / 2,
                    "larghezza": f("larghezza", 2.4), "altezza": f("altezza", 2.3)})
    return out


def frontali_da_valori(v, c):
    """normalizza le righe 'montanti diversi per frontale / campata'; le campate che non esistono più vengono ignorate"""
    out = []
    raw = v.get("frontali_campate")
    for d in raw if isinstance(raw, list) else []:
        if not isinstance(d, dict): continue
        f = lambda k, dflt: float(str(d.get(k) if d.get(k) not in ("", None) else dflt).replace(",", "."))
        camp = int(f("campata", 0))
        if not 0 <= camp <= c: continue
        out.append({"frontale": d.get("frontale") if d.get("frontale") in FRONTALI else "A e B", "campata": camp,
                    "montanti": max(int(f("montanti", 2)), 0), "interasse": max(f("interasse", 0), 0)})
    return out


def serra(v):
    v = _valori(v)
    num = lambda k: float(str(v[k]).replace(",", "."))
    porte = porte_da_valori(v, int(num("campate")), num("lunghezza"))
    mon = v.get("monconi", "Automatico")
    mon = 0 if str(mon).lower().startswith("auto") else int(float(mon))
    s = regole.Serra(int(num("campate")), num("larghezza"), num("lunghezza"), num("passo"),
                     copertura=v["copertura"], finestra=v["finestra"],
                     laterali_aperti=bool(v["laterali_aperti"]), frontali_aperti=int(num("n_frontali")) == 0,
                     fungo=bool(v["fungo"]), ali_gabbiano=bool(v["ali_gabbiano"]), porte=len(porte),
                     pilastri=v["pilastri"], magnelis=bool(v["magnelis"]), h_gronda=num("h_gronda"),
                     porta_l=porte[0]["larghezza"] if porte else 2.4, porta_h=porte[0]["altezza"] if porte else 2.3,
                     interramento=num("interramento"),
                     fondazione=v["fondazione"], cliente=str(v["cliente"]).strip(), localita=str(v["localita"]).strip(),
                     n_disegno=str(v["numero"]).strip(), n_doc=str(v["numero"]).strip(),
                     monconi=mon, rinforzi_v=bool(v["rinforzi_v"]), montanti_campata=int(num("montanti_campata")),
                     interasse_montanti=num("interasse_montanti"), porte_lista=porte)
    s.n_frontali = int(num("n_frontali"))
    s.frontali_lista = frontali_da_valori(v, s.c)
    # geometria: una sola fonte, la stessa del disegno (freccia dallo sviluppo arco del master)
    mis, std = disegno.misure_arco(s.W)
    sv, mo = mis[0], mis[2]
    s.misure_custom = None if std else mis
    W = s.W * 1000
    f = disegno.freccia_da_sviluppo(W, sv)
    s.h_colmo = round(s.h_gronda + f / 1000, 2)
    arco = disegno.arco_pts(0, 0, W, f, 400)
    s.interasse_effettivo = disegno.interasse_auto(s.W, s.interasse_montanti)
    # montanti per frontale e campata, stipiti porta compresi: stessa regola del disegno (pianta, prospetti, sezione, 3D)
    cfg = disegno.config_frontali(s)
    xm = [x for nome in "AB" for i in range(s.c) for x in disegno.montanti_campata_frontale(s, nome, i, W, W / 2, cfg)]
    s.n_montanti_tot = len(xm)
    s.montanti_dettaglio = {k: len(disegno.montanti_campata_frontale(s, k[0], k[1], W, W / 2, cfg)) for k in cfg}
    xm = xm or disegno.montanti_pos(W, 2, s.interasse_effettivo * 1000, W / 2)
    s.l_montante = round(s.h_gronda + sum(disegno.quota(arco, x) for x in xm) / len(xm) / 1000, 2)
    nmon = s.monconi or disegno.monconi_auto(s.W)
    if nmon > 1:                                         # zig-zag: per 8-9-10 m coincide con il rinforzo M del master
        s.l_moncone_lat = disegno.lunghezze_capriata(s.W, sv, nmon)[1] or None
    s.monconi_effettivi = nmon
    return s


def avvisi(s, con_calcolo):
    a = []
    _, std = disegno.misure_arco(s.W)
    if not std:
        sv, ti, mo, rv, rm = s.misure_custom or disegno.misure_arco(s.W)[0]
        a.append({"livello": "attenzione", "testo": f"Larghezza {s.W:g} m fuori standard ({', '.join(f'{x:g}' for x in LARGHEZZE_STD)}): "
                  f"misure ricavate dal master per interpolazione (sviluppo arco {sv:g}, moncone {mo:g}, V {rv:g}, M {rm:g} m) e scritte nel master, che da solo le lascerebbe vuote. Da verificare."})
    if abs(s.L / s.p - round(s.L / s.p)) > 1e-6:
        a.append({"livello": "attenzione", "testo": f"Lunghezza non multipla del passo: il programma conta {s.N} archi; proponi {round(s.L / s.p) * s.p:g} m."})
    viste = {}
    for i, d in enumerate(s.porte_lista, 1):
        if d["posizione"].startswith("Frontale"):
            chiave = (d["posizione"], d["campata"])
            if chiave in viste:
                a.append({"livello": "attenzione", "testo": f"Porta {i}: {d['posizione']} campata {d['campata']} ha già la porta {viste[chiave]}: nel disegno ne compare una sola."})
            viste.setdefault(chiave, i)
            if d["larghezza"] > s.W - 1.0:
                a.append({"livello": "attenzione", "testo": f"Porta {i}: larghezza {d['larghezza']:g} m troppo grande per una campata da {s.W:g} m."})
            if d["altezza"] + 0.3 > s.h_gronda:
                a.append({"livello": "attenzione", "testo": f"Porta {i}: altezza {d['altezza']:g} m troppo vicina alla gronda ({s.h_gronda:g} m)."})
            if disegno.config_frontali(s)[(d["posizione"][-1], d["campata"] - 1)][0] == 0:
                a.append({"livello": "info", "testo": f"Porta {i}: campata senza montanti frontali, i due stipiti della porta sono contati come montanti."})
        else:
            if d["larghezza"] > s.p - 0.1:
                tolti = sum(1 for j in range(1, s.N - 1) if abs(j * s.p - d["distanza"]) < d["larghezza"] / 2 - 0.05)
                a.append({"livello": "attenzione", "testo": f"Porta {i} ({d['posizione']}): larghezza {d['larghezza']:g} m oltre il passo {s.p:g} m: "
                          f"{tolti} pilastr{'o' if tolti == 1 else 'i'} tolt{'o' if tolti == 1 else 'i'}, serve trave saltapasso (non conteggiata)."})
            if not (d["larghezza"] / 2 < d["distanza"] < s.L - d["larghezza"] / 2):
                a.append({"livello": "attenzione", "testo": f"Porta {i}: posizione fuori dalla lunghezza della serra."})
    if any(d["larghezza"] != 2.4 or d["altezza"] != 2.3 for d in s.porte_lista):
        a.append({"livello": "info", "testo": "Il prezzo porta del master si riferisce alla 2,40 x 2,30: per misure diverse verificare il costo."})
    if s.monconi_effettivi > 1 and s.W not in (8, 9, 10):
        a.append({"livello": "info", "testo": f"Monconi laterali a zig-zag su {s.W:g} m: il master non ha la misura, lunghezza {s.l_moncone_lat:g} m calcolata dal disegno."})
    if s.laterali_aperti and s.finestra != "Nessuna":
        a.append({"livello": "info", "testo": "Laterali aperti: le finestre laterali non vengono conteggiate."})
    if con_calcolo:
        a.append({"livello": "info", "testo": "Con calcolo strutturale: il preventivo sarà PRELIMINARE e passa in stato 'da verificare' finché il tecnico non conferma i profili."})
    elif s.copertura != "Nylon" and s.W > 10:
        a.append({"livello": "attenzione", "testo": "Copertura rigida con luce oltre 10 m: valuta il calcolo strutturale."})
    return a


def calcola(valori, con_calcolo=False):
    s = serra(valori)
    _, note = regole.celle(s)
    m = s.ml()
    return {
        "titolo": s.titolo(),
        "area_m2": round(s.area, 2),
        "larghezza_totale": round(s.B, 2),
        "archi_per_campata": s.N,
        "monconi": s.monconi_effettivi,
        "h_colmo": s.h_colmo,
        "ml_aperture": {"tendina": m["tl"] + m["tf"], "ghigliottina": m["gl"] + m["gf"], "fungo": m["fu"]},
        "quantita": [{"voce": v, "qta": q, "regola": r, "affidabilita": af} for v, q, r, af in note],
        "avvisi": avvisi(s, con_calcolo),
    }


def anteprima_svg(valori):
    """disegna la tavola A3 in un DXF temporaneo e la converte in SVG (stesso disegno del DWG)"""
    from ezdxf.addons.drawing import Frontend, RenderContext, layout, svg
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
    import ezdxf
    s = serra(valori)
    fd, path = tempfile.mkstemp(suffix=".dxf"); os.close(fd)
    try:
        disegno.genera(s, path)
        doc = ezdxf.readfile(path)
        backend = svg.SVGBackend()
        cfg = Configuration(background_policy=BackgroundPolicy.OFF, color_policy=ColorPolicy.BLACK)
        Frontend(RenderContext(doc), backend, config=cfg).draw_layout(doc.modelspace())
        page = layout.Page(420, 297, layout.Units.mm, margins=layout.Margins.all(0))
        return backend.get_string(page, settings=layout.Settings(fit_page=True))
    finally:
        os.remove(path)


def genera_documenti(valori, con_calcolo=False):
    s = serra(valori)
    r = genera.genera(s)
    if con_calcolo:
        rp = os.path.join(r["cartella"], "Riepilogo.txt")
        with open(rp, encoding="utf-8") as f:
            testo = f.read()
        with open(rp, "w", encoding="utf-8") as f:
            f.write("*** PRELIMINARE — SOGGETTO A CALCOLO STRUTTURALE: profili da confermare dall'ufficio tecnico ***\n\n" + testo)
    t = r["totali"]
    note = []
    ps_master = (t.get("totale_eur") or 0) - (t.get("struttura_eur") or 0)
    if t.get("ps_totale") and abs(ps_master - t["ps_totale"]) > 1:
        it = lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        note.append(f"Nel master i pezzi speciali entrano nel totale per € {it(ps_master)} ma il foglio Pezzi Speciali "
                    f"somma € {it(t['ps_totale'])} (al costo, senza ricarico). Qui si usa il valore del foglio con il margine.")
    return {"cartella": r["cartella"], "totali": t, "area_m2": s.area, "titolo": s.titolo(),
            "costi": prezzi.costi_da_master(t), "note": note}
