"""Regole per compilare il master 2026 'COMPUTO ANALITICO CON QUOTAZIONI MATERIALI AGGIORNATE.xls'.
Il master calcola già da solo archi, tiranti, monconi, correntini, grondaie, cordolo, fasce, cappucci, guide.
Qui si calcolano solo i dati di ingresso e le quantità che nel master sono scritte a mano.
Regole ricavate da 333 computi 2024-2026 (di cui 149 sul modello 2026)."""
import math, os, datetime

# Cartella radice "Serre" (sovrascrivibile con la variabile d'ambiente SERRE_BASE)
BASE = os.environ.get("SERRE_BASE") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
MASTER = os.path.join(BASE, "03_pilota", "master2026", "COMPUTO ANALITICO CON QUOTAZIONI MATERIALI AGGIORNATE.xls")


# Tipi di fondazione: interramento pilastro di default (m), dimensioni fondazione (m), nota per disegno/riepilogo
FONDAZIONI = {
    "Tubo PVC Ø160 con cls": dict(interr=0.50, b=0.16, h=0.60, nota="TUBO IN PVC Ø160 DA RIEMPIRE CON CLS"),
    "Plinto in cls 40x40": dict(interr=0.40, b=0.40, h=0.50, nota="PLINTO IN CLS cm 40 x 40 x 50"),
    "Plinto in cls 50x50": dict(interr=0.50, b=0.50, h=0.60, nota="PLINTO IN CLS cm 50 x 50 x 60"),
    "Cordolo in c.a. + piastra e tirafondi": dict(interr=0.0, b=0.30, h=0.40, nota="CORDOLO IN C.A. cm 30 x 40 - PIASTRA DI BASE CON N.4 TIRAFONDI M12"),
    "Piastra su platea esistente (tasselli)": dict(interr=0.0, b=0.0, h=0.0, nota="PIASTRA DI BASE SU PLATEA ESISTENTE - N.4 TASSELLI CHIMICI M12"),
    "Palo infisso nel terreno": dict(interr=0.80, b=0.0, h=0.0, nota="PILASTRO INFISSO NEL TERRENO (SENZA CLS)"),
    "Vite di fondazione": dict(interr=0.0, b=0.08, h=1.00, nota="VITE DI FONDAZIONE ZINCATA L. 1,00 m CON FLANGIA"),
}


class Serra:
    def __init__(self, campate, larghezza, lunghezza, passo=2.5, copertura="Nylon", finestra="Tendina",
                 laterali_aperti=False, frontali_aperti=False, fungo=False, ali_gabbiano=False, porte=1,
                 pilastri="Zincati (Z.C.)", magnelis=False, h_gronda=3.0, h_colmo=None,
                 porta_l=2.4, porta_h=2.3, interramento=None, fondazione="Tubo PVC Ø160 con cls",
                 cliente="", localita="", n_disegno="", n_doc="",
                 monconi=0, rinforzi_v=True, montanti_campata=2, interasse_montanti=0, porte_lista=None):
        self.c, self.W, self.L, self.p = int(campate), float(larghezza), float(lunghezza), float(passo)
        self.copertura, self.finestra = copertura, finestra
        self.laterali_aperti, self.frontali_aperti = laterali_aperti, frontali_aperti
        self.fungo, self.ali_gabbiano, self.porte = fungo, ali_gabbiano, int(porte)
        self.pilastri, self.magnelis = pilastri, magnelis
        self.h_gronda = float(h_gronda)
        self.fondazione = fondazione if fondazione in FONDAZIONI else "Tubo PVC Ø160 con cls"
        self.porta_l, self.porta_h = float(porta_l), float(porta_h)
        self.interramento = float(interramento) if interramento is not None else FONDAZIONI[self.fondazione]["interr"]
        self.h_colmo = float(h_colmo) if h_colmo else round(self.h_gronda + 0.2 * self.W, 2)
        self.cliente, self.localita, self.n_disegno, self.n_doc = cliente, localita, n_disegno, n_doc
        # scelte dell'ufficio tecnico (0 monconi = automatico come il master)
        self.monconi, self.rinforzi_v = int(monconi or 0), bool(rinforzi_v)
        self.montanti_campata, self.interasse_montanti = int(montanti_campata), float(interasse_montanti)
        self.porte_lista = porte_lista or []
        # lunghezze calcolate dal disegno (impostate da chi crea la Serra, se disponibili)
        self.l_montante = None
        self.l_moncone_lat = None
        self.misure_custom = None          # (sviluppo, tirante, moncone, V, M) se la larghezza non è nella tabella del master

    N = property(lambda s: int(round(s.L / s.p)) + 1)          # archi per campata
    B = property(lambda s: s.c * s.W)                          # larghezza totale
    area = property(lambda s: s.B * s.L)
    nylon = property(lambda s: s.copertura.lower().startswith("nylon"))

    # metri lineari di aperture
    def ml(self):
        lat = 0 if self.laterali_aperti else 2 * self.L
        nfr = 0 if self.frontali_aperti else int(getattr(self, "n_frontali", 2))
        fro = nfr * self.B
        tend = self.finestra.lower().startswith("tend")
        ghig = self.finestra.lower().startswith("ghigl")
        return dict(tl=lat if tend else 0, tf=fro if tend else 0, gl=lat if ghig else 0, gf=fro if ghig else 0,
                    fu=self.c * self.L if self.fungo else 0)

    def titolo(self):
        f = lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if self.c > 1:
            return f"Serra m ({f(self.W)} x n.{self.c} x {f(self.L)}) = mq. {f(self.area)}"
        return f"Serra m {f(self.W)} x {f(self.L)} = mq. {f(self.area)}"


