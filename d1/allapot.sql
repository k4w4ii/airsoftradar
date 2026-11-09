-- ÁLLAPOT (Cloudflare D1): Dashboard -> Storage & databases -> D1 -> airsofthunter -> Console -> beillesztés -> Run
-- boltonként az utolsó futás és az ajánlatok
SELECT s.slug AS bolt, r.status AS utolso_futas, r.offers_seen AS letoltve,
       (SELECT count(*) FROM offers o WHERE o.shop_id = s.id) AS ajanlat_osszesen,
       (SELECT count(*) FROM offers o WHERE o.shop_id = s.id AND o.product_id IS NOT NULL) AS parositva,
       CASE WHEN json_valid(r.errors) THEN json_array_length(r.errors) ELSE 0 END AS hibak,
       CASE WHEN json_valid(r.errors) THEN json_extract(r.errors, '$[0]') END AS elso_hiba,
       substr(r.started_at, 1, 16) AS mikor_utc
FROM shops s
LEFT JOIN scrape_runs r ON r.id = (SELECT max(id) FROM scrape_runs x WHERE x.shop_id = s.id)
ORDER BY s.slug;
