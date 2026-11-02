"""Test di regressione: le quantità devono restare quelle validate sul caso Maimone 3x9x50 (Riepilogo del prototipo)."""
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)
MAIMONE = {"campate": 3, "larghezza": 9, "lunghezza": 50, "passo": 2, "h_gronda": 3.5}


def calcola(valori, con_calcolo=False):
    r = c.post("/api/famiglie/serre/calcola", json={"valori": valori, "con_calcolo": con_calcolo})
    assert r.status_code == 200, r.text
    return r.json()


def test_quantita_maimone():
    r = calcola(MAIMONE)
    q = {x["voce"]: x["qta"] for x in r["quantita"]}
    assert r["area_m2"] == 1350 and r["archi_per_campata"] == 26
    assert q["Pilastri laterali e centrali Z.C."] == 104
    assert q["Montanti frontali Z.C."] == 12
    assert q["Tubo per tendina"] == 26
    assert q["Controvento di falda"] == 48
    assert q["Staffe guida tendina"] == 77


def test_h_colmo_da_sviluppo_arco():
    assert calcola(MAIMONE)["h_colmo"] == 5.35          # 3,50 + freccia 1,85 ricavata dallo sviluppo arco 9,98 m (stessa fonte del disegno)


def test_monconi_e_montanti_scelti():
    r = calcola({**MAIMONE, "larghezza": 8, "monconi": 3, "montanti_campata": 4, "rinforzi_v": False})
    q = {x["voce"]: x["qta"] for x in r["quantita"]}
    assert r["monconi"] == 3
    assert q["Monconi laterali (rinforzi a M)"] == 26 * 3 * 2      # archi x campate x 2 laterali
    assert q["Montanti frontali Z.C."] == 4 * 3 * 2               # 4 per campata x 3 campate x 2 frontali
    assert q["Rinforzi a V"] == 0
    assert calcola({**MAIMONE, "larghezza": 8})["monconi"] == 1   # automatico come il master
    assert calcola(MAIMONE)["monconi"] == 3                       # 9 m: rinforzi a M nel master


def test_porte():
    porte = [{"posizione": "Frontale A", "campata": 2, "larghezza": 2.4, "altezza": 2.3},
             {"posizione": "Laterale 1", "distanza": 20, "larghezza": 5, "altezza": 3}]
    r = calcola({**MAIMONE, "porte": porte})
    q = {x["voce"]: x["qta"] for x in r["quantita"]}
    assert q["Porta scorrevole"] == 2 and q["Fascioneria porta"] == 2
    assert any("saltapasso" in a["testo"] for a in r["avvisi"])
    assert {x["voce"]: x["qta"] for x in calcola({**MAIMONE, "porte": 3})["quantita"]}["Porta scorrevole"] == 3   # vecchio formato


def test_avvisi():
    testi = " ".join(a["testo"] for a in calcola({"larghezza": 9.5, "lunghezza": 51})["avvisi"])
    assert "fuori standard" in testi and "multipla del passo" in testi
    assert any("calcolo" in a["testo"] for a in calcola(MAIMONE, True)["avvisi"])


def test_dati_non_validi():
    assert c.post("/api/famiglie/serre/calcola", json={"valori": {"lunghezza": "abc"}}).status_code == 422
    assert c.get("/api/famiglie/capannoni/schema").status_code == 404


def test_zigzag_monconi_come_master():
    """tralicciatura a zig-zag (DWG 23129, 23138): V e moncone laterale hanno le lunghezze del master"""
    import math, disegno
    for w in (8, 9, 10):
        (sv, _, mo, rv, rm), _ = disegno.misure_arco(w)
        f = disegno.freccia_da_sviluppo(w * 1000, sv)
        nodi = disegno.nodi_zigzag(w * 1000, f, 3)
        assert abs(math.dist(nodi[0], nodi[1]) / 1000 - rv) < 0.01          # rinforzo V
        assert abs(math.dist(nodi[1], nodi[2]) / 1000 - rm) < 0.01          # moncone laterale (rinforzo M)
        assert nodi[2][0] > nodi[1][0]                                      # scende verso l'esterno: zig-zag
        assert abs(disegno.lunghezze_capriata(w, sv, 1)[0] - mo) < 0.12     # moncone centrale come il master
    r = calcola({**MAIMONE, "monconi": 3})
    assert any(x["voce"] == "Lunghezza moncone laterale (m)" and x["qta"] == 1.54 for x in r["quantita"])


