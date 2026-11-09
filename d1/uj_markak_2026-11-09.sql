-- Új márkák (2026-11-09): a „brands” lista alapján. D1 → Console → az egész beillesztése → Run.
-- Újrafuttatható (INSERT OR IGNORE). Utána: GitHub → Actions → rematch → Run workflow.

-- 1) HTML-entitások javítása a már letöltött címekben („G&amp;G” → „G&G”)
UPDATE offers SET title_raw = replace(replace(title_raw, '&amp;amp;', '&'), '&amp;', '&') WHERE title_raw LIKE '%&amp;%';
UPDATE offers SET brand_raw = replace(replace(brand_raw, '&amp;amp;', '&'), '&amp;', '&') WHERE brand_raw LIKE '%&amp;%';
UPDATE products SET name = replace(replace(name, '&amp;amp;', '&'), '&amp;', '&') WHERE name LIKE '%&amp;%';

-- 2) 188 új gyártó
INSERT OR IGNORE INTO manufacturers (slug, name) VALUES
('acm','ACM'),
('retro-arms','Retro Arms'),
('pdi','PDI'),
('angel-custom','Angel Custom'),
('wosport','Wosport'),
('5ku','5KU'),
('ctm-tactical','CTM Tactical'),
('maxx-model','Maxx Model'),
('fma','FMA'),
('e-and-c','E&C'),
('epes','EPeS'),
('jtg','JTG'),
('helikon-tex','Helikon-Tex'),
('balystik','Balystik'),
('slong','Slong'),
('madbull','Madbull'),
('emerson','Emerson'),
('8fields','8Fields'),
('invader-gear','Invader Gear'),
('double-eagle','Double Eagle'),
('matrix','Matrix'),
('jj-airsoft','JJ Airsoft'),
('a-and-k','A&K'),
('army-armament','Army Armament'),
('511','5.11'),
('clawgear','Clawgear'),
('solink','SoLink'),
('t-eagle','T-Eagle'),
('pirate-arms','Pirate Arms'),
('primal-gear','Primal Gear'),
('systema','Systema'),
('mechanix','Mechanix'),
('pyramex','Pyramex'),
('6mmproshop','6mmProShop'),
('gfc','GFC'),
('ghk','GHK'),
('bluemax','Bluemax'),
('range-solutions','Range Solutions'),
('e-shooter','E-Shooter'),
('tasmanian-tiger','Tasmanian Tiger'),
('bolle','Bollé'),
('mil-tec','Mil-Tec'),
('kwc','KWC'),
('aimtop','AimTop'),
('aim-o','Aim-O'),
('earmor','Earmor'),
('hogue','Hogue'),
('t238','T238'),
('km-head','KM Head'),
('wadsn','WADSN'),
('tti-airsoft','TTI Airsoft'),
('acetech','AceTech'),
('crye-precision','Crye Precision'),
('warrior-assault-systems','Warrior Assault Systems'),
('utg','UTG'),
('vb-power','VB Power'),
('satac','SATAC'),
('armorer-works','Armorer Works'),
('bushnell','Bushnell'),
('da-vinci','Da Vinci'),
('super-shooter','Super Shooter'),
('z-tactical','Z-Tactical'),
('cygnus-armory','Cygnus Armory'),
('lambda','Lambda'),
('lambda-defence','Lambda Defence'),
('templars-gear','Templar''s Gear'),
('imperator-tactical','Imperator Tactical'),
('strike-industries','Strike Industries'),
('tnt-studio','TNT Studio'),
('101-inc','101 Inc'),
('amomax','Amomax'),
('wii-tech','Wii Tech'),
('poseidon','Poseidon'),
('armored-claw','Armored Claw'),
('airtech-studios','Airtech Studios'),
('turnigy','Turnigy'),
('cyalume','Cyalume'),
('fosco','Fosco'),
('defcon-5','Defcon 5'),
('enola-gaye','Enola Gaye'),
('foyoto','Foyoto'),
('mayflower','Mayflower'),
('zc-leopard','ZC Leopard'),
('baofeng','Baofeng'),
('protech-guns','ProTech Guns'),
('swiss-eye','Swiss Eye'),
('dboys','D-Boys'),
('fenix','Fenix'),
('m-tac','M-Tac'),
('hfc','HFC'),
('task-force-2215','Task Force 2215'),
('unicorn-airsoft','Unicorn Airsoft'),
('holosun','Holosun'),
('magpul','Magpul'),
('n8','N8'),
('raven','Raven'),
('swamp-deer','Swamp Deer'),
('zion-arms','Zion Arms'),
('storm-airsoft','Storm Airsoft'),
('pentagon','Pentagon'),
('6labs','6Labs'),
('code-red-headsets','Code Red Headsets'),
('eagle-industries','Eagle Industries'),
('energizer','Energizer'),
('hazard-4','Hazard 4'),
('shellback-tactical','Shellback Tactical'),
('s-and-t','S&T'),
('4uad','4UAD'),
('night-evolution','Night Evolution'),
('nineball','Nineball'),
('redline','Redline'),
('nitecore','Nitecore'),
('p6-workshop','P6 Workshop'),
('silent-industries','Silent Industries'),
('dytac','Dytac'),
('ess','ESS'),
('laylax','Laylax'),
('salvo-precision','Salvo Precision'),
('taginn','TAGInn'),
('tasco','Tasco'),
('orga','Orga'),
('rwa','RWA'),
('smart-gas','Smart Gas'),
('dr-black','Dr.Black'),
('bo-manufacture','BO Manufacture'),
('fps-softair','FPS Softair'),
('tac-sky','Tac-Sky'),
('maruyama','Maruyama'),
('firefield','Firefield'),
('aim-sports','Aim Sports'),
('sightmark','Sightmark'),
('echo1','Echo1'),
('mechlabs','Mechlabs'),
('kpyk','KPYK'),
('alpha-parts','Alpha Parts'),
('grey-ghost-gear','Grey Ghost Gear'),
('tactical-tailor','Tactical Tailor'),
('viper-tactical','Viper Tactical'),
('maxpedition','Maxpedition'),
('pro-arms','Pro Arms'),
('tanaka','Tanaka'),
('apfg','APFG'),
('streamlight','Streamlight'),
('barska','Barska'),
('bcm-air','BCM Air'),
('caa','CAA'),
('dye','DYE'),
('inforce','Inforce'),
('knights-armament','Knight''s Armament Airsoft'),
('victoptics','VictOptics'),
('socom-gear','Socom Gear'),
('sig-sauer','SIG Sauer'),
('amped-airsoft','Amped Airsoft'),
('cytac','Cytac'),
('siegetek','Siegetek'),
('ra-tech','RA-Tech'),
('haley-strategic','Haley Strategic'),
('hera-arms','Hera Arms'),
('gsg','GSG'),
('blackhawk','Blackhawk'),
('xtreme-precision','Xtreme Precision'),
('warhead','Warhead'),
('airsoft-artisan','Airsoft Artisan'),
('akriva','Akriva'),
('ksc','KSC'),
('marushin','Marushin'),
('valken','Valken'),
('bt-air','B&T Air'),
('prowin','ProWin'),
('speed-airsoft','Speed Airsoft'),
('tokyo-arms','Tokyo Arms'),
('primary-arms','Primary Arms'),
('vortex','Vortex'),
('daniel-defense','Daniel Defense'),
('waldo-dynamics','Waldo Dynamics'),
('gens-ace','Gens Ace'),
('wellpro','WellPro'),
('alta','Alta'),
('avatar-grenade','Avatar Grenade'),
('etiny','ETINY'),
('tapp-airsoft','Tapp Airsoft'),
('amarok','Amarok'),
('redox','Redox'),
('bb-king','BB King'),
('rothco','Rothco'),
('conquer-tactical','Conquer Tactical Gear'),
('ultimate-tactical','Ultimate Tactical'),
('topmax','TopMax');

