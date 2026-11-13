"""
Kategória- és platform-besorolás (eredetileg Postgres SQL-függvény volt, ennek pontos Python-megfelelője).
A D1 (SQLite) nem tud regexet, ezért a besorolás itt fut (scraper/summary.py hívja). A mintákat a SQL-ből
generáltuk (\\y -> \\b); ha a szabály változik, mindkét helyen módosítsd (teszt: test_classify.py).
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

_C = {
    'BUNDLE': re.compile('(\\s\\+|\\sw/|\\b(with|incl|including|included|mit|avec|con|včetně|vcetne|vč|plus|és|w zestawie|z zestawem|set with)\\b|\\s(\\d+ ?(db|ks|pcs)? ?)?tárr?al\\b).*$', re.I),
    'W': re.compile('\\b(aeg|aep|gbbr?|gbber|co2|guns?|nbb|hpa|ebbr?|sbr|mws|ptw|gas blowback|rifles?|carbines?|karabély\\w*|karabin\\w*|puska\\w*|pušk\\w*|pusk\\w*|pistols?|pistole\\w*|pistolet\\w*|pistola\\w*|pisztoly(?!tok)\\w*|replica\\w*|replik\\w*|réplique\\w*|gewehr\\w*|fusil\\w*|zbraň\\w*|zbran\\w*|shotguns?|sörétes|brokovnic\\w*|samopal\\w*|submachine|smg|lmg|sniper|revolver\\w*)\\b', 0),
    'F': re.compile('\\b(for|do|pro|für|pour|per|compatible|kompatib\\w*|\\w+(hoz|hez|höz))\\b', 0),
    'M1': re.compile('\\b(for|für|pour|compatible|kompatib\\w*)\\s+(\\S+\\s+){0,2}\\S*(\\d|m4|ak|glock|hi-?capa|vsr|mp5|g36|l96|aeg|gbb|pistol\\w*|rifle\\w*|pu[sš]k\\w*|replik\\w*|replic\\w*|karabin\\w*)', 0),
    'M2': re.compile('(^|\\s)(pro|do|per)\\s+(\\S+\\s+){0,2}\\S*(\\d|[Mm]4|AK|[Gg]lock|[Hh]i-?[Cc]apa|VSR|vsr|MP5|mp5|G36|g36|pistol|rifle|pu[sš]k|replik|karabin)', 0),
    'M3': re.compile('\\S*(\\d|m4|ak|glock|vsr|mp5|g36)\\S*-(hoz|hez|höz)\\b', 0),
    'GEAR': re.compile('(\\bpatch(es)?\\b|nášivk|nasivk|naszywk|felvarró|morale|pouch|\\btasak|holster|pisztolytok|\\bslings?\\b|heveder|\\bvests?\\b|mellény|plate ?carrier|chest ?rig|backpack|hátizsák|\\b(gun|rifle|pistol|hard|soft|transport) ?(cases?|bags?)\\b|fegyvertásk|(?<!bolt )(?<!bolt-)\\bcarriers?\\b|\\bscabbards?\\b|\\btorba\\b|\\bkufr|pouzdr|futerał|futeral|pokrowi|\\bbelt\\b|\\böv\\b|\\btok\\b|táska|lanyard|wallet|(safety|pistol|lanyard) cord|pistol attachment|(shotgun|breaching|admin) panel|carabiner|plattenträger|webbing|hook and loop|armband|\\bflags?\\b|buckles?|\\bd ?rings?\\b|\\brope\\b|smartube|fastmag|rack cover|\\bbags?\\b|pockets?|holders?|\\bporta\\b|inserts?|placard|ghillie|parka|\\bcape\\b|bolero|kaptur|\\bhood\\b|storage box|back ?panel|front ?panel|harness|\\bscarf|\\bpants?\\b|trousers|hydration|(?<!battery )(?<!batterie )(?<!akku )(?<!starter )(?<!core )(?<![\\d-])(?<!\\d )\\bpacks?\\b(?!:)|\\bpoche\\b|\\bcases?\\b|scabbard|bandolier|drop ?leg|övegység|\\bbdu\\b|combat ?(shirt|pants|trousers|jacket)|egyenruha|uniform)', 0),
    'PROTECT': re.compile('(hearing|earmuffs?|ear ?defend\\w*|\\bmasks?\\b|maszk|goggles?|szemüveg|\\bglasses\\b|helmets?|sisak|face ?shield|\\bear ?pro|kesztyű|\\bgloves?\\b|knee ?pads?|elbow ?pads?|headphones|kopfhörer|tactical (pistol )?shield|schutzbrille|casco|kaciga|\\bhelm\\b|spectacles|handschuhe|bollé|bolle|pyramex|mechanix|swiss eye|\\bdye\\b|safety glasses|ohrstöpsel|ear ?plugs?|earmor|\\bess\\b|\\bgogle|crossblade|térdvédő|könyökvédő)', 0),
    'MAG': re.compile('(magazin|cartuch|cartucc|moon ?clip|ladehülse|trommel|pistol loader|baseplate|\\b\\d{2,4} ?rds\\b|magacin|xhi-?cap|\\bdrum\\b|magazyn|\\bmags?\\b|\\bhi-?caps?\\b|\\bmid-?caps?\\b|\\blow-?caps?\\b|\\btár(ak|at|ral)?\\b|zásobník|zasobnik|chargeur|cargador|caricator|\\bshells?\\b|hüvely(?!k)|huvely|nábojnic|łusk|lusk|\\bcartridges?\\b|speed ?loader|gyorstölt|mag ?loader|bb ?loader|magazynek|caricatore)', 0),
    'AMMO': re.compile('(\\bgas\\b(?!.{0,25}\\boil).{0,25}\\b\\d{3,4} ?ml\\b|\\bbbs?\\b|\\b\\d[.,]\\d{2} ?g\\b|\\bgolyó\\b|golyók\\b|kuličky\\b|kulki\\b|(green|black|red|yellow|top|power) ?gas|\\bpropane|co2 ?(cartridge|capsule|patron|bombičk|bombick|kapsuł|kapsul)|gáz ?palack|\\bgas ?(can|bottle|refill)s?\\b)', 0),
    'POWER': re.compile('(\\b(hpa|air|co2) ?(tanks?|bottles?)\\b|\\btanks?\\b|lahev|palack|batter(y|ies)|\\bakku|akkumul|\\bbaterie|akumul|batterie|\\bli-?po\\b|\\bli-?ion\\b|\\bli-?fe\\b|\\bnimh\\b|chargers?\\b|\\btöltő|nabíječk|ładowar|ladowar|akumulátor|akkumulátor|nabíječ)', 0),
    'OPTICS': re.compile('(scopes?\\b|scout light|latar[ek]|nachtkijker|night ?vision|noktowizyj|termowizyj|thermal|monocul|prismatic|mounted .{0,20}light|mirino|viseur|visier|dalekomet|romeo\\d|t-eagle|aim-o|bushnell|hawke|killflash|\\bzoom\\b|\\d ?x ?mag\\b|rotpunkt|zielfernrohr|cannocchiale|mira point|punto rojo|crveni|\\bacog\\b|aimpoint|holosun|sightmark|eotech|optical sight|(pistol|gun|weapon|rifle|tactical) ?lights?\\b|\\blumen\\b|\\btlr-?\\d|\\bx300\\b|wadsn|nitecore|streamlight|\\bpk-?a\\b|céltávcs|red ?dots?|holo(graphic)? ?sights?|reflex|dot ?sights?|rangefinder|range ?finder|dalmierz|távolságmérő|night ?vision|éjjellátó|thermal|binocular|kolimátor|kolimator|celownik|zaměřovač|magnifier|\\boptics?\\b|flashlights?|lámpa|\\blasers?\\b|puškohled|puskohled|\\bluneta)', 0),
    'HOPUP': re.compile('(hop-?up|canon inox|stahllauf|\\bhop\\b|flat-?hop|chamber|packing|pressure arm|\\b[if]-? ?key\\b|pusher|tensioner|adjustment wheel|komora|\\b6[.,]0\\d ?mm\\b|\\bcső\\b|cijev|barrel precision|précision|hop ?up|bucking|inner ?barrel|belső ?cső|precision ?barrel|tight ?bore|\\br-?hop|hop ?chamber|\\bnub\\b|hlaveň|hlaven|\\blufa\\b|\\blauf\\b|\\bcanna\\b|gumičk|gumick)', 0),
    'MOTOR': re.compile('(\\bmotors?\\b|\\bcables?\\b|\\bwires?\\b|wired|\\bswitch\\b|\\bboard\\b|usb-?link|microcontroller|controller|processor unit|\\bfcu\\b|leviathan|perun|jefftron|mosfet|wiring|kábelez|kabelez|trigger ?board|micro ?switch|szénkefe|\\bpini?o\\w*|pinion|biztosíték|\\bfuse\\b|t-?dean|tamiya|\\bdeans?\\b)', 0),
    'INTERNAL': re.compile('(gearbox|sebességváltó|hajtómű|spring main|main spring|rebuild kit|repair kit|service kit|upgrade (set|kit)|gas guide|gas route|springs? (set|kit|guide)|\\bhoses?\\b|braided|delayer|shims?|connectors?|tune-?up|delay|késleltet|verzögerung|opóźniaj|retard|odgađ|klizač|latch|needle|\\bfilter\\b|macroline|cushion|bypass|cut-?off lever|stopper|buffer|(co2|hpa|npt).{0,20}adapt|adapt.{0,20}(co2|hpa|npt|macroline)|bolt ?(head|carrier|assembly|set)|(cnc|steel|aluminium|aluminum|complete|performance) (\\w+ )?bolt\\b|cilind|springs? \\d{2,3}|newton|(lock(ing)?|return|lever|ball|reload|leaf|hammer|nozzle|valve|selector|safety|follower|blow ?lock) springs?|\\b(m|sp)(9\\d|1\\d{2})[a-z]{0,3} ?springs?|(dual-)?sector gear|bevel gear|spur gear|hpa line|\\bqd connectors?|foster|sorbo|\\bdampers?\\b|shock ?absorb|(?<!butt )(?<!recoil )(?<!knee )(?<!elbow )\\bpads?\\b|tlumení|nózi|\\bnozi|fúvóka|fuvoka|dugattyúfej|\\bkakas|\\bhammers?\\b|visszarúgó|elsütőszerkezet|\\bbbu\\b|\\b(spare |original )?parts?\\b|hard ?gears?|\\b\\d{2}:1\\b|bolt ?carrier|regulators?\\b|\\breg\\b|feed ?plate|adagolólap|\\btriggers?\\b|trigger ?(box|unit|set)|hpa ?engine|fusion ?engine|mosfet|mechabox|gear ?sets?|\\bgears\\b|fogaskerék|piston|dugattyú|cylinder|\\bhenger|nozzle|tappet|spring ?guide|rugóvezet|bushings?|bearings?|anti-?reversal|selector ?plate|air ?seal|o-?rings?|(main|aeg|upgrade|gearbox|power|valve|nozzle|hammer|recoil|tappet|trigger) ?springs?|\\bsprings? (m|sp)([89]\\d|1\\d{2})\\b|\\b(m|sp)([89]\\d|1\\d{2}) ?springs?|\\brugó(szett|készlet|k)?\\b|pružin|sprężyn|sprezyn|blowback ?unit|\\bvalves?\\b|\\bsear\\b|\\bválec|\\bvalec|\\bválce|\\bpíst|\\bpist(u|y|em)?\\b|tłok|\\btlok|kolben|zylinder|cylindre|cilindro|pistone|\\bfeder\\b|ressort|\\bmolla\\b|muelle|těsnění|tesneni|tömítés|převod|prevod|ozuben|spoušť|spoust|ravasz|(upgrade|tuning) ?(set|kit)|ersatzteil|náhradní|nahradni|alkatrész|części|czesci)', 0),
    'EXTERNAL': re.compile('(suppressor|silencer|hangtompító|tlumič|flash ?hider|compensator|bipod|villaláb|tłumik|tlumik|conversion ?kit|konverz|\\badapters?\\b|feed ?cover|kit only|front set|zárkar|gas block|muzzle|front end|\\bnuts?\\b|c-?clip|\\bbuttons?\\b|turret|forward assist|gas tube|\\bdummy\\b|\\bcatch\\b|\\bflap\\b|ejection|\\bcovers?\\b|\\bknob\\b|\\bramp\\b|sliders?|sleeve|overlay|\\bpins?\\b|spacers?|\\bbarrels?\\b|\\blevers?\\b|magwell|selectors?|picatinny|extensions?|bolt (catch|stop|release)|(rear|front|iron|flip-up) sights?|\\btracer\\b|muzzle ?brake)', 0),
    'STRONG_W': re.compile('\\b(aeg|aep|gbbr?|gbber|ebbr?|sniper|lmg|smg|machine ?gun|replica|replika|carbine|gas blowback)\\b', 0),
    'PISTOL_POWER': re.compile('\\b(gbb|gas blowback|co2|nbb|gnb)\\b', 0),
    'GRENADE': re.compile('(smoke ?(grenade|bomb|canister)|micro smoke|rauchbomb|thunderflash|storm ?360|storm apocalypse|tornado \\d|timer frag|maaws|taginn|spikes tactical havoc|gránát|granát|grenade|granate|granada|granata|launcher|\\b40 ?mm\\b|\\bm203\\b|\\bm320\\b|\\bgl-?06\\b|claymore)', 0),
    'GRENADE_NOT': re.compile('(pouch|tasak|holder|tartó|zseb|pocket|sumka|\\bpatch|nášivk|nasivk|naszywk|felvarró|velcro|morale|sticker|matrica|keychain|kulcstartó|t-shirt|póló|\\btoy\\b|holster|\\bbelt\\b|\\bcases?\\b|flashlight|\\blight\\b|\\bsights?\\b|stock system|heat shield|\\bskin\\b|motion sensor|dummy|\\blens)', 0),
    'M_EXTERNAL': re.compile('(handguard|calcio|culata|kundak|schaft|crosse|puskatus|buttstock|forend|\\bris\\b|keymod|m-?lok|\\brails?\\b|\\bstocks?\\b|válltámasz|\\bgrips?\\b|markolat|outer ?barrel|külső ?cső|\\bbody\\b|receiver|\\bslides?\\b|sights?\\b|\\bmounts?\\b|pažb|pazb|\\bkolba\\b|předpažb|előagy|rukojeť|rukojet|chwyt|conversion)', 0),
    'AMBIG_EXTERNAL': re.compile('(handguard|calcio|culata|kundak|schaft|crosse|puskatus|buttstock|forend|\\bris\\b|keymod|m-?lok|\\brails?\\b|\\bstocks?\\b|válltámasz|\\bgrips?\\b|markolat|outer ?barrel|külső ?cső|\\bbody\\b|receiver|\\bslides?\\b|iron ?sights?|\\bmounts?\\b|buffer ?tube|charging ?handle|\\bframes?\\b|dust ?cover|\\bpistolgrip)', 0),
    'OTHER_MISC': re.compile('(cleaning|\\bracks?\\b|\\bstands?\\b|display|maintenance|\\boil\\b|olaj|silicon|szilikon|grease|\\btargets?\\b|céltábl|chrono|\\bpatch|\\bradio|headset|knife|\\bkés\\b|bayonet|\\btools?\\b|szerszám|teflon|zsír|zsir|tisztít|cleaning|\\bcleaner|kronográf|kronograf|csavarrögzít|thread ?lock|loctite|rastrelliera|compressor|kompresszor|wall ?panel|holder rifles|armou?rer(?! works)|wrench|powerbank|\\bbev\\b|midland|battle brick|lubric|\\blube\\b|battery ?tester)', 0),
    'SNIPER': re.compile('(sniper|\\btrg\\b|\\bpgm\\b|\\.338|\\bhti\\b|\\bm40a\\d|kar ?98|enfield|\\ble4\\b|mesterlövész|odstřel|odstrel|\\bdmr\\b|\\bsvd\\b|dragunov|\\bvsr|\\bl96|\\bawm\\b|\\baw ?338|\\bm24\\b|\\bm40\\b|\\bm700\\b|(?<!cm16 )\\bsrs\\b|\\bssg-?\\d{2}|\\bmb-? ?(0?\\d|1\\d)\\b|bolt[- ]action|\\bsr-?25|\\bm14\\b|\\bg28\\b|\\bsr-?10\\b|\\bmk ?1[12]\\b|\\btac-?41|(?<!ronin tactical )\\bt-?10\\b|\\bscout\\b|marksman|mauser(?! m712)|barrett|\\bcm\\.? ?70\\d|\\br700|\\bmb ?44\\d\\d|\\bvss\\b|\\bcm\\.?099|\\bas-01|aac t1[01]|\\bev03|mod24|msr-?338|\\bpc1\\b|cheytac|\\bm200\\b|edm200|\\bm110|\\bmk ?20\\b|\\bsass\\b|\\bg980|snr ?25|\\bmk ?14\\b|\\bebr\\b|\\bgr14|kc-02|\\bbar ?10|socom 16|mosin|\\baw ?308\\b|\\bm107|\\bspr\\b|\\bsas ?\\d|fieldcraft|\\bsmle\\b|type ?38\\b|\\bvks\\b)', 0),
    'LMG': re.compile('(\\blmg\\b|géppuska|kulomet|(?<!sub)(?<!sub-)(?<!sub )machine[ -]?gun|\\bm249|\\bm60(e\\d)?\\b|\\bpkm?\\b|\\brpk|\\bmg ?(3|4|42|5)\\b|\\bmk ?4[68]\\b|minimi|minigun|fightlite|\\bm1918|zb-?(26|30)|mini vulcan|\\bm13[2-4]\\b|\\bmk ?43|\\bm1919|g?mg ?42|\\bnegev|\\bm240|\\brpd\\b|\\bsaw\\b)', 0),
    'SHOTGUN': re.compile('(shotgun|sörétes|brokovnic|fusil à pompe|\\bm870|\\bspas|\\bm1014|\\baa-?12|\\bmp-?153|\\bksg\\b|\\bm3 super|\\bpump\\b|flinta|\\b1887\\b|\\bcm\\.? ?35\\d|saiga-?12|sgr-?12|\\bm1887|dracarys|mossberg|benelli|fabarm|\\bm590|\\bm500\\b)', 0),
    'SMG': re.compile('(\\bsmg\\b|\\bpp-?2k\\b|\\bots-?126|géppisztoly|samopal|submachine|sub-machine|pistolet[- ]mitrailleur|\\bmp ?5|\\bmp ?7\\b|\\bp ?90\\b|\\bump|\\bvector\\b|kriss|scorpion|\\buzi\\b|\\bmp ?9\\b|\\bmac[- ]?1[01]|\\bvmp|ppsh|thompson|\\bsten\\b|\\bmp ?40|\\bpp-?19|bizon|\\bpp-?2000|\\barp ?9\\b|\\bfar ?9\\b|\\bprk ?9|\\bsmc-?9|\\bmxc ?9|\\btgm\\b|\\bpcc-?45|\\bgpm9|\\bpw9\\b|\\bjg ?5\\b|\\bp ?90\\w*|\\bmp ?5\\w*|skorpion|\\bnp5\\w*|\\bsd[56]\\b|\\bjg ?100\\b|\\bmpx|scw-?9|[um]dp-?9|ghm ?9|\\bmp-?18\\b|\\bmp-?41\\b|grease gun|\\bm3a1\\b|tec-?9|kmp-?9|\\bbro 9mm|\\bpcc 9mm|pistol caliber|space invader|\\bm45 [sx]-class|ppk ?20|fmg-?9|\\bsr-?3\\b|vikhr|\\bm11a1|swordfish|pmg-?5|\\bgsg ?5\\b|gsg 522|utr ?45)', 0),
    'PISTOL': re.compile('(pisztoly(?!tok)|\\bpistol|\\bpistole|\\bpistolet|\\bpistola|handgun|revolver|glock|\\bg ?1[789]\\b|hi-?capa|\\b1911|\\bm9\\b|\\bp226|\\bp320|\\busp\\b|beretta|desert eagle|\\bcz ?75|\\bcz ?p-?0\\d|\\bm&p|five-seven|walther|\\bppk|makarov|\\btt-?33|\\baep\\b|hi[- ]?capa|m1911|\\bsp-01|shadow ?2?\\b|\\bkp-?\\d{2}|\\bm29\\b|cs defender|\\bsport 106|\\bm9a1\\b|\\bp38|grach|hudson|\\bh9\\b|\\bzev\\b|\\boz9|maxim 9|salient arms blu|\\bblu (compact|gbb|standard)|\\bx[12] (ultimate|extreme)|srt-?1\\d|ssx ?23|\\bwe01\\b|\\bh-22\\b|strike micro|\\b103y|\\bm712|gpm ?92?\\b|bodyguard|compact carry|\\blcp\\b|colt|taurus|\\bpt ?92|\\bfns-?9|\\bfn ?509|socom|\\bmk ?23|python|dan wesson|90two|savaging bull|\\bm10 \\d|\\b2011\\b|\\bm92|luger|\\bp08\\b)', 0),
    'RIFLE': re.compile('(\\baeg\\b|\\bgbbr\\b|\\bgbber\\b|\\bebbr?\\b|\\bsbr\\b|\\bmws\\b|\\bptw\\b|\\bmtw\\b|\\bmcx\\b|\\bpc1\\b|\\bl85|\\bel?ak-?\\d{2}|\\blk-?33|\\bheretic labs|\\bgarand\\b|replica|replika|réplique|rifle|carbine|karabély|karabin|puska|puška|zbraň|zbran|fusil|gewehr|\\bm4\\b|\\bm16|\\bar-?15|\\bhk ?416|\\bak-?\\d{2}|\\baks|\\bakm|\\bg36|\\bscar|\\baug\\b|famas|\\bsa-[a-z]\\d|\\bcm\\.?\\d{3}|assault rifle|\\belak\\w*|\\bg74c?\\b|\\bpdw\\b|trident|\\bcrb\\b|\\blm4|\\bemr\\b|\\barx ?160|\\bssg-1\\b|\\barp ?556|\\bmcp ?556|\\btr16|\\bgc16|\\bcm16|\\bbamf|\\blevar|lever action|winchester|\\b1892|\\bsoc slr)', 0),
    'URL_PARTS': re.compile('(parts|alkatr|części|czesci|díly|dily|ersatzteil|tuning|upgrade|ricambi|repuestos|pieces-detachees)', 0),
    'URL_ACC': re.compile('(accessor|kiegeszit|zubehor|prislusenstvi|akcesori|accessoires|accesorios)', 0),
    'URL_SNIPER': re.compile('(sniper|odstrel|mesterlovesz)', 0),
    'URL_PISTOL': re.compile('(pistol|pisztoly|pistole|pistolet)', 0),
    'URL_SMG': re.compile('(smg|submachine|samopal|geppisztoly)', 0),
    'URL_RIFLE': re.compile('(rifle|carbine|karabin|gewehr|assault|aeg|elektromos|airsoft-guns|airsoftove-zbrane)', 0),
}
_BUNDLE_O = re.compile(_C['BUNDLE'].pattern, re.I)

WEAPONS = {'rifle', 'pistol', 'smg', 'sniper', 'lmg', 'shotgun', 'grenade'}
# egyedi építésű / tuningolt / HPA / használt fegyverek külön csoportban (summary.py dönti el a termék szintjén)
CUSTOM = {'custom_rifle', 'custom_pistol', 'custom_sniper'}


ALL_CATEGORIES = WEAPONS | CUSTOM | {'part_internal', 'part_hopup', 'part_motor', 'part_external', 'acc_mag', 'acc_power',
                                     'acc_optics', 'acc_ammo', 'acc_protect', 'acc_gear', 'other'}


def custom_of(cat: str) -> str:
    return 'custom_pistol' if cat == 'pistol' else 'custom_sniper' if cat == 'sniper' else 'custom_rifle'


def is_gun(cat: str | None) -> bool:
    return cat in WEAPONS or cat in CUSTOM
_SUBS = [('GEAR', 'acc_gear'), ('PROTECT', 'acc_protect'), ('MAG', 'acc_mag'), ('AMMO', 'acc_ammo'), ('POWER', 'acc_power'),
         ('OPTICS', 'acc_optics'), ('HOPUP', 'part_hopup'), ('MOTOR', 'part_motor'), ('INTERNAL', 'part_internal'),
         ('EXTERNAL', 'part_external')]
_WEAPON_RULES = [('SNIPER', 'sniper'), ('SMG', 'smg'), ('LMG', 'lmg'), ('SHOTGUN', 'shotgun'), ('PISTOL', 'pistol'), ('RIFLE', 'rifle')]
_URL_TYPES = [('URL_SNIPER', 'sniper'), ('URL_PISTOL', 'pistol'), ('URL_SMG', 'smg'), ('URL_RIFLE', 'rifle')]


# Árküszöb (Ft): ennél olcsóbb tétel nem lehet ilyen fegyver. Csak modellnév (M4, AK, SCAR, 1911, SVD…) és nincs
# fegyverszó (AEG, GBB, puska, pistol, replika…) -> magasabb küszöb. Így a „Šroub pažbičky M4” (csavar, 673 Ft)
# vagy a „Klapka pro SVD GBB” nem kerül a fegyverek közé. Ár nélkül (terméknév-szavazat) nincs küszöb.
_FLOOR = {'pistol': 2500, 'shotgun': 4000, 'smg': 5000, 'rifle': 6000, 'sniper': 6000, 'lmg': 20000}
_FLOOR_MODEL_ONLY = {'pistol': 8000, 'shotgun': 10000}
_FLOOR_MODEL_ONLY_DEFAULT = 15000


def _weapon_ok(cat: str, p: float, explicit: bool) -> bool:
    if p <= 0:
        return True
    if p < _FLOOR.get(cat, 6000):
        return False
    return explicit or p >= _FLOOR_MODEL_ONLY.get(cat, _FLOOR_MODEL_ONLY_DEFAULT)


_MODEL_CODE = re.compile(r"(?<![\w])[A-Z]{1,5}[-.]?\d{2,4}[A-Z]?(?![\w])")   # CM048, SA-C08, AM-007, LVOA-S nincs


_TAIL_NOISE = re.compile(r"(\W+(black|tan|od|olive|fde|de|grey|gray|green|coyote|multicam|silver|red|blue|sand|desert|"
                         r"dark earth|bronze|gold|white|airsoftpl[aá]za|airsoft|m-?lok|keymod|mil|spec|mil-spec|style|type|model|version|ver|"
                         r"inch|inches|color|colour|raw|outlet|ranger green|od green|tan|limited|edition|\w{1,2}|\d+\w*))+\W*$")
_ENDS_PIECE = re.compile(r"\b(stocks?|handguards?|forends?|grips?|receivers?|body|slides?|mounts?|"
                         r"buffer tube|outer barrel|charging handle|dust cover|magwell|frame)\W*$")


_HEAD_PIECE = re.compile(r"\b(stocks?|handguards?|forends?|grips?|receivers?|body|slides?|mounts?|rails?|buffer tube|outer barrel|"
                         r"charging handle|dust cover|magwell|frame|(?<!starter )(?<!complete )(?<!full )(?<!go airsoft )kits?|"
                         r"conversions?|upper|lower|chassis|shell|housing|barrels?|extensions?|sights?|levers?|release|safety|adapters?|brake|tracer|bolt|"
                         r"handle|cylinder|motor|unit|system)\W*$")
_MULTI = re.compile(r"\b([2-9]|\d{2,}) ?(pcs|pc|db|ks|szt|stk|st|pieces|darab|kusů|ks\.)\b|\b(set|sada|zestaw|készlet) (of )?([2-9]|\d{2,})\b")
# Leíró kifejezések egy komplett fegyver címében („… MOSFET ETU”, „… Green Gas”, „Optics Ready”, „Metal slide”, „2x Magazine”,
# „with silencer”): ha a cím fegyverre utal (fegyverszó / modellkód, elég magas ár), ezek nem teszik alkatrésszé / tartozékká.
_DESCR = re.compile(r"\b(mosfet( ?\+ ?lipo)?|lipo ?\+ ?mosfet|lipo edition|etu|electronic trigger|elekt\.? trigger|x-asr|"
                    r"gate (aster|titan|x-asr)( ii)?|green gas( powered)?|co2 powered|gas powered|"
                    r"(direct )?optics? ready|d\.o\.r\.?|(metal|steel|composite|polymer|fixed|aluminium|aluminum) (slide|bolt|frame|body)|"
                    r"(railed|standard|strike|black|tan) frame|full metal|"
                    r"(full|fixed|polymer|wood|faux wood|nylon|folding|skeleton|crane) stock|stock emod\w*|"
                    r"(\d+ ?x?|double[- ]stack|extra) (magazines?|mags?|zásobník\w*)|(with|without|bez|ohne) (battery|akku|lipo)|"
                    r"no flashlight\w*|with hop[- ]?up\w*|fixed slide|compensator|(polymer|metal) receiver|lever[- ]action|"
                    r"(black|silver|tan|grey|gray|gold|pink|blue|od|red|green|chrome|bronze|fde|wood) (bolt|slide|frame|lower|upper)|"
                    r"(open|high speed|split|metal) bolt( version)?|"
                    r"(built-in |x-asr/)tracer|"
                    r"twin motor|wire cutter|dual power( spring)?|dummy light|(steel|alpha) parts|light[- ]ops( stock)?|silencerco|etu( \w+)? selector|"
                    r"shell ejecting|shell loading|(\d-round burst )?multi-shot|(bez|no|without) (ris )?rails?|double barrel|fixed-barrel|"
                    r"hop[- ]?up-?(pal|val|vel|om)\b)\b")
_DESCR_STOCK = re.compile(r"\b(full|fixed|polymer|wood|faux wood|imitation wood|nylon|folding|skeleton|crane|para|pdw|rs1|no|w-|bez|"
                          r"retractable|collapsible|side folding|underfolding) ?stock( version)?\b")
_DESCR_W = re.compile(r"\b((split|metal|upgraded|reinforced) gearbox|(with )?(silencer|suppressor)( included)?|(silver|black|gold|tan|short|long|threaded|fluted|multi-|[\d.]+\"?( ?inch)?) ?barrel( version)?|barrel se thread)\b")
_EXPL = re.compile(r"\b(spring|springer|gas|gaz|nbb|gnb|manual|lever[- ]action|fixed slide|blowback|non-blowback)\b")
_PISTOL_PIECE = re.compile(r"\b(slides?|frames?|bolt release|safety lever|grip safety|thumb safety|rear sight|front sight|outer barrel|"
                           r"external barrel|barrel extension|upper|lower|kit only|magwell|feed cover|rails?|foregrip|handguard kit|split side)\W*$")
# Az utolsó szó a tárgy, ha a cím nem utal komplett fegyverre (nincs AEG/GBB/rifle… szó, se gyári fegyver-sorozat):
# „Mancraft CNC M4 Body Ver.2”, „Madbull MK18 12.5 Inch Daniel Defense RIS II”, „Silverback SRS A1 A2 26 inch fluted Barrel”.
_ENDS_X = re.compile(r"\b(stocks?|buttstock|handguards?|forends?|grips?( kit)?|receivers?|body|slides?|mounts?|buffer tube|barrels?|"
                     r"charging handle|dust cover|magwell|frame|ris|rails?|upper|lower|top cover|sights?|kit|set|extension|supporter|"
                     r"selector|handle|monopod|bipod|brake|bolt|pipe|cover|panel|parka|cape|hood|bolero|suit|unit|motor|controller|"
                     r"chamber|cylinder|head|assembly|trigger|module|shield|sight set|case)\W*$")
_PISTOL_MODEL = re.compile(r"(glock|hi[- ]?capa|1911|\bm9\b|m9a1|beretta|p226|p320|\busp\b|desert eagle|cz ?75|five-seven|\bppk|makarov|"
                           r"\bg ?1[789]|\baep\b|revolver|python)")
_W_NOUN = re.compile(r"\b(rifles?|carbines?|karabin\w*|karabély\w*|pistol\w*|pisztoly\w*|shotguns?|sörétes|smg|lmg|sniper|"
                     r"replica\w*|replik\w*|puska\w*|machine ?gun|submachine|gewehr\w*|fusil\w*|zbraň\w*|géppisztoly|revolver\w*)\b")
_STRONG_PIECE = re.compile(r"\b(handguards?|stocks?|buttstock|receivers?|body|slides?|frames?|upper|lower|outer barrel|forends?|"
                           r"calcio|culata|kundak|schaft|crosse|puskatus)\b")
_PISTOL_MAKER = re.compile(r"\b(kwc|armorer works|vorsk|y&p|army armament|we (e99|p99|m84|712|bulldog|samurai edge|desert warrior|"
                           r"m\.?e\.?u|r1[78]|para|kimber|hi-?capa|g1[789]|m9|m92)|poseidon xg|tti (combat master|ballerina))")
_GUN_MAKER = re.compile(r"\b(ics|lct|vfc|bolt|krytac|classic army|g&g|double bell|jg( works)?|e&c|e&l|ares|modify|apl|amoeba|silverback|"
                        r"king arms|arcturus|golden eagle|src|asg|cyma|specna arms|lancer tactical|tokyo marui|emg|a&k|ghk|"
                        r"wolverine|evolution|cybergun|umarex|we|novritsch|ak-?\d|real sword|well|snow wolf|agm|dboys|d-boys)\b")
_PIECE_ANY = re.compile(r"\b(kit|set|silencer|suppressor|body|frame|stock|panel|sight|nozzle|hpa system|pump|compressor|"
                        r"handguard|rail|ris|keymod|m-?lok|receiver|upper|lower|barrel|tube|gas block|engine|creator)\b")
_GUNCTX_GATE = re.compile(r"\b(edge|core|prime|flex|sport ?line|full metal|cm\.?\d{3}|sa-[a-z]\d{2})")
_GUNCTX = re.compile(r"\b(etu|ecu|bldc|aster|titan|kestrel|hal|edge|core|prime|flex|sport ?line|full metal|cm\.?\d{3}|sa-[a-z]\d{2})")
_COMPLETE = re.compile(r"\b(complete|completed|pre-?built|installed|fully assembled)\b")


# SZIGORÚ 1. SZŰRÉS (a projekt szabályrendszere): ezek a szavak/kifejezések a címben ÁRTÓL FÜGGETLENÜL alkatrészt, tartozékot
# vagy felszerelést jelentenek – soha nem fegyvert. (A leíró jellegű szavak – mosfet, ETU, hop-up, hangtompító – nem ide
# tartoznak, mert egy komplett fegyver címében is szerepelhetnek; azokra a régi, árküszöbös logika marad.)
# gyenge felszerelés-szavak: csak ha más tárgyszó nincs a címben („Variable Cap … Magazine” = tár, „Velcro Patch” = felszerelés)
_WEAK_GEAR = re.compile(r"((?<!-)\bcaps?\b|\bbadges?\b|velcro|molle|helikon|tasmanian tiger|crye|mil-tec|invader gear|primal gear|condor|"
                        r"emerson ?gear|wosport|z-tactical)")
_PRE_SUBS = [
    # nem airsoft: 4,5 mm-es légfegyver (diabolo), paprikaspray, gáz-riasztó
    ('other', re.compile(r"(air ?gun|\b4[.,]5 ?mm\b|\b5[.,]5 ?mm\b|diabolo|\bpellets?\b|\bpcp\b|pepper|blank cartridge)")),
    ('other', re.compile(r"((hpa|hand|air|stage) ?pump|compressor|kompresszor|interactive gun|nachtkijker)")),
    ('acc_gear', re.compile(r"(\bsuit\b|ghillie|bolero|kaptur|camouflage cape|sniper (suit|cape|parka|hood)|helmet cover|sisakhuzat|helmet (velcro|rail|modification|attachment|counterweight)|goggle swivel|"
                            r"mask wrap|balaclava|scabbard|bandolier|drop ?leg|battle ?belt|övegység|\bbdu\b|combat ?(shirt|pants|trousers|jacket)|"
                            r"shells? ?(holder|pouch|carrier)|egyenruha|\buniform)")),
    ('acc_ammo', re.compile(r"(co2[^,]{0,14}(cartridges?|capsules?|bulbs?|patron\w*|kapsul\w*|bombi\w*)|"
                            r"(cartridges?|capsules?|bulbs?|patron\w*)[^,]{0,14}co2|(black|red|yellow) ?gas(?! ?blowback))")),
    ('part_external', re.compile(r"(mag(azine)? ?(catch|release|lock)|tárkioldó|charging ?handle|felhúzókar|fire ?selector|tűzváltó|"
                                 r"selector ?(switch|lever)|buffer ?tube|stock ?tube|(vertical|angled|tactical) ?grip|hand ?stop|"
                                 r"\bpistolgrip|pisztolymarkolat|tracer ?unit|mock ?(suppressor|silencer)|\bpeq\b|szíjkengyel|"
                                 r"sling ?swivel|dust ?cover|trigger ?guard|gas block|bolt handle|zárkar|cheek ?(rest|riser|pad)|\bmounts?\b|risers?|scope rings?|\bbipod|"
                                 r"monopod|fib(re|er) ?(optic )?sights?|\boffset\b|(catch|release|lever|button|ramp|sleeve|overlay|foot lock|sliders?)( \w+){0,2} magazine|"
                                 r"magazine (catch|release|button|well|shaft|adaptor))")),
    ('part_internal', re.compile(r"(hpa system(?!.{0,25}tank)|\bpulsar\b|redline (mechanical|hpa|snow|n7|sfr|mini)|\bn7 gen|inferno premium|(inlet|outlet|fill) valve|valve (key|set)|(?<!navy )\bseals?\b|o-?rings?|gasket|follower|mag(azine)? lips?|"
                                 r"hpa ?engine|fusion ?engine|polar ?star|wolverine (bolt|inferno|reaper|storm)|gearbox ?shell|mechabox|\bregulator|trigger ?bar|\bsear\b|"
                                 r"(fill|output|release) ?valve|blowback ?(housing|unit)|\bbbu\b|recoil ?spring|tappet ?plate)")),
]


def _norm(t: str) -> str:
    """Egységesített írásmód: „hand guard” = handguard, „pistol grip” = pistolgrip (a „pistol” itt nem fegyver)."""
    t = re.sub(r"(?i)hand[ -]guards?", "handguard", t)
    t = re.sub(r"(?i)fore[ -]ends?", "forend", t)
    t = re.sub(r"(?i)pistol[ -]grips?", "pistolgrip", t)
    t = re.sub(r"(?i)sub[ -]?machine[ -]?gun", "submachine gun", t)
    return t


def _translated(title: str) -> str:
    try:                                   # késleltetett import (a dictionary -> names -> matcher lánc ezt a modult is használja)
        from dictionary import translate
        return translate(title) or ''
    except Exception:                      # pragma: no cover
        return ''


def category(title: str | None, url: str | None = None, price: float | None = None) -> str:
    title = _norm(title or '')
    tt = _translated(title)                # idegen nyelvű cím: az angol fordítás is számít („SPEGNIFIAMMA” = flash hider)
    extra = tt if tt and tt.lower() != title.lower() else ''
    def _cut(t, rx):
        m = rx.search(t)
        if m and not _C['F'].search(t.lower()) and not _C['STRONG_W'].search(t[:m.start()].lower()):
            w2 = _C['STRONG_W'].search(t[m.start():].lower())
            if w2 and not re.search(r"[(:]", t[m.start():m.start() + w2.start()]):   # „… with Metal bolt Gas blowback GBB”: a tartozék-rész kimarad, a fegyverszó megmarad
                return t[:m.start()] + ' ' + t[m.start() + w2.start():]
        return rx.sub('', t)
    o = (_cut(title, _BUNDLE_O) + ' ' + _BUNDLE_O.sub('', extra)).strip()
    c = (_cut(title.lower(), _C['BUNDLE']) + ' ' + _C['BUNDLE'].sub('', extra.lower())).strip()
    u = urlsplit(url or '').path.lower()            # csak az útvonal: az „airsoft-guns.eu” domain nem fegyver
    p = float(price or 0)
    p0 = float(price or 0)
    gate_min = 20000 if (_C['PISTOL_POWER'].search(c) or _EXPL.search(c)) else 25000
    if not _C['F'].search(c) and p0 >= gate_min and (_C['W'].search(c) or _MODEL_CODE.search(o) or _EXPL.search(c)
                                                    or _GUNCTX_GATE.search(c)
                                                    or _C['PISTOL'].search(c) or [x for x in platforms(o) if not x.startswith('gb_')]
                                                    or (p0 >= 40000 and any(_C[k].search(c) for k, _ in _WEAPON_RULES))):
        if _C['W'].search(c) or _EXPL.search(c) or re.search(r"\b(cm\.?\d{3}|sa-[a-z]\d{2})", c):
            c = _DESCR_W.sub(" ", c)                           # „silver Barrel”, „Short Barrel Version”: csak fegyverszó mellett
        c = re.sub(r"\((model|color|colour|length|version|package|size|style)\s*:(?![^)]*(kit only|engine|unit|pack of))[^)]*\)?|\b(model|color|colour|length|package)\s*:(?!.*(kit only|engine|unit|pack of)).*$", " ", c)
        if p0 >= 45000:
            c = _DESCR_STOCK.sub(" ", c)
        c = re.sub(r"\s+", " ", _DESCR.sub(" ", c)).strip()       # fegyvercím: a leíró kifejezések nem döntenek
    has = lambda k, s=c: _C[k].search(s) is not None
    w, f = has('W'), has('F')
    full = (title + ' ' + extra).lower()
    # „Stock w/ Adjustable Buttpad … for CM.708 Sniper Rifles”: a „w/” utáni rész nem csomag, a „for X” a fő tárgyra vonatkozik
    piece = has('AMBIG_EXTERNAL') or has('M_EXTERNAL') or any(has(k) for k, _ in _SUBS)
    m = has('M1') or has('M2', o) or has('M3') or (piece and has('M1', full))
    f = f or (piece and has('M1', full))
    sub = next((name for k, name in _SUBS if has(k)), None)
    if sub is None and _WEAK_GEAR.search(c) and not _W_NOUN.search(c):
        sub = 'acc_gear'
    if sub is None and not w and p < 40000 and re.search(r'\betu\b', c):
        sub = 'part_motor'                                  # „Gate ETU”: fegyverszó nélkül elektronika
    if has('GRENADE') and not has('GRENADE_NOT'):
        return 'grenade'                                  # a gránát-alkatrész is itt marad (a „Gránát típusa” szűrőben: alkatrész)
    if 0 < p < 15000 and re.search(r"\bm(9\d|1\d\d)(sp|s)?\b", c) and re.search(r"\bsprings?\b", c):
        return 'part_internal'                            # „Archwick M170 SPR 300 VSR 10 Spring 9mm”: rugó, nem rugós fegyver
    for name, rx in _PRE_SUBS:
        if rx.search(c):
            return name                                   # szigorú 1. szűrés: soha nem fegyver
    if m:
        return sub or ('part_external' if has('M_EXTERNAL') else 'other')
    # „Sniper M82 … Scope + bipod”, „FMG-9 tracer GBB”, „KAR98K Green Gas”: a tartozékszó a fegyver része, nem a termék
    gun_typed = any(has(k) for k, _ in _WEAPON_RULES if k != 'PISTOL')
    weapon_first = not f and sub in ('acc_optics', 'acc_ammo', 'acc_gear', 'acc_mag', 'acc_power') and (
        (has('STRONG_W') and p >= 30000 and sub != 'acc_mag')                     # 5-ös tárcsomag ≠ fegyver
        or (gun_typed and p >= 90000 and sub in ('acc_ammo', 'acc_mag')))         # „rifle scope”, „Rifle Plate Carrier” ≠ puska
    if weapon_first and sub == 'acc_gear' and _C['GEAR'].search(c).start() < _C['STRONG_W'].search(c).start():
        weapon_first = False          # „Gas Tank Cordura Pouch … M249 Machine Gun”: a tok a tárgy, a fegyver csak a „mihez”
    # „Sniper Scope”, „Sniper Parka”: ha a tartozékszó a cím vége, az a tárgy (nem a fegyver része)
    if weapon_first and re.search(r"\b(scopes?|sights?|lights?|parka|cape|hood|suit|case|bag|pouch|holster)\W*$", _TAIL_NOISE.sub('', title.lower())):
        weapon_first = False
    # a leíró kifejezések (mosfet, green gas, silencer…) fegyvercímből már ki vannak véve: ami alkatrész-szó marad, az a tárgy
    if sub and not weapon_first:
        return sub
    if has('AMBIG_EXTERNAL') and (f or (not w and p < 40000 and not _GUNCTX.search(c)) or 0 < p < 15000):
        return 'part_external'
    # „A&K M1A Airsoft Rifle Polymer Stock”, „AAP01 SMG forend, M-LOK”: a cím utolsó szava a tárgy (színek, márka nélkül)
    if 0 < p < 60000 and _ENDS_PIECE.search(_TAIL_NOISE.sub('', c)):
        return 'part_external'
    if _STRONG_PIECE.search(c) and not w and not _W_NOUN.search(c) and not re.search(r"\b(cm\.?\d{3}|sa-[a-z]\d{2})", c) \
            and not has('PISTOL_POWER'):
        return sub or 'part_external'                     # „Magpul ZHUKOV Hand Guard AK47”, „A&K M1 Gun Polymer Stock”
    tail = _TAIL_NOISE.sub('', c)
    if 0 < p < 250000 and not _W_NOUN.search(c) and not _GUNCTX.search(c) and _ENDS_X.search(tail) and not (
            re.search(r"\b(ris|ras)\W*$", tail) and _GUN_MAKER.search(c) and p >= 45000):     # „A&K Masada RIS”: fegyvernév
        return sub or ('other' if has('OTHER_MISC') else 'part_external')
    # „Dr.Black TM Hi-Capa 5.1 GBB Slide Type V”, „… Frame Type 02”, „… Bolt release”: drága, de a tárgy a szán / váz / kezelőszerv
    if 0 < p < 150000 and _PISTOL_PIECE.search(_TAIL_NOISE.sub('', c)) and not _W_NOUN.search(title.lower()):
        return 'part_external'
    # „King Arms CNC PDW M11 Kit for KWA … Sub-Machine Gun”, „VIK II M-LOK Handguard for Kriss Vector SMG”: a „for” előtti
    # rész (a termék maga) alkatrész/készlet -> árától függetlenül nem fegyver (kivéve a gyárilag összeszerelt „Complete” csomag)
    if f and (fm := _C['F'].search(c)) and _HEAD_PIECE.search(_TAIL_NOISE.sub('', c[:fm.start()])) and not _COMPLETE.search(c):
        return 'part_external'
    if _MULTI.search(c) and not has('M1'):
        return sub or ('part_external' if has('M_EXTERNAL') else 'other')     # „SorboPad AEG set 4 pcs”: több darab = nem fegyver
    if has('OTHER_MISC') and (not w or 0 < p < 40000):
        return 'other'
    explicit = (w or _EXPL.search(c) is not None) and not f
    not_weapon = 'part_external' if (has('M_EXTERNAL') or platforms(o)) else 'other'
    if not f and not sub and not has('M1') and _PISTOL_MAKER.search(c) and 6000 <= p < 100000 \
            and not _PIECE_ANY.search(c) and not any(has(k) for k, _ in _WEAPON_RULES if k != 'PISTOL') \
            and not re.search(r"\b(submachine|sniper|rifle|shotgun|smg)\b", c):
        return 'pistol'
    for k, name in _WEAPON_RULES:
        if has(k):
            if k == 'PISTOL' and not _PISTOL_MODEL.search(c) and (
                    re.search(r"\b(aeg|gbbr|ebbr?|s-aeg)\b", c) or {'m4', 'ak'} & set(platforms(o))):
                continue                      # „Colt M4 Pistol AEG”, „DDM4 V7P Pistol AEG”: rövid csövű puska, nem pisztoly
            return name if _weapon_ok(name, p, explicit) else not_weapon
    # általános fegyverszó (GBB, gas blowback, HPA…) típus nélkül: drágán fegyver; GBB 120 000 Ft alatt pisztoly, felette puska
    if explicit and p >= 6000 and has('PISTOL_POWER') and p < 120000 and not platforms(o):
        return 'pistol'                                            # „Army Armament R28 GBB”, „Rogue 11 CO2”
    if explicit and p >= 25000:
        return 'rifle'
    if has('URL_PARTS', u) and p < 40000:
        return 'part_internal'
    if has('URL_ACC', u) and p < 40000:
        return 'other'
    for k, name in _URL_TYPES:
        if has(k, u):
            return name if _weapon_ok(name, p, explicit) else not_weapon
    if not f and not sub and not has('M1') and not _PIECE_ANY.search(c) and not has('M_EXTERNAL') and not has('AMBIG_EXTERNAL') \
            and not _ENDS_X.search(_TAIL_NOISE.sub('', c)):
        if _GUN_MAKER.search(c) and 45000 <= p < 900000:
            return 'pistol' if (_C['PISTOL_POWER'].search(full) or _C['PISTOL'].search(full)) and p < 100000 else 'rifle'
    # végső tartalék: drága, de semmi nem utal fegyverre -> csak akkor puska, ha modellkód vagy platform van a címben
    if p >= 40000 and ([x for x in platforms(o) if not x.startswith('gb_')] or _MODEL_CODE.search(o)):
        return 'rifle'
    if p >= 40000 and not f and _C['STRONG_W'].search(full) and not any(_C[k].search(full) for k, _ in _SUBS):
        return 'pistol' if _C['PISTOL'].search(full) else 'rifle'
    return 'other'


def group(cat: str | None) -> str:
    if cat in WEAPONS:
        return 'weapons'
    if cat in CUSTOM:
        return 'custom'
    return 'parts' if (cat or '').startswith('part_') else 'acc'


_PLATFORMS = [
    ('m4', re.compile('(\\bm4a?1?\\b|\\bm16|\\bar-?15|\\bhk ?416|\\bmk ?18\\b|\\bcqb-?r|\\burg-?i|\\bsr-?16|\\bsa-[ce]\\d)', re.I)),
    ('ak', re.compile('(\\bak-?\\d{2,3}[a-z]{0,3}\\b|\\bakm[sn]?\\b|\\baks-?\\d{2}|\\bak ?47|\\brpk|\\bsaiga|\\bkrinkov|\\bvepr)', re.I)),
    ('g36', re.compile('\\bg36', re.I)),
    ('mp5', re.compile('\\bmp ?5', re.I)),
    ('aug', re.compile('\\baug\\b', re.I)),
    ('scar', re.compile('\\bscar', re.I)),
    ('m14', re.compile('(\\bm14\\b|\\bebr\\b)', re.I)),
    ('p90', re.compile('\\bp ?90\\b', re.I)),
    ('vsr', re.compile('(\\bvsr|\\bmb ?0?(1|2|3|4)\\b|\\bbar ?10\\b)', re.I)),
    ('l96', re.compile('(\\bl96|\\bawp\\b|\\bmb ?(44|4401|01)\\b)', re.I)),
    ('glock', re.compile('(glock|\\bg ?1[789]x?\\b)', re.I)),
    ('hicapa', re.compile('(hi-?capa|\\b1911|\\bm1911)', re.I)),
    ('m9', re.compile('(\\bm9\\b|\\bm92|\\bm9a1|beretta ?92)', re.I)),
    ('gb_v2', re.compile('((gearbox|mechabox)[^,]{0,20}\\bv ?2\\b|\\bv ?2\\b[^,]{0,20}(gearbox|mechabox))', re.I)),
    ('gb_v3', re.compile('((gearbox|mechabox)[^,]{0,20}\\bv ?3\\b|\\bv ?3\\b[^,]{0,20}(gearbox|mechabox))', re.I)),
]


def platforms(title: str | None) -> list[str]:
    t = title or ''
    return [name for name, rx in _PLATFORMS if rx.search(t)]


# Működés (hajtás): a szűrő „AEG / GBB / gáz / CO2 / rugós / HPA / AEP” értékei – fegyvereknél és alkatrészeknél is
# (alkatrésznél a „mihez jó”: „Hop-up rubber for GBB”, „gearbox V2” = AEG). Sorrend = a szűrő sorrendje.
POWERS = ['aeg', 'gbb', 'gas', 'co2', 'spring', 'hpa', 'aep']
_NBB = re.compile(r'\b(nbb|gnb|non[- ]?blow ?back)\b', re.I)
_POWER_RX = {
    'aeg': re.compile(r'\b(aeg|ebbr?|ptw|electric|elektromos|elektrick\w*|elektryczn\w*|gearbox\w*|mechabox\w*|mosfet|ngrs)\b', re.I),
    'gbb': re.compile(r'\b(gbbr?|gbber|gas ?blow ?back|blowback|mws|gbb\w*|gas ?mag\w*)\b', re.I),
    'gas': re.compile(r'\b(nbb|gnb|non[- ]?blow ?back)\b', re.I),
    'co2': re.compile(r'\bco2\b', re.I),
    'hpa': re.compile(r'\b(hpa|polar ?star|fusion engine|wolverine|inferno|mtw|reaper|heretic labs)\b', re.I),
    'aep': re.compile(r'\baep\b', re.I),
}
_SPRING_GUN = re.compile(r'\b(spring|springer|bolt[- ]action|manu[aá]l\w*|rug[oó]s|vsr-?\d*|l96|bar-?10|mb-?0\d+|ssg-?\d*)\b', re.I)
_SPRING_PART = re.compile(r'\b(vsr-?\d*|l96|bar-?10|mb-?0\d+|ssg-?\d*|bolt[- ]action|spring[- ]powered)\b', re.I)


def powers(title: str | None, gun: bool = True) -> list[str]:
    """A cím hajtás-típusai. gun=False (alkatrész/kiegészítő): a „spring” szó itt rugót jelent, nem rugós fegyvert."""
    t = title or ''
    out = {k for k, rx in _POWER_RX.items() if rx.search(t)}
    if _NBB.search(t):
        out.discard('gbb')                       # „non-blowback” ≠ GBB
    if (_SPRING_GUN if gun else _SPRING_PART).search(t) and (not gun or not out - {'co2'}):
        out.add('spring')                        # rugós fegyver: csak ha nincs más hajtás (pl. „VSR-10 GBB” gázos)
    if gun and 'aep' in out:
        out.discard('aeg')
    return [p for p in POWERS if p in out]


# Gránátok altípusa (szűrő a gránát-kategórián belül). Sorrend = a szűrő sorrendje.
GRENADE_TYPES = ['sound', 'bb', 'smoke', 'flash', 'pyro', 'launcher', 'shell', 'part']
_GT_RX = {
    'launcher': re.compile(r'(launcher|gránátvető|granatvet|lanciagranat\w*|granátomet|granatnik|\bm203\b|\bm320\b|\bm79\b|'
                           r'\bgl-?06\b|\bgp-?25\b|\bag-?36\b|milkor|\bm32\b|\brpg\b|\bat-?4\b|rocket)', re.I),
    'shell': re.compile(r'(\b40 ?mm\b.*\b(shells?|cartridges?|rounds?|grenades?|lövedék\w*|patron\w*|nábojnic\w*|granat\w*)|'
                        r'moscart|gas ?shell|cartouche|\bshells? 40)', re.I),
    'smoke': re.compile(r'(smoke|füst|fumogen\w*|\bdym\w*|kouř\w*|rauch)', re.I),
    'flash': re.compile(r'(flash ?bang|flashbang|villanó|záblesk\w*|błysk\w*|\bflash\b)', re.I),
    'sound': re.compile(r'(thunder ?b|sound|sonic|\bhang\w*|dźwięk\w*|zvukov\w*|acoustic|petard)', re.I),
    'bb': re.compile(r'(\bco2\b|\bbbs?\b|kulk\w*|kuličk\w*|impact|tornado|storm 360|\btag-?\d|spring grenade|kimera|bb-?s|szétnyíl\w*|spray)', re.I),
    'pyro': re.compile(r'(\bpyro|\bpiro|pirotechn\w*|pyrotechn\w*|p-?67|tűzijáték)', re.I),
    'part': re.compile(r'(\b(spare|part|parts|o-?rings?|seals?|pins?|adapter|valve|spring|repair|tömítés\w*|zawleczk\w*|skorup\w*|'
                       r'héj\w*|shells? for|plug|nozzle|bearings?)\b|\bfor\b|\bdo\b|\bpro\b|-hoz\b|-hez\b)', re.I),
}


def grenade_types(title: str | None, price: float | None = None) -> list[str]:
    """Gránát-altípusok egy címből (több is lehet: „Thunder B + 12 shells” = hang + alkatrész)."""
    t = title or ''
    out = {k for k, rx in _GT_RX.items() if rx.search(t)}
    if 'part' in out and price and price >= 15000 and out & {'launcher', 'sound', 'bb', 'smoke', 'flash', 'pyro'}:
        out.discard('part')                       # drága tétel: maga a gránát / gránátvető, nem alkatrész
    if 'part' in out and price and price < 8000:
        return ['part']                           # olcsó „… for/do Thunder B”, héj, gyűrű: alkatrész
    if 'launcher' in out and not re.search(r'\b(shells?|cartridges?|rounds?|lövedék\w*|patron\w*)\b', t, re.I):
        out.discard('shell')                      # „40mm Grenade Launcher” ≠ lövedék
    if out & {'launcher', 'shell'}:
        out -= {'bb', 'sound'}                    # a 40 mm-es „BB-s” lövedék nem kézigránát
    return [g for g in GRENADE_TYPES if g in out]
