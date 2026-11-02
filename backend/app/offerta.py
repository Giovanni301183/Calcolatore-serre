"""PDF dell'offerta al cliente (HTML -> PDF con PyMuPDF, nessuna dipendenza esterna).
Mostra i prezzi per categoria, MAI costi e margini."""
import datetime, html, os
import pymupdf

INTESTAZIONE = {
    "ragione": "TERRANOVA S.r.l. — Costruzioni metalmeccaniche",
    "indirizzo": "C.da S. Silvestro, 457/C — 91025 Marsala (TP)",
    "contatti": "Tel. +39 0923 990606 / 990786",
}

CSS = """
* { font-family: sans-serif; }
body { font-size: 10pt; color: #1d2420; }
h1 { font-size: 15pt; color: #1c4125; margin: 0 0 2pt 0; }
h2 { font-size: 11pt; color: #1c4125; margin: 14pt 0 4pt 0; border-bottom: 1px solid #b9cdbd; }
.small { font-size: 8.5pt; color: #555; }
table { width: 100%; border-collapse: collapse; }
td, th { padding: 4pt 5pt; vertical-align: top; }
th { text-align: left; background-color: #e4efe6; font-size: 9pt; }
.r { text-align: right; }
.tot td { font-weight: bold; border-top: 1.5px solid #1c4125; }
.box { background-color: #fff6e0; border: 1px solid #e0b84f; padding: 6pt; margin-top: 8pt; }
"""


def _eur(v):
    return "€ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _porte(cfg):
    from .famiglie.serre import porte_da_valori
    c, L = int(float(cfg.get("campate", 1))), float(cfg.get("lunghezza", 0))
    porte = porte_da_valori(cfg, c, L)
    if not porte:
        return "Nessuna porta."
    fm = lambda x: f"{x:.2f}".replace(".", ",")
    det = "; ".join(f"{d['posizione'].lower()}" + (f" (campata {d['campata']})" if d["posizione"].startswith("Frontale") else "")
                    + f" da m {fm(d['larghezza'])} x {fm(d['altezza'])}" for d in porte)
    return html.escape(f"N. {len(porte)} port{'a' if len(porte) == 1 else 'e'} scorrevol{'e' if len(porte) == 1 else 'i'}: {det}.")


def descrizione_serra(cfg: dict, titolo: str):
    e = lambda x: html.escape(str(x))
    finestre = cfg.get("finestra", "Tendina")
    righe = [
        f"<b>{e(titolo)}</b>",
        f"Struttura ad arco in tubolari di acciaio zincato, {e(cfg.get('campate'))} campat{'e' if int(cfg.get('campate', 1)) > 1 else 'a'} "
        f"da m {e(cfg.get('larghezza'))}, lunghezza m {e(cfg.get('lunghezza'))}, passo archi m {e(cfg.get('passo'))}.",
        f"Altezza in gronda m {e(cfg.get('h_gronda'))}. Pilastri {e(cfg.get('pilastri', '')).lower()}.",
        f"Copertura: {e(cfg.get('copertura'))}.",
        f"Aperture laterali: {'nessuna (laterali aperti)' if cfg.get('laterali_aperti') else e(finestre).lower()}"
        f"{'; finestra a fungo al colmo' if cfg.get('fungo') else ''}{'; ali di gabbiano' if cfg.get('ali_gabbiano') else ''}.",
        _porte(cfg),
        f"Fondazioni previste: {e(cfg.get('fondazione'))} (opere edili escluse salvo diversa indicazione).",
    ]
    return "<br/>".join(righe)


