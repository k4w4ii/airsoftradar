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


# ---------------------------------------------------------------------------------------------
# Alkatrész / kiegészítő felismerése a címből. A párosító ezzel akadályozza meg, hogy egy tár vagy
# alkatrész („Magazine for CM.041K”) a fegyver modellkódja alapján a fegyverhez kerüljön.
# Szigorú lista: csak egyértelmű szavak (a stock/grip/rail/slide/barrel fegyverneveben is előfordul).
# Ugyanez a logika SQL-ben: supabase/migrations/0010 (airsoft_category).
_PART = [
    # tárak, töltények
    r"magazines?", r"mags?", r"hi-?caps?", r"mid-?caps?", r"low-?caps?", r"drum ?mags?", r"t[aá]r(?:ak|at|ral)?",
    r"z[aá]sobn[ií]k\w*", r"magazyn\w*", r"chargeurs?", r"magazin(?:e|es)?", r"cargador\w*", r"caricator\w*", r"shells?",
    # akku, töltő
    r"batter(?:y|ies)", r"akku\w*", r"akkumul[aá]tor\w*", r"bateri[ea]\w*", r"akumul[aá]tor\w*", r"batterie\w*",
    r"li-?po", r"li-?ion", r"li-?fe", r"nimh", r"chargers?", r"t[oö]lt[oő]\w*", r"nab[ií]je[cč]k\w*", r"[lł]adowar\w*",
    # optika
    r"scopes?", r"c[eé]lt[aá]vcs[oő]\w*", r"red ?dots?", r"holo(?:graphic)? ?sights?", r"kolim[aá]tor\w*", r"celownik\w*",
    r"zam[eě][rř]ova[cč]\w*", r"magnifiers?", r"optics?",
    # gearbox, belső alkatrészek
    r"gearbox\w*", r"mechabox\w*", r"gear ?sets?", r"gears", r"fogasker[eé]k\w*", r"pistons?", r"piston ?heads?",
    r"dugatty[uú]\w*", r"cylinders?", r"cylinder ?heads?", r"nozzles?", r"tappet\w*", r"spring ?guides?",
    r"rug[oó]vezet[oő]\w*", r"bushings?", r"bearings?", r"anti-?reversal", r"selector ?plates?", r"air ?seal\w*",
    r"o-?rings?", r"(?:main|aeg|upgrade|gearbox|power|valve|nozzle|hammer|recoil|tappet|trigger) ?springs?",
    r"springs? (?:m|sp)\d{2,3}", r"(?:m|sp)\d{2,3} ?springs?", r"rug[oó]", r"pru[zž]in\w*", r"spr[eę][zż]yn\w*",
    # hop-up, belső cső
    r"hop-?up\w*", r"bucking\w*", r"inner ?barrels?", r"bels[oő] ?cs[oő]\w*", r"precision ?barrels?", r"tight ?bore",
    r"r-?hop", r"hop ?chambers?",
    # motor, elektronika
    r"motors?", r"mosfet\w*", r"wiring",
    # védő- és taktikai felszerelés, egyéb
    r"masks?", r"maszk\w*", r"goggles?", r"szem[uü]veg\w*", r"helmets?", r"sisak\w*", r"holsters?", r"pisztolytok\w*",
    r"pouch\w*", r"tasak\w*", r"slings?", r"heveder\w*", r"vests?", r"mell[eé]ny\w*", r"plate ?carriers?",
    r"chest ?rigs?", r"backpacks?", r"h[aá]tizs[aá]k\w*", r"(?:gun|rifle|pistol|hard|soft|transport) ?(?:cases?|bags?)",
    r"fegyvert[aá]sk\w*", r"kufr\w*", r"pouzdr\w*", r"futera[lł]\w*", r"pokrowi\w*",
    r"bbs?", r"\d[.,]\d{2} ?g", r"goly[oó]\w*", r"kuli[cč]k\w*", r"kulki", r"kulek", r"billes", r"kugeln", r"pallini",
    r"green ?gas", r"top ?gas", r"propane", r"co2 ?(?:cartridges?|capsules?|patron\w*|bombi[cč]k\w*|kapsu[lł]\w*)",
    r"g[aá]z ?palack\w*", r"speed ?loaders?", r"bb ?loaders?", r"targets?", r"c[eé]lt[aá]bl\w*", r"chrono\w*",
    r"tracers?", r"suppressors?", r"silencers?", r"hangtomp[ií]t[oó]\w*", r"tlumi[cč]\w*", r"flash ?hiders?",
    r"flashlights?", r"l[aá]mp[aá]\w*", r"bipods?", r"villal[aá]b\w*", r"mounts?", r"cleaning", r"silicone? ?oil",
    r"szilikon\w*", r"grease",
]
PART_RX = re.compile(r"(?<![\w])(?:" + "|".join(_PART) + r")(?![\w])", re.I)
# „vele járó” részek levágása: „M4 AEG with battery and charger”, „Glock 17 + 2 magazines”
BUNDLE_RX = re.compile(r"(?:\s\+|(?<![\w])(?:with|w/|incl\.?|including|included|mit|avec|con|com|v[cč]etn[eě]|v[cč]\.|plus|[eé]s|w zestawie|z zestawem|set with)(?![\w])).*$", re.I)
# fegyverre utaló szavak (főnév vagy rendszer)
WEAPON_RX = re.compile(r"(?<![\w])(?:aeg|aep|gbbr?|nbb|hpa|ebb|rifles?|carbines?|karab[eé]ly\w*|karabin\w*|puska\w*|pu[sš]k\w*|"
                       r"pistols?|pistole\w*|pistolet\w*|pistola\w*|pisztoly(?!tok)\w*|replica\w*|replik\w*|r[eé]plique\w*|"
                       r"gewehr\w*|fusil\w*|zbra[nň]\w*|shotguns?|s[oö]r[eé]tes|brokovnic\w*|samopal\w*|submachine|smg|lmg|"
                       r"sniper|revolver\w*)(?![\w])", re.I)
