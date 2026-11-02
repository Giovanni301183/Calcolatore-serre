"""Disegno serra ad arco sullo standard Terranova: foglio A3 con cartiglio reale (da DWG 22959),
prospetto frontale, sezione strutturale A-A, pianta quotata, vista 3D con note. Unità: mm."""
import math, os, json, datetime
import ezdxf
from regole import FONDAZIONI
from ezdxf.math import Matrix44, Vec2
from ezdxf.enums import TextEntityAlignment as TA

APP = os.path.dirname(os.path.abspath(__file__))
MODELLO = os.path.join(APP, "modello_cartiglio_A3.dxf")
CAMPI = json.load(open(os.path.join(APP, "modello_campi.json")))

# misure componenti arco dal master 2026 (colonna K): larghezza -> (sviluppo arco, tirante, moncone, rinforzo V, rinforzo M)
ARCO = {5.5: (6.15, 5.45, 0.95, 0, 0), 6: (6.74, 5.95, 1.12, 1.43, 0), 6.5: (7.2, 6.45, 1.19, 1.51, 0),
        7: (7.8, 6.95, 1.2, 1.53, 0), 7.5: (8.31, 7.45, 1.35, 1.72, 0), 8: (8.87, 7.95, 1.46, 2.0, 1.46),
        9: (9.98, 8.95, 1.65, 2.0, 1.54), 10: (11.0, 9.95, 1.8, 2.4, 2.0)}
SCALE = [50, 75, 100, 125, 150, 200, 250, 300, 400, 500, 750, 1000, 1500, 2000]


def misure_arco(W):
    """misure del master per la larghezza W (m). Fuori tabella (es. 7,75 / 8,50 / 9,50): interpolazione lineare tra le
    due larghezze standard vicine; oltre 10 m o sotto 5,5 m: in proporzione alla più vicina. Ritorna (misure, standard)."""
    if W in ARCO: return ARCO[W], True
    ks = sorted(ARCO)
    if ks[0] < W < ks[-1]:
        a = max(x for x in ks if x < W); b = min(x for x in ks if x > W); t = (W - a) / (b - a)
        A, Bm = ARCO[a], ARCO[b]
        val = [A[i] + (Bm[i] - A[i]) * t for i in range(5)]
        if A[4] == 0 and Bm[4]: val[4] = Bm[4] * W / b       # rinforzo M: il master lo dà solo da 8 m, si scala dal vicino
        if A[3] == 0 and Bm[3]: val[3] = Bm[3] * W / b
    else:
        k = ks[0] if W < ks[0] else ks[-1]
        val = [v * W / k for v in ARCO[k]]
    val[1] = W - 0.05                                     # tirante: luce - 5 cm come nel master
    return tuple(round(v, 2) for v in val), False


def fm(x, d=2):  # numero all'italiana
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


class Foglio:
    def __init__(self, S):
        self.S = S                                            # 1 mm di carta = S mm di modello
        self.doc = ezdxf.readfile(MODELLO)
        self.msp = self.doc.modelspace()
        m = Matrix44.scale(S, S, S)
        for e in self.msp: e.transform(m)
        d = self.doc
        for name, col in (("STRUTTURA", 7), ("ARCHI", 1), ("sottili", 4), ("QUOTE", 3), ("TESTI", 7), ("PILASTRI", 7), ("ASSI", 8), ("GRONDAIE", 5)):
            if name not in d.layers: d.layers.add(name, color=col)
        if "DASHED" not in d.linetypes: d.linetypes.add("DASHED", pattern=[0.5 * S, 0.3 * S, -0.2 * S], description="- - -")
        if "CENTER" not in d.linetypes: d.linetypes.add("CENTER", pattern=[3.0 * S, 2.0 * S, -0.5 * S, 0.0, -0.5 * S], description="__ . __")
        st = d.dimstyles.duplicate_entry("ISO-25", "TN") if "TN" not in d.dimstyles else d.dimstyles.get("TN")
        st.dxf.dimtxsty = "Standard"; st.dxf.dimtxt = 2.0; st.dxf.dimasz = 1.5; st.dxf.dimtsz = 1.2   # tratti obliqui come nei vostri disegni
        st.dxf.dimexe = 1.0; st.dxf.dimexo = 1.0; st.dxf.dimgap = 0.6; st.dxf.dimtad = 1; st.dxf.dimdsep = ord(","); st.dxf.dimclrt = 7
        st.dxf.dimscale = S

    def T(self, txt, x, y, h=2.5, al=TA.LEFT, layer="TESTI", rot=0, style="Standard"):
        t = self.msp.add_text(txt, height=h * self.S, rotation=rot, dxfattribs={"layer": layer, "style": style})
        t.set_placement((x, y), align=al); return t

    def dim(self, p1, p2, base, angle=0, lfac=1.0, dec=0, text=None):
        # valore calcolato qui: ezdxf arrotonda all'intero prima di applicare dimlfac
        a = math.radians(angle)
        mis = abs((p2[0] - p1[0]) * math.cos(a) + (p2[1] - p1[1]) * math.sin(a)) * lfac
        d = self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=angle, dimstyle="TN", text=text or (str(int(round(mis))) if dec == 0 else fm(mis, dec)),
                                    override={"dimlfac": lfac, "dimdec": dec, "dimzin": 0}, dxfattribs={"layer": "QUOTE"})
        d.render()

    def aligned(self, p1, p2, dist, lfac=1.0, dec=2):
        mis = math.dist(p1, p2) * lfac
        d = self.msp.add_aligned_dim(p1=p1, p2=p2, distance=dist, dimstyle="TN", text=fm(mis, dec),
                                     override={"dimlfac": lfac, "dimdec": dec, "dimzin": 0}, dxfattribs={"layer": "QUOTE"})
        d.render()

    def nota(self, testo, punta, testo_pos, h=1.8):
        self.msp.add_line(punta, testo_pos, dxfattribs={"layer": "TESTI"})
        y = testo_pos[1]
        for riga in testo.split("\n"):
            self.T(riga, testo_pos[0] + 1 * self.S, y, h); y -= h * 1.5 * self.S

    def cartiglio(self, s, n_tavola=""):
        oggi = datetime.date.today().strftime("%d %m %Y")
        if s.c > 1:
            tit = f"SERRA m ({fm(s.W)} x n.{s.c}) {fm(s.B)} x {fm(s.L)} = m² {fm(s.area)}"
        else:
            tit = f"SERRA m {fm(s.W)} x {fm(s.L)} = m² {fm(s.area)}"
        val = {"cliente": f"{s.cliente} {s.localita}".strip().upper(), "numero": s.n_disegno or "", "data": oggi, "titolo": tit}
        for k, v in val.items():
            c = CAMPI[k]
            mt = self.msp.add_mtext(v, dxfattribs={"layer": "cartiglio", "style": c["style"], "char_height": 1.9 * self.S,
                                                   "attachment_point": c["att"], "width": (85 if k == "titolo" else 60) * self.S})
            mt.set_location((c["x"] * self.S, c["y"] * self.S))