def genera_pdf(p: dict, risultato: dict, imp: dict, path: str):
    oggi = datetime.date.today()
    cfg = p.get("configurazione") or {}
    if p["famiglia"] == "serre":
        desc = descrizione_serra(cfg, p.get("titolo") or "")
    else:
        desc = f"<b>{html.escape(p.get('titolo') or '')}</b><br/>" + html.escape(p.get("descrizione") or "").replace("\n", "<br/>")

    righe_tab = "".join(
        f"<tr><td>{html.escape(c['nome'])}</td><td class='r'>{_eur(c['prezzo'])}</td></tr>" for c in risultato["categorie"] if c["prezzo"] > 0)
    sconto = (f"<tr><td>Sconto {risultato['sconto_pct']:g}%</td><td class='r'>- {_eur(risultato['sconto'])}</td></tr>"
              if risultato["sconto"] else "")
    esclusi = [c for c in ("montaggio", "trasporto") if c not in {x["id"] for x in risultato["categorie"]}]
    prelim = ("<div class='box'><b>OFFERTA PRELIMINARE</b> — la struttura è soggetta a calcolo strutturale: profili, quantità e prezzi "
              "potranno variare a seguito della verifica dell'ufficio tecnico.</div>") if p.get("con_calcolo") else ""

    corpo = f"""
    <table><tr>
      <td><h1>TERRANOVA</h1><span class='small'>{INTESTAZIONE['ragione']}<br/>{INTESTAZIONE['indirizzo']}<br/>{INTESTAZIONE['contatti']}</span></td>
      <td class='r'><b>OFFERTA N. {html.escape(p.get('numero') or '')}{' rev.' + str(p['versione']) if p.get('versione', 1) > 1 else ''}</b><br/>
          Marsala, {oggi:%d/%m/%Y}</td>
    </tr></table>
    <h2>Spett.le</h2>
    <p><b>{html.escape(p.get('cliente') or '')}</b><br/>{html.escape(p.get('localita') or '')}</p>
    <h2>Oggetto: fornitura {('e posa in opera ' if 'montaggio' not in esclusi else '')}{html.escape((p.get('titolo') or '').lower())}</h2>
    <p>{desc}</p>
    {prelim}
    <h2>Offerta economica</h2>
    <table>
      <tr><th>Descrizione</th><th class='r'>Importo</th></tr>
      {righe_tab}
      {sconto}
      <tr class='tot'><td>TOTALE (IVA esclusa)</td><td class='r'>{_eur(risultato['prezzo_finale'])}</td></tr>
    </table>
    {"<p class='small'>Pari a " + _eur(risultato['eur_m2']) + " al m².</p>" if risultato.get('eur_m2') else ""}
    <h2>Condizioni</h2>
    <p class='small'>
      Validità dell'offerta: {imp.get('validita_giorni', 30)} giorni dalla data.<br/>
      Pagamento: {html.escape(str(imp.get('condizioni_pagamento', '')))}.<br/>
      Esclusi: {', '.join(esclusi + ['opere edili e fondazioni', 'allacci elettrici e idrici', 'pratiche autorizzative salvo dove indicato'])}. IVA a carico del committente.<br/>
      Tempi di consegna: da concordare all'ordine.
    </p>
    {"<p class='small'>Allegato: disegno di massima.</p>" if p['famiglia'] == 'serre' else ''}
    <br/><table><tr><td class='small'>Per accettazione (timbro e firma)<br/><br/>______________________</td>
    <td class='r small'>TERRANOVA S.r.l.<br/><br/>______________________</td></tr></table>
    """
    story = pymupdf.Story(html=corpo, user_css=CSS)
    writer = pymupdf.DocumentWriter(path)
    pagina = pymupdf.paper_rect("a4")
    area = pagina + (45, 40, -45, -50)
    altro = 1
    while altro:
        dev = writer.begin_page(pagina)
        altro, _ = story.place(area)
        story.draw(dev)
        writer.end_page()
    writer.close()

    # numeri di pagina (e filigrana se preliminare)
    doc = pymupdf.open(path)
    for i, pg in enumerate(doc):
        pg.insert_text((pagina.width - 90, pagina.height - 25), f"Pagina {i + 1} di {len(doc)}", fontsize=8, color=(0.4, 0.4, 0.4))
        if p.get("con_calcolo"):
            pg.insert_text((130, 560), "PRELIMINARE", fontsize=80, rotate=0, color=(0.93, 0.9, 0.82), overlay=False,
                           morph=(pymupdf.Point(300, 450), pymupdf.Matrix(1, 1).prerotate(35)))
    doc.saveIncr()
    doc.close()
    return path


def nome_file(p):
    return f"Offerta {(p.get('numero') or '').replace('/', '-')}{' rev' + str(p['versione']) if p.get('versione', 1) > 1 else ''}.pdf"
