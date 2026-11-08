-- ÁLLAPOT: boltonként az utolsó futás és az ajánlatok (Supabase SQL Editor -> Run)
select s.slug                                    as bolt,
       r.status                                  as utolso_futas,
       r.offers_seen                             as letoltve,
       (select count(*) from offers o where o.shop_id = s.id)                           as ajanlat_osszesen,
       (select count(*) from offers o where o.shop_id = s.id and o.product_id is not null) as parositva,
       coalesce(jsonb_array_length(r.errors), 0) as hibak,
       r.errors -> 0 ->> 'error'                 as elso_hiba,
       to_char(r.started_at at time zone 'Europe/Budapest', 'MM-DD HH24:MI') as mikor
from shops s
left join lateral (select * from scrape_runs x where x.shop_id = s.id order by x.id desc limit 1) r on true
order by s.slug;
