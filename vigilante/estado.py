"""Persistencia en docs/*.json (se publica con GitHub Pages) y utilidades de fecha."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
VERSION = 1


def _ultimo_domingo(anio, mes):
    d = datetime(anio, mes + 1, 1) - timedelta(days=1) if mes < 12 else datetime(anio, 12, 31)
    while d.weekday() != 6:
        d -= timedelta(days=1)
    return d


def ahora_madrid(utc=None):
    """Hora de España. Usa zoneinfo; si no está la base de zonas, aplica la regla UE del horario de verano."""
    utc = utc or datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        return utc.astimezone(ZoneInfo("Europe/Madrid"))
    except Exception:
        a = utc.year
        ini = _ultimo_domingo(a, 3).replace(hour=1, tzinfo=timezone.utc)
        fin = _ultimo_domingo(a, 10).replace(hour=1, tzinfo=timezone.utc)
        off = 2 if ini <= utc < fin else 1
        return utc.astimezone(timezone(timedelta(hours=off)))


def leer(nombre, defecto):
    try:
        return json.loads((DOCS / nombre).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return defecto


def escribir(nombre, datos):
    DOCS.mkdir(exist_ok=True)
    (DOCS / nombre).write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def estado_inicial():
    return {"version": VERSION, "ultima_ok": None, "ultima_fecha_boe": None, "fuentes": {}, "errores_consecutivos": 0}


def novedades_inicial():
    return {"version": VERSION, "actualizado": None, "items": []}
