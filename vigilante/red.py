"""Descarga con reintentos. Solo biblioteca estándar."""
import time
import urllib.error
import urllib.request

UA = "tai-vigilante/1.0 (uso personal; seguimiento de publicaciones oficiales)"


class NoEncontrado(Exception):
    """El servidor respondió 404."""


def descargar(url, cabeceras=None, intentos=3, espera=3):
    h = {"User-Agent": UA}
    h.update(cabeceras or {})
    ultimo = None
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NoEncontrado(url)
            ultimo = e
        except Exception as e:  # red, DNS, timeout
            ultimo = e
        time.sleep(espera * (i + 1))
    raise RuntimeError(f"No se pudo descargar {url}: {ultimo}")
