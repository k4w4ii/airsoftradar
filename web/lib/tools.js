// Kalkulátorok: útvonalak és SEO-tartalom (cím, leírás, bevezető, „hogyan számol”, GYIK). A számítás: lib/toolcalc.js.
export const TOOLS = [
  { slug: "fps-joule-calculator", icon: "bolt" },
  { slug: "spring-motor-calculator", icon: "spring" },
  { slug: "cylinder-volume-ratio", icon: "cylinder" },
  { slug: "lipo-rof-calculator", icon: "battery" },
];
export const toolBySlug = (slug) => TOOLS.find((t) => t.slug === slug) || null;
export const toolPath = (locale, slug) => `/${locale}/tools${slug ? `/${slug}` : ""}`;

export const TOOLS_INDEX = {
  hu: {
    nav: "Kalkulátorok",
    title: "Airsoft kalkulátorok – FPS, Joule, rugó, henger, LiPo",
    description: "Ingyenes airsoft kalkulátorok: FPS–Joule átváltás bármilyen BB-súllyal, rugó- és motorválasztó, henger–cső térfogatarány, LiPo és tűzgyorsaság.",
    h1: "Airsoft kalkulátorok",
    intro: "Tuningolás, kronózás vagy akkuvásárlás előtt: számold ki pár másodperc alatt, és nézd meg mellette a hozzá illő, raktáron lévő termékeket a legolcsóbb európai boltokból.",
    open: "Megnyitom",
    others: "További kalkulátorok",
    how: "Hogyan számol?",
    faq: "Gyakori kérdések",
    disclaimer: "A rugó-, motor- és hengerajánlás tapasztalati közelítés: a valódi érték a légzárástól, a hop-uptól és az alkatrészek minőségétől is függ. Mindig kronózz!",
  },
  en: {
    nav: "Tools",
    title: "Airsoft calculators – FPS, Joule, spring, cylinder, LiPo",
    description: "Free airsoft calculators: FPS to Joule with any BB weight, spring and motor picker, cylinder to barrel volume ratio, LiPo and rate of fire.",
    h1: "Airsoft calculators",
    intro: "Before upgrading, chronographing or buying a battery: get the numbers in seconds, with matching in-stock products from the cheapest European shops next to them.",
    open: "Open",
    others: "More calculators",
    how: "How does it work?",
    faq: "FAQ",
    disclaimer: "Spring, motor and cylinder suggestions are empirical estimates: real results also depend on air seal, hop-up and part quality. Always chrono your gun!",
  },
};

