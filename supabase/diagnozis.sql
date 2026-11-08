-- DIAGNÓZIS: miért ad egy bolt 0 terméket? (http válaszok, példa URL-ek, sitemapek)
select s.slug,
       r.errors->0->'http'          as http_valaszok,
       r.errors->0->>'linkek'       as linkek_szama,
       r.errors->0->>'locs'         as sitemap_urlek,
       r.errors->0->'minta'         as pelda_urlek,
       r.errors->0->'sitemapek'     as sitemapek,
       r.errors->0->>'url'          as hibas_url
from shops s
join lateral (select * from scrape_runs x where x.shop_id = s.id order by x.id desc limit 1) r on true
where r.status <> 'ok'
order by s.slug;
