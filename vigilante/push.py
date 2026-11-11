"""Envío de notificaciones con la API de Expo Push (gratuita). El token llega por variable de entorno."""
import json
import urllib.request

URL = "https://exp.host/--/api/v2/push/send"
ICONO = {"urgente": "🔴", "importante": "🟠", "informativo": "🔵"}


def componer(nuevas):
    """Un solo aviso por ejecución, con el nivel más alto."""
    orden = ["urgente", "importante", "informativo"]
    nivel = min((n["nivel"] for n in nuevas), key=orden.index)
    titulo = {"urgente": "🔔 NOVEDAD URGENTE — TAI", "importante": "🔔 NOVEDAD IMPORTANTE — TAI",
              "informativo": "🔔 Novedad — TAI"}[nivel]
    if len(nuevas) == 1:
        cuerpo = f"{ICONO[nivel]} {nuevas[0]['categoria']}: {nuevas[0]['titulo']}"[:180]
    else:
        cuerpo = f"{len(nuevas)} novedades oficiales relacionadas con tu oposición. Pulsa para consultarlas."
    return titulo, cuerpo, nivel


def enviar(token, nuevas, simular=False, url=URL):
    """Devuelve (ok, detalle). No lanza excepciones."""
    titulo, cuerpo, nivel = componer(nuevas)
    msg = {"to": token, "title": titulo, "body": cuerpo, "sound": "default", "priority": "high",
           "channelId": "novedades", "data": {"abrir": "novedades", "ids": [n["id"] for n in nuevas]}}
    if simular:
        return True, "simulado: " + json.dumps({k: msg[k] for k in ("title", "body")}, ensure_ascii=False)
    try:
        req = urllib.request.Request(url, data=json.dumps(msg).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.loads(r.read())
        ticket = res.get("data") or {}
        if isinstance(ticket, list):
            ticket = ticket[0] if ticket else {}
        if ticket.get("status") == "ok":
            return True, "enviado"
        return False, f"Expo rechazó el aviso: {ticket.get('message') or ticket}"
    except Exception as e:
        return False, f"error de red al enviar: {e}"
