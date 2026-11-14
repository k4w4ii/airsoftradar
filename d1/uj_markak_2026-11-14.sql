-- Új márkák (2026-11-14): a párosításra váró (pending) ajánlatok leggyakoribb, airsoftos márkái (kb. 1000 ajánlat).
-- D1 → Console → az egész beillesztése → Run. Újrafuttatható.
-- Kimaradt (szándékosan): kések, paintball, légpuska (Morakniv, Spyderco, JSB, Hatsan, HK Army…) és a túl általános
-- szavak (Metal, Point, Source, Glock, Royal, Fuel, Evolution…), mert a címekben sok rossz találatot adnának.

INSERT INTO manufacturers (slug, name) SELECT 'delta-six', 'Delta Six' WHERE NOT EXISTS (SELECT 1 FROM manufacturers WHERE lower(name) = lower('Delta Six') OR slug = 'delta-six');
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'deltasix', id FROM manufacturers WHERE lower(name) = lower('Delta Six') OR slug = 'delta-six' ORDER BY id LIMIT 1;
INSERT INTO manufacturers (slug, name) SELECT 'powair', 'PowAir' WHERE NOT EXISTS (SELECT 1 FROM manufacturers WHERE lower(name) = lower('PowAir') OR slug = 'powair');
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'powair', id FROM manufacturers WHERE lower(name) = lower('PowAir') OR slug = 'powair' ORDER BY id LIMIT 1;
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'powair6', id FROM manufacturers WHERE lower(name) = lower('PowAir') OR slug = 'powair' ORDER BY id LIMIT 1;
INSERT INTO manufacturers (slug, name) SELECT 'griffon-industries', 'Griffon Industries' WHERE NOT EXISTS (SELECT 1 FROM manufacturers WHERE lower(name) = lower('Griffon Industries') OR slug = 'griffon-industries');
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'griffonindustries', id FROM manufacturers WHERE lower(name) = lower('Griffon Industries') OR slug = 'griffon-industries' ORDER BY id LIMIT 1;
INSERT INTO manufacturers (slug, name) SELECT 'dasta', 'Dasta' WHERE NOT EXISTS (SELECT 1 FROM manufacturers WHERE lower(name) = lower('Dasta') OR slug = 'dasta');
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'dasta', id FROM manufacturers WHERE lower(name) = lower('Dasta') OR slug = 'dasta' ORDER BY id LIMIT 1;
INSERT INTO manufacturers (slug, name) SELECT 'imaxrc', 'iMaxRC' WHERE NOT EXISTS (SELECT 1 FROM manufacturers WHERE lower(name) = lower('iMaxRC') OR slug = 'imaxrc');
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'imaxrc', id FROM manufacturers WHERE lower(name) = lower('iMaxRC') OR slug = 'imaxrc' ORDER BY id LIMIT 1;
INSERT INTO manufacturers (slug, name) SELECT 'toparms', 'TopArms' WHERE NOT EXISTS (SELECT 1 FROM manufacturers WHERE lower(name) = lower('TopArms') OR slug = 'toparms');
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'toparms', id FROM manufacturers WHERE lower(name) = lower('TopArms') OR slug = 'toparms' ORDER BY id LIMIT 1;
INSERT INTO manufacturers (slug, name) SELECT 'cl-project-design', 'CL Project Design' WHERE NOT EXISTS (SELECT 1 FROM manufacturers WHERE lower(name) = lower('CL Project Design') OR slug = 'cl-project-design');
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'clprojectdesign', id FROM manufacturers WHERE lower(name) = lower('CL Project Design') OR slug = 'cl-project-design' ORDER BY id LIMIT 1;
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'clpd', id FROM manufacturers WHERE lower(name) = lower('CL Project Design') OR slug = 'cl-project-design' ORDER BY id LIMIT 1;
INSERT INTO manufacturers (slug, name) SELECT 'maxtact', 'Maxtact' WHERE NOT EXISTS (SELECT 1 FROM manufacturers WHERE lower(name) = lower('Maxtact') OR slug = 'maxtact');
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'maxtact', id FROM manufacturers WHERE lower(name) = lower('Maxtact') OR slug = 'maxtact' ORDER BY id LIMIT 1;
INSERT INTO manufacturers (slug, name) SELECT 'xcrs', 'XCRS' WHERE NOT EXISTS (SELECT 1 FROM manufacturers WHERE lower(name) = lower('XCRS') OR slug = 'xcrs');
INSERT OR IGNORE INTO manufacturer_aliases (alias_norm, manufacturer_id) SELECT 'xcrs', id FROM manufacturers WHERE lower(name) = lower('XCRS') OR slug = 'xcrs' ORDER BY id LIMIT 1;
