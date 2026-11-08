-- =====================================================================
-- 0009: kiegészítő- és alkatrészgyártók (hogy a tárak, akkuk, BB-k, alkatrészek is megjelenjenek),
--       a már letöltött ruházati ajánlatok elrejtése. Adatot NEM töröl. Újrafuttatható.
-- =====================================================================
insert into manufacturers (slug, name) values
  ('nimrod','Nimrod'), ('bls','BLS'), ('rockets','Rockets'), ('lonex','Lonex'), ('maple-leaf','Maple Leaf'),
  ('shs','SHS'), ('prometheus','Prometheus'), ('gate','GATE'), ('perun','Perun'), ('jefftron','Jefftron'),
  ('guarder','Guarder'), ('element','Element'), ('big-dragon','Big Dragon'), ('battleaxe','BattleAxe'),
  ('vector-optics','Vector Optics'), ('theta-optics','Theta Optics'), ('abbey','Abbey'), ('puff-dino','Puff Dino'),
  ('mancraft','Mancraft'), ('polarstar','PolarStar'), ('xcortech','Xcortech'), ('bolt-airsoft','BOLT Airsoft'),
  ('g-and-p','G&P'), ('cowcow','CowCow'), ('pts','PTS Syndicate'), ('magpul','Magpul'), ('ipower','iPower'),
  ('electro-river','Electro River'), ('titan-power','Titan Power'), ('ase-utra','ASE Utra'), ('swiss-arms-acc','Strike Systems')
on conflict (slug) do nothing;

insert into manufacturer_aliases (alias_norm, manufacturer_id)
select a, m.id from manufacturers m
join (values
  ('nimrod','nimrod'), ('bls','bls'), ('blsbbs','bls'), ('rockets','rockets'), ('rocketsprofessional','rockets'),
  ('lonex','lonex'), ('mapleleaf','maple-leaf'), ('shs','shs'), ('prometheus','prometheus'), ('gate','gate'),
  ('gateenterprise','gate'), ('perun','perun'), ('jefftron','jefftron'), ('guarder','guarder'), ('element','element'),
  ('bigdragon','big-dragon'), ('battleaxe','battleaxe'), ('vectoroptics','vector-optics'), ('thetaoptics','theta-optics'),
  ('abbey','abbey'), ('puffdino','puff-dino'), ('mancraft','mancraft'), ('polarstar','polarstar'), ('xcortech','xcortech'),
  ('boltairsoft','bolt-airsoft'), ('gp','g-and-p'), ('gandp','g-and-p'), ('cowcow','cowcow'), ('cowcowtechnology','cowcow'),
  ('pts','pts'), ('ptssyndicate','pts'), ('magpul','magpul'), ('ipower','ipower'), ('electroriver','electro-river'),
  ('titanpower','titan-power'), ('aseutra','ase-utra'), ('strikesystems','swiss-arms-acc')
) v(a, slug) on v.slug = m.slug
on conflict (alias_norm) do nothing;

-- már letöltött ruházat elrejtése (a scraper mostantól le sem tölti)
update offers set is_active = false
where is_active and (title_raw || ' ' || url) ~* '(\y(clothing|apparel|uniforms?|trousers|pants|t-?shirts?|shirts?|hoodies?|jackets?|softshell|fleece|boots|shoes|socks|nadrág|póló|kabát|bakancs|egyenruha|pulóver|mundur|spodnie|koszul\w*|kurtk\w*|buty|bluz\w*|kalhoty|bunda|boty)\y)';

select refresh_product_summary();
select (select count(*) from manufacturers) as gyartok, (select count(*) from offers where not is_active) as rejtett_ajanlatok;
