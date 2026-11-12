-- TÖBBNYELVŰ BOLTOK (Cloudflare D1 Console): boltonként az ajánlat-URL-ek első útvonal-eleme (pl. /hu/, /de/, /hr/).
-- Ha egy boltnál több nyelvkód is sok ajánlattal szerepel, ugyanaz a termék több nyelven, külön termékként jött létre.
-- A letöltő ezt mostantól magától szűri (csak egy nyelv marad), a régi ajánlatok pár nap alatt inaktiválódnak.
SELECT s.slug AS bolt,
       substr(o.url, instr(substr(o.url, 9), '/') + 9, instr(substr(o.url, instr(substr(o.url, 9), '/') + 10), '/')) AS elso_szint,
       count(*) AS ajanlat,
       min(o.title_raw) AS pelda
FROM offers o JOIN shops s ON s.id = o.shop_id
WHERE o.is_active = 1
GROUP BY s.slug, elso_szint
HAVING count(*) >= 20
ORDER BY s.slug, ajanlat DESC;
