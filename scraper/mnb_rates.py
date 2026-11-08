"""Napi MNB árfolyam -> exchange_rates. Futtatás: python scraper/mnb_rates.py [--dry-run]"""
from __future__ import annotations

import sys
import urllib.request
import xml.etree.ElementTree as ET
from decimal import Decimal

MNB_URL = "http://www.mnb.hu/arfolyamok.asmx"
SOAP_ACTION = "http://www.mnb.hu/webservices/MNBArfolyamServiceSoap/GetCurrentExchangeRates"
ENVELOPE = (
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
    'xmlns:web="http://www.mnb.hu/webservices/"><soapenv:Header/>'
    "<soapenv:Body><web:GetCurrentExchangeRates/></soapenv:Body></soapenv:Envelope>"
)


def fetch_soap() -> str:
    req = urllib.request.Request(MNB_URL, data=ENVELOPE.encode(), method="POST", headers={
        "Content-Type": "text/xml; charset=utf-8", "SOAPAction": SOAP_ACTION})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse(soap_xml: str) -> list[dict]:
    """A SOAP válasz egy escape-elt XML stringet tartalmaz: <MNBCurrentExchangeRates><Day date=..><Rate unit curr>385,40</Rate>"""
    root = ET.fromstring(soap_xml)
    inner = next(el.text for el in root.iter() if el.tag.endswith("GetCurrentExchangeRatesResult"))
    day = ET.fromstring(inner).find("Day")
    rows = []
    for rate in day.findall("Rate"):
        unit = Decimal(rate.get("unit", "1"))
        value = Decimal(rate.text.strip().replace(",", "."))
        rows.append({"currency": rate.get("curr"), "rate_date": day.get("date"),
                     "huf_per_unit": str((value / unit).quantize(Decimal("0.0001"))), "source": "MNB"})
    return rows


def main() -> None:
    rows = parse(fetch_soap())
    if not rows:
        sys.exit("MNB: üres válasz")
    if "--dry-run" in sys.argv:
        for r in rows:
            print(r)
        return
    from db import DB
    DB().upsert("exchange_rates", rows, on_conflict="currency,rate_date", returning=False)
    print(f"MNB: {len(rows)} árfolyam mentve ({rows[0]['rate_date']})")


if __name__ == "__main__":
    main()
