# tai-vigilante

Vigila fuentes **oficiales** (BOE, INAP) y avisa al móvil de novedades de la oposición **TAI** (Técnicos Auxiliares de
Informática de la AGE). Uso personal. Sin IA, sin base de datos, sin dependencias: solo Python estándar.

## Cómo funciona
1. GitHub Actions ejecuta `python -m vigilante.main` cada día (a partir de las 8:00 de Madrid, una vez al día).
2. Lee el sumario del BOE (API de datos abiertos) y el RSS del INAP.
3. `vigilante/clasificar.py` decide con reglas (`vigilante/reglas.json`) si algo trata de TAI y su nivel:
   🔴 urgente · 🟠 importante · 🔵 informativo. Un cambio de ley del temario va aparte (`canal: norma`) y **nunca**
   se presenta como cambio del programa (`canal: programa`).
4. Guarda `docs/novedades.json` (historial, sin duplicados por id) y `docs/estado.json` (última comprobación correcta).
   GitHub Pages sirve la carpeta `docs/`; la app lee de ahí.
5. Si hay novedades, envía una notificación con la API de Expo Push. Si falla una fuente, lo registra, avisa y la
   ejecución termina en rojo (GitHub te envía un correo).

## Secreto necesario
`EXPO_PUSH_TOKEN` (Settings → Secrets and variables → Actions). Sin él, el vigilante funciona pero no avisa.
Las claves de envío de Android se suben a Expo con `eas credentials`; nunca van en este repositorio.

## Uso local
```
python -m unittest discover -s tests -t .
python -m vigilante.main --simular --forzar     # lee fuentes reales, no escribe ni avisa
```

## Primera ejecución
Guarda ~30 días de historial **sin avisar** (marcado `inicial`). A partir de ahí, solo avisa de lo nuevo.

## Añadir una fuente
Crea `vigilante/fuentes/<nombre>.py` con una función que devuelva items `{id, fuente, titulo, url, fecha}` y llámala
en `main.py`. Fuentes pendientes de verificar su URL oficial: Función Pública (SEFP) y Punto de Acceso General.

## Normas del temario
`vigilante/normas_temario.json` (norma → temas) se genera con `tools/extraer_normas.py` desde el temario local.
Algunas entradas pueden ser erratas del temario de origen (p. ej. Ley 50/1996–1999): revisar antes de fiarse.