def _a_capo(testo, n):
    """spezza il testo in righe di al massimo n caratteri (a parole)"""
    righe, r = [], ""
    for p in testo.split():
        if r and len(r) + 1 + len(p) > n: righe.append(r); r = p
        else: r = f"{r} {p}".strip()
    return righe + ([r] if r else [])


def scegli_scala(dim_mm, spazio_mm):
    for sc in SCALE:
        if all(d / sc <= sp for d, sp in zip(dim_mm, spazio_mm)): return sc
    return SCALE[-1]


def arco_pts(x0, y0, W, f, n=40):
    """punti dell'arco circolare per tre punti (x0,y0)-(x0+W,y0) con freccia f"""
    r = (W ** 2 / 4 + f ** 2) / (2 * f); cx, cy = x0 + W / 2, y0 + f - r
    a = math.asin((W / 2) / r)
    return [(cx + r * math.sin(t), cy + r * math.cos(t)) for t in [-a + 2 * a * i / n for i in range(n + 1)]]


# Tirante curvo: sale di 0,027 W al centro (misurato sui DWG 23129 Genna 10 m e 23138 Marino 9 m; con questo valore
# il moncone centrale torna con il master: 1,43 su 1,46 a 8 m, 1,60 su 1,65 a 9 m). Il vecchio 22959 saliva di 0,058 W.
# Freccia dell'arco ricavata dallo sviluppo arco del master.
RISALITA_TIRANTE = 0.027
POS_V = 0.174          # nodo del rinforzo V sull'arco quando il master non dà la lunghezza (5,5 m)
# Grondaia sopra ogni pilastro (profilo semplificato dai DWG 23129/23138, mm rispetto a asse pilastro e quota gronda):
# fondo 150 mm sotto l'imposta dell'arco, bordi a 200 mm sopra, larghezza circa 400 mm
GRONDAIA = [(-200, 200), (-160, 200), (-140, 170), (-140, 110), (-50, -150), (50, -150), (140, 110), (140, 170), (160, 200), (200, 200)]


def freccia_da_sviluppo(W, sv):
    """freccia (mm) dell'arco di corda W (mm) e sviluppo sv (m)"""
    L = lambda f: 2 * ((W * W / 4 + f * f) / (2 * f)) * math.asin((W / 2) / ((W * W / 4 + f * f) / (2 * f)))
    lo, hi = 1.0, W / 2
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if L(mid) < sv * 1000 else (lo, mid)
    return lo


def monconi_auto(W_m):
    """come il master: rinforzi a M (monconi laterali) solo per 9 e 10 m; per le larghezze custom oltre 8 m (8,50, 9,50...)
    si mettono anche lì, perché la luce è maggiore di quella dell'8 m che nel master non li ha"""
    return 3 if W_m > 8 else 1


def quota(pts, x):
    return min(pts, key=lambda q: abs(q[0] - x))[1]


def _cerchio(W, f):
    """raggio e quota del centro (rispetto alla corda) dell'arco di corda W e freccia f"""
    r = (W * W / 4 + f * f) / (2 * f)
    return r, f - r


def _z_arco(W, f, d):
    """quota (dalla gronda) del punto d'arco a distanza d dall'asse della campata"""
    r, cy = _cerchio(W, f)
    return cy + math.sqrt(max(r * r - d * d, 0))


def _z_tirante(W, d):
    return _z_arco(W, RISALITA_TIRANTE * W, d)


def _a_distanza(p, L, zf, d0, d1):
    """primo punto (d, zf(d)) con d in [d0, d1] a distanza L dal punto p; None se non c'è"""
    prec = None
    for i in range(401):
        d = d0 + (d1 - d0) * i / 400
        s = math.dist(p, (d, zf(d))) - L
        if prec is not None and prec[1] < 0 <= s:
            lo, hi = prec[0], d
            for _ in range(40):
                m = (lo + hi) / 2
                lo, hi = (m, hi) if math.dist(p, (m, zf(m))) < L else (lo, m)
            return lo
        prec = (d, s)
    return None


def nodi_zigzag(W, f, n):
    """nodi della tralicciatura a zig-zag (mezza capriata; distanza dall'asse, quota dalla gronda):
    [T0 centro tirante, A sull'arco, B sul tirante, C sull'arco, ...].
    Come nei DWG 23129 e 23138: il rinforzo V va da T0 al nodo A sull'arco, il moncone laterale (rinforzo M)
    scende da A al nodo B sul tirante. A e B vengono dalle lunghezze del master (V e M): disegno e computo coincidono."""
    (sv, ti, mo, rv, rm), _ = misure_arco(W / 1000)
    t0 = (0.0, _z_tirante(W, 0))
    za, zt = (lambda d: _z_arco(W, f, d)), (lambda d: _z_tirante(W, d))
    a = (_a_distanza(t0, rv * 1000, za, 0, 0.42 * W) if rv else None) or POS_V * W
    nodi = [t0, (a, za(a))]
    m = max(int(n) - 1, 0) // 2                           # coppie di monconi laterali
    if m >= 1:
        b = (_a_distanza(nodi[1], rm * 1000, zt, a, 0.46 * W) if rm else None) or a + 0.45 * (W / 2 - a)
        nodi.append((b, zt(b)))
        passo = (0.47 * W - b) / (m - 0.5) if m > 1 else 0  # monconi in più (5, 7): zig-zag a passo costante verso l'imposta
        for k in range(2, m + 1):
            d = min(b + passo * (k - 1), 0.47 * W)
            nodi.append((d, za(d) if k % 2 == 0 else zt(d)))
    return nodi


def capriata(W, hg, f, monconi=1, rinf_v=True, x0=0.0):
    """capriata della campata come nei disegni reali: tirante curvo, moncone centrale verticale,
    rinforzi a V e monconi laterali a zig-zag (rinforzi a M). Ritorna segmenti (x1, z1, x2, z2, tipo)."""
    cx = x0 + W / 2
    tp = arco_pts(x0, hg, W, RISALITA_TIRANTE * W, 12)
    seg = [(a[0], a[1], b[0], b[1], "tirante") for a, b in zip(tp, tp[1:])]
    nodi = nodi_zigzag(W, f, monconi)
    seg.append((cx, hg + nodi[0][1], cx, hg + f, "moncone"))
    for sg in (-1, 1):
        for j, (p, q) in enumerate(zip(nodi, nodi[1:])):
            if j == 0 and not rinf_v: continue
            seg.append((cx + sg * p[0], hg + p[1], cx + sg * q[0], hg + q[1], "rinforzo" if j == 0 else "moncone_lat"))
    return seg


