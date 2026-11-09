"""A scraper adatbázisa: Cloudflare D1 (scraper/d1db.py). Env: D1_API_URL, D1_API_TOKEN."""
from __future__ import annotations


def get_db():
    from d1db import D1DB
    return D1DB()
