"""
Mit NEM gyűjtünk: ruházat és lábbeli (az oldal fegyverekre és kiegészítőkre fókuszál).
A védő- és taktikai felszerelés (szemüveg, maszk, kesztyű, mellény, tasak, tok, sisak) marad.
URL-re (letöltés előtt, időt spórol) és címre (letöltés után) is alkalmazzuk. Csak stdlib.
"""
from __future__ import annotations

import re

_CLOTHING = [
    # en
    r"clothing", r"apparel", r"uniforms?", r"trousers", r"pants", r"t-?shirts?", r"shirts?", r"hoodies?", r"sweatshirts?",
    r"jackets?", r"softshell", r"fleece", r"boots", r"shoes", r"footwear", r"sneakers", r"socks", r"beanies?",
    r"baseball[- ]cap", r"boonie", r"underwear", r"combat[- ]shirt", r"bdu", r"acu",
    # hu
    r"ruha\w*", r"ruházat\w*", r"nadrág\w*", r"póló\w*", r"kabát\w*", r"dzseki\w*", r"bakancs\w*", r"cipő\w*",
    r"zokni\w*", r"egyenruha\w*", r"pulóver\w*", r"ing(?:ek)?",
    # pl
    r"odzie[żz]\w*", r"mundur\w*", r"spodnie", r"koszul\w*", r"kurtk\w*", r"buty", r"obuwie", r"bluz\w*", r"czapk\w*",
    # de
    r"bekleidung", r"kleidung", r"hemd\w*", r"jacke\w*", r"stiefel", r"schuhe", r"socken", r"mütze\w*",
    # fr
    r"v[eê]tements?", r"pantalons?", r"chemises?", r"chaussures?", r"rangers", r"casquettes?", r"blousons?",
    # cs / sk
    r"oble[cč]en[ií]", r"kalhoty", r"ko[sš]ile", r"bundy?", r"boty", r"pono[zž]ky", r"[cč]epice", r"uniformy",
    # es / it / nl
    r"ropa", r"camisetas?", r"chaquetas?", r"botas", r"zapatos", r"abbigliamento", r"pantaloni", r"giacca", r"scarpe",
    r"stivali", r"kleding", r"broeken?", r"schoenen", r"laarzen", r"jassen",
]
CLOTHING_RX = re.compile(r"(?<![a-z0-9])(?:" + "|".join(_CLOTHING) + r")(?![a-z0-9])", re.I)


def is_clothing(*texts: str | None) -> bool:
    """URL-ben a kötőjeles/perjeles szavakat is nézi (pl. /uniforms-and-clothing-396.html)."""
    return any(t and CLOTHING_RX.search(t.replace("-", " ").replace("_", " ").replace("/", " ")) for t in texts)
