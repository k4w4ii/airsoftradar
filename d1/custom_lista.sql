-- Az „Egyedi és tuningolt” kategória termékei és az ajánlatok bolti címei (ellenőrzéshez).
-- Cloudflare → D1 → Console → ezt beilleszteni → Run. Ha rossz termék van benne, küldd el a sorát.
SELECT ps.category, ps.name, ps.offer_count,
       (SELECT group_concat(s.slug || ': ' || o.title_raw, ' || ')
          FROM offers o JOIN shops s ON s.id = o.shop_id
         WHERE o.product_id = ps.id AND o.is_active = 1) AS bolti_cimek
FROM product_summary ps
WHERE ps.category IN ('custom_rifle', 'custom_pistol', 'custom_sniper')
ORDER BY ps.offer_count DESC, ps.name
LIMIT 400;
