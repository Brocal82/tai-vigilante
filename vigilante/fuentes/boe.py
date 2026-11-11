"""BOE: API de datos abiertos (sumarios diarios). Requiere Accept: application/xml."""
import xml.etree.ElementTree as ET
from datetime import date, timedelta

from ..red import NoEncontrado, descargar

URL = "https://www.boe.es/datosabiertos/api/boe/sumario/{f}"


def parsear_sumario(contenido):
    """Devuelve la lista de disposiciones de un sumario (bytes XML)."""
    raiz = ET.fromstring(contenido)
    f = (raiz.findtext(".//metadatos/fecha_publicacion") or "").strip()
    fecha = f"{f[:4]}-{f[4:6]}-{f[6:8]}" if len(f) == 8 else None
    items = []
    for sec in raiz.iter("seccion"):
        for dep in sec.findall("departamento"):
            for it in dep.iter("item"):
                ident = (it.findtext("identificador") or "").strip()
                if not ident:
                    continue
                items.append({
                    "id": ident,
                    "fuente": "BOE",
                    "seccion": sec.get("codigo"),
                    "organismo": dep.get("nombre"),
                    "titulo": " ".join((it.findtext("titulo") or "").split()),
                    "url": (it.findtext("url_html") or "").strip(),
                    "url_pdf": (it.findtext("url_pdf") or "").strip(),
                    "fecha": fecha,
                })
    return items


def sumario_del_dia(d):
    """Items del BOE de un día. None si ese día no hay sumario (404)."""
    try:
        return parsear_sumario(descargar(URL.format(f=d.strftime("%Y%m%d")),
                                         {"Accept": "application/xml"}))
    except NoEncontrado:
        return None


def consultar(desde, hasta):
    """Recorre los días desde..hasta (inclusive). Devuelve (items, ultimo_dia_completo).
    Un 404 es normal en domingo/festivo; en el propio día de hoy puede ser que aún no esté publicado."""
    items, ultimo, d = [], desde - timedelta(days=1), desde
    while d <= hasta:
        dia = sumario_del_dia(d)
        if dia is None:
            if d == hasta and d.weekday() != 6:
                break  # hoy aún sin publicar: se reintenta en la próxima ejecución
        else:
            items.extend(dia)
        ultimo = d
        d += timedelta(days=1)
    return items, ultimo