def lunghezze_capriata(W_m, sv, monconi):
    """lunghezze (m) del moncone centrale e media dei monconi laterali a zig-zag, per le quantità"""
    W = W_m * 1000; f = freccia_da_sviluppo(W, sv)
    nodi = nodi_zigzag(W, f, monconi)
    lat = [math.dist(p, q) / 1000 for p, q in zip(nodi[1:], nodi[2:])]
    return round((f - nodi[0][1]) / 1000, 2), (round(sum(lat) / len(lat), 2) if lat else 0)


def interasse_auto(W_m, valore=0):
    """interasse (m) dei montanti frontali centrali: 0 = automatico come i disegni reali
    (2,40 fino a 8 m come il 22959; W/3 da 9 m come 23138 = 3,00 e 23129 = 3,33)"""
    if valore and valore > 0: return float(valore)
    return round(W_m / 3, 2) if W_m > 8 else 2.4


def grondaia(msp, T, x, hg, layer="GRONDAIE"):
    """profilo della grondaia sopra il pilastro in x; T = trasformazione (x, z) -> foglio"""
    msp.add_lwpolyline([T(x + dx, hg + dz) for dx, dz in GRONDAIA], dxfattribs={"layer": layer, "lineweight": 25})


def montanti_pos(W, n, interasse, cx):
    """x dei montanti frontali di una campata: 2 = coppia centrale a +/- interasse/2; 4 = più una coppia esterna a metà
    verso i pilastri; 1 = al centro; 3 = centro più due a +/- interasse; 5 o più = equidistanti"""
    a = min(interasse / 2, W / 2 - 300)
    if n <= 0: return []
    if n == 1: return [cx]
    if n == 3:
        a3 = min(interasse, W / 2 - 300)
        return [cx - a3, cx, cx + a3]
    if n >= 5:
        return [cx - W / 2 + W * (j + 1) / (n + 1) for j in range(n)]
    xs = [cx - a, cx + a]
    if n >= 4:
        b = a + (W / 2 - a) / 2
        xs += [cx - b, cx + b]
    return sorted(xs)


def montanti_frontale(W, n, interasse, cx, porta=None):
    """x dei montanti di una campata del frontale; con la porta i montanti dentro il vano diventano i due stipiti.
    Unica regola per pianta, prospetti e 3D (così le tre viste coincidono sempre)."""
    xs = montanti_pos(W, n, interasse, cx)
    if porta:
        pw = porta["larghezza"] * 1000
        xs = sorted([x for x in xs if abs(x - cx) > max(interasse, pw) / 2 + 1] + [cx - pw / 2, cx + pw / 2])
    return xs


def config_frontali(s):
    """{(frontale 'A'/'B', indice campata 0..c-1): (n. montanti, interasse in m)}.
    Base = valori generali della maschera; poi le righe di s.frontali_lista, in ordine (la riga dopo vale sulla prima).
    Riga: frontale 'A e B' / 'Frontale A' / 'Frontale B', campata 0 = tutte, montanti, interasse 0 = come il generale."""
    base_i = interasse_auto(s.W, float(getattr(s, "interasse_montanti", 0) or 0))
    cfg = {(nome, i): (int(getattr(s, "montanti_campata", 2)), base_i) for nome in "AB" for i in range(s.c)}
    for r in getattr(s, "frontali_lista", None) or []:
        nomi = "AB" if r["frontale"] == "A e B" else r["frontale"][-1]
        camp = range(s.c) if not r["campata"] else [r["campata"] - 1]
        for nome in nomi:
            for i in camp:
                if (nome, i) in cfg:
                    cfg[(nome, i)] = (int(r["montanti"]), float(r["interasse"]) if r.get("interasse") else base_i)
    return cfg


def porta_frontale(porte, nome, i):
    """porta sul frontale nome ('A'/'B') nella campata di indice i (la prima, se ce ne sono due)"""
    return next((d for d in porte if d["posizione"] == f"Frontale {nome}" and int(d["campata"]) == i + 1), None)


def montanti_campata_frontale(s, nome, i, W, cx, cfg=None):
    """x (mm) dei montanti della campata i sul frontale nome, stipiti porta compresi: unica fonte per disegno e computo"""
    n, it = (cfg or config_frontali(s))[(nome, i)]
    return montanti_frontale(W, n, it * 1000, cx, porta_frontale(getattr(s, "porte_lista", None) or [], nome, i))


def correntini_pos(W, hg, f, n, x0=0.0):
    """posizioni (x,z) dei correntini longitudinali distribuiti in modo simmetrico sull'arco"""
    pts = arco_pts(x0, hg, W, f, 400)
    return [pts[round(400 * j / (n + 1))] for j in range(1, n + 1)]


