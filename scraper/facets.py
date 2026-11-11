"""
Kategóriánkénti extra szűrők („Gránát típusa”, „Alkatrész típusa”, „BB súlya”, „Akku típusa”, „Optika típusa”…).

Egy termék értékei a product_summary.subtypes oszlopba kerülnek „,dim=érték,” alakban (a működés a powers oszlopban).
A weboldal a web/lib/facets.json-ból tudja, melyik szűrő melyik kategóriához tartozik és mi a felirata
(a gen_facets_json() készíti – a test_facets.py ellenőrzi, hogy friss-e).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import classify
from filters import BUNDLE_RX, specs

WEAPON_LEAVES = ["rifle", "pistol", "smg", "sniper", "lmg", "shotgun", "custom_rifle", "custom_pistol", "custom_sniper"]
PART_LEAVES = ["part_internal", "part_hopup", "part_motor", "part_external"]

# dim -> (kategóriák, (HU, EN) cím, [(érték, HU, EN), ...]) – az értékek sorrendje = a szűrő sorrendje
DIMS: dict[str, dict] = {
    "pow": {"cats": WEAPON_LEAVES + ["part_internal", "part_hopup", "part_motor", "acc_mag"], "label": ("Működés", "Power type"),
            "values": [("aeg", "AEG (elektromos)", "AEG (electric)"), ("gbb", "GBB / GBBR (gázos)", "GBB / GBBR (gas)"),
                       ("gas", "Gáz, nem visszacsapó", "Gas, non-blowback"), ("co2", "CO2", "CO2"),
                       ("spring", "Rugós (manuális)", "Spring (manual)"), ("hpa", "HPA (sűrített levegő)", "HPA (compressed air)"),
                       ("aep", "AEP (elektromos pisztoly)", "AEP (electric pistol)")]},
    "mdl": {"cats": WEAPON_LEAVES, "label": ("Modell / platform", "Model / platform"), "sort": "count",
            "values": []},          # a _MODELS-ből töltjük (lent)
    "gt": {"cats": ["grenade"], "label": ("Gránát típusa", "Grenade type"),
           "values": [("sound", "Hanggránát (pl. Thunder B)", "Sound grenade (e.g. Thunder B)"),
                      ("bb", "BB-szóró (szétnyíló) gránát", "BB-spraying grenade"), ("smoke", "Füstgránát", "Smoke grenade"),
                      ("flash", "Villanógránát", "Flashbang"), ("pyro", "Pirotechnikai gránát", "Pyrotechnic grenade"),
                      ("launcher", "Gránátvető", "Grenade launcher"), ("shell", "40 mm-es gránát / lövedék", "40 mm grenade / shell"),
                      ("part", "Alkatrész, utántöltő", "Parts, refills")]},
    "pt": {"cats": PART_LEAVES, "label": ("Alkatrész típusa", "Part type"),
           "values": [("gearbox", "Gearbox (komplett / ház)", "Gearbox (complete / shell)"),
                      ("piston", "Dugattyú, henger, fejek", "Piston, cylinder, heads"), ("spring", "Rugó, rugóvezető", "Spring, spring guide"),
                      ("gears", "Fogaskerék, csapágy, persely", "Gears, bearings, bushings"), ("nozzle", "Fúvóka, tappet", "Nozzle, tappet"),
                      ("electronics", "Mosfet, elektronika, kábelezés", "Mosfet, electronics, wiring"),
                      ("trigger", "Ravasz, selector", "Trigger, selector"), ("motor", "Motor", "Motor"),
                      ("bucking", "Hop-up gumi", "Hop-up bucking"), ("barrel", "Belső cső", "Inner barrel"),
                      ("hopunit", "Hop-up egység", "Hop-up unit"), ("valve", "Szelep, tömítés (gáz)", "Valve, seal (gas)"),
                      ("stock", "Tus", "Stock"), ("handguard", "Előagy, sín", "Handguard, rail"), ("grip", "Markolat", "Grip"),
                      ("muzzle", "Hangtompító, lángrejtő", "Suppressor, flash hider"), ("body", "Test, tok, szán", "Body, receiver, slide"),
                      ("sights", "Irányzék, szerelék", "Sights, mounts")]},
    "bbw": {"cats": ["acc_ammo"], "label": ("BB súlya", "BB weight"),
            "values": [(v, f"{v.replace('.', ',')} g", f"{v} g") for v in
                       ["0.12", "0.20", "0.23", "0.25", "0.28", "0.30", "0.32", "0.36", "0.38", "0.40", "0.43", "0.45", "0.48"]]
            + [("heavy", "0,50 g felett", "Over 0.50 g")]},
    "bbt": {"cats": ["acc_ammo"], "label": ("BB fajta", "BB kind"),
            "values": [("bio", "Bio (lebomló)", "Bio (biodegradable)"), ("std", "Hagyományos", "Standard"),
                       ("tracer", "Nyomjelző (tracer)", "Tracer")]},
    "bbq": {"cats": ["acc_ammo"], "label": ("BB kiszerelés", "BB pack size"),
            "values": [("s", "Kicsi (max. 1500 db)", "Small (up to 1,500)"), ("m", "Közepes (~1 kg, 2000–3500 db)", "Medium (~1 kg)"),
                       ("l", "Nagy (4000–6000 db)", "Large (4,000–6,000)"), ("xl", "Óriás (2 kg felett)", "Bulk (over 2 kg)")]},
    "gas": {"cats": ["acc_ammo"], "label": ("Gáz típusa", "Gas type"),
            "values": [("green", "Zöld (standard)", "Green (standard)"), ("high", "Erős (red / black / ultra)", "Strong (red / black / ultra)"),
                       ("low", "Gyenge (white / grey / blue)", "Weak (white / grey / blue)"), ("propane", "Propán", "Propane"),
                       ("co2_12", "CO2 patron (12 g)", "CO2 capsule (12 g)"), ("co2_big", "CO2 palack (88–90 g)", "CO2 bottle (88–90 g)")]},
    "gml": {"cats": ["acc_ammo"], "label": ("Gáz kiszerelés", "Gas size"),
            "values": [("small", "500 ml-ig", "Up to 500 ml"), ("mid", "501–800 ml", "501–800 ml"), ("big", "800 ml felett", "Over 800 ml")]},
    "pk": {"cats": ["acc_power"], "label": ("Termék", "Product"),
           "values": [("battery", "Akkumulátor", "Battery"), ("charger", "Töltő", "Charger"),
                      ("accessory", "Kábel, csatlakozó, tároló", "Cable, connector, bag")]},
    "chem": {"cats": ["acc_power"], "label": ("Akku típusa", "Battery type"),
             "values": [("lipo", "LiPo", "LiPo"), ("liion", "Li-Ion", "Li-Ion"), ("life", "LiFe", "LiFe"), ("nimh", "NiMH", "NiMH")]},
    "volt": {"cats": ["acc_power"], "label": ("Feszültség", "Voltage"),
             "values": [(v, f"{v.replace('.', ',')} V", f"{v} V") for v in ["3.7", "6.6", "7.4", "8.4", "9.6", "9.9", "11.1", "14.8"]]},
    "conn": {"cats": ["acc_power"], "label": ("Csatlakozó", "Connector"),
             "values": [("deans", "Deans / T-plug", "Deans / T-plug"), ("minitamiya", "Mini Tamiya", "Mini Tamiya"),
                        ("tamiya", "Nagy Tamiya", "Large Tamiya"), ("xt30", "XT30", "XT30"), ("xt60", "XT60", "XT60")]},
    "chg": {"cats": ["acc_power"], "label": ("Töltő – mihez", "Charger for"),
            "values": [("lipo", "LiPo / Li-Ion (balanszer)", "LiPo / Li-Ion (balancer)"), ("nimh", "NiMH", "NiMH"),
                       ("universal", "Univerzális (minden típus)", "Universal (all types)"), ("usb", "USB-s", "USB")]},
    "ot": {"cats": ["acc_optics"], "label": ("Típus", "Type"),
           "values": [("reddot", "Red dot / holo", "Red dot / holo"), ("scope", "Céltávcső", "Scope"), ("magnifier", "Nagyító", "Magnifier"),
                      ("lamp", "Lámpa", "Flashlight"), ("laser", "Lézer", "Laser"), ("peq", "PEQ / lézer-lámpa doboz", "PEQ / laser-light box"),
                      ("nv", "Éjjellátó, hőkamera", "Night vision, thermal"), ("mount", "Szerelék, védő, kiegészítő", "Mount, cover, accessory")]},
}

# Fegyver-modellek (a „Modell / platform” szűrő): (kulcs, HU, EN, regex). Kategóriánként csak a hozzá illők számítanak
# (a „M4 Super 90” sörétes ne legyen M4, a Glock ne kerüljön a géppuskákhoz). A szűrő csak a ténylegesen előforduló
# modelleket mutatja, darabszám szerint.
_MODELS = {
    "rifle": [
        ("m4", "M4 / AR-15 / HK416", "M4 / AR-15 / HK416", r"\bm4a?1?\b|\bm16|\bar-?15|\bhk ?416|\b416a?\d?\b|\bmk ?18\b|\bcqb-?r|\burg-?i|\bsr-?16|\bsa-[abcehv]\d|\bcm\.?16|\blvoa|\bm27\b|\bnemesis|\bsr ?15|\bl119"),
        ("ak", "AK (AK-47, AK-74, AKM…)", "AK (AK-47, AK-74, AKM…)", r"\bak-?\d{2,3}[a-z]{0,3}\b|\bakm[sn]?\b|\baks-?\d{0,2}|\bak ?47|\bsaiga|\bkrinkov|\bvepr|\bsa-j\d|\bak ?12|\brk-?\d{2}|\bcm\.?04\d"),
        ("g36", "G36", "G36", r"\bg36|\bsa-g\d"),
        ("scar", "SCAR", "SCAR", r"\bscar|\bmk ?1[67]\b"),
        ("aug", "Steyr AUG", "Steyr AUG", r"\baug\b|\bsteyr"),
        ("famas", "FAMAS", "FAMAS", r"famas"),
        ("l85", "L85 / SA80", "L85 / SA80", r"\bl85|\bsa ?80"),
        ("g3", "G3 / HK417", "G3 / HK417", r"\bg3\b|\bhk ?417|\bmc ?51|\bptr-?91|\bg3a\d"),
        ("mcx", "SIG MCX / Spear", "SIG MCX / Spear", r"\bmcx|\bspear\b|\bsig ?516"),
        ("acr", "ACR / Masada", "ACR / Masada", r"\bacr\b|masada"),
        ("tavor", "Tavor / X95", "Tavor / X95", r"tavor|\btar-?21|\bx95"),
        ("f2000", "FN F2000", "FN F2000", r"f2000"),
        ("sig55x", "SIG 550 / 552", "SIG 550 / 552", r"\bsg ?55\d|\bsig ?55\d"),
        ("galil", "Galil", "Galil", r"galil"),
        ("m14", "M14 / EBR", "M14 / EBR", r"\bm14\b|\bebr\b|\bm1a\b"),
        ("ar10", "AR-10 / SR-25 / G28", "AR-10 / SR-25 / G28", r"\bar-?10\b|\bsr-?25|\bm110|\bg28\b|\bsr-?10\b|\bmk ?11\b"),
        ("ww2", "Történelmi (II. vh.)", "Historic (WWII)", r"garand|\bstg ?44|\bmp ?44|\bkar ?98|\bm1 carbine|\bsten\b|\bppsh|thompson|\bmp ?40|\bmosin|\bsvt|\benfield|\bsks\b|\bm3a1|grease gun|\bww ?ii|\bwwii|\btype ?99|arisaka|\bmg ?42|\bm1903|springfield"),
    ],
    "smg": [
        ("mp5", "MP5", "MP5", r"\bmp ?5|\bsw ?5|\bmp5k|\bcm\.?041"),
        ("mp7", "MP7", "MP7", r"\bmp ?7\b|\bmp7a"),
        ("p90", "P90", "P90", r"\bp ?90\b|\bps ?90"),
        ("ump", "UMP", "UMP", r"\bump"),
        ("vector", "Kriss Vector", "Kriss Vector", r"vector|kriss"),
        ("scorpion", "Scorpion EVO", "Scorpion EVO", r"scorpion|\bevo ?3"),
        ("mp9", "MP9 / TP9", "MP9 / TP9", r"\bmp ?9\b|\btp ?9\b|\bmp-?ix|\bvmp"),
        ("mpx", "SIG MPX", "SIG MPX", r"\bmpx"),
        ("mac", "MAC-10 / M11", "MAC-10 / M11", r"\bmac-?1[01]|\bm11\b|\bm11a1|ingram|\bmax ?11"),
        ("uzi", "Uzi", "Uzi", r"\buzi"),
        ("thompson", "Thompson", "Thompson", r"thompson"),
        ("ppsh", "PPSh-41", "PPSh-41", r"\bppsh|\bpps-?43"),
        ("bizon", "PP-19 Bizon / Vityaz", "PP-19 Bizon / Vityaz", r"bizon|vityaz|\bpp-?19"),
        ("pp2000", "PP-2000", "PP-2000", r"\bpp-?2000"),
        ("ww2", "Történelmi (II. vh.)", "Historic (WWII)", r"\bsten\b|\bppsh|thompson|\bmp ?40|\bm3a1|grease gun|\bww ?ii|\bwwii|\bpps-?43"),
    ],
    "pistol": [
        ("glock", "Glock", "Glock", r"glock|\bg ?(17|18|19|19x|22|23|26|34|45|47)c?\b"),
        ("aap01", "AAP-01", "AAP-01", r"\baap-?01"),
        ("hicapa", "Hi-Capa", "Hi-Capa", r"hi-?capa"),
        ("m1911", "1911 / MEU", "1911 / MEU", r"1911|\bmeu\b|\bm45a1|kimber"),
        ("m9", "M9 / Beretta 92", "M9 / Beretta 92", r"\bm9\b|\bm92|\bm9a\d|beretta ?92|\b92 ?fs"),
        ("sig", "SIG P226 / P320", "SIG P226 / P320", r"\bp ?226|\bp ?229|\bp ?320|\bm1[78]\b|\bp ?365"),
        ("hk", "HK USP / VP9", "HK USP / VP9", r"\busp\b|\bvp9|\bhk ?45|\bp30\b"),
        ("cz", "CZ (75, P-09, Shadow)", "CZ (75, P-09, Shadow)", r"\bcz ?75|\bcz ?p-?\d{2}|\bshadow ?2|\bsp-?01|\bcz\b"),
        ("deagle", "Desert Eagle", "Desert Eagle", r"desert eagle|deagle"),
        ("mp_sw", "S&W M&P", "S&W M&P", r"m&p"),
        ("walther", "Walther (PPK, PPQ, P99)", "Walther (PPK, PPQ, P99)", r"walther|\bppk|\bppq|\bp99|\bpdp\b"),
        ("fiveseven", "Five-seveN", "Five-seveN", r"five-?seven"),
        ("makarov", "Makarov / TT-33", "Makarov / TT-33", r"makarov|\bpmm\b|\btt-?33|tokarev"),
        ("revolver", "Revolver", "Revolver", r"revolver|revolv\w*|python|peacemaker|\bsaa\b|webley|\bm29\b|\bmr ?\d{3}"),
    ],
    "sniper": [
        ("vsr", "VSR-10 platform", "VSR-10 platform", r"\bvsr|\bbar ?10\b|\bmb ?0?(2|3|4)\b|\bssg ?10|\bt-?10\b"),
        ("l96", "L96 / AWP / AWM", "L96 / AWP / AWM", r"\bl96|\bawp\b|\bawm\b|\baw ?338|\bmb ?(44|4401|01)\b|\bssg ?96"),
        ("m24", "M24 / M700 / M40", "M24 / M700 / M40", r"\bm24\b|\bm700|\bm40a?\d?\b|\br700"),
        ("silverback", "Silverback (SRS, TAC-41, HTI)", "Silverback (SRS, TAC-41, HTI)", r"silverback|\bsrs\b|\btac-?41|\bhti\b"),
        ("ssg24", "Novritsch SSG24", "Novritsch SSG24", r"\bssg ?24"),
        ("svd", "SVD / Dragunov", "SVD / Dragunov", r"\bsvd|dragunov"),
        ("barrett", "Barrett M82 / M107", "Barrett M82 / M107", r"barrett|\bm82|\bm107"),
        ("m14", "M14 / EBR", "M14 / EBR", r"\bm14\b|\bebr\b|\bm1a\b"),
        ("ar10", "AR-10 / SR-25 / G28", "AR-10 / SR-25 / G28", r"\bar-?10\b|\bsr-?25|\bm110|\bg28\b|\bsr-?10\b|\bmk ?1[12]\b"),
        ("trg", "Sako TRG / PGM", "Sako TRG / PGM", r"\btrg|\bpgm\b|\bm200\b|cheytac"),
        ("ww2", "Történelmi (II. vh.)", "Historic (WWII)", r"\bkar ?98|\bmosin|\benfield|\bm1903|springfield|arisaka|\btype ?99|\bww ?ii|\bwwii"),
    ],
    "lmg": [
        ("m249", "M249 / Minimi / Mk46 / Mk48", "M249 / Minimi / Mk46 / Mk48", r"\bm249|minimi|\bmk ?4[68]\b|\bsaw\b|\blwmg"),
        ("m60", "M60", "M60", r"\bm60|\bmk ?43\b"),
        ("pkm", "PKM / PKP", "PKM / PKP", r"\bpk[mp]?\b|pecheneg"),
        ("mg42", "MG42 / MG3", "MG42 / MG3", r"\bmg ?42|\bmg ?3\b"),
        ("mg4", "MG4 / MG5 / MG36", "MG4 / MG5 / MG36", r"\bmg ?(4|5|36)\b"),
        ("negev", "Negev", "Negev", r"negev"),
        ("m240", "M240 / FN MAG", "M240 / FN MAG", r"\bm240|\bfn mag\b"),
        ("rpk", "RPK / RPD", "RPK / RPD", r"\brp[kd]"),
        ("stoner", "Stoner / Ultimax / Ameli", "Stoner / Ultimax / Ameli", r"stoner|ultimax|ameli|\blmg ?63|\bm63"),
    ],
    "shotgun": [
        ("m870", "M870 / Remington", "M870 / Remington", r"\bm?870|remington|\bmxr"),
        ("m1014", "M1014 / Benelli M4", "M1014 / Benelli M4", r"\bm1014|benelli|super ?90"),
        ("spas", "SPAS-12", "SPAS-12", r"spas"),
        ("aa12", "AA-12", "AA-12", r"\baa-?12"),
        ("ksg", "KSG", "KSG", r"\bksg"),
        ("saiga12", "Saiga-12 / Vepr-12", "Saiga-12 / Vepr-12", r"saiga|vepr"),
        ("lever", "Karos (M1887, Winchester)", "Lever action (M1887, Winchester)", r"\bm1887|lever|winchester"),
        ("double", "Kétcsövű / csonkolt", "Double barrel / sawed-off", r"double[- ]barrel|sawed|sawn|lupara|kétcsöv\w*|\bdb ?(12|shotgun)"),
    ],
}
_MODELS["custom_rifle"] = _MODELS["rifle"] + _MODELS["smg"] + _MODELS["lmg"] + _MODELS["shotgun"]
_MODELS["custom_pistol"] = _MODELS["pistol"]
_MODELS["custom_sniper"] = _MODELS["sniper"]
_MODELS_RX = {cat: [(k, re.compile(rx, re.I)) for k, _, _, rx in lst] for cat, lst in _MODELS.items()}
_seen: dict[str, tuple[str, str]] = {}
for _cat in ("rifle", "smg", "pistol", "sniper", "lmg", "shotgun"):
    for _k, _hu, _en, _ in _MODELS[_cat]:
        _seen.setdefault(_k, (_hu, _en))
DIMS["mdl"]["values"] = [(k, hu, en) for k, (hu, en) in _seen.items()]


def models(cat: str, title: str | None) -> list[str]:
    """A fegyver modellje/platformja a kategórián belül (több is lehet: „PPSh-41 WWII” = PPSh + történelmi)."""
    t = BUNDLE_RX.sub("", title or "")
    return [k for k, rx in _MODELS_RX.get(cat, []) if rx.search(t)]


_PT = [  # sorrend számít: az első találat nyer (a „gearbox with M120 spring” gearbox)
    ("gearbox", r"gearbox|mechabox|gear ?box"), ("motor", r"\bmotor"), ("electronics", r"mosfet|\betu\b|titan|aster|warfet|wiring|kábel|wire|fuse|biztosíték|switch|trigger ?(board|unit|contact)|electronic|elektron"),
    ("piston", r"piston|dugattyú|cylinder|henger|válec|\bhead\b|fej\b|tłok|sorbo"), ("spring", r"spring|rugó|pružin|sprężyn|feder"),
    ("gears", r"\bgears?\b|gear ?set|fogaskerék|bushing|bearing|csapágy|persely|\bshims?\b|alátét|\d{2}:1"),
    ("nozzle", r"nozzle|fúvóka|tappet|tryska"), ("trigger", r"trigger|ravasz|selector|spoušť|sear|anti-?reversal"),
    ("bucking", r"bucking|hop-?up rubber|hop ?up gumi|gumičk|rubber"), ("barrel", r"inner barrel|belső cső|precision barrel|tight ?bore|\b6[.,]0\d ?mm|hlaveň|lufa|cső\b|cijev"),
    ("hopunit", r"hop-?up (unit|chamber)|hop ?chamber|komora|\bnub\b|r-?hop"), ("valve", r"valve|szelep|seal|tömítés|o-?ring|těsnění|ventil"),
    ("muzzle", r"suppressor|silencer|hangtompító|tlumič|tłumik|flash ?hider|lángrejtő|compensator|tracer unit|muzzle"),
    ("stock", r"\bstocks?\b|\btus\b|válltámasz|pažb|kolba|buffer tube"), ("handguard", r"handguard|előagy|\bris\b|keymod|m-?lok|\brails?\b|forend"),
    ("grip", r"\bgrips?\b|markolat|rukojeť|chwyt"), ("body", r"receiver|\bbody\b|\bslides?\b|frame|\btok\b|korpus|\bház\b|upper|lower"),
    ("sights", r"sights?\b|irányzék|mount|szerelék|montáž|muška|hledí"),
]
_PT_RX = [(k, re.compile(rx, re.I)) for k, rx in _PT]
_OT = [
    ("nv", r"night ?vision|éjjellátó|thermal|hőkamera|termow|nokto|nvg"), ("peq", r"\bpeq|\bdbal|\bngal|\banpeq|la-?5|\bmawl"),
    ("magnifier", r"magnifier|nagyító|zvětš"),
    ("mount", r"killflash|kill flash|\bcovers?\b|protector|védő|riser|\bmounts?\b|\brings?\b|szerelék|montáž|lens cap|flip-?up"),
    ("reddot", r"red ?dot|holo|reflex|kolim|\brmr\b|\bt-?1\b|\bt-?2\b|\beotech|\b55[1-8]\b|\bdot sight|prism"),
    ("scope", r"scope|távcső|céltávcső|puškohled|luneta|lunette|zielfernrohr|\d+-\d+ ?x ?\d{2}|\d ?x ?\d{2}\b"),
    ("laser", r"laser|lézer|lazer"), ("lamp", r"flashlight|lamp|lámpa|torch|svítiln|latark|\bwml\b|lumen|\bm[3-9]\d{2}\b|\bx300|\bm600|\bm300"),
    ("mount", r"mount|szerelék|cover|killflash|protector|védő|riser|ring|caps?\b|switch|kapcsoló|filter"),
]
_OT_RX = [(k, re.compile(rx, re.I)) for k, rx in _OT]
_BB = re.compile(r"\bbbs?\b|\bkulk|kuličk|golyó|billes|pallini|\bbb-?k\b|\d[.,]\d\d ?g", re.I)
_BIO = re.compile(r"\bbio|lebomló|biodegrad", re.I)
_TRACER = re.compile(r"tracer|nyomjelző|fluo|glow|świecąc|svítící", re.I)
_CO2 = re.compile(r"\bco2\b", re.I)
_PROPANE = re.compile(r"propan|propane|propán", re.I)
_CHARGER = re.compile(r"charger|töltő|nabíječ|ładowar|chargeur|caricabatter|ladegerät", re.I)
_BATT = re.compile(r"li-?po|li-?ion|li-?fe|nimh|ni-?mh|akku|batter|bateri|akumul|\d{3,5} ?mah", re.I)
_CHEM = [("lipo", r"li-?po|lipol|li-?pol"), ("liion", r"li-?ion"), ("life", r"li-?fe|lifepo"), ("nimh", r"ni-?mh")]
_CHEM_RX = [(k, re.compile(rx, re.I)) for k, rx in _CHEM]
_CONN = [("deans", r"deans|t-?plug|t-?conn|\bt-?type|\bdean"), ("minitamiya", r"mini ?tamiya|small tamiya|kis tamiya"),
         ("xt30", r"xt-?30"), ("xt60", r"xt-?60"), ("tamiya", r"tamiya")]
_CONN_RX = [(k, re.compile(rx, re.I)) for k, rx in _CONN]
_USB = re.compile(r"\busb", re.I)
_UNIVERSAL = re.compile(r"universal|univerzál|multi|imax|b6\b|all types|mindegyik", re.I)


def _first(rxs, text):
    return next((k for k, rx in rxs if rx.search(text)), None)


def attributes(cat: str, title: str | None, price: float | None = None) -> set[str]:
    """Egy cím szűrő-értékei a kategóriához („dim=érték” halmaz, pl. {"bbw=0.25", "bbt=bio", "bbq=l"})."""
    t = title or ""
    core = BUNDLE_RX.sub("", t)
    out: set[str] = set()
    if cat in _MODELS_RX:
        out |= {f"mdl={m}" for m in models(cat, t)}
    if cat == "grenade":
        out |= {f"gt={g}" for g in classify.grenade_types(t, price)}
    elif cat in PART_LEAVES:
        if pt := _first(_PT_RX, core):
            out.add(f"pt={pt}")
    elif cat == "acc_optics":
        if ot := _first(_OT_RX, core):
            out.add(f"ot={ot}")
    elif cat == "acc_power":
        sp = specs(t)
        if _CHARGER.search(core):
            out.add("pk=charger")
            if _UNIVERSAL.search(t):
                out.add("chg=universal")
            for k, rx in (("lipo", re.compile(r"li-?po|li-?ion|balanc|balansz", re.I)), ("nimh", re.compile(r"ni-?mh", re.I))):
                if rx.search(t):
                    out.add(f"chg={k}")
            if _USB.search(t):
                out.add("chg=usb")
        elif _BATT.search(core):
            out.add("pk=battery")
            if chem := _first(_CHEM_RX, t):
                out.add(f"chem={chem}")
            v = sp.get("volt")
            if v and any(v == x for x, _, _ in DIMS["volt"]["values"]):
                out.add(f"volt={v}")
            if conn := _first(_CONN_RX, t):
                out.add(f"conn={conn}")
        else:
            out.add("pk=accessory")
    elif cat == "acc_ammo":
        sp = specs(t)
        if sp.get("bb_g") or (_BB.search(t) and not _CO2.search(t)):
            w = sp.get("bb_g")
            if not w and (m := re.search(r"(?<![\d])[.,](\d{2}) ?g\b", t)):
                w = "0." + m.group(1)                                 # „Model: .20g”
            if w:
                w = f"{float(w):.2f}"
                out.add("bbw=heavy" if float(w) >= 0.5 else f"bbw={w}" if any(w == x for x, _, _ in DIMS["bbw"]["values"]) else "")
            out.add("bbt=bio" if _BIO.search(t) else "bbt=std")
            if _TRACER.search(t):
                out.add("bbt=tracer")
            n = float(sp.get("count") or sp.get("rounds") or 0)
            if not n and sp.get("mass_g") and w:
                n = float(sp["mass_g"]) / float(w)
            mass = float(sp.get("mass_g") or 0)
            if mass >= 2000 or n > 6500:
                out.add("bbq=xl")
            elif n:
                out.add("bbq=s" if n <= 1500 else "bbq=m" if n < 3800 else "bbq=l")
        elif _CO2.search(t):
            g = float(sp.get("mass_g") or 0)
            out.add("gas=co2_big" if g >= 80 else "gas=co2_12")
        elif _PROPANE.search(t):
            out.add("gas=propane")
        elif sp.get("gas") or sp.get("ml") or re.search(r"\b(gas|gáz|gaz|plyn)\b", t, re.I):
            g = sp.get("gas")
            out.add("gas=" + ("green" if g in (None, "green", "top") else "high" if g in ("red", "black", "ultra", "purple") else "low"))
            ml = float(sp.get("ml") or 0)
            if ml:
                out.add("gml=small" if ml <= 500 else "gml=mid" if ml <= 800 else "gml=big")
    out.discard("")
    return out


def gen_facets_json(path: Path | None = None) -> Path:
    path = path or Path(__file__).parent.parent / "web" / "lib" / "facets.json"
    data = {k: {"cats": d["cats"], "label": list(d["label"]), "values": [list(v) for v in d["values"]],
                **({"sort": d["sort"]} if d.get("sort") else {})} for k, d in DIMS.items()}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(gen_facets_json())