export const TOOL_TEXT = {
  "fps-joule-calculator": {
    hu: {
      card: "Mért FPS vagy m/s átváltása Joule-ra bármilyen BB-súllyal, illő BB-kkel.",
      name: "FPS / Joule / BB súly kalkulátor",
      title: "FPS Joule kalkulátor BB súllyal – torkolati energia számítás",
      description: "Számold át a kronón mért FPS-t vagy m/s-t torkolati energiára (Joule) bármilyen BB-súllyal 0,20 és 0,48 g között, és nézd meg a hozzá illő BB-ket az európai boltokból.",
      h1: "FPS / Joule / BB súly kalkulátor",
      intro: "Add meg a kronón mért sebességet és a használt BB súlyát: megkapod a torkolati energiát Joule-ban, alatta pedig az ehhez az energiához illő, raktáron lévő BB-ket.",
      how: [
        "A torkolati energia E = ½ · m · v², ahol m a BB tömege kilogrammban, v a sebesség m/s-ban (1 m/s = 3,28 fps). Például 0,25 g-os BB 110 m/s-mal: 0,5 · 0,00025 · 110² ≈ 1,51 J.",
        "Ugyanaz a sebesség nehezebb BB-vel nagyobb energiát jelent: 380 fps 0,20 g-mal ≈ 1,34 J, 0,25 g-mal már ≈ 1,68 J. Ezért a mért értékhez mindig add meg a használt BB súlyát.",
        "A „Joule creep” miatt egyes (főleg gázos és HPA) fegyvereknél nehezebb BB-vel nő az energia, ezért a határ ellenőrzéséhez azzal a BB-vel kronózz, amivel játszol.",
      ],
      faq: [
        ["Mennyi 400 fps Joule-ban?", "0,20 g-os BB-vel 400 fps (≈ 122 m/s) körülbelül 1,49 J, 0,25 g-os BB-vel ugyanez a sebesség ≈ 1,86 J."],
        ["Milyen súlyú BB-t használjak?", "Nagyobb energiához nehezebb BB stabilabb: ~1 J alatt 0,20–0,25 g, 1,2–1,5 J között 0,28–0,30 g, 2 J felett 0,36–0,40 g, 3 J körül 0,40–0,48 g."],
        ["Ugyanannyi lesz az energia nehezebb BB-vel?", "AEG-nél jellemzően közel azonos vagy kicsit nagyobb, gázos és HPA fegyvernél érezhetően nőhet (Joule creep). Ezért a saját BB-ddel mérd."],
      ],
    },
    en: {
      card: "Convert measured FPS or m/s to Joule with any BB weight, with matching BBs.",
      name: "FPS / Joule / BB weight calculator",
      title: "FPS to Joule calculator with BB weight – muzzle energy",
      description: "Convert your chrono reading in FPS or m/s to muzzle energy (Joule) with any BB weight from 0.20 to 0.48 g, and see matching BBs from European shops.",
      h1: "FPS / Joule / BB weight calculator",
      intro: "Enter the chrono reading and the BB weight you used: you get the muzzle energy in Joule, with in-stock BBs that suit that energy below.",
      how: [
        "Muzzle energy is E = ½ · m · v², with m the BB mass in kg and v the speed in m/s (1 m/s = 3.28 fps). Example: a 0.25 g BB at 110 m/s gives 0.5 · 0.00025 · 110² ≈ 1.51 J.",
        "The same speed means more energy with a heavier BB: 380 fps is ≈ 1.34 J with 0.20 g but ≈ 1.68 J with 0.25 g. That is why you always need the BB weight next to the reading.",
        "Because of “Joule creep”, some guns (mostly gas and HPA) gain energy with heavier BBs, so chrono with the BB you actually play with.",
      ],
      faq: [
        ["How many Joule is 400 fps?", "With 0.20 g BBs, 400 fps (≈ 122 m/s) is about 1.49 J; the same speed with 0.25 g BBs is ≈ 1.86 J."],
        ["Which BB weight should I use?", "Higher energy is more stable with heavier BBs: below ~1 J 0.20–0.25 g, 1.2–1.5 J 0.28–0.30 g, above 2 J 0.36–0.40 g, around 3 J 0.40–0.48 g."],
        ["Is the energy the same with heavier BBs?", "With AEGs it is usually similar or slightly higher; gas and HPA guns can gain noticeably (Joule creep). Measure with your own BBs."],
      ],
    },
  },
  "spring-motor-calculator": {
    hu: {
      card: "Célenergia + csőhossz + áttétel alapján ajánlott M-rugó és motor.",
      name: "AEG rugó- és motorválasztó",
      title: "AEG rugó és motor kalkulátor – M90–M150 rugó, áttétel, TPA",
      description: "Melyik rugó kell a cél FPS-hez? Add meg a célenergiát, a belső cső hosszát és a fogaskerék-áttételt: ajánlott M-rugó (M90–M150) és motortípus (TPA).",
      h1: "AEG rugó- és motorválasztó kalkulátor",
      intro: "Add meg, mekkora energiát szeretnél (Joule-ban vagy 0,20 g-os FPS-ben), milyen hosszú a belső cső és milyen áttételű a fogaskerék-szett: megkapod az ajánlott rugóerősséget és a hozzá illő motortípust.",
      how: [
        "Kiindulás: egy jó légzárású, 363 mm-es csövű AEG-ben az M100-as rugó kb. 330 fps-t ad 0,20 g-os BB-vel, és M10-enként ≈ 30 fps-sel nő.",
        "A csőhossz módosítja a hatásfokot: 250 mm alatti csőben a levegő egy része „elfogy”, mire a BB kiér (≈ 6–10% veszteség), 450–510 mm-es csőben kis többlet van. A kalkulátor ezzel korrigál.",
        "A motorterhelés a rugóerő és az áttétel viszonya: rövid (13:1, 16:1) áttételnél ugyanaz a rugó jóval nehezebb feladat, ezért ott nyomatékosabb (22+ TPA) motor és 11,1 V ajánlott.",
      ],
      faq: [
        ["Milyen rugó kell 1,5 J-hoz?", "363 mm-es csővel, jó légzárással jellemzően M120–M125 körül; rövidebb csőnél eggyel erősebb, hosszabbnál eggyel gyengébb rugó kell. Kronóval ellenőrizd!"],
        ["Mit jelent a TPA?", "Turns Per Armature: a motor tekercsének menetszáma. Több menet = nagyobb nyomaték, kisebb fordulatszám (High Torque); kevesebb = gyorsabb, de gyengébb (High Speed)."],
        ["Melyik áttételt válasszam?", "18:1 – kiegyensúlyozott, sokoldalú; 16:1 – gyorsabb, erősebb motort kér; 13:1 – nagy tűzgyorsaság, erős motor + 11,1 V + MOSFET kell; 32:1 – erős rugókhoz (DMR)."],
      ],
    },
    en: {
      card: "Recommended M-spring and motor from target energy, barrel length and gear ratio.",
      name: "AEG spring and motor picker",
      title: "AEG spring and motor calculator – M90–M150 spring, gear ratio, TPA",
      description: "Which spring do you need for your target FPS? Enter target energy, inner barrel length and gear ratio to get the recommended M-spring (M90–M150) and motor type (TPA).",
      h1: "AEG spring and motor calculator",
      intro: "Enter the energy you want (in Joule or 0.20 g FPS), your inner barrel length and gear ratio: you get the recommended spring strength and the motor type that fits it.",
      how: [
        "Baseline: in a well-sealed AEG with a 363 mm barrel, an M100 spring gives about 330 fps with 0.20 g BBs, adding roughly 30 fps per M10.",
        "Barrel length changes efficiency: below 250 mm part of the air is wasted before the BB leaves (≈ 6–10% loss), 450–510 mm barrels give a small gain. The calculator corrects for this.",
        "Motor load is spring strength relative to gear ratio: with short ratios (13:1, 16:1) the same spring is much harder to pull, so a high-torque (22+ TPA) motor and 11.1 V are recommended.",
      ],
      faq: [
        ["Which spring do I need for 1.5 J?", "With a 363 mm barrel and a good seal, typically around M120–M125; one step stronger for shorter barrels, one weaker for longer ones. Always chrono!"],
        ["What does TPA mean?", "Turns Per Armature: the number of winding turns. More turns = more torque, lower speed (high torque); fewer = faster but weaker (high speed)."],
        ["Which gear ratio should I choose?", "18:1 – balanced; 16:1 – faster, needs a stronger motor; 13:1 – high rate of fire, needs a strong motor, 11.1 V and a MOSFET; 32:1 – for strong springs (DMR)."],
      ],
    },
  },
  "cylinder-volume-ratio": {
    hu: {
      card: "Cső- és hengertérfogat aránya, ajánlott Type 0–4 henger a BB-súlyhoz.",
      name: "Henger–belső cső térfogatarány",
      title: "Henger cső térfogatarány kalkulátor – Type 0, 1, 2, 3, 4 henger választás",
      description: "Melyik henger kell a belső csőhöz? Add meg a cső hosszát, átmérőjét és a BB súlyát: térfogatarány és ajánlott henger (Type 0 teljes vagy Type 1–4 furatolt).",
      h1: "Henger–belső cső térfogatarány kalkulátor",
      intro: "A jó légzárás mellett a henger és a belső cső térfogatának aránya határozza meg, mennyire hatékony a lövés. Add meg a cső hosszát, átmérőjét és a BB súlyát: megkapod az arányt és az ajánlott hengertípust.",
      how: [
        "A cső térfogata V = π · (d/2)² · L. Egy teljes (Type 0) AEG henger hasznos térfogata ≈ 22 000 mm³ (Ø 24 mm × 49 mm löket); a furatolt Type 1–4 hengereknél a furat előtti rész nem nyom levegőt, így kisebb a hasznos térfogat.",
        "Ideális arány: 0,20 g-os BB-hez ≈ 1,4 : 1, nehezebb BB-hez több levegő kell (0,25 g ≈ 1,55, 0,30 g ≈ 1,7, 0,40 g ≈ 2,0). Kevés levegő: a BB lassul a csőben; túl sok: a felesleg kárba vész és instabilabb lehet a lövés.",
        "Ökölszabály csőhossz szerint (0,25 g): 450–550 mm → Type 0, 400–450 mm → Type 1, 300–400 mm → Type 2, 250–300 mm → Type 3, 250 mm alatt → Type 4.",
      ],
      faq: [
        ["Mi a különbség a Type 0 és a Type 1–4 henger között?", "A Type 0 zárt (furatolatlan), teljes térfogatú henger; a Type 1–4 hengerek oldalán furat van, ami csökkenti a hasznos térfogatot – minél nagyobb a szám, annál rövidebb csőhöz való."],
        ["363 mm-es csőhöz melyik henger kell?", "0,25 g-os BB-vel jellemzően Type 2; 0,20 g-mal Type 3, 0,30 g felett Type 1 felé érdemes menni."],
        ["Számít a cső átmérője?", "Kicsit: egy 6,08 mm-es cső kb. 1,7%-kal nagyobb térfogatú, mint egy 6,03-as, ez határesetben egy típusnyi különbség lehet."],
      ],
    },
    en: {
      card: "Barrel and cylinder volume ratio, recommended Type 0–4 cylinder for your BB.",
      name: "Cylinder to barrel volume ratio",
      title: "Cylinder to barrel volume ratio calculator – Type 0, 1, 2, 3, 4 cylinder",
      description: "Which cylinder fits your inner barrel? Enter barrel length, bore and BB weight to get the volume ratio and the recommended cylinder (Type 0 full or Type 1–4 ported).",
      h1: "Cylinder to barrel volume ratio calculator",
      intro: "Besides a good air seal, the ratio of cylinder volume to inner barrel volume decides how efficient the shot is. Enter barrel length, bore and BB weight to get the ratio and the recommended cylinder type.",
      how: [
        "Barrel volume is V = π · (d/2)² · L. A full (Type 0) AEG cylinder has about 22,000 mm³ of usable volume (Ø 24 mm × 49 mm stroke); ported Type 1–4 cylinders do not push air before the port, so their usable volume is smaller.",
        "Ideal ratio: about 1.4 : 1 for 0.20 g BBs, more air for heavier BBs (0.25 g ≈ 1.55, 0.30 g ≈ 1.7, 0.40 g ≈ 2.0). Too little air slows the BB in the barrel; too much is wasted and can make shots less consistent.",
        "Rule of thumb by barrel length (0.25 g): 450–550 mm → Type 0, 400–450 mm → Type 1, 300–400 mm → Type 2, 250–300 mm → Type 3, below 250 mm → Type 4.",
      ],
      faq: [
        ["What is the difference between Type 0 and Type 1–4 cylinders?", "Type 0 is a full, unported cylinder; Type 1–4 have a port on the side that reduces usable volume – the higher the number, the shorter the barrel it suits."],
        ["Which cylinder for a 363 mm barrel?", "With 0.25 g BBs typically Type 2; Type 3 for 0.20 g, towards Type 1 above 0.30 g."],
        ["Does the bore matter?", "A little: a 6.08 mm barrel has about 1.7% more volume than a 6.03 mm one, which can mean one type in borderline cases."],
      ],
    },
  },
  "lipo-rof-calculator": {
    hu: {
      card: "Max. áram (mAh × C), lövésszám egy töltéssel és becsült tűzgyorsaság.",
      name: "LiPo / Li-Ion akku és ROF kalkulátor",
      title: "LiPo akku kalkulátor – C érték, amper, lövésszám és ROF (BB/s)",
      description: "Mennyit bír az akku? Feszültség, kapacitás és C-érték alapján maximális áram, becsült lövésszám egy töltéssel, és motor-fordulatszám + áttétel alapján tűzgyorsaság (ROF).",
      h1: "LiPo / Li-Ion akku- és tűzgyorsaság (ROF) kalkulátor",
      intro: "Add meg az akku feszültségét, kapacitását és C-értékét, opcionálisan a motor fordulatszámát és az áttételt: megkapod a maximális folyamatos áramot, a becsült lövésszámot és a várható tűzgyorsaságot.",
      how: [
        "Maximális folyamatos áram = kapacitás (Ah) × C-érték. Egy 1600 mAh-s, 25C-s akku: 1,6 × 25 = 40 A. Egy átlagos AEG indításkor 20–40 A-t is kérhet, erős rugóval ennél többet.",
        "Lövésszám: ökölszabály szerint mAh-nként 1,5–2 lövés (rugótól, motortól, áttételtől függ) – egy 1600 mAh-s akku így kb. 2400–3200 lövés.",
        "Tűzgyorsaság: egy lövéshez a szektorkeréknek egyszer kell körbefordulnia, ami „áttételnyi” motorfordulat. ROF ≈ fordulatszám × (feszültség / 11,1) × 0,75 / áttétel / 60 – a 0,75 a terhelés alatti lassulás.",
      ],
      faq: [
        ["7,4 V vagy 11,1 V LiPo?", "A 7,4 V a legtöbb gyári AEG-hez elég és kíméli a kapcsolót; a 11,1 V gyorsabb ravaszreakciót és nagyobb tűzgyorsaságot ad, de MOSFET ajánlott hozzá."],
        ["Mit jelent a C-érték?", "A kisütési ráta: hányszorosa lehet a kapacitásnak a folyamatos áram. 20–25C a legtöbb AEG-hez bőven elég; nagyobb C ritkán ad érezhető előnyt."],
        ["Mennyi lövés jön ki egy töltésből?", "Durván mAh-nként 1,5–2 lövés; erős rugóval, rövid áttétellel a sáv alja, gyári beállítással a teteje a reális."],
      ],
    },
    en: {
      card: "Max. current (mAh × C), shots per charge and estimated rate of fire.",
      name: "LiPo / Li-Ion battery and ROF calculator",
      title: "LiPo battery calculator – C rating, amps, shots per charge and ROF",
      description: "How much can your battery deliver? Max. continuous current from voltage, capacity and C rating, estimated shots per charge, and rate of fire from motor RPM and gear ratio.",
      h1: "LiPo / Li-Ion battery and rate of fire (ROF) calculator",
      intro: "Enter voltage, capacity and C rating, optionally motor RPM and gear ratio: you get the max. continuous current, estimated shots per charge and expected rate of fire.",
      how: [
        "Max. continuous current = capacity (Ah) × C rating. A 1600 mAh 25C battery: 1.6 × 25 = 40 A. An average AEG can draw 20–40 A on start-up, more with a strong spring.",
        "Shots: as a rule of thumb 1.5–2 shots per mAh (depends on spring, motor and gears) – about 2,400–3,200 shots from a 1600 mAh pack.",
        "Rate of fire: each shot needs one turn of the sector gear, which equals “gear ratio” motor turns. ROF ≈ RPM × (voltage / 11.1) × 0.75 / ratio / 60 – the 0.75 accounts for slow-down under load.",
      ],
      faq: [
        ["7.4 V or 11.1 V LiPo?", "7.4 V is enough for most stock AEGs and is easy on the trigger contacts; 11.1 V gives faster trigger response and higher rate of fire, but a MOSFET is recommended."],
        ["What does the C rating mean?", "The discharge rate: how many times the capacity the continuous current can be. 20–25C is plenty for most AEGs; higher C rarely makes a noticeable difference."],
        ["How many shots per charge?", "Roughly 1.5–2 shots per mAh; the low end with strong springs and short gear ratios, the high end with stock setups."],
      ],
    },
  },
};

export const toolText = (slug, locale) => TOOL_TEXT[slug]?.[locale === "hu" ? "hu" : "en"] || null;