def genera(s, path):
    W, L, c, p = s.W * 1000, s.L * 1000, s.c, s.p * 1000
    B = W * c
    (sv, ti, mo, rv, rm), std = misure_arco(s.W)
    hg = s.h_gronda * 1000
    f = freccia_da_sviluppo(W, sv)      # freccia dallo sviluppo arco del master (come i tubi tagliati)
    hc = hg + f
    s.h_colmo = round(hc / 1000, 2)
    nmon = int(getattr(s, "monconi", 0) or 0) or monconi_auto(s.W)
    rinf_v = bool(getattr(s, "rinforzi_v", True))
    cfg = config_frontali(s)                          # montanti per frontale e campata (scelti in maschera)
    mont_xs = lambda nome, i, cx: montanti_campata_frontale(s, nome, i, W, cx, cfg)
    porte = getattr(s, "porte_lista", None) or []

    # scale delle viste (spazi in mm di carta)
    Sp = scegli_scala((L, B), (190, 120))            # pianta
    F = Foglio(Sp); msp = F.msp
    k = lambda sv_: Sp / sv_                          # fattore per disegnare una vista a scala diversa
    F.cartiglio(s)

    # ---------- PIANTA (in alto a destra) ----------
    ox, oy = 215 * Sp, 140 * Sp + (120 * Sp - B) / 2
    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + B), (ox, oy + B)], close=True,
                       dxfattribs={"layer": "STRUTTURA", "lineweight": 50})
    q = 0.9 * Sp
    ys = [min(j * p, L) for j in range(s.N)]
    if ys[-1] < L: ys.append(L)
    def libero(i, x):                                 # pilastro tolto se cade dentro una porta laterale (trave saltapasso)
        for d in porte:
            riga = 0 if d["posizione"] == "Laterale 1" else c if d["posizione"] == "Laterale 2" else None
            if riga == i and abs(x - d["distanza"] * 1000) < d["larghezza"] * 500 - 50 and 0 < x < L:
                return True
        return False
    for i in range(c + 1):
        for x in ys:
            if libero(i, x): continue
            msp.add_lwpolyline([(ox + x - q, oy + i * W - q), (ox + x + q, oy + i * W - q), (ox + x + q, oy + i * W + q), (ox + x - q, oy + i * W + q)],
                               close=True, dxfattribs={"layer": "PILASTRI"})
        gq = max(150, 0.45 * Sp)                      # grondaia lungo ogni fila di pilastri (interne = compluvi, esterne = gronde laterali)
        for sg in (-1, 1):
            msp.add_line((ox, oy + i * W + sg * gq), (ox + L, oy + i * W + sg * gq), dxfattribs={"layer": "GRONDAIE"})
    m = s.ml()
    lat = "TENDINA LATERALE" if m["tl"] else ("GHIGLIOTTINA LATERALE" if m["gl"] else ("APERTO" if s.laterali_aperti else "CHIUSO"))
    F.T(f"{lat} - {s.copertura}", ox + L / 2, oy + B + 2.5 * Sp, 2.8, TA.BOTTOM_CENTER)
    fro = "TENDINA FRONTALE" if m["tf"] else ("GHIGLIOTTINA FRONTALE" if m["gf"] else ("APERTO" if s.frontali_aperti else "CHIUSO"))
    F.T(fro + " (A)", ox - 10 * Sp, oy + B / 2, 2.8, TA.BOTTOM_CENTER, rot=90)
    F.T("B", ox + L + 9 * Sp, oy + B + 2.5 * Sp, 2.8, TA.BOTTOM_CENTER)
    def freccia(x1, y1, x2, y2):                      # freccia porta: dal punto 1 verso la parete (punto 2)
        msp.add_lwpolyline([(x1, y1), (x2, y2)], dxfattribs={"layer": "TESTI", "lineweight": 35})
        dx, dy = (x2 - x1), (y2 - y1); n = math.hypot(dx, dy) or 1; ux, uy = dx / n, dy / n
        b = (x2 - 2 * Sp * ux, y2 - 2 * Sp * uy)
        msp.add_solid([(x2, y2), (b[0] - 0.9 * Sp * uy, b[1] + 0.9 * Sp * ux), (b[0] + 0.9 * Sp * uy, b[1] - 0.9 * Sp * ux)], dxfattribs={"layer": "TESTI"})
    def vano(p1, p2):                                 # porta in pianta come nel 22959: rettangolo tratteggiato a cavallo della parete
        (x1, y1), (x2, y2) = p1, p2
        vert = abs(x2 - x1) < 1
        e = 0.55 * Sp
        for s_ in (-e, e):
            a, b = ((x1 + s_, y1), (x2 + s_, y2)) if vert else ((x1, y1 + s_), (x2, y2 + s_))
            msp.add_line(a, b, dxfattribs={"layer": "STRUTTURA", "linetype": "DASHED", "lineweight": 25})
        for p_ in (p1, p2):
            a, b = ((p_[0] - e, p_[1]), (p_[0] + e, p_[1])) if vert else ((p_[0], p_[1] - e), (p_[0], p_[1] + e))
            msp.add_line(a, b, dxfattribs={"layer": "STRUTTURA", "lineweight": 25})
    qm = 0.7 * Sp                                     # montante frontale: quadratino poco più piccolo del pilastro
    def montante(x, y):
        msp.add_lwpolyline([(x - qm, y - qm), (x + qm, y - qm), (x + qm, y + qm), (x - qm, y + qm)], close=True,
                           dxfattribs={"layer": "PILASTRI"})
        h_ = msp.add_hatch(color=7, dxfattribs={"layer": "PILASTRI"}); h_.set_solid_fill()
        h_.paths.add_polyline_path([(x - qm, y - qm), (x + qm, y - qm), (x + qm, y + qm), (x - qm, y + qm)], is_closed=True)
    for nome, xw, sg in (("A", ox, -1), ("B", ox + L, 1)):          # montanti frontali e porte sui due frontali
        for i in range(c):
            d = porta_frontale(porte, nome, i)
            for yy in mont_xs(nome, i, W / 2):
                montante(xw, oy + i * W + yy)
            if d:
                pl = d["larghezza"] * 1000; yc = oy + (i + 0.5) * W
                vano((xw, yc - pl / 2), (xw, yc + pl / 2))
                freccia(xw + sg * 8 * Sp, yc, xw + sg * 1.2 * Sp, yc)
                F.T(f"PORTA {fm(d['larghezza'])} x {fm(d['altezza'])}", xw - sg * 2 * Sp, yc, 1.6,      # scritta dentro la serra, accanto alla porta
                    TA.MIDDLE_LEFT if sg < 0 else TA.MIDDLE_RIGHT)
    for d in porte:                                   # porte laterali: stesso simbolo, tra i pilastri
        if d["posizione"].startswith("Frontale"): continue
        pl = d["larghezza"] * 1000
        yw = oy if d["posizione"] == "Laterale 1" else oy + B
        sg = 1 if d["posizione"] == "Laterale 1" else -1
        xc = ox + d["distanza"] * 1000
        vano((xc - pl / 2, yw), (xc + pl / 2, yw))
        for xx in (xc - pl / 2, xc + pl / 2): montante(xx, yw)
        F.T(f"PORTA {fm(d['larghezza'])} x {fm(d['altezza'])}", xc + 1.5 * Sp, yw + sg * 3 * Sp, 1.6, TA.MIDDLE_LEFT)   # accanto alla freccia
        freccia(xc, yw + sg * 8 * Sp, xc, yw + sg * 1.2 * Sp)
    # quote del passo staccate dai pilastri e dalla grondaia: passo a 5 mm sotto il perimetro, totale a 11 mm
    yq = [x for x in ys if not libero(0, x)]            # sul laterale 1 la porta larga toglie pilastri: quota il campo intero (es. 5000)
    tutte = min(b - a for a, b in zip(yq, yq[1:])) / Sp >= 11    # ogni campo almeno 11 mm sulla carta: "2500" leggibile
    if tutte:
        for a, b in zip(yq, yq[1:]): F.dim((ox + a, oy), (ox + b, oy), (ox, oy - 5 * Sp))
    else:                                               # troppo fitte: primi due campi quotati + scritta riassuntiva
        for a, b in list(zip(yq, yq[1:]))[:2]: F.dim((ox + a, oy), (ox + b, oy), (ox, oy - 5 * Sp))
        F.T(f"N. {len(ys) - 1} CAMPI DA {s.p * 1000:.0f} = {L:.0f}" + (" (con campo porta)" if len(yq) != len(ys) else ""),
            ox + L / 2, oy - 13 * Sp, 1.8, TA.TOP_CENTER)                # sotto la quota totale: non tocca le quote dei campi
    F.dim((ox, oy), (ox + L, oy), (ox, oy - 11 * Sp))
    xr = ox + L + 12 * Sp
    for i in range(c): F.dim((ox + L, oy + i * W), (ox + L, oy + (i + 1) * W), (xr, 0), angle=90)
    if c > 1: F.dim((ox + L, oy), (ox + L, oy + B), (xr + 5 * Sp, 0), angle=90)
    F.T("PIANTA", ox, oy + B + 9 * Sp, 3.5)

    # ---------- PROSPETTI FRONTALI (sotto il cartiglio, a sinistra) ----------
    # Visti da fuori: sul frontale A il laterale 1 è a destra, sul frontale B a sinistra (coerente con la pianta,
    # dove il frontale A è a sinistra e il laterale 1 in basso). Il prospetto B si disegna solo se è diverso dall'A
    # (porte o montanti diversi).
    con_b = any(d["posizione"] == "Frontale B" for d in porte) or any(cfg[("A", i)] != cfg[("B", i)] for i in range(c))
    Sf = scegli_scala((B, hc), (180, 32 if con_b else 85)); kf = k(Sf)
    fx = 15 * Sp
    traversi = [z for z in (200, 0.31 * hg, 0.62 * hg) if z < hg - 300]          # come nei disegni reali (0,20 / ~1,10 / ~2,18 m su 3,50)

    def frontale(P, x0, xs, porta, lf, y_quota):
        """montanti, fascioni e porta di una campata del frontale: stessa regola nei prospetti e nella sezione A-A"""
        cx = x0 + W / 2
        pts = arco_pts(x0, hg, W, f)
        pw = ph = 0
        if porta:
            pw, ph = porta["larghezza"] * 1000, porta["altezza"] * 1000
        for x in xs:                                                               # montanti frontali: da terra fino all'arco
            msp.add_line(P(x, 0), P(x, quota(pts, x)), dxfattribs={"layer": "STRUTTURA", "lineweight": 25})
        # fascioneria frontale (master, riga 53): fascione di gronda doppio a tutta larghezza, fascioni intermedi e basso.
        # Quelli che attraversano il vano porta si fermano sugli stipiti (nel master: la linea da W - 2 m).
        for z in (hg - 120, hg - 60):
            msp.add_line(P(x0, z), P(x0 + W, z), dxfattribs={"layer": "sottili"})
        for z in traversi:
            if porta and z < ph + 60:
                msp.add_line(P(x0, z), P(cx - pw / 2, z), dxfattribs={"layer": "sottili"})
                msp.add_line(P(cx + pw / 2, z), P(x0 + W, z), dxfattribs={"layer": "sottili"})
            else:
                msp.add_line(P(x0, z), P(x0 + W, z), dxfattribs={"layer": "sottili"})
        if porta:
            l_, r_ = cx - pw / 2, cx + pw / 2
            for z in (ph, ph + 60):                                                # fascione porta (architrave doppio) da stipite a stipite
                msp.add_line(P(l_, z), P(r_, z), dxfattribs={"layer": "STRUTTURA", "lineweight": 25})
            for a, b in ((l_, cx), (cx, r_)):                                      # due ante scorrevoli dentro il vano, battuta al centro
                msp.add_lwpolyline([P(a + 20, 20), P(a + 20, ph - 20), P(b - 20, ph - 20), P(b - 20, 20)], close=True,
                                   dxfattribs={"layer": "sottili"})
            F.dim(P(l_, 0), P(r_, 0), (P(l_, 0)[0], y_quota), lfac=lf, dec=2)
            F.dim(P(r_, 0), P(r_, ph), (P(r_, 0)[0] + 3 * Sp, 0), angle=90, lfac=lf, dec=2)

    def prospetto(nome, fy, specchio, completo):
        P = lambda x, y: (fx + x * kf, fy + y * kf)
        lf = 1 / kf / 1000
        msp.add_line(P(-600, 0), P(B + 600, 0), dxfattribs={"layer": "STRUTTURA"})
        for i in range(c):
            j = c - 1 - i if specchio else i                                       # posizione della campata i nel prospetto
            x0 = j * W; cx = x0 + W / 2
            pts = arco_pts(x0, hg, W, f)
            msp.add_lwpolyline([P(*q_) for q_ in pts], dxfattribs={"layer": "ARCHI", "lineweight": 35})
            msp.add_lwpolyline([P(*q_) for q_ in arco_pts(x0 + 60, hg, W - 120, f - 60)], dxfattribs={"layer": "ARCHI"})
            for x1, z1, x2, z2, _ in capriata(W, hg, f, nmon, rinf_v, x0):        # tirante curvo, moncone, V e monconi a zig-zag
                msp.add_line(P(x1, z1), P(x2, z2), dxfattribs={"layer": "STRUTTURA", "lineweight": 25})
            msp.add_line(P(cx, -400), P(cx, hc + 500), dxfattribs={"layer": "ASSI", "linetype": "CENTER"})
            if c > 1: F.T(f"C.{i + 1}", *P(cx + 150, hc + 250), 1.8, TA.BOTTOM_LEFT)  # numero campata come in maschera
            frontale(P, x0, mont_xs(nome, i, cx), porta_frontale(porte, nome, i), lf, fy - 4 * Sp)   # con la porta i montanti fanno da stipiti
        for i in range(c + 1):
            msp.add_lwpolyline([P(i * W - 30, 0), P(i * W - 30, hg), P(i * W + 30, hg), P(i * W + 30, 0)], close=True,
                               dxfattribs={"layer": "PILASTRI", "lineweight": 35})
            grondaia(msp, P, i * W, hg)
        sx_, dx_ = ("LAT. 2", "LAT. 1") if specchio else ("LAT. 1", "LAT. 2")
        F.T(sx_, *P(-300, hg + 250), 1.8, TA.BOTTOM_RIGHT); F.T(dx_, *P(B + 300, hg + 250), 1.8, TA.BOTTOM_LEFT)
        yq = fy - (9 if completo else 8) * Sp
        for i in range(c): F.dim(P(i * W, 0), P((i + 1) * W, 0), (fx, yq), lfac=lf, dec=3)
        if c > 1 and completo: F.dim(P(0, 0), P(B, 0), (fx, fy - 14 * Sp), lfac=lf, dec=3)
        F.dim(P(0, 0), P(0, hg), (fx - 6 * Sp, 0), angle=90, lfac=lf, dec=2)
        # quota H colmo spostata dall'asse (non si sovrappone al moncone), nella prima campata senza porta del prospetto
        con_porta = {(c - 1 - i if specchio else i) for i in range(c) if porta_frontale(porte, nome, i)}
        jh = next((j for j in range(c) if j not in con_porta), 0)
        xh = jh * W + W / 2 + W * 0.3
        F.dim(P(jh * W + W / 2, hc), P(jh * W + W / 2, 0), (P(xh, 0)[0], 0), angle=90, lfac=lf, dec=2)
        F.T(f"PROSPETTO FRONTALE {nome}  - Scala 1:{Sf} -", fx, P(0, hc)[1] + 5 * Sp, 3.0)

    if con_b:
        prospetto("A", 190 * Sp, True, False)
        prospetto("B", 140 * Sp, False, False)
        y_altre = 129 * Sp
    else:
        prospetto("A", 150 * Sp, True, True)
        y_altre = 130 * Sp
    altre = [d for d in porte if d["posizione"].startswith("Laterale")]
    if altre:
        desc = "; ".join(f"{d['posizione']} a m {fm(d['distanza'])} ({fm(d['larghezza'])} x {fm(d['altezza'])})" for d in altre)
        F.T(f"PORTE LATERALI (vedi pianta): {desc}", fx, y_altre, 2.0)

    # ---------- SEZIONE STRUTTURALE A-A (in basso a sinistra), una campata ----------
    # A sinistra il PARTICOLARE FONDAZIONE in scala grande (le quote della fondazione stanno solo lì), a destra la sezione.
    Ss = scegli_scala((W + 1800, hc + 1500), (112, 92)); ks = k(Ss)
    sx, sy = 68 * Sp, 28 * Sp
    Q = lambda x, y: (sx + x * ks, sy + y * ks)
    msp.add_line(Q(-900, 0), Q(W + 900, 0), dxfattribs={"layer": "STRUTTURA", "lineweight": 35})
    F.T("P.C. 0,00", *Q(W + 950, 50), 1.8)
    fd = FONDAZIONI.get(getattr(s, "fondazione", ""), FONDAZIONI["Tubo PVC Ø160 con cls"])
    tipo = getattr(s, "fondazione", "Tubo PVC Ø160 con cls")
    hi = getattr(s, "interramento", fd["interr"]) * 1000               # parte di pilastro sotto il piano campagna
    fb, fh = fd["b"] * 1000, fd["h"] * 1000
    if tipo.startswith("Tubo"): fh = max(fh, hi + 100)                 # il tubo PVC scende 10 cm sotto il pilastro
    hp = max(fh, hi, 150 if tipo.startswith("Piastra") else 0)        # profondità massima disegnata

    def cls(T, pts_):                                                  # campitura calcestruzzo
        h_ = msp.add_hatch(color=8, dxfattribs={"layer": "sottili"}); h_.set_pattern_fill("AR-CONC", scale=0.02 * Sp)
        h_.paths.add_polyline_path([T(*p_) for p_ in pts_], is_closed=True)

    def fondazione(T, x, est):
        """fondazione sotto il pilastro in x (solo la parte interrata); est = semilarghezza della platea disegnata"""
        L_ = lambda pts_, **a: msp.add_lwpolyline([T(*p_) for p_ in pts_], **a)
        L_([(x - 30, -hi), (x - 30, 0), (x + 30, 0), (x + 30, -hi)], dxfattribs={"layer": "PILASTRI", "lineweight": 35})
        if tipo.startswith("Tubo") or tipo.startswith("Plinto"):
            L_([(x - fb / 2, -fh), (x - fb / 2, 0), (x + fb / 2, 0), (x + fb / 2, -fh)], close=True,
               dxfattribs={"layer": "STRUTTURA", "lineweight": 25, "linetype": "DASHED" if tipo.startswith("Tubo") else "CONTINUOUS"})
            cls(T, [(x - fb / 2, -fh), (x - 30, -fh), (x - 30, 0), (x - fb / 2, 0)]); cls(T, [(x + 30, -fh), (x + fb / 2, -fh), (x + fb / 2, 0), (x + 30, 0)])
            if fh > hi: cls(T, [(x - 30, -fh), (x + 30, -fh), (x + 30, -hi), (x - 30, -hi)])
        elif tipo.startswith("Cordolo"):
            L_([(x - fb / 2, -fh), (x - fb / 2, 0), (x + fb / 2, 0), (x + fb / 2, -fh)], close=True, dxfattribs={"layer": "STRUTTURA", "lineweight": 25})
            cls(T, [(x - fb / 2, -fh), (x + fb / 2, -fh), (x + fb / 2, 0), (x - fb / 2, 0)])
        elif tipo.startswith("Piastra"):
            L_([(x - est, 0), (x + est, 0), (x + est, -150), (x - est, -150)], close=True, dxfattribs={"layer": "STRUTTURA"})
            cls(T, [(x - est, -150), (x + est, -150), (x + est, 0), (x - est, 0)])
        elif tipo.startswith("Palo"):
            L_([(x - 30, -hi), (x, -hi - 120), (x + 30, -hi)], dxfattribs={"layer": "PILASTRI", "lineweight": 35})
        elif tipo.startswith("Vite"):
            L_([(x - 40, -fh + 150), (x - 40, 0), (x + 40, 0), (x + 40, -fh + 150), (x, -fh)], close=True, dxfattribs={"layer": "STRUTTURA", "lineweight": 25})
            for zz in range(150, int(fh) - 150, 120):
                msp.add_line(T(x - 110, -zz - 40), T(x + 110, -zz + 40), dxfattribs={"layer": "STRUTTURA"})
        if tipo.startswith(("Cordolo", "Piastra", "Vite")):                # piastra di base con tirafondi / tasselli
            L_([(x - 110, 0), (x + 110, 0), (x + 110, 12), (x - 110, 12)], close=True, dxfattribs={"layer": "STRUTTURA", "lineweight": 35})
            if not tipo.startswith("Vite"):
                for dx in (-70, 70):
                    msp.add_line(T(x + dx, 40), T(x + dx, -300 if tipo.startswith("Cordolo") else -120), dxfattribs={"layer": "STRUTTURA", "lineweight": 25})

    for x in (0, W):
        msp.add_lwpolyline([Q(x - 30, 0), Q(x - 30, hg), Q(x + 30, hg), Q(x + 30, 0)], close=True, dxfattribs={"layer": "PILASTRI", "lineweight": 35})
        grondaia(msp, Q, x, hg)
        fondazione(Q, x, 450)
    # frontale visto in sezione: la campata con la prima porta sui frontali (A prima di B), altrimenti la centrale del frontale A
    fr_sez, i_sez = "A", (c - 1) // 2
    for nome_ in "AB":
        d_ = next((d for d in porte if d["posizione"] == f"Frontale {nome_}"), None)
        if d_:
            fr_sez, i_sez = nome_, int(d_["campata"]) - 1
            break
    porta_sez = porta_frontale(porte, fr_sez, i_sez)
    frontale(Q, 0, mont_xs(fr_sez, i_sez, W / 2), porta_sez, 1 / ks / 1000, sy - 5 * Sp)

    # ---------- PARTICOLARE FONDAZIONE (scala grande, con tutte le quote) ----------
    lar_d = max(fb, 220) + 1100                                        # quote a sinistra + testo P.C. a destra
    alt_d = hp + 600 + 450
    Sd = next((sc for sc in (10, 15, 20, 25, 30, 40, 50) if lar_d / sc <= 44 and alt_d / sc <= 66), 50); kd = k(Sd)
    dx0 = 13 * Sp + (max(fb, 220) / 2 + 700) * kd                     # asse del pilastro
    dz0 = 26 * Sp + (hp + 300) * kd                                   # piano campagna
    D = lambda x, z: (dx0 + x * kd, dz0 + z * kd)
    e_ = max(fb / 2, 110) + 350
    msp.add_line(D(-e_ - 150, 0), D(e_, 0), dxfattribs={"layer": "STRUTTURA", "lineweight": 35})
    for xx in [-e_ - 150 + 80 * j for j in range(int((e_ * 2 + 150) / 80))]:   # terreno
        if abs(xx) > max(fb / 2, 110) + 20: msp.add_line(D(xx, 0), D(xx - 60, -60), dxfattribs={"layer": "sottili"})
    msp.add_lwpolyline([D(-30, 0), D(-30, 550), D(30, 550), D(30, 0)], dxfattribs={"layer": "PILASTRI", "lineweight": 35})
    msp.add_lwpolyline([D(-90, 550), D(-15, 550), D(-5, 590), D(5, 510), D(15, 550), D(90, 550)], dxfattribs={"layer": "sottili"})  # taglio
    fondazione(D, 0, e_)
    lfd = 1 / kd / 1000
    xq = -max(fb / 2, 110)
    if hi > 0: F.dim(D(-30, 0), D(-30, -hi), (D(xq - 220, 0)[0], 0), angle=90, lfac=lfd, dec=2)
    if fh > 0 and not tipo.startswith("Piastra"):
        F.dim(D(xq, 0), D(xq, -fh), (D(xq - 480, 0)[0], 0), angle=90, lfac=lfd, dec=2)
        if fb > 0: F.dim(D(-fb / 2, -fh), D(fb / 2, -fh), (0, D(0, -fh - 220)[1]), lfac=lfd, dec=2)
    F.T("P.C. 0,00", *D(e_ - 250, 40), 1.6, TA.BOTTOM_LEFT)
    F.T("PILASTRO Ø60x2", *D(70, 400), 1.6, TA.LEFT)
    F.T("PARTICOLARE FONDAZIONE", D(-e_ - 150, 0)[0], D(0, 550)[1] + 7 * Sp, 2.5)
    F.T(f"- Scala 1:{Sd} -", D(-e_ - 150, 0)[0], D(0, 550)[1] + 3.5 * Sp, 2.0)
    yn = D(0, -hp)[1] - (12 if fb > 0 and fh > 0 and not tipo.startswith("Piastra") else 5) * Sp
    for riga in _a_capo(fd["nota"], 24):
        F.T(riga, D(-e_ - 150, 0)[0], yn, 1.6); yn -= 2.6 * Sp
    pts = arco_pts(0, hg, W, f)
    msp.add_lwpolyline([Q(*q_) for q_ in pts], dxfattribs={"layer": "ARCHI", "lineweight": 50})
    def su_arco(x): return min(pts, key=lambda q_: abs(q_[0] - x))[1]
    for x1, z1, x2, z2, _ in capriata(W, hg, f, nmon, rinf_v):
        msp.add_line(Q(x1, z1), Q(x2, z2), dxfattribs={"layer": "STRUTTURA", "lineweight": 25})
    msp.add_line(Q(W / 2, -300), Q(W / 2, hc + 600), dxfattribs={"layer": "ASSI", "linetype": "CENTER"})   # asse di simmetria
    ncorr = 3 if s.nylon else int(round(s.W))
    for xx, zz in correntini_pos(W, hg, f, ncorr):
        msp.add_lwpolyline([Q(xx - 60, zz), Q(xx + 60, zz), Q(xx + 60, zz + 120), Q(xx - 60, zz + 120)], close=True, dxfattribs={"layer": "STRUTTURA"})
    F.dim(Q(0, 0), Q(W, 0), (sx, sy - 12 * Sp), lfac=1 / ks / 1000, dec=2)
    F.dim(Q(0, 0), Q(0, hg), (Q(-600, 0)[0], 0), angle=90, lfac=1 / ks / 1000, dec=2)
    F.dim(Q(W, 0), Q(W, hc), (Q(W + 600, 0)[0], 0), angle=90, lfac=1 / ks / 1000, dec=2)
    F.T("GRONDA", *Q(-850, hg + 80), 1.8); F.T("COLMO", *Q(W / 2 + 120, hc + 120), 1.8)
    nx = Q(W + 1250, 0)[0]
    F.nota(f"ARCO: TUBO Ø60 x 1,5\nSVILUPPO ARCO mt. {fm(sv)}", Q(W * 0.8, su_arco(W * 0.8)), (nx, Q(0, hc + 300)[1]))
    nodi = nodi_zigzag(W, f, nmon)
    F.nota(f"MONCONE (CANDELA) mt. {fm(mo)}", Q(W / 2, hg + f * 0.75), (nx, Q(0, hc - 450)[1]))
    if rinf_v:
        pv = ((nodi[0][0] + nodi[1][0]) / 2, (nodi[0][1] + nodi[1][1]) / 2)
        F.nota(f'RINFORZI A "V" mt. {fm(rv)}', Q(W / 2 + pv[0], hg + pv[1]), (nx, Q(0, hc - 1000)[1]))
    if nmon > 1:
        pm = ((nodi[1][0] + nodi[2][0]) / 2, (nodi[1][1] + nodi[2][1]) / 2)
        lm = lunghezze_capriata(s.W, sv, nmon)[1]
        F.nota(f'MONCONI LATERALI A ZIG-ZAG (RINF. "M")\nN.{nmon - 1} PER ARCO - mt. {fm(lm)}' + (" (media)" if nmon > 3 else ""),
               Q(W / 2 + pm[0], hg + pm[1]), (nx, Q(0, hc - 1550)[1]))
    F.nota("GRONDAIA" + (" IN MAGNELIS" if getattr(s, "magnelis", False) else " IN ACCIAIO ZINCATO"), Q(W + 150, hg + 150), (nx, Q(0, hg - 1300)[1]))
    F.nota(f"TIRANTE CURVO mt. {fm(ti)}", Q(W * 0.85, hg + RISALITA_TIRANTE * W * 0.5), (nx, Q(0, hg - 600)[1]))
    F.nota(f"PILASTRO Ø60 x 2 - L mt. {fm(s.h_gronda + hi / 1000)}" + (f"\n(di cui interrato mt. {fm(hi / 1000)})" if hi else ""),
           Q(W, hg * 0.5), (nx, Q(0, hg * 0.35)[1]))
    F.nota("FONDAZIONE: VEDI PARTICOLARE", Q(W + max(fb, 80) / 2, -max(hp, 100) * 0.5), (nx, Q(0, -hp - 100)[1]))
    cx_, cz_ = correntini_pos(W, hg, f, ncorr)[-1]                  # correntino a destra: la linea non attraversa il titolo
    F.nota(f"N.{ncorr} CORRENTINI PER CAMPATA", Q(cx_, cz_), (nx, Q(0, hc + 1000)[1]))
    F.T(f"SEZIONE STRUTTURALE A-A  - Scala 1:{Ss} -", sx, Q(0, hc)[1] + 7 * Sp, 3.0)
    F.T(f"VERSO FRONTALE {fr_sez}" + (f" - CAMPATA {i_sez + 1}" if c > 1 else ""),
        sx, Q(0, hc)[1] + 3.5 * Sp, 1.8)
    if not std:
        F.T("LARGHEZZA FUORI STANDARD: MISURE ARCO INTERPOLATE DAL MASTER - VERIFICARE", sx, sy - 17 * Sp, 2.0)

    # ---------- VISTA 3D (in basso a destra) ----------
    c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
    iso = lambda x, y, z: ((x + y) * c30, (y - x) * s30 + z)     # frontale in basso a sinistra, lunghezza verso l'alto a destra
    pts3 = [iso(0, 0, 0), iso(B, L, hc), iso(B, 0, 0), iso(0, L, 0)]
    wx = max(q_[0] for q_ in pts3) - min(q_[0] for q_ in pts3); wy = max(q_[1] for q_ in pts3) - min(q_[1] for q_ in pts3)
    S3 = scegli_scala((wx, wy), (185, 105)); k3 = k(S3)
    minx = min(q_[0] for q_ in pts3); miny = min(q_[1] for q_ in pts3)
    gx, gy = 220 * Sp, 18 * Sp
    I = lambda x, y, z: (gx + (iso(x, y, z)[0] - minx) * k3, gy + (iso(x, y, z)[1] - miny) * k3)
    cap = capriata(W, hg, f, nmon, rinf_v)
    for i in range(c):
        ap = arco_pts(i * W, hg, W, f, 16)
        for yy in ys:
            msp.add_lwpolyline([I(xx, yy, zz) for xx, zz in ap], dxfattribs={"layer": "ARCHI"})
            for x1, z1, x2, z2, _ in cap:                                                    # tirante, moncone, rinforzi su ogni arco
                msp.add_line(I(i * W + x1, yy, z1), I(i * W + x2, yy, z2), dxfattribs={"layer": "sottili"})
        for xx, zz in correntini_pos(W, hg, f, ncorr, i * W):                                # correntini longitudinali
            msp.add_line(I(xx, 0, zz), I(xx, L, zz), dxfattribs={"layer": "STRUTTURA"})
    for i in range(c + 1):
        for dx in (-150, 150):                                                             # grondaie (doppia linea = canale)
            msp.add_line(I(i * W + dx, 0, hg + 100), I(i * W + dx, L, hg + 100), dxfattribs={"layer": "GRONDAIE"})
        for yy in (0, L):
            msp.add_line(I(i * W, yy, 0), I(i * W, yy, hg), dxfattribs={"layer": "PILASTRI"})
    ar0 = arco_pts(0, hg, W, f, 400)
    for i in range(c):                                                                     # montanti frontali e porte sui due frontali
        cx = i * W + W / 2
        for nome, yy in (("A", 0), ("B", L)):
            d = porta_frontale(porte, nome, i)
            xs = mont_xs(nome, i, cx)
            if d:
                pw, ph = d["larghezza"] * 1000, d["altezza"] * 1000
                msp.add_lwpolyline([I(cx - pw / 2, yy, 0), I(cx - pw / 2, yy, ph), I(cx + pw / 2, yy, ph), I(cx + pw / 2, yy, 0)],
                                   dxfattribs={"layer": "STRUTTURA", "lineweight": 25})
            for x in xs:
                msp.add_line(I(x, yy, 0), I(x, yy, quota(ar0, x - i * W)), dxfattribs={"layer": "sottili"})
    for yy in ys:
        for x in (0, B): msp.add_line(I(x, yy, 0), I(x, yy, hg), dxfattribs={"layer": "PILASTRI"})
    msp.add_lwpolyline([I(0, 0, 0), I(B, 0, 0), I(B, L, 0), I(0, L, 0)], close=True, dxfattribs={"layer": "STRUTTURA"})
    F.aligned(I(0, 0, 0), I(B, 0, 0), 6 * Sp, lfac=1 / k3 / 1000, dec=2)
    F.aligned(I(B, 0, 0), I(B, L, 0), 6 * Sp, lfac=1 / k3 / 1000, dec=2)
    cop = {"Nylon": "COPERTURA IN\nFILM DI POLIETILENE", "Policarbonato": "COPERTURA IN\nPOLICARBONATO"}.get(s.copertura, "COPERTURA IN\nLASTRE RIGIDE")
    F.nota(cop, I(B / 2, L * 0.6, hc), (I(0, L * 0.5, hc)[0], min(I(0, L * 0.5, hc)[1] + 12 * Sp, 120 * Sp)))   # sotto la pianta
    if m["tl"] or m["gl"]:
        F.nota('APERTURE LATERALI A "TENDINA"\nMANUALE AVVOLGIBILE' if m["tl"] else "APERTURE LATERALI\nA GHIGLIOTTINA",
               I(B, L * 0.55, hg * 0.6), (I(B, L, 0)[0] - 30 * Sp, I(B, L * 0.55, 0)[1] - 14 * Sp))
    F.T(f"VISTA ASSONOMETRICA", gx, gy - 6 * Sp, 3.0)

    # vista dall'alto centrata sul foglio (il modello ereditava una vista isometrica)
    for vp in F.doc.viewports.get("*Active") or []:
        vp.dxf.direction = (0, 0, 1); vp.dxf.target = (0, 0, 0); vp.dxf.view_twist = 0
        vp.dxf.center = (210 * Sp, 148.5 * Sp); vp.dxf.height = 310 * Sp; vp.dxf.aspect_ratio = 1.45
        vp.dxf.ucs_origin = (0, 0, 0); vp.dxf.ucs_xaxis = (1, 0, 0); vp.dxf.ucs_yaxis = (0, 1, 0)
    for name in [u.dxf.name for u in F.doc.ucs]:
        F.doc.ucs.remove(name)
    F.doc.header["$INSUNITS"] = 4
    F.doc.header["$UCSXDIR"] = (1, 0, 0); F.doc.header["$UCSYDIR"] = (0, 1, 0); F.doc.header["$UCSORG"] = (0, 0, 0)
    F.doc.saveas(path)
    return path
