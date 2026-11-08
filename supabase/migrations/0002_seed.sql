-- 0002: törzsadatok (boltok, gyártók, kategóriák) – migrációként, hogy a későbbi migrációk ráépülhessenek
-- Boltok (weboldal_pelda.txt alapján)
insert into shops (slug, name, base_url, country, currency, scraper_key) values
  ('gunfire',         'Gunfire',          'https://gunfire.com',          'PL', 'PLN', 'jsonld'),
  ('taiwangun',       'Taiwangun',        'https://www.taiwangun.com',    'PL', 'EUR', 'jsonld'),
  ('evike-europe',    'Evike Europe',     'https://evike-europe.com',     'HU', 'EUR', 'jsonld'),
  ('powair6',         'Powair6',          'https://www.powair6.com',      'FR', 'EUR', 'jsonld'),
  ('airsoftpro',      'AirsoftPro',       'https://airsoftpro.cz',        'CZ', 'CZK', 'jsonld'),
  ('combat-zone',     'Combat-Zone',      'https://www.combat-zone.hu',   'HU', 'HUF', 'jsonld'),
  ('airsoftplaza',    'AirsoftPlaza',     'https://airsoftplaza.hu',      'HU', 'HUF', 'jsonld'),
  ('airsoftcentrum',  'AirsoftCentrum',   'https://www.airsoftcentrum.hu','HU', 'HUF', 'jsonld');

-- Gyártók + aliasok (alias_norm: lowercase, csak a-z0-9)
insert into manufacturers (slug, name) values
  ('cyma','CYMA'), ('specna-arms','Specna Arms'), ('tokyo-marui','Tokyo Marui'),
  ('gg-armament','G&G Armament'), ('ares','ARES'), ('double-bell','Double Bell'),
  ('arcturus','Arcturus'), ('lct','LCT'), ('e-and-l','E&L'), ('krytac','Krytac'),
  ('vfc','VFC'), ('we','WE'), ('jg','JG'), ('arsenal','Arsenal (ASG)');

insert into manufacturer_aliases (alias_norm, manufacturer_id)
select a, m.id from manufacturers m
join (values
  ('cyma','cyma'), ('specnaarms','specna-arms'), ('specna','specna-arms'),
  ('tokyomarui','tokyo-marui'), ('marui','tokyo-marui'), ('tm','tokyo-marui'),
  ('ggarmament','gg-armament'), ('gg','gg-armament'), ('ares','ares'),
  ('doublebell','double-bell'), ('db','double-bell'), ('arcturus','arcturus'),
  ('lct','lct'), ('el','e-and-l'), ('eandl','e-and-l'), ('krytac','krytac'),
  ('vfc','vfc'), ('vegaforcecompany','vfc'), ('we','we'), ('jg','jg'),
  ('arsenal','arsenal'), ('asg','arsenal')
) v(a, slug) on v.slug = m.slug;

insert into categories (slug, name_hu) values
  ('aeg-rifle','Elektromos puskák (AEG)'), ('gbb-rifle','Gázos puskák (GBBR)'),
  ('pistol','Pisztolyok'), ('sniper','Mesterlövész puskák'), ('dmr','DMR'), ('smg','Géppisztolyok');