# „X-hez”, „for X”: biztosan alkatrész/kiegészítő
FOR_RX = re.compile(r"(?<![\w])(?:for|do|pro|f[uü]r|pour|per|para|compatible|kompatib\w*|\w+(?:hoz|hez|h[oö]z))(?![\w])", re.I)
WEAPON_MIN_HUF = 30000


def is_part(title: str | None, price_huf: float | None = None) -> bool:
    """Igaz, ha a cím alkatrészt/kiegészítőt jelöl (nem fegyvert). A csomag-részeket („with battery”) figyelmen kívül hagyja.
    Ha fegyverszó is van és az ár fegyverár (>= 30 000 Ft), fegyvernek tekinti – kivéve „for X / X-hez” alakban."""
    if not title:
        return False
    core = BUNDLE_RX.sub("", title.replace("_", " "))
    m = PART_RX.search(core)
    if not m:
        return False
    if FOR_RX.search(core):
        return True
    if WEAPON_RX.search(core) and price_huf is not None and price_huf >= WEAPON_MIN_HUF:
        return False
    return True


# ---------------------------------------------------------------------------------------------
# Egyedi / átépített változat („Evike Custom CYMA CM048 ... with Wolverine Inferno HPA System”):
# ugyanaz a modellkód, de más termék és más árkategória. Ilyen ajánlat csak ilyen termékhez párosulhat.
# Ugyanez SQL-ben: supabase/migrations/0011 (airsoft_is_variant).
VARIANT_RX = re.compile(
    r"(?<![\w])(?:custom|hpa|wolverine|polarstar|inferno|fusion ?engine|jack ?engine|tuned|tuning|upgraded|"
    r"high ?speed ?build|dmr ?build|full ?upgrade|egyedi|tuningolt|felújított|refurbished|used|használt)(?![\w])", re.I)


def is_variant(title: str | None) -> bool:
    return bool(title and VARIANT_RX.search(BUNDLE_RX.sub("", title)))
