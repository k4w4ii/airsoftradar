-- =====================================================================
-- 0008: 12 új EU-s bolt (UK nélkül) + Evike Europe valójában francia + néhány új gyártó.
-- Adatot NEM töröl. Újrafuttatható.
-- =====================================================================
update shops set country = 'FR', lang = 'en' where slug = 'evike-europe';

insert into shops (slug, name, base_url, country, currency, scraper_key, lang) values
  ('begadi',          'Begadi',          'https://www.begadi.com',        'DE', 'EUR', 'jsonld', 'de'),
  ('airsoftsports',   'Airsoft Sports',  'https://airsoftsports.de',      'DE', 'EUR', 'jsonld', 'de'),
  ('airsoft-guns-eu', 'AirsoftGuns.eu',  'https://www.airsoft-guns.eu',   'CZ', 'EUR', 'jsonld', 'en'),
  ('airsoftmania',    'Airsoftmania',    'https://airsoftmania.eu',       'IT', 'EUR', 'jsonld', 'en'),
  ('gunshot',         'Gunshot',         'https://www.gunshot.it',        'IT', 'EUR', 'jsonld', 'it'),
  ('vsgun',           'VSGUN',           'https://www.vsgun.com',         'ES', 'EUR', 'jsonld', 'es'),
  ('airsoft-legends', 'Airsoft Legends', 'https://www.airsoft-legends.nl','NL', 'EUR', 'jsonld', 'nl'),
  ('bunker501',       'Bunker501',       'https://www.bunker501.nl',      'NL', 'EUR', 'jsonld', 'nl'),
  ('phenixairsoft',   'Phenix Airsoft',  'https://www.phenixairsoft.com', 'FR', 'EUR', 'jsonld', 'fr'),
  ('militaria',       'Militaria.pl',    'https://militaria.pl',          'PL', 'PLN', 'jsonld', 'pl'),
  ('redberet',        'Red Beret',       'https://www.redberet.pl',       'PL', 'PLN', 'jsonld', 'pl'),
  ('atom-airsoft',    'Atom Airsoft',    'https://atom-airsoft.fi',       'FI', 'EUR', 'jsonld', 'fi')
on conflict (slug) do nothing;

insert into manufacturers (slug, name) values
  ('begadi','Begadi'), ('swiss-arms','Swiss Arms'), ('agm','AGM'), ('wolverine','Wolverine Airsoft'),
  ('tippmann','Tippmann'), ('phylax','Phylax'), ('archwick','Archwick'), ('saigo','Saigo Defense')
on conflict (slug) do nothing;

insert into manufacturer_aliases (alias_norm, manufacturer_id)
select a, m.id from manufacturers m
join (values ('begadi','begadi'), ('swissarms','swiss-arms'), ('agm','agm'), ('wolverine','wolverine'),
             ('wolverineairsoft','wolverine'), ('tippmann','tippmann'), ('phylax','phylax'), ('archwick','archwick'),
             ('saigo','saigo'), ('saigodefense','saigo'), ('eliteforce','umarex')) v(a, slug) on v.slug = m.slug
on conflict (alias_norm) do nothing;

select count(*) as boltok from shops;