-- 3) 239 alias (a cím / márkamező normalizált formája → gyártó); utasításonként egy (a D1 korlátozza az összetett lekérdezéseket)
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'acm', id FROM manufacturers WHERE slug = 'acm';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'allchinamade', id FROM manufacturers WHERE slug = 'acm';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'retroarms', id FROM manufacturers WHERE slug = 'retro-arms';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'pdi', id FROM manufacturers WHERE slug = 'pdi';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'angelcustom', id FROM manufacturers WHERE slug = 'angel-custom';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'wosport', id FROM manufacturers WHERE slug = 'wosport';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT '5ku', id FROM manufacturers WHERE slug = '5ku';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ctmtactical', id FROM manufacturers WHERE slug = 'ctm-tactical';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ctm', id FROM manufacturers WHERE slug = 'ctm-tactical';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'maxxmodel', id FROM manufacturers WHERE slug = 'maxx-model';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'maxxmodelproducts', id FROM manufacturers WHERE slug = 'maxx-model';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'maxx', id FROM manufacturers WHERE slug = 'maxx-model';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'fma', id FROM manufacturers WHERE slug = 'fma';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ec', id FROM manufacturers WHERE slug = 'e-and-c';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'eastandcrane', id FROM manufacturers WHERE slug = 'e-and-c';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'eastcrane', id FROM manufacturers WHERE slug = 'e-and-c';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'epes', id FROM manufacturers WHERE slug = 'epes';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'epesairsoft', id FROM manufacturers WHERE slug = 'epes';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'jtg', id FROM manufacturers WHERE slug = 'jtg';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'helikontex', id FROM manufacturers WHERE slug = 'helikon-tex';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'helikon', id FROM manufacturers WHERE slug = 'helikon-tex';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'balystik', id FROM manufacturers WHERE slug = 'balystik';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'slong', id FROM manufacturers WHERE slug = 'slong';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'slongairsoft', id FROM manufacturers WHERE slug = 'slong';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'madbull', id FROM manufacturers WHERE slug = 'madbull';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'emerson', id FROM manufacturers WHERE slug = 'emerson';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'emersongear', id FROM manufacturers WHERE slug = 'emerson';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT '8fields', id FROM manufacturers WHERE slug = '8fields';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'invadergear', id FROM manufacturers WHERE slug = 'invader-gear';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'doubleeagle', id FROM manufacturers WHERE slug = 'double-eagle';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'matrix', id FROM manufacturers WHERE slug = 'matrix';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'jjairsoft', id FROM manufacturers WHERE slug = 'jj-airsoft';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ak', id FROM manufacturers WHERE slug = 'a-and-k';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'armyarmament', id FROM manufacturers WHERE slug = 'army-armament';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT '511', id FROM manufacturers WHERE slug = '511';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT '511tactical', id FROM manufacturers WHERE slug = '511';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'clawgear', id FROM manufacturers WHERE slug = 'clawgear';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'solink', id FROM manufacturers WHERE slug = 'solink';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'teagle', id FROM manufacturers WHERE slug = 't-eagle';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'piratearms', id FROM manufacturers WHERE slug = 'pirate-arms';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'primalgear', id FROM manufacturers WHERE slug = 'primal-gear';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'systema', id FROM manufacturers WHERE slug = 'systema';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'mechanix', id FROM manufacturers WHERE slug = 'mechanix';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'mechanixwear', id FROM manufacturers WHERE slug = 'mechanix';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'pyramex', id FROM manufacturers WHERE slug = 'pyramex';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT '6mmproshop', id FROM manufacturers WHERE slug = '6mmproshop';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'gfc', id FROM manufacturers WHERE slug = 'gfc';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'gfctactical', id FROM manufacturers WHERE slug = 'gfc';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'gfcenergy', id FROM manufacturers WHERE slug = 'gfc';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ghk', id FROM manufacturers WHERE slug = 'ghk';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'bluemax', id FROM manufacturers WHERE slug = 'bluemax';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'rangesolutions', id FROM manufacturers WHERE slug = 'range-solutions';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'eshooter', id FROM manufacturers WHERE slug = 'e-shooter';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tasmaniantiger', id FROM manufacturers WHERE slug = 'tasmanian-tiger';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'bolle', id FROM manufacturers WHERE slug = 'bolle';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'bollesafety', id FROM manufacturers WHERE slug = 'bolle';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'miltec', id FROM manufacturers WHERE slug = 'mil-tec';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'kwc', id FROM manufacturers WHERE slug = 'kwc';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'aimtop', id FROM manufacturers WHERE slug = 'aimtop';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'aimo', id FROM manufacturers WHERE slug = 'aim-o';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'earmor', id FROM manufacturers WHERE slug = 'earmor';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'eararmor', id FROM manufacturers WHERE slug = 'earmor';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'hogue', id FROM manufacturers WHERE slug = 'hogue';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 't238', id FROM manufacturers WHERE slug = 't238';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'kmhead', id FROM manufacturers WHERE slug = 'km-head';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'kmhead1950', id FROM manufacturers WHERE slug = 'km-head';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'wadsn', id FROM manufacturers WHERE slug = 'wadsn';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ttiairsoft', id FROM manufacturers WHERE slug = 'tti-airsoft';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tti', id FROM manufacturers WHERE slug = 'tti-airsoft';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'acetech', id FROM manufacturers WHERE slug = 'acetech';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'cryeprecision', id FROM manufacturers WHERE slug = 'crye-precision';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'warriorassaultsystems', id FROM manufacturers WHERE slug = 'warrior-assault-systems';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'utg', id FROM manufacturers WHERE slug = 'utg';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'leapers', id FROM manufacturers WHERE slug = 'utg';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'vbpower', id FROM manufacturers WHERE slug = 'vb-power';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'satac', id FROM manufacturers WHERE slug = 'satac';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'armorerworks', id FROM manufacturers WHERE slug = 'armorer-works';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'awcustom', id FROM manufacturers WHERE slug = 'armorer-works';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'armorerworkscustom', id FROM manufacturers WHERE slug = 'armorer-works';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'bushnell', id FROM manufacturers WHERE slug = 'bushnell';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'davinci', id FROM manufacturers WHERE slug = 'da-vinci';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'davinciairsoft', id FROM manufacturers WHERE slug = 'da-vinci';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'supershooter', id FROM manufacturers WHERE slug = 'super-shooter';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'shssupershooter', id FROM manufacturers WHERE slug = 'super-shooter';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'shs', id FROM manufacturers WHERE slug = 'super-shooter';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ztactical', id FROM manufacturers WHERE slug = 'z-tactical';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ztac', id FROM manufacturers WHERE slug = 'z-tactical';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'cygnusarmory', id FROM manufacturers WHERE slug = 'cygnus-armory';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'lambda', id FROM manufacturers WHERE slug = 'lambda';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'lambdaairsoft', id FROM manufacturers WHERE slug = 'lambda';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'lambdadefence', id FROM manufacturers WHERE slug = 'lambda-defence';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'templarsgear', id FROM manufacturers WHERE slug = 'templars-gear';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'imperatortactical', id FROM manufacturers WHERE slug = 'imperator-tactical';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'strikeindustries', id FROM manufacturers WHERE slug = 'strike-industries';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tntstudio', id FROM manufacturers WHERE slug = 'tnt-studio';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tnt', id FROM manufacturers WHERE slug = 'tnt-studio';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tntairsoft', id FROM manufacturers WHERE slug = 'tnt-studio';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT '101inc', id FROM manufacturers WHERE slug = '101-inc';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'amomax', id FROM manufacturers WHERE slug = 'amomax';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'wiitech', id FROM manufacturers WHERE slug = 'wii-tech';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'poseidon', id FROM manufacturers WHERE slug = 'poseidon';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'armoredclaw', id FROM manufacturers WHERE slug = 'armored-claw';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'airtechstudios', id FROM manufacturers WHERE slug = 'airtech-studios';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'turnigy', id FROM manufacturers WHERE slug = 'turnigy';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'cyalume', id FROM manufacturers WHERE slug = 'cyalume';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'fosco', id FROM manufacturers WHERE slug = 'fosco';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'defcon5', id FROM manufacturers WHERE slug = 'defcon-5';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'enolagaye', id FROM manufacturers WHERE slug = 'enola-gaye';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'foyoto', id FROM manufacturers WHERE slug = 'foyoto';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'mayflower', id FROM manufacturers WHERE slug = 'mayflower';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'mayflowerresearch', id FROM manufacturers WHERE slug = 'mayflower';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'zcleopard', id FROM manufacturers WHERE slug = 'zc-leopard';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'baofeng', id FROM manufacturers WHERE slug = 'baofeng';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'protechguns', id FROM manufacturers WHERE slug = 'protech-guns';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'protech', id FROM manufacturers WHERE slug = 'protech-guns';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'swisseye', id FROM manufacturers WHERE slug = 'swiss-eye';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'swisseyetactical', id FROM manufacturers WHERE slug = 'swiss-eye';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'dboys', id FROM manufacturers WHERE slug = 'dboys';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'boyi', id FROM manufacturers WHERE slug = 'dboys';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'fenix', id FROM manufacturers WHERE slug = 'fenix';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'mtac', id FROM manufacturers WHERE slug = 'm-tac';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'hfc', id FROM manufacturers WHERE slug = 'hfc';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'taskforce2215', id FROM manufacturers WHERE slug = 'task-force-2215';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'unicornairsoft', id FROM manufacturers WHERE slug = 'unicorn-airsoft';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'holosun', id FROM manufacturers WHERE slug = 'holosun';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'magpul', id FROM manufacturers WHERE slug = 'magpul';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'magpulpts', id FROM manufacturers WHERE slug = 'magpul';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'n8', id FROM manufacturers WHERE slug = 'n8';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'raven', id FROM manufacturers WHERE slug = 'raven';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'swampdeer', id FROM manufacturers WHERE slug = 'swamp-deer';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'zionarms', id FROM manufacturers WHERE slug = 'zion-arms';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'stormairsoft', id FROM manufacturers WHERE slug = 'storm-airsoft';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'pentagon', id FROM manufacturers WHERE slug = 'pentagon';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT '6labs', id FROM manufacturers WHERE slug = '6labs';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'coderedheadsets', id FROM manufacturers WHERE slug = 'code-red-headsets';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'eagleindustries', id FROM manufacturers WHERE slug = 'eagle-industries';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'energizer', id FROM manufacturers WHERE slug = 'energizer';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'hazard4', id FROM manufacturers WHERE slug = 'hazard-4';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'shellbacktactical', id FROM manufacturers WHERE slug = 'shellback-tactical';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'st', id FROM manufacturers WHERE slug = 's-and-t';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'starmament', id FROM manufacturers WHERE slug = 's-and-t';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT '4uad', id FROM manufacturers WHERE slug = '4uad';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT '4uantum', id FROM manufacturers WHERE slug = '4uad';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT '4uadsmartairsoft', id FROM manufacturers WHERE slug = '4uad';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'nightevolution', id FROM manufacturers WHERE slug = 'night-evolution';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'nineball', id FROM manufacturers WHERE slug = 'nineball';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'redline', id FROM manufacturers WHERE slug = 'redline';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'nitecore', id FROM manufacturers WHERE slug = 'nitecore';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'p6workshop', id FROM manufacturers WHERE slug = 'p6-workshop';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'silentindustries', id FROM manufacturers WHERE slug = 'silent-industries';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'dytac', id FROM manufacturers WHERE slug = 'dytac';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ess', id FROM manufacturers WHERE slug = 'ess';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'laylax', id FROM manufacturers WHERE slug = 'laylax';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'salvoprecision', id FROM manufacturers WHERE slug = 'salvo-precision';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'taginn', id FROM manufacturers WHERE slug = 'taginn';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tasco', id FROM manufacturers WHERE slug = 'tasco';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'orga', id FROM manufacturers WHERE slug = 'orga';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'orgamagnus', id FROM manufacturers WHERE slug = 'orga';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'rwa', id FROM manufacturers WHERE slug = 'rwa';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'smartgas', id FROM manufacturers WHERE slug = 'smart-gas';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'drblack', id FROM manufacturers WHERE slug = 'dr-black';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'bomanufacture', id FROM manufacturers WHERE slug = 'bo-manufacture';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'fpssoftair', id FROM manufacturers WHERE slug = 'fps-softair';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tacsky', id FROM manufacturers WHERE slug = 'tac-sky';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'maruyama', id FROM manufacturers WHERE slug = 'maruyama';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'firefield', id FROM manufacturers WHERE slug = 'firefield';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'aimsports', id FROM manufacturers WHERE slug = 'aim-sports';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'sightmark', id FROM manufacturers WHERE slug = 'sightmark';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'echo1', id FROM manufacturers WHERE slug = 'echo1';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'mechlabs', id FROM manufacturers WHERE slug = 'mechlabs';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'kpyk', id FROM manufacturers WHERE slug = 'kpyk';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'kpykindustries', id FROM manufacturers WHERE slug = 'kpyk';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'alphaparts', id FROM manufacturers WHERE slug = 'alpha-parts';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'greyghostgear', id FROM manufacturers WHERE slug = 'grey-ghost-gear';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tacticaltailor', id FROM manufacturers WHERE slug = 'tactical-tailor';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'vipertactical', id FROM manufacturers WHERE slug = 'viper-tactical';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'maxpedition', id FROM manufacturers WHERE slug = 'maxpedition';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'proarms', id FROM manufacturers WHERE slug = 'pro-arms';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tanaka', id FROM manufacturers WHERE slug = 'tanaka';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tanakaworks', id FROM manufacturers WHERE slug = 'tanaka';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'apfg', id FROM manufacturers WHERE slug = 'apfg';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'streamlight', id FROM manufacturers WHERE slug = 'streamlight';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'barska', id FROM manufacturers WHERE slug = 'barska';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'bcmair', id FROM manufacturers WHERE slug = 'bcm-air';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'caa', id FROM manufacturers WHERE slug = 'caa';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'caaairsoftdivision', id FROM manufacturers WHERE slug = 'caa';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'caatactical', id FROM manufacturers WHERE slug = 'caa';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'dye', id FROM manufacturers WHERE slug = 'dye';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'inforce', id FROM manufacturers WHERE slug = 'inforce';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'knightsarmamentairsoft', id FROM manufacturers WHERE slug = 'knights-armament';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'knightsarmament', id FROM manufacturers WHERE slug = 'knights-armament';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'victoptics', id FROM manufacturers WHERE slug = 'victoptics';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'socomgear', id FROM manufacturers WHERE slug = 'socom-gear';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'sigsauer', id FROM manufacturers WHERE slug = 'sig-sauer';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'sigair', id FROM manufacturers WHERE slug = 'sig-sauer';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'proforce', id FROM manufacturers WHERE slug = 'sig-sauer';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ampedairsoft', id FROM manufacturers WHERE slug = 'amped-airsoft';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'cytac', id FROM manufacturers WHERE slug = 'cytac';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'siegetek', id FROM manufacturers WHERE slug = 'siegetek';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ratech', id FROM manufacturers WHERE slug = 'ra-tech';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'haleystrategic', id FROM manufacturers WHERE slug = 'haley-strategic';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'heraarms', id FROM manufacturers WHERE slug = 'hera-arms';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'gsg', id FROM manufacturers WHERE slug = 'gsg';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'blackhawk', id FROM manufacturers WHERE slug = 'blackhawk';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'xtremeprecision', id FROM manufacturers WHERE slug = 'xtreme-precision';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'warhead', id FROM manufacturers WHERE slug = 'warhead';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'airsoftartisan', id FROM manufacturers WHERE slug = 'airsoft-artisan';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'akriva', id FROM manufacturers WHERE slug = 'akriva';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ksc', id FROM manufacturers WHERE slug = 'ksc';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'marushin', id FROM manufacturers WHERE slug = 'marushin';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'valken', id FROM manufacturers WHERE slug = 'valken';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'btair', id FROM manufacturers WHERE slug = 'bt-air';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'prowin', id FROM manufacturers WHERE slug = 'prowin';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'speedairsoft', id FROM manufacturers WHERE slug = 'speed-airsoft';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tokyoarms', id FROM manufacturers WHERE slug = 'tokyo-arms';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'primaryarms', id FROM manufacturers WHERE slug = 'primary-arms';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'vortex', id FROM manufacturers WHERE slug = 'vortex';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'danieldefense', id FROM manufacturers WHERE slug = 'daniel-defense';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'waldodynamics', id FROM manufacturers WHERE slug = 'waldo-dynamics';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'gensace', id FROM manufacturers WHERE slug = 'gens-ace';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'wellpro', id FROM manufacturers WHERE slug = 'wellpro';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'alta', id FROM manufacturers WHERE slug = 'alta';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'altaindustries', id FROM manufacturers WHERE slug = 'alta';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'altatactical', id FROM manufacturers WHERE slug = 'alta';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'avatargrenade', id FROM manufacturers WHERE slug = 'avatar-grenade';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'etiny', id FROM manufacturers WHERE slug = 'etiny';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'tappairsoft', id FROM manufacturers WHERE slug = 'tapp-airsoft';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'amarok', id FROM manufacturers WHERE slug = 'amarok';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'redox', id FROM manufacturers WHERE slug = 'redox';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'bbking', id FROM manufacturers WHERE slug = 'bb-king';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'rothco', id FROM manufacturers WHERE slug = 'rothco';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'conquertacticalgear', id FROM manufacturers WHERE slug = 'conquer-tactical';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'ultimatetactical', id FROM manufacturers WHERE slug = 'ultimate-tactical';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'topmax', id FROM manufacturers WHERE slug = 'topmax';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'jinggong', id FROM manufacturers WHERE slug = 'jg';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'kjw', id FROM manufacturers WHERE slug = 'kj-works';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'aresamoeba', id FROM manufacturers WHERE slug = 'amoeba';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'silverbackairsoft', id FROM manufacturers WHERE slug = 'silverback';
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'arcturustactical', id FROM manufacturers WHERE slug = 'arcturus';

SELECT (SELECT count(*) FROM manufacturers) AS gyartok, (SELECT count(*) FROM manufacturer_aliases) AS aliasok;
