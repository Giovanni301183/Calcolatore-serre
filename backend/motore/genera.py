"""Dalla Serra (dati maschera) genera: Excel computo compilato, DXF, DWG, riepilogo. Gli originali non vengono toccati."""
import os, re, subprocess, datetime, tempfile
import regole, disegno

APP = os.path.dirname(os.path.abspath(__file__))
USCITA = os.path.join(regole.BASE, "04_preventivi")
ACCORE = r"C:\Program Files\Autodesk\AutoCAD 2024\accoreconsole.exe"


def _cartella(s):
    nome = re.sub(r'[\\/:*?"<>|]+', "_", s.cliente or "senza_nome").strip()[:40]
    d = os.path.join(USCITA, f"{datetime.date.today():%Y%m%d}_{nome}_{s.c}x{s.W:g}x{s.L:g}")
    os.makedirs(d, exist_ok=True)
    return d


def excel(s, cartella):
    master, w_master = regole.MASTER, s.W
    fogli, righe = regole.celle(s)
    tmp = os.path.join(cartella, "_celle.txt")
    with open(tmp, "w", encoding="utf-16") as f:
        for foglio, cel in fogli.items():
            for k, v in cel.items():
                f.write(f"{foglio}\t{k}\t{'N' if isinstance(v, (int, float)) else 'S'}\t{v}\n")
    out = os.path.join(cartella, f"Computo {s.c}x{s.W:g}x{s.L:g} {s.copertura} {s.finestra}.xls")
    riep = os.path.join(cartella, "_totali.txt")
    subprocess.run(["cscript", "//nologo", os.path.join(APP, "compila.vbs"), master, out, tmp, riep],
                   check=True, capture_output=True, timeout=180)
    tot = {}
    num = lambda v: float(v.replace(",", ".")) if re.match(r"^-?[\d.,]+(E[-+]?\d+)?$", v.strip()) else None
    if os.path.exists(riep):
        for line in open(riep, encoding="utf-16"):
            p = line.rstrip("\n").split("\t")
            if p[0] == "peso_kg": tot["peso_kg"] = num(p[1])
            elif p[0] == "ricarico": tot["ricarico"] = num(p[1])
            elif p[0] == "voce" and len(p) >= 6:                  # riga struttura: costo €/kg, prezzo €/kg, prezzo riga
                ck, pk, ab = num(p[3]), num(p[4]), num(p[5])
                if ab and pk:
                    kg = ab / pk
                    tot.setdefault("voci_struttura", []).append(
                        {"riga": int(p[1]), "voce": re.sub(r"\s+", " ", p[2]).strip(), "kg": kg, "costo_kg": ck or 0,
                         "costo": kg * (ck or 0), "prezzo_master": ab})
            elif p[0] == "ps" and len(p) >= 5:                     # pezzi speciali: descrizione, q.tà, prezzo unit., costo
                q, u, c = num(p[2]), num(p[3]), num(p[4])
                if q:
                    tot.setdefault("pezzi_speciali", []).append(
                        {"voce": re.sub(r"\s+", " ", p[1]).strip(), "qta": q, "unitario": u or 0, "costo": c or 0})
            elif p[0] == "ps_totale": tot["ps_totale"] = num(p[1])
            elif p[0].startswith("col") and len(p) >= 5:
                v, sopra, destra, formula = num(p[1]), p[2].upper(), p[3], p[4].upper()
                if v is None: continue
                if "PEZZI SPECIALI" in formula: tot["pezzi_speciali_eur"] = v
                elif "/M²" in destra.upper() or "/M2" in destra.upper() or "/D7" in formula:
                    tot.setdefault("eur_m2_list", []).append(v)
                elif "TOTALE" in sopra: tot["totale_eur"] = v
                elif "SUM(Z" in formula or "SUM(AB" in formula: tot["struttura_eur"] = v
                elif "SUM(O15" in formula: tot["materiale_eur"] = v
                elif "SUM(X15" in formula: tot["materiale_ricaricato_eur"] = v
    if tot.get("eur_m2_list"): tot["eur_m2"] = tot["eur_m2_list"][-1]
    if "totale_eur" not in tot and "struttura_eur" in tot:
        tot["totale_eur"] = tot["struttura_eur"] + tot.get("pezzi_speciali_eur", 0)
    os.remove(tmp)
    return out, master, w_master, righe, tot


