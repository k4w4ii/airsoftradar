-- GYANÚS FEGYVEREK (Cloudflare D1 Console): fegyver-kategóriás termékek a legolcsóbbtól, a gyanús szavakkal elöl.
-- Futtasd, majd a táblázatot (Copy / Download CSV) küldd el: ezekből lesznek az új besorolási szabályok és tesztek.
SELECT category AS kategoria, name AS termek, manufacturer AS gyarto, CAST(best_price_huf AS INT) AS ar_ft, offer_count AS boltok,
       'https://www.airsofthunter.com/hu/p/' || slug AS link
FROM product_summary
WHERE category IN ('rifle','pistol','smg','sniper','lmg','shotgun')
  AND (best_price_huf < 25000
       OR lower(name) GLOB '*[0-9] db*' OR lower(name) GLOB '*[0-9] pcs*' OR lower(name) GLOB '*[0-9]pcs*'
       OR lower(name) LIKE '%set%' OR lower(name) LIKE '%kit%' OR lower(name) LIKE '% for %'
       OR lower(name) LIKE '%bag%' OR lower(name) LIKE '%case%' OR lower(name) LIKE '%carrier%' OR lower(name) LIKE '%pad%'
       OR lower(name) LIKE '%spring%' OR lower(name) LIKE '%barrel%' OR lower(name) LIKE '%stock%' OR lower(name) LIKE '%grip%')
ORDER BY best_price_huf
LIMIT 300;
