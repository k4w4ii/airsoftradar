-- DIAGNÓZIS (Cloudflare D1 Console): miért ad egy bolt 0 terméket? (http válaszok, példa URL-ek, sitemapek)
SELECT s.slug,
       json_extract(r.errors, '$[0].http')      AS http_valaszok,
       json_extract(r.errors, '$[0].linkek')    AS linkek_szama,
       json_extract(r.errors, '$[0].locs')      AS sitemap_urlek,
       json_extract(r.errors, '$[0].minta')     AS pelda_urlek,
       json_extract(r.errors, '$[0].sitemapek') AS sitemapek,
       json_extract(r.errors, '$[0].url')       AS hibas_url
FROM shops s
JOIN scrape_runs r ON r.id = (SELECT max(id) FROM scrape_runs x WHERE x.shop_id = s.id)
WHERE r.status <> 'ok' AND json_valid(r.errors)
ORDER BY s.slug;