def dwg(dxf_path):
    """converte il DXF in DWG con AutoCAD Core Console (se presente)"""
    if not os.path.exists(ACCORE): return None
    out = os.path.splitext(dxf_path)[0] + ".dwg"
    scr = os.path.join(tempfile.gettempdir(), "tn_saveas.scr")
    with open(scr, "w", encoding="ascii") as f:
        f.write(f'_.SAVEAS\n2018\n"{out}"\n_.QUIT\n_Y\n')
    try:
        subprocess.run([ACCORE, "/i", dxf_path, "/s", scr, "/l", "it-IT"], capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None
    return out if os.path.exists(out) else None


def pdf(dwg_path):
    """stampa il DWG in PDF A3 (vista salvata) con AutoCAD Core Console"""
    if not dwg_path or not os.path.exists(ACCORE): return None
    out = os.path.splitext(dwg_path)[0] + ".pdf"
    scr = os.path.join(tempfile.gettempdir(), "tn_plot.scr")
    with open(scr, "w", encoding="ascii") as f:
        f.write("-PLOT\nY\nModel\nDWG To PDF.pc3\nISO full bleed A3 (420.00 x 297.00 MM)\nM\nL\nN\nD\nF\nC\nY\n"
                f'monochrome.ctb\nY\nA\n"{out}"\nN\nY\n_.QUIT\n_Y\n')
    try:
        subprocess.run([ACCORE, "/i", dwg_path, "/s", scr, "/l", "it-IT"], capture_output=True, timeout=150)
    except subprocess.TimeoutExpired:
        return None
    return out if os.path.exists(out) else None


def genera(s):
    d = _cartella(s)
    xls, master, w_master, righe, tot = excel(s, d)
    dxf = disegno.genera(s, os.path.join(d, f"Disegno {s.c}x{s.W:g}x{s.L:g}.dxf"))
    dw = dwg(dxf)
    pdf(dw)
    lines = [s.titolo(), f"Cliente: {s.cliente}  {s.localita}",
             f"Copertura {s.copertura}, finestra {s.finestra}, fungo {'sì' if s.fungo else 'no'}, pilastri {s.pilastri}",
             f"Passo {s.p} m - archi per campata {s.N} - H gronda {s.h_gronda} m - H colmo {s.h_colmo} m",
             f"Fondazione: {s.fondazione} - pilastro interrato {s.interramento} m (opere in cls/c.a. NON incluse nel computo)", "",
             f"Master usato: {os.path.basename(master)}", "",
             "QUANTITÀ INSERITE DAL PROGRAMMA (il resto lo calcola il master):"]
    for voce, q, reg, af in righe:
        lines.append(f"  {voce:40} {q:>8}   [{reg}; affidabilità {af}]")
    if tot:
        lines += ["", "TOTALI (calcolati da Excel con i prezzi del master):",
                  f"  Peso struttura: {tot.get('peso_kg', 0):,.0f} kg",
                  f"  Struttura: € {tot.get('struttura_eur', 0):,.2f}   Pezzi speciali: € {tot.get('pezzi_speciali_eur', 0):,.2f}",
                  f"  TOTALE: € {tot.get('totale_eur', 0):,.2f}   (€ {tot.get('eur_m2', 0):,.2f} / m²)",
                  "  NB: nei Pezzi Speciali gaffe, bulloneria, motoriduttori e quadri restano quelli del master: controllare."]
    with open(os.path.join(d, "Riepilogo.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return {"cartella": d, "excel": xls, "dxf": dxf, "dwg": dw, "totali": tot, "righe": righe, "master": master}


if __name__ == "__main__":
    import sys, json
    prove = [regole.Serra(2, 10, 45, 2.5, "Nylon", "Tendina", cliente="PROVA GENNA SAMUELE"),
             regole.Serra(2, 9, 40, 2.5, "Policarbonato", "Nessuna", laterali_aperti=True, frontali_aperti=True, cliente="PROVA MARINO ACCURSIO"),
             regole.Serra(4, 9, 20, 2.5, "Nylon", "Tendina", cliente="PROVA ANTONIO LALA")]
    for s in prove:
        r = genera(s)
        print(s.cliente, json.dumps(r["totali"], ensure_ascii=False), r["dwg"] is not None)
