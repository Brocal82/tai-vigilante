"""Clasificador por reglas (sin IA). Punto de enganche para IA futura: ver `analizar_con_ia`."""
import json
import re
from pathlib import Path

AQUI = Path(__file__).parent
NIVELES = {"urgente": 3, "importante": 2, "informativo": 1}


def _cargar(nombre):
    return json.loads((AQUI / nombre).read_text(encoding="utf-8"))


def _re(p):
    return re.compile(p, re.I)


class Clasificador:
    def __init__(self, reglas=None, normas=None):
        r = reglas or _cargar("reglas.json")
        self.r = r
        self.rel = [_re(p) for p in r["relevancia_tai"][:1]] + [re.compile(p) for p in r["relevancia_tai"][1:]]
        self.excl = [_re(p) for p in r["excluir_tai"]]
        self.tipos = [(t, _re(t["patron"])) for t in r["tipos"]]
        self.prog = _re(r["programa"]["patron"])
        self.verbos = _re(r["norma"]["verbos"])
        nor = normas if normas is not None else _cargar("normas_temario.json")["normas"]
        self.normas = []
        for n in nor:
            nombre = n["norma"]
            m = re.search(r"(\d+/\d{4}|\d{4}/\d+)", nombre)
            if nombre.startswith("Constitución"):
                pat = re.compile(r"Constituci[oó]n Espa[ñn]ola", re.I)
            elif m:
                # Tipo y número deben ir juntos: "Ley 4/2026" no es "Ley Orgánica 4/2026".
                tipo = nombre[:m.start()].strip()
                if tipo in ("Real Decreto Legislativo", "Real Decreto-ley"):
                    tipo_re = r"Real Decreto(?:-ley|\s+Legislativo)"   # el temario los mezcla a veces
                else:
                    tipo_re = r"\s+".join(map(re.escape, tipo.split()))
                pat = re.compile(r"\b" + tipo_re + r"\s+" + re.escape(m.group(1)) + r"\b", re.I)
            else:
                continue
            self.normas.append((nombre, n["temas"], pat))

    def es_tai(self, texto):
        """Relevante si nombra el Cuerpo completo; las siglas TAI solo valen si no es de universidades,
        ayuntamientos, etc. (TAIEX no coincide por el límite de palabra)."""
        if self.rel[0].search(texto):
            return True
        if any(p.search(texto) for p in self.excl):
            return False
        return any(p.search(texto) for p in self.rel[1:])

    def clasificar(self, item):
        """Devuelve el item enriquecido o None si no es relevante."""
        texto = f"{item['titulo']} {item.get('resumen', '')}"
        if self.es_tai(texto):
            tipo = None
            for t, p in self.tipos:
                if p.search(texto):
                    tipo = t
                    break
            salida = dict(item)
            if self.prog.search(texto) and (tipo is None or tipo["categoria"] not in ("Lista de admitidos y excluidos",)):
                pr = self.r["programa"]
                salida.update(categoria=pr["categoria"], grupo=pr["grupo"], nivel=pr["nivel"], canal="programa")
            elif tipo:
                salida.update(categoria=tipo["categoria"], grupo=tipo["grupo"], nivel=tipo["nivel"], canal="proceso")
            else:
                salida.update(categoria=self.r["categoria_por_defecto"], grupo="convocatorias",
                              nivel=self.r["nivel_por_defecto"], canal="proceso")
            return salida
        # Cambio de una norma del temario (solo BOE, y solo si se modifica algo)
        if item.get("fuente") == "BOE" and self.verbos.search(item["titulo"]):
            afectadas = [(n, t) for n, t, p in self.normas if p.search(item["titulo"])]
            if afectadas:
                nr = self.r["norma"]
                temas = sorted({x for _, ts in afectadas for x in ts})
                salida = dict(item)
                salida.update(categoria=nr["categoria"], grupo=nr["grupo"], nivel=nr["nivel"], canal="norma",
                              normas=[n for n, _ in afectadas], temas_posiblemente_afectados=temas)
                return salida
        return None


def analizar_con_ia(item):  # pragma: no cover
    """Gancho futuro: devolver un resumen/valoración usando un modelo de IA. En la v1 no se usa."""
    return None