def celle(s: Serra):
    """ritorna (dict foglio->{cella: valore}, lista note [(voce, valore, regola, affidabilità)])"""
    m = s.ml()
    c, W, L, N = s.c, s.W, s.L, s.N
    zc = s.pilastri.startswith("Zinc")
    nero = s.pilastri.startswith("Neri")
    scat = s.pilastri.startswith("Scatol")
    oggi = datetime.date.today().strftime("%d %m %Y")
    nome = (s.cliente or "").upper()
    A = {"A1": f"ANALISI PESI DOC. N.{s.n_doc}", "C1": f"DEL {oggi}", "E1": f"Rif. Dis. Doc. N. {s.n_disegno}",
         "G3": nome, "D3": c, "D4": W, "D5": L, "D11": s.p,
         "F5": 3 if s.nylon else int(round(W)),
         "F6": 1 if (nero or scat) else 0, "F7": 1 if scat else 0, "F8": 1 if s.magnelis else 0, "F9": 1 if s.ali_gabbiano else 0,
         "M3": m["tl"], "M4": m["tf"], "M7": m["fu"], "M8": m["gl"], "M9": m["gf"], "M10": 0 if s.nylon else 1}
    note = []
    def q(sheet, cell, val, voce, regola, aff):
        sheet[cell] = val
        note.append((voce, val, regola, aff))
    q(A, "D20", N * (c + 1) if zc else 0, "Pilastri laterali e centrali Z.C.",
      "(L/passo + 1) x (campate + 1)" if zc else "0: calcolati dal master nella sezione nero/scatolari", "alta (85%)")
    A["K20"] = round(s.h_gronda + s.interramento, 2)
    nm = s.montanti_campata
    tot = getattr(s, "n_montanti_tot", None)
    if tot is None:
        q(A, "D22", nm * c * 2 if zc else 0, "Montanti frontali Z.C.", f"{nm} per campata x 2 frontali (scelta in maschera)", "dato")
    else:
        det = getattr(s, "montanti_dettaglio", {})
        uguali = len(set(det.values())) == 1 and not getattr(s, "frontali_lista", None)
        regola = (f"{nm} per campata x 2 frontali (stipiti porta compresi)" if uguali else
                  "somma per frontale e campata: " + " / ".join(
                      f"{n_}: " + "-".join(str(det[(n_, i)]) for i in range(c)) for n_ in "AB") + " (stipiti porta compresi)")
        q(A, "D22", tot if zc else 0, "Montanti frontali Z.C.", regola, "dato")
    if s.l_montante:
        A["K22"] = round(s.l_montante + s.interramento, 2)
        note.append(("Lunghezza montante frontale (m)", A["K22"], "altezza all'arco nel punto del montante + interrato", "calcolata dal disegno"))
    if not s.rinforzi_v:
        q(A, "D35", 0, "Rinforzi a V", "esclusi in maschera", "dato")
    if s.monconi:
        n_lat = s.N * c * (s.monconi - 1)
        q(A, "D37", n_lat, "Monconi laterali (rinforzi a M)", f"archi x {s.monconi - 1} (scelta: {s.monconi} monconi per capriata)", "dato")
        if s.monconi > 1 and s.l_moncone_lat:
            A["K37"] = s.l_moncone_lat
            note.append(("Lunghezza moncone laterale (m)", s.l_moncone_lat, "dal disegno: tralicciatura a zig-zag (per 8-9-10 m = rinforzo M del master)", "calcolata dal disegno" if s.monconi == 3 else "media: verificare"))
    mc = getattr(s, "misure_custom", None)                  # larghezza fuori tabella: il master lascia vuote queste celle
    if mc:
        sv, ti, mo, rv, rm = mc
        A.update({"K15": sv, "K31": ti, "K33": mo, "K35": round(rv * 2, 2), "K54": round(sv + 0.3, 2), "K55": round(W + 0.3, 2),
                  "K57": round(W - 2, 2) if W >= 7 else 0})
        note.append(("Misure arco per larghezza custom (m)", f"sviluppo {sv} / tirante {ti} / moncone {mo} / V {rv}",
                     "interpolate tra le larghezze del master e scritte nel master (K15, K31, K33, K35, K54-K57)", "media: verificare"))
        nm_eff = getattr(s, "monconi_effettivi", s.monconi) or 1
        if not s.monconi:                                   # automatico: il master non li calcola fuori tabella
            q(A, "D37", s.N * c * (nm_eff - 1), "Monconi laterali (rinforzi a M)", f"archi x {nm_eff - 1} (automatico: larghezza custom)", "media: verificare")
            if nm_eff > 1 and s.l_moncone_lat: A["K37"] = s.l_moncone_lat
    tend_ml = m["tl"] + m["tf"]
    q(A, "D24", math.ceil((2 * L + 2 * s.B) / 6) if (s.nylon and tend_ml == 0 and m["gl"] + m["gf"] == 0) else 0,
      "Tubo tiraggio nylon", "perimetro/6 solo se nylon senza finestre, altrimenti 0", "bassa: verificare")
    q(A, "D28", math.ceil(tend_ml / 6) if tend_ml else 0, "Tubo per tendina", "ml tendina / 6", "alta (94%)")
    q(A, "D39", (16 if L <= 50 else 24) * c, "Controvento di falda", "16 per campata (24 oltre 50 m)", "media")
    q(A, "D41", 8 if L <= 30 else 12 if L <= 50 else 24, "Controvento laterale", "8 fino a 30 m, 12 fino a 50 m, poi 24", "media")
    q(A, "D61", s.porte, "Fascioneria porta", "n. porte dalla maschera", "dato")
    P = {"C3": c, "C4": W, "C5": L, "C6": s.B, "C7": s.area, "C8": s.p}
    q(P, "C11", math.ceil(m["fu"] / 2), "Cremagliere fungo", "ml fungo / 2", "media")
    q(P, "C14", s.porte, "Porta scorrevole", "n. porte", "dato")
    q(P, "C15", math.ceil(tend_ml / 2), "Staffe guida tendina", "ml tendina / 2", "alta")
    q(P, "C19", 4 if tend_ml else 0, "Cricchetto fascione laterale/frontale", "4 se c'è tendina", "alta (77%)")
    q(P, "C26", 2 if tend_ml else 0, "Maniglia tiraggio", "2 se c'è tendina", "media")
    return {"Analisi Pesi": A, "Pezzi Speciali": P}, note
