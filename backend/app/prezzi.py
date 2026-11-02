"""Motore prezzi: dai costi (per categoria) al prezzo cliente con le marginalità desiderate.

Convenzione: MARGINE sul prezzo -> prezzo = costo / (1 - margine).
Il master Excel usa un RICARICO sul costo (x1,6 = +60%), che equivale a un margine del 37,5%."""
import os, re

CATEGORIE = [
    {"id": "struttura", "nome": "Struttura metallica zincata", "descrizione": "Archi, pilastri, tiranti, correntini, grondaie… (costo €/kg del master)"},
    {"id": "pezzi_speciali", "nome": "Accessori e pezzi speciali", "descrizione": "Gaffe, porte, staffe, giunti, bulloneria, motorizzazioni"},
    {"id": "copertura", "nome": "Copertura", "descrizione": "Film, lastre, policarbonato"},
    {"id": "montaggio", "nome": "Montaggio", "descrizione": "Manodopera in cantiere"},
    {"id": "trasporto", "nome": "Trasporto", "descrizione": "Viaggi fino al cantiere"},
    {"id": "progettazione", "nome": "Progettazione e calcolo strutturale", "descrizione": "Relazione di calcolo, pratiche"},
    {"id": "altro", "nome": "Altro", "descrizione": "Voci libere"},
]
NOMI = {c["id"]: c["nome"] for c in CATEGORIE}

# Valori di partenza: DA CONFERMARE con la direzione (modificabili da Impostazioni)
DEFAULT = {
    "margini": {"struttura": 37.5, "pezzi_speciali": 30.0, "copertura": 25.0, "montaggio": 25.0, "trasporto": 10.0, "progettazione": 30.0, "altro": 25.0},
    "margine_minimo": 20.0,          # sotto questa soglia l'offerta richiede approvazione
    "margine_attenzione": 28.0,      # tra minimo e attenzione: semaforo giallo
    "sconto_max_commerciale": 5.0,   # % di sconto concedibile senza approvazione
    "montaggio_eur_m2": 0.0,         # 0 = non incluso finché non viene definito
    "trasporto_eur_viaggio": 0.0,
    "kg_per_viaggio": 12000.0,
    "progettazione_eur": 0.0,
    "validita_giorni": 30,
    "condizioni_pagamento": "30% all'ordine, 60% alla consegna dei materiali, 10% a fine lavori",
    "da_confermare": True,
}


def impostazioni(salvate: dict):
    out = {**DEFAULT, **(salvate or {})}
    out["margini"] = {**DEFAULT["margini"], **(salvate or {}).get("margini", {})}
    return out


def r2(x):
    return round(float(x or 0), 2)


def costi_da_master(tot: dict):
    """converte l'export del master (genera.excel) in righe di costo unificate"""
    righe = []
    for v in tot.get("voci_struttura", []):
        righe.append({"categoria": "struttura", "voce": v["voce"].title(), "qta": r2(v["kg"]), "unita": "kg",
                      "costo_unitario": v["costo_kg"], "costo": r2(v["costo"]), "fonte": f"master riga {v['riga']}"})
    for v in tot.get("pezzi_speciali", []):
        righe.append({"categoria": "pezzi_speciali", "voce": v["voce"].capitalize(), "qta": v["qta"], "unita": "cad",
                      "costo_unitario": v["unitario"], "costo": r2(v["costo"]), "fonte": "master Pezzi Speciali"})
    return righe


