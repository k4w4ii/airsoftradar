-- =====================================================================
-- AirsoftHunter – Cloudflare D1 (SQLite) séma. Újrafuttatható (IF NOT EXISTS).
-- A besorolás, az összesítés és a kiugró árak nincsenek SQL-ben:
-- a scraper Pythonban számolja (scraper/classify.py, scraper/summary.py) és ide írja.
-- Logikai értékek: 0/1. Időpontok: ISO-8601 szöveg (UTC). Tömbök: vesszővel határolt szöveg (",m4,ak,").
-- =====================================================================

CREATE TABLE IF NOT EXISTS shops (
  id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL, base_url TEXT NOT NULL,
  country TEXT NOT NULL, currency TEXT NOT NULL, affiliate_template TEXT, scraper_key TEXT NOT NULL DEFAULT '',
  is_active INTEGER NOT NULL DEFAULT 1, last_scraped_at TEXT, lang TEXT NOT NULL DEFAULT 'en', ships_to TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS manufacturers (id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS manufacturer_aliases (alias_norm TEXT PRIMARY KEY, manufacturer_id INTEGER NOT NULL);

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY, manufacturer_id INTEGER NOT NULL, model_code TEXT, model_code_norm TEXT,
  name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, image_url TEXT, name_lang TEXT NOT NULL DEFAULT 'en',
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS products_code_uq ON products (manufacturer_id, model_code_norm) WHERE model_code_norm IS NOT NULL;

CREATE TABLE IF NOT EXISTS product_codes (
  product_id INTEGER NOT NULL, code_type TEXT NOT NULL, code_norm TEXT NOT NULL, manufacturer_id INTEGER,
  PRIMARY KEY (code_type, code_norm, product_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS product_codes_ean_uq ON product_codes (code_norm) WHERE code_type = 'ean';
CREATE UNIQUE INDEX IF NOT EXISTS product_codes_model_uq ON product_codes (manufacturer_id, code_norm) WHERE code_type <> 'ean';

CREATE TABLE IF NOT EXISTS offers (
  id INTEGER PRIMARY KEY, shop_id INTEGER NOT NULL, external_id TEXT NOT NULL, url TEXT NOT NULL,
  title_raw TEXT NOT NULL, brand_raw TEXT, sku_raw TEXT, ean_raw TEXT, image_url TEXT,
  price REAL NOT NULL, currency TEXT NOT NULL, stock TEXT NOT NULL DEFAULT 'unknown',
  product_id INTEGER, match_status TEXT NOT NULL DEFAULT 'pending', match_method TEXT, match_confidence REAL,
  is_active INTEGER NOT NULL DEFAULT 1, is_outlier INTEGER NOT NULL DEFAULT 0,
  first_seen_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  last_seen_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE (shop_id, external_id)
);
CREATE INDEX IF NOT EXISTS offers_product ON offers (product_id) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS offers_match_queue ON offers (match_status) WHERE match_status IN ('pending', 'review');

CREATE TABLE IF NOT EXISTS price_history (
  offer_id INTEGER NOT NULL, observed_on TEXT NOT NULL, price REAL NOT NULL, currency TEXT NOT NULL,
  price_huf REAL NOT NULL, price_eur REAL, stock TEXT NOT NULL,
  PRIMARY KEY (offer_id, observed_on)
);

CREATE TABLE IF NOT EXISTS exchange_rates (
  currency TEXT NOT NULL, rate_date TEXT NOT NULL, huf_per_unit REAL NOT NULL, source TEXT NOT NULL DEFAULT 'MNB',
  PRIMARY KEY (currency, rate_date)
);
CREATE VIEW IF NOT EXISTS latest_rates AS
SELECT currency, huf_per_unit, rate_date FROM exchange_rates e
WHERE rate_date = (SELECT max(rate_date) FROM exchange_rates x WHERE x.currency = e.currency);

CREATE TABLE IF NOT EXISTS scrape_runs (
  id INTEGER PRIMARY KEY, shop_id INTEGER, started_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  finished_at TEXT, status TEXT NOT NULL DEFAULT 'running', offers_seen INTEGER DEFAULT 0, offers_new INTEGER DEFAULT 0,
  errors TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS match_candidates (
  offer_id INTEGER NOT NULL, product_id INTEGER NOT NULL, score REAL NOT NULL, reasons TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY (offer_id, product_id)
);

-- A weboldal ebből olvas. A scraper (summary.py) építi újra a napi futás végén (csak a változott sorokat írja).
CREATE TABLE IF NOT EXISTS product_summary (
  id INTEGER PRIMARY KEY, slug TEXT NOT NULL, name TEXT NOT NULL, model_code TEXT, image_url TEXT,
  manufacturer TEXT NOT NULL, search_code TEXT NOT NULL DEFAULT '', category TEXT NOT NULL, platforms TEXT NOT NULL DEFAULT '', powers TEXT NOT NULL DEFAULT '',
  best_price_huf REAL, best_price_eur REAL, max_price_huf REAL, min_price_any_huf REAL, min_price_any_eur REAL,
  offer_count INTEGER NOT NULL, in_stock_count INTEGER NOT NULL, shop_countries TEXT NOT NULL DEFAULT '',
  stock TEXT NOT NULL, updated_at TEXT, price REAL, sig TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS product_summary_slug ON product_summary (slug);
CREATE INDEX IF NOT EXISTS product_summary_cat ON product_summary (category);
CREATE INDEX IF NOT EXISTS product_summary_pop ON product_summary (offer_count DESC, price);
CREATE INDEX IF NOT EXISTS product_summary_mfr ON product_summary (manufacturer);
