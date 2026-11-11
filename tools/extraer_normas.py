"""Genera vigilante/normas_temario.json (norma -> temas) leyendo data/temario/*.json de OPOSICION-TAI.
Solo lectura sobre el temario. Uso: python tools/extraer_normas.py RUTA/data/temario
Ejecutar en local; el resultado se revisa y se sube. No usa red."""
import collections
import glob
import json
import re
import sys

TIPOS = [
    (r"Real Decreto Legislativo|RDLeg|RDLegislativo", "Real Decreto Legislativo"),
    (r"Real Decreto-ley|Real Decreto ley|RDL", "Real Decreto-ley"),
    (r"Real Decreto|RD", "Real Decreto"),
    (r"Ley Org[aá]nica|LO", "Ley Orgánica"),
    (r"Ley", "Ley"),
]
PAT = re.compile(r"\b(" + "|".join(t for t, _ in TIPOS) + r")\s+(\d{1,3}/\d{4})\b")
PAT_UE = re.compile(r"\b(Reglamento|Directiva)\s+\(UE\)\s+(\d{4}/\d+|\d+/\d{4})")


def canon(tipo):
    for pat, nombre in TIPOS:
        if re.fullmatch(pat, tipo):
            return nombre
    return tipo


def main(ruta):
    m = collections.defaultdict(set)
    for f in sorted(glob.glob(ruta + "/*.json")):
        d = json.load(open(f, encoding="utf-8"))
        texto = "\n".join(s["texto"] for s in d["secciones"])
        for t, n in PAT.findall(texto):
            m[f"{canon(t)} {n}"].add(d["id"])
        for t, n in PAT_UE.findall(texto):
            m[f"{t} (UE) {n}"].add(d["id"])
        if re.search(r"Constituci[oó]n Espa[ñn]ola", texto):
            m["Constitución Española"].add(d["id"])
    sal = [{"norma": k, "temas": sorted(v)} for k, v in sorted(m.items())]
    json.dump({"generado_de": "data/temario", "normas": sal}, open("vigilante/normas_temario.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(len(sal), "normas")


if __name__ == "__main__":
    main(sys.argv[1])