def test_interasse_montanti_automatico():
    import disegno
    assert disegno.interasse_auto(8) == 2.4 and disegno.interasse_auto(9) == 3.0 and disegno.interasse_auto(10) == 3.33
    assert disegno.interasse_auto(9, 2.4) == 2.4


def test_due_porte_stessa_campata():
    porte = [{"posizione": "Frontale A", "campata": 1}, {"posizione": "Frontale A", "campata": 1}]
    assert any("ne compare una sola" in a["testo"] for a in calcola({**MAIMONE, "porte": porte})["avvisi"])


def test_larghezze_custom():
    """8,50 / 9,50 / 11: il master lascia vuote le misure dell'arco, il programma le interpola e le scrive"""
    import disegno, regole
    from app.famiglie import serre
    (sv, ti, mo, rv, rm), std = disegno.misure_arco(8.5)
    assert not std and sv == 9.43 and ti == 8.45 and mo == 1.55 and rv == 2.0 and rm == 1.5
    s = serre.serra({**MAIMONE, "larghezza": 8.5})
    A = regole.celle(s)[0]["Analisi Pesi"]
    assert A["K15"] == 9.43 and A["K33"] == 1.55 and A["K35"] == 4.0 and A["D37"] == 26 * 3 * 2 and A["K37"] == s.l_moncone_lat
    assert s.interasse_effettivo == 2.83
    A8 = regole.celle(serre.serra(MAIMONE | {"larghezza": 8}))[0]["Analisi Pesi"]
    assert "K15" not in A8                                   # larghezza standard: il master calcola da solo
    for w in (5.75, 7.25, 9.5, 11, 12.5):                   # il disegno si genera anche fuori tabella
        assert calcola({**MAIMONE, "larghezza": w})["h_colmo"] > 3.5


def test_montanti_per_frontale_e_campata():
    """righe per frontale/campata: la riga dopo vale sulla prima; stipiti porta contati come montanti"""
    righe = [{"frontale": "A e B", "campata": 0, "montanti": 4, "interasse": 0},     # tutte le campate: 4
             {"frontale": "Frontale B", "campata": 3, "montanti": 0, "interasse": 0}]  # B campata 3: nessuno
    r = calcola({**MAIMONE, "porte": [], "frontali_campate": righe})
    q = {x["voce"]: x["qta"] for x in r["quantita"]}
    assert q["Montanti frontali Z.C."] == 4 * 3 * 2 - 4
    porte = [{"posizione": "Frontale B", "campata": 3, "larghezza": 2.4, "altezza": 2.3}]
    r = calcola({**MAIMONE, "porte": porte, "frontali_campate": righe})
    assert {x["voce"]: x["qta"] for x in r["quantita"]}["Montanti frontali Z.C."] == 4 * 3 * 2 - 4 + 2
    assert any("stipiti" in a["testo"] for a in r["avvisi"])
    assert calcola({**MAIMONE, "frontali_campate": [{"frontale": "A e B", "campata": 7, "montanti": 4}]})["quantita"]  # campata inesistente: ignorata


def test_anteprima_porte_in_campate_diverse():
    porte = [{"posizione": "Frontale A", "campata": 1, "larghezza": 2.4, "altezza": 2.3},
             {"posizione": "Frontale A", "campata": 3, "larghezza": 3, "altezza": 2.5},
             {"posizione": "Frontale B", "campata": 2, "larghezza": 2.4, "altezza": 2.3}]
    righe = [{"frontale": "Frontale B", "campata": 1, "montanti": 4, "interasse": 0}]
    r = c.post("/api/famiglie/serre/anteprima", json={"valori": {**MAIMONE, "porte": porte, "frontali_campate": righe}})
    assert r.status_code == 200 and r.text.lstrip().startswith("<")
