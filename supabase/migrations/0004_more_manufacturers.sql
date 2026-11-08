-- Kétértelmű angol szavak (well, bolt, ultimate, evolution) szándékosan NEM címalias.
-- 0004: probe alapján hiányzó gyártók + gyakori európai márkák; Gunfire /en EUR-ban ad árat
update shops set currency = 'EUR' where slug = 'gunfire';

insert into manufacturers (slug, name) values
  ('emg','EMG'), ('amoeba','Amoeba'), ('novritsch','Novritsch'), ('classic-army','Classic Army'),
  ('ics','ICS'), ('kwa','KWA'), ('bolt','BOLT'), ('aps','APS'), ('golden-eagle','Golden Eagle'),
  ('cybergun','Cybergun'), ('umarex','Umarex'), ('kj-works','KJ Works'), ('action-army','Action Army'),
  ('silverback','Silverback'), ('well','Well'), ('lancer-tactical','Lancer Tactical'),
  ('evolution','Evolution Airsoft'), ('nuprol','Nuprol'), ('delta-armory','Delta Armory'),
  ('modify','Modify'), ('snow-wolf','Snow Wolf'), ('king-arms','King Arms'), ('vorsk','Vorsk'),
  ('asg','ASG'), ('ultimate','Ultimate'), ('src','SRC'), ('apex','APEX'), ('real-sword','Real Sword')
on conflict (slug) do nothing;

-- 'arsenal' korábban 'asg' aliast is kapott; ASG (Action Sport Games) külön gyártó
delete from manufacturer_aliases where alias_norm = 'asg';

insert into manufacturer_aliases (alias_norm, manufacturer_id)
select a, m.id from manufacturers m
join (values
  ('emg','emg'), ('amoeba','amoeba'), ('novritsch','novritsch'), ('classicarmy','classic-army'),
  ('ics','ics'), ('kwa','kwa'), ('boltairsoft','bolt'), ('aps','aps'),
  ('goldeneagle','golden-eagle'), ('cybergun','cybergun'), ('umarex','umarex'), ('kjworks','kj-works'),
  ('kj','kj-works'), ('actionarmy','action-army'), ('silverback','silverback'),
  ('wellfire','well'), ('lancertactical','lancer-tactical'), ('lancer','lancer-tactical'),
  ('evolutionairsoft','evolution'), ('nuprol','nuprol'),
  ('deltaarmory','delta-armory'), ('modify','modify'), ('snowwolf','snow-wolf'), ('kingarms','king-arms'),
  ('vorsk','vorsk'), ('asg','asg'), ('actionsportgames','asg'), ('src','src'),
  ('apex','apex'), ('realsword','real-sword'), ('jgworks','jg'), ('jingong','jg')
) v(a, slug) on v.slug = m.slug
on conflict (alias_norm) do nothing;
