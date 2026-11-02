"""Registro delle famiglie di prodotto mostrate nella home.
Per aggiungere una famiglia configurabile: un modulo con schema(), calcola(), anteprima_svg(), genera_documenti()
e una riga in TESSERE. Le famiglie a voci libere (lavori speciali) usano un percorso dedicato."""
from . import serre

MODULI = {serre.ID: serre}

TESSERE = [
    {"id": "serre", "nome": "Serre ad arco", "descrizione": "Monocampata e multicampata, nylon, rigida, policarbonato", "icona": "serra", "attiva": True, "calcolo": True},
    {"id": "capannoni", "nome": "Capannoni e tettoie", "descrizione": "Strutture in IPE/HEA e scatolari", "icona": "capannone", "attiva": False, "calcolo": True, "nota": "Fase 4 — intanto usa Lavori speciali"},
    {"id": "speciali", "nome": "Lavori speciali", "descrizione": "Preventivo a voci libere dal listino, con margini", "icona": "speciale", "attiva": True, "calcolo": False, "percorso": "/speciali/nuovo"},
    {"id": "tunnel", "nome": "Tunnel", "descrizione": "Tunnel monocampata", "icona": "tunnel", "attiva": False, "calcolo": False, "nota": "Fase 4"},
    {"id": "ombrai", "nome": "Ombrai / antigrandine", "descrizione": "Strutture a rete", "icona": "ombraio", "attiva": False, "calcolo": False, "nota": "Fase 4"},
    {"id": "fotovoltaico", "nome": "Fotovoltaico", "descrizione": "Strutture e pensiline FV", "icona": "sole", "attiva": False, "calcolo": True, "nota": "Fase 4"},
]
