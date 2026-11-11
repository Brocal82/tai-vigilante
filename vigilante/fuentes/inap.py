"""INAP: canal RSS oficial."""
import html
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from ..red import descargar

URL = "https://www.inap.es/es/rss-inap.xml"


def _limpio(t):
    return " ".join(re.sub(r"<[^>]+>", " ", html.unescape(t or "")).replace("\xa0", " ").split())


def parsear(contenido):
    items = []
    for it in ET.fromstring(contenido).iter("item"):
        guid = (it.findtext("guid") or it.findtext("link") or "").strip()
        if not guid:
            continue
        try:
            fecha = parsedate_to_datetime(it.findtext("pubDate")).date().isoformat()
        except Exception:
            fecha = None
        items.append({
            "id": "INAP:" + guid,
            "fuente": "INAP",
            "titulo": _limpio(it.findtext("title")),
            "resumen": _limpio(it.findtext("description"))[:400],
            "url": (it.findtext("link") or guid).strip(),
            "fecha": fecha,
        })
    return items


def consultar():
    return parsear(descargar(URL))
