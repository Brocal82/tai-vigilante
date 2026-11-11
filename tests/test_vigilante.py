"""Pruebas. Los textos marcados SINTÉTICO son entradas de prueba inventadas para comprobar reglas;
los archivos de tests/fixtures son respuestas reales guardadas del BOE y del INAP (10-11-2026)."""
import unittest
from datetime import datetime, timezone
from pathlib import Path

from vigilante import estado, push
from vigilante.clasificar import Clasificador
from vigilante.fuentes import boe, inap

FX = Path(__file__).parent / "fixtures"
C = Clasificador()
CUERPO = "Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado"


def item(titulo, fuente="BOE", resumen=""):
    return {"id": "x", "fuente": fuente, "titulo": titulo, "resumen": resumen}


class Fuentes(unittest.TestCase):
    def test_sumario_boe_real(self):
        items = boe.parsear_sumario((FX / "boe_sumario_20261110.xml").read_bytes())
        self.assertGreater(len(items), 100)
        self.assertTrue(all(i["id"].startswith("BOE-") and i["fecha"] == "2026-11-10" for i in items))

    def test_rss_inap_real(self):
        items = inap.parsear((FX / "inap_rss.xml").read_bytes())
        self.assertGreater(len(items), 5)
        self.assertTrue(all(i["id"].startswith("INAP:") for i in items))

    def test_real_sin_falsos_positivos_tai(self):
        # En estos archivos reales no hay nada de TAI: el clasificador no debe inventar avisos.
        for i in boe.parsear_sumario((FX / "boe_sumario_20261110.xml").read_bytes()) + \
                inap.parsear((FX / "inap_rss.xml").read_bytes()):
            r = C.clasificar(i)
            self.assertFalse(r and r["canal"] != "norma", r)


class Relevancia(unittest.TestCase):
    def test_taiex_no_es_tai(self):
        self.assertIsNone(C.clasificar(item("Visita TAIEX - TSI", "INAP")))

    def test_universidad_no_es_tai(self):  # SINTÉTICO
        self.assertIsNone(C.clasificar(item("Resolución de la Universidad X: TAI, Escala Técnica Auxiliar de Informática")))

    def test_cuerpo_tai_si(self):  # SINTÉTICO
        r = C.clasificar(item(f"Resolución por la que se convocan pruebas selectivas, {CUERPO}."))
        self.assertEqual((r["nivel"], r["canal"]), ("urgente", "proceso"))


class Tipos(unittest.TestCase):  # SINTÉTICO
    def n(self, texto):
        return C.clasificar(item(f"{texto}. {CUERPO}."))

    def test_admitidos(self):
        self.assertEqual(self.n("Lista de personas admitidas y excluidas")["nivel"], "urgente")

    def test_correccion(self):
        self.assertEqual(self.n("Corrección de errores de la convocatoria")["categoria"], "Corrección de errores")

    def test_plantilla(self):
        self.assertEqual(self.n("Publicación de la plantilla de respuestas")["categoria"], "Exámenes y plantillas")

    def test_programa_es_canal_distinto(self):
        r = self.n("Se modifica el programa de materias del proceso")
        self.assertEqual(r["canal"], "programa")

    def test_defecto_informativo(self):
        self.assertEqual(self.n("Nota sobre el proceso")["nivel"], "informativo")


class Normas(unittest.TestCase):
    def test_ley_y_ley_organica_no_se_confunden(self):  # SINTÉTICO
        self.assertIsNone(C.clasificar(item("Ley Orgánica 4/2026, por la que se modifica algo")))   # temario cita "Ley 4/2026"
        r = C.clasificar(item("Ley 4/2026, de 1 de enero, por la que se modifica la Ley 39/2015, de 1 de octubre"))
        self.assertEqual(r["canal"], "norma")
        self.assertIn("Ley 39/2015", r["normas"])
        self.assertIn(106, r["temas_posiblemente_afectados"])

    def test_norma_no_es_cambio_de_programa(self):  # SINTÉTICO
        r = C.clasificar(item("Ley 3/2018 se modifica el artículo 5 de la Ley 39/2015"))
        self.assertNotEqual(r["canal"], "programa")

    def test_norma_sin_verbo_no_avisa(self):  # SINTÉTICO
        self.assertIsNone(C.clasificar(item("Anuncio relativo a la Ley 39/2015, de 1 de octubre")))


class Soporte(unittest.TestCase):
    def test_hora_madrid_verano_e_invierno(self):
        self.assertEqual(estado.ahora_madrid(datetime(2026, 7, 1, 6, 0, tzinfo=timezone.utc)).hour, 8)
        self.assertEqual(estado.ahora_madrid(datetime(2026, 11, 11, 7, 0, tzinfo=timezone.utc)).hour, 8)

    def test_push_composicion(self):
        t, c, nivel = push.componer([{"nivel": "informativo", "categoria": "a", "titulo": "t1"},
                                     {"nivel": "urgente", "categoria": "b", "titulo": "t2"}])
        self.assertEqual(nivel, "urgente")
        self.assertIn("URGENTE", t)
        self.assertIn("2 novedades", c)

    def test_push_simulado_no_envia(self):
        ok, det = push.enviar("tok", [{"id": "1", "nivel": "importante", "categoria": "c", "titulo": "t"}], simular=True)
        self.assertTrue(ok)
        self.assertTrue(det.startswith("simulado"))


if __name__ == "__main__":
    unittest.main()
