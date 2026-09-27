"""Pruebas locales sin red, credenciales reales ni servidor activo."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.diagnostico_zotero import evaluar, main, rutas_predeterminadas


class DiagnosticoZoteroTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raiz = Path(self.temp.name)
        self.servidor = self.raiz / "ZOTERO_NOVIO_SERVIDOR.py"
        self.perfil = self.raiz / "zotero-astra-novio.yaml"
        self.servidor.write_text("# servidor de prueba\n", encoding="utf-8")
        self.perfil.write_text(
            "control_plane:\n  api_key: env:CONTROL_PLANE_API_KEY\n",
            encoding="utf-8",
        )
        self.entorno = {
            "CONTROL_PLANE_API_KEY": "CLAVE_FICTICIA_QUE_NO_DEBE_APARECER",
            "OPENAI_API_KEY": "OTRA_CLAVE_FICTICIA",
        }

    def test_configuracion_local_correcta(self):
        resultados = evaluar(self.servidor, self.perfil, self.entorno, (3, 12))
        self.assertTrue(all(r.estado == "OK" for r in resultados))

    def test_clave_control_faltante(self):
        resultados = evaluar(self.servidor, self.perfil, {}, (3, 12))
        self.assertEqual(
            next(r.estado for r in resultados if r.codigo == "control_key"),
            "ERROR",
        )

    def test_perfil_sin_referencia(self):
        self.perfil.write_text("control_plane:\n  api_key: otro_valor\n", encoding="utf-8")
        resultados = evaluar(self.servidor, self.perfil, self.entorno, (3, 12))
        self.assertEqual(next(r.estado for r in resultados if r.codigo == "perfil"), "ERROR")

    def test_archivos_ausentes(self):
        resultados = evaluar(
            self.raiz / "sin.py", self.raiz / "sin.yaml", self.entorno, (3, 12)
        )
        self.assertEqual(
            {r.codigo for r in resultados if r.estado == "ERROR"},
            {"servidor", "perfil"},
        )

    def test_python_anterior_a_312(self):
        resultados = evaluar(self.servidor, self.perfil, self.entorno, (3, 11))
        self.assertEqual(next(r.estado for r in resultados if r.codigo == "python"), "ERROR")

    def test_json_nunca_muestra_claves(self):
        salida = io.StringIO()
        with patch.dict("os.environ", self.entorno, clear=True):
            with contextlib.redirect_stdout(salida):
                codigo = main([
                    "--servidor", str(self.servidor),
                    "--perfil", str(self.perfil),
                    "--json",
                ])
        texto = salida.getvalue()
        self.assertEqual(codigo, 0)
        self.assertTrue(json.loads(texto)["listo_para_doctor"])
        self.assertNotIn(self.entorno["CONTROL_PLANE_API_KEY"], texto)
        self.assertNotIn(self.entorno["OPENAI_API_KEY"], texto)

    def test_json_con_errores(self):
        salida = io.StringIO()
        with patch.dict("os.environ", {}, clear=True):
            with contextlib.redirect_stdout(salida):
                codigo = main([
                    "--servidor", str(self.servidor),
                    "--perfil", str(self.perfil),
                    "--json",
                ])
        self.assertEqual(codigo, 1)
        self.assertFalse(json.loads(salida.getvalue())["listo_para_doctor"])

    def test_rutas_adaptables(self):
        servidor, perfil = rutas_predeterminadas(
            {"APPDATA": "C:/Users/OTRO/AppData/Roaming"},
            Path("C:/Users/OTRO"),
        )
        self.assertEqual(servidor.name, "ZOTERO_NOVIO_SERVIDOR.py")
        self.assertEqual(perfil.name, "zotero-astra-novio.yaml")


if __name__ == "__main__":
    unittest.main()