def calcola(costi: list, scelte: dict, imp: dict, area_m2=None, peso_kg=None, con_calcolo=False, riferimento_master=None):
    """costi: righe [{categoria, costo}]; scelte: {margini, montaggio_eur_m2, trasporto_eur_viaggio, viaggi, progettazione_eur, sconto_pct}"""
    scelte = scelte or {}
    margini = {**imp["margini"], **(scelte.get("margini") or {})}
    righe = [dict(r) for r in costi]

    # voci aggiunte dalle scelte (solo se la famiglia non le ha già come righe)
    cats_presenti = {r["categoria"] for r in righe}
    extra = []
    if area_m2 and "montaggio" not in cats_presenti:
        eur = float(scelte.get("montaggio_eur_m2", imp["montaggio_eur_m2"]) or 0)
        if eur:
            extra.append({"categoria": "montaggio", "voce": f"Montaggio ({r2(area_m2)} m² x € {eur:g}/m²)", "costo": r2(area_m2 * eur)})
    if "trasporto" not in cats_presenti:
        eur_v = float(scelte.get("trasporto_eur_viaggio", imp["trasporto_eur_viaggio"]) or 0)
        viaggi = scelte.get("viaggi")
        if viaggi in (None, ""):
            viaggi = max(1, -(-float(peso_kg or 0) // float(imp["kg_per_viaggio"] or 1))) if peso_kg else 1
        if eur_v:
            extra.append({"categoria": "trasporto", "voce": f"Trasporto ({int(viaggi)} viaggi x € {eur_v:g})", "costo": r2(eur_v * int(viaggi))})
    if con_calcolo and "progettazione" not in cats_presenti:
        eur = float(scelte.get("progettazione_eur", imp["progettazione_eur"]) or 0)
        extra.append({"categoria": "progettazione", "voce": "Progettazione e calcolo strutturale", "costo": r2(eur)})
    righe += extra

    per_cat = {}
    for r in righe:
        per_cat.setdefault(r["categoria"], 0.0)
        per_cat[r["categoria"]] += float(r.get("costo") or 0)

    categorie = []
    for c in CATEGORIE:
        if c["id"] not in per_cat:
            continue
        costo = per_cat[c["id"]]
        m = min(max(float(margini.get(c["id"], 0)), 0), 95)
        prezzo = costo / (1 - m / 100)
        categorie.append({"id": c["id"], "nome": c["nome"], "costo": r2(costo), "margine": m, "prezzo": r2(prezzo),
                          "ricarico": r2((prezzo / costo - 1) * 100) if costo else 0})

    costo_tot = sum(c["costo"] for c in categorie)
    listino = sum(c["prezzo"] for c in categorie)
    sconto_pct = min(max(float(scelte.get("sconto_pct") or 0), 0), 50)
    sconto = listino * sconto_pct / 100
    finale = listino - sconto
    margine = (finale - costo_tot) / finale * 100 if finale else 0

    avvisi = []
    if margine < imp["margine_minimo"]:
        semaforo = "rosso"
        avvisi.append(f"Margine {margine:.1f}% sotto il minimo ({imp['margine_minimo']:g}%): serve l'approvazione della direzione.")
    elif margine < imp["margine_attenzione"]:
        semaforo = "giallo"
    else:
        semaforo = "verde"
    if sconto_pct > imp["sconto_max_commerciale"]:
        avvisi.append(f"Sconto {sconto_pct:g}% oltre il massimo concedibile dal commerciale ({imp['sconto_max_commerciale']:g}%).")
    if "montaggio" not in per_cat:
        avvisi.append("Montaggio non incluso (costo €/m² non impostato).")
    if "trasporto" not in per_cat:
        avvisi.append("Trasporto non incluso (costo a viaggio non impostato).")
    if con_calcolo and per_cat.get("progettazione", 0) == 0:
        avvisi.append("Con calcolo strutturale: il costo di progettazione è a zero.")
    if imp.get("da_confermare"):
        avvisi.append("Margini e soglie sono valori di partenza da confermare con la direzione (Impostazioni).")

    return {
        "righe": righe, "categorie": categorie,
        "costo_totale": r2(costo_tot), "prezzo_listino": r2(listino), "sconto_pct": sconto_pct, "sconto": r2(sconto),
        "prezzo_finale": r2(finale), "margine_reale": round(margine, 2),
        "ricarico_equivalente": round((finale / costo_tot - 1) * 100, 2) if costo_tot else 0,
        "eur_m2": r2(finale / area_m2) if area_m2 else None,
        "semaforo": semaforo, "richiede_approvazione": margine < imp["margine_minimo"] or sconto_pct > imp["sconto_max_commerciale"],
        "riferimento_master": r2(riferimento_master) if riferimento_master else None,
        "avvisi": avvisi,
    }


# ---------------- listino iniziale dal master 2026 ----------------

def listino_da_master(master_path):
    """legge i costi unitari dal master 2026: €/kg delle voci di struttura (col. X) e prezzi dei pezzi speciali"""
    import xlrd
    righe = []
    b = xlrd.open_workbook(master_path, on_demand=True)
    sh = b.sheet_by_name("Analisi Pesi")
    desc = ""
    for r in range(14, min(sh.nrows, 106)):
        a, d = str(sh.cell_value(r, 0)).strip(), re.sub(r"\s+", " ", str(sh.cell_value(r, 1))).strip()
        if a and d:
            desc = d
        x = sh.cell_value(r, 23)
        if isinstance(x, float) and x > 0 and desc:
            sez = " ".join(str(sh.cell_value(r, c)) for c in range(4, 9) if str(sh.cell_value(r, c)).strip())
            righe.append({"categoria": "struttura", "voce": desc.title(), "unita": "kg", "costo": round(x, 4),
                          "fonte": f"Master 2026, riga {r + 1} (materia {sh.cell_value(r, 14)} €/kg + manod. {sh.cell_value(r, 17)}%)" + (f" — {sez[:40]}" if sez else "")})
    ps = b.sheet_by_name("Pezzi Speciali")
    for r in range(9, ps.nrows):
        if "TOTALE" in str(ps.cell_value(r, 4)).upper():
            break
        d, u = re.sub(r"\s+", " ", str(ps.cell_value(r, 1))).strip(), ps.cell_value(r, 3)
        if d and isinstance(u, float):
            righe.append({"categoria": "pezzi_speciali", "voce": d.capitalize(), "unita": "cad", "costo": u,
                          "fonte": f"Master 2026, Pezzi Speciali riga {r + 1}", "da_confermare": True})
    righe += [
        {"categoria": "montaggio", "voce": "Montaggio serra (squadra)", "unita": "m²", "costo": 0, "fonte": "da definire", "da_confermare": True},
        {"categoria": "montaggio", "voce": "Squadra di montaggio", "unita": "giorno", "costo": 0, "fonte": "da definire", "da_confermare": True},
        {"categoria": "trasporto", "voce": "Viaggio bilico", "unita": "viaggio", "costo": 0, "fonte": "da definire", "da_confermare": True},
        {"categoria": "progettazione", "voce": "Relazione di calcolo strutturale", "unita": "corpo", "costo": 0, "fonte": "da definire", "da_confermare": True},
        {"categoria": "struttura", "voce": "Lavorazione carpenteria (taglio, foratura, saldatura)", "unita": "ora", "costo": 0, "fonte": "da definire", "da_confermare": True},
        {"categoria": "struttura", "voce": "Zincatura a caldo", "unita": "kg", "costo": 0, "fonte": "da definire", "da_confermare": True},
    ]
    return righe
