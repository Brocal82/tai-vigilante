"""Vigilante de novedades TAI. Uso:
  python -m vigilante.main            # ejecución normal (solo actúa desde las 8:00 de Madrid y una vez al día)
  python -m vigilante.main --simular  # lee fuentes reales, NO escribe archivos ni envía avisos
  python -m vigilante.main --forzar   # ignora la hora y el "ya comprobado hoy"
Variables de entorno: EXPO_PUSH_TOKEN (secreto de GitHub)."""
import argparse
import os
import sys
from datetime import date, timedelta

from . import estado as E
from . import push
from .clasificar import Clasificador
from .fuentes import boe, inap

MAX_ITEMS = 500
MAX_ATRAS = 31       # tras una parada larga, no se reprocesa más de un mes de BOE
ARRANQUE = 30        # primera ejecución: historial de los últimos 30 días, sin avisos


def run(args, hoy_madrid=None):
    ahora = hoy_madrid or E.ahora_madrid()
    hoy = ahora.date()
    est = E.leer("estado.json", E.estado_inicial())
    nov = E.leer("novedades.json", E.novedades_inicial())

    if not args.forzar:
        if ahora.hour < 8:
            print(f"Aún no son las 8:00 en Madrid ({ahora:%H:%M}). Nada que hacer.")
            return 0
        if est.get("ultima_ok_dia") == hoy.isoformat():
            print("Hoy ya se comprobó correctamente. Nada que hacer.")
            return 0

    arranque = est.get("ultima_fecha_boe") is None
    if arranque:
        desde = hoy - timedelta(days=ARRANQUE)
    else:
        desde = date.fromisoformat(est["ultima_fecha_boe"]) + timedelta(days=1)
        desde = max(desde, hoy - timedelta(days=MAX_ATRAS))

    candidatos, errores = [], {}
    ahora_iso = ahora.isoformat(timespec="seconds")
    fuentes = est.setdefault("fuentes", {})

    ultimo_dia = None
    try:
        items, ultimo_dia = boe.consultar(desde, hoy)
        candidatos += items
        fuentes["BOE"] = {"ok": True, "ultima_ok": ahora_iso, "error": None, "revisados": len(items)}
    except Exception as e:
        errores["BOE"] = str(e)
        fuentes["BOE"] = {**fuentes.get("BOE", {}), "ok": False, "error": str(e)}
    try:
        items = inap.consultar()
        candidatos += items
        fuentes["INAP"] = {"ok": True, "ultima_ok": ahora_iso, "error": None, "revisados": len(items)}
    except Exception as e:
        errores["INAP"] = str(e)
        fuentes["INAP"] = {**fuentes.get("INAP", {}), "ok": False, "error": str(e)}

    clasif = Clasificador()
    conocidos = {i["id"] for i in nov["items"]}
    nuevos = []
    for it in candidatos:
        if it["id"] in conocidos:
            continue
        c = clasif.clasificar(it)
        if c:
            conocidos.add(c["id"])
            c["detectado"] = ahora_iso
            c["avisado"] = bool(arranque)   # el historial inicial no genera avisos
            if arranque:
                c["inicial"] = True
            nuevos.append(c)
    nov["items"] = sorted(nov["items"] + nuevos, key=lambda x: (x.get("fecha") or "", x["id"]), reverse=True)[:MAX_ITEMS]
    nov["actualizado"] = ahora_iso

    # Avisos: lo nuevo y lo que quedó sin avisar en ejecuciones anteriores
    token = os.environ.get("EXPO_PUSH_TOKEN", "").strip()
    pendientes = [i for i in nov["items"] if not i.get("avisado")]
    msg_push = None
    if pendientes:
        if not token and not args.simular:
            msg_push = "Hay novedades pero falta EXPO_PUSH_TOKEN: no se envió el aviso."
        else:
            ok, det = push.enviar(token, pendientes, simular=args.simular)
            msg_push = det
            if ok and not args.simular:
                for i in pendientes:
                    i["avisado"] = True

    # Estado
    if ultimo_dia is not None and "BOE" not in errores:
        est["ultima_fecha_boe"] = ultimo_dia.isoformat()
    if not errores:
        est["ultima_ok"] = ahora_iso
        est["ultima_ok_dia"] = hoy.isoformat()
        est["errores_consecutivos"] = 0
    else:
        est["errores_consecutivos"] = est.get("errores_consecutivos", 0) + 1
    est["ultima_ejecucion"] = ahora_iso

    # Aviso de fallo del propio sistema (primer fallo y luego cada 3.º)
    aviso_fallo = None
    if errores and est["errores_consecutivos"] % 3 == 1 and (token or args.simular):
        n = [{"id": "fallo", "nivel": "importante", "categoria": "Vigilante",
              "titulo": "El vigilante TAI no ha podido comprobar: " + ", ".join(errores)}]
        aviso_fallo = push.enviar(token, n, simular=args.simular)[1]

    print(f"Fecha (Madrid): {ahora:%Y-%m-%d %H:%M}  Rango BOE: {desde} → {hoy}  Arranque: {arranque}")
    print(f"Candidatos revisados: {len(candidatos)}  Nuevos relevantes: {len(nuevos)}  Pendientes de aviso: {len(pendientes)}")
    for n in nuevos:
        print(f"  [{n['nivel']}] {n['canal']}/{n['categoria']}: {n['titulo'][:110]}  ({n['id']})")
    if msg_push:
        print("Aviso:", msg_push)
    if aviso_fallo:
        print("Aviso de fallo:", aviso_fallo)
    for k, v in errores.items():
        print(f"ERROR {k}: {v}", file=sys.stderr)

    if args.simular:
        print("(simulación: no se ha escrito nada ni enviado nada)")
    else:
        E.escribir("novedades.json", nov)
        E.escribir("estado.json", est)
    return 1 if errores else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", action="store_true")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--probar-push", action="store_true",
                    help="Envía solo una notificación de PRUEBA (no toca novedades ni estado)")
    args = ap.parse_args(argv)
    if args.probar_push:
        token = os.environ.get("EXPO_PUSH_TOKEN", "").strip()
        if not token:
            print("Falta EXPO_PUSH_TOKEN.", file=sys.stderr)
            return 1
        ok, det = push.enviar(token, [{
            "id": "prueba", "prueba": True, "nivel": "informativo", "categoria": "PRUEBA",
            "titulo": "Notificación de prueba del vigilante TAI. No es una novedad oficial."}])
        print("Prueba:", det)
        return 0 if ok else 1
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
