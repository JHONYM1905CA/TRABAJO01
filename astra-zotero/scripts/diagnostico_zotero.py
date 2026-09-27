#!/usr/bin/env python3
"""Diagnóstico local, solo lectura, para un túnel MCP de Zotero en Windows.

Nunca lee el valor de las claves más allá de comprobar que no estén vacías.
No realiza solicitudes de red y no ejecuta el servidor MCP ni el túnel.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Comprobacion:
    codigo: str
    estado: str  # OK | ERROR | AVISO
    descripcion: str
    accion: str = ""


def rutas_predeterminadas(entorno: Mapping[str, str], inicio: Path) -> tuple[Path, Path]:
    """Deriva las rutas sin depender de un nombre de usuario concreto."""
    servidor = inicio / "Documents" / "ZOTERO_NOVIO" / "TUNNEL_CLIENT" / "ZOTERO_NOVIO_SERVIDOR.py"
    appdata = Path(entorno.get("APPDATA") or inicio / "AppData" / "Roaming")
    perfil = appdata / "tunnel-client" / "zotero-astra-novio.yaml"
    return servidor, perfil


def evaluar(
    servidor: Path,
    perfil: Path,
    entorno: Mapping[str, str],
    version_python: Sequence[int] = sys.version_info,
) -> list[Comprobacion]:
    """Inspecciona solo existencia de ficheros y presencia de variables de entorno."""
    resultados: list[Comprobacion] = []

    if tuple(version_python[:2]) >= (3, 12):
        resultados.append(Comprobacion("python", "OK", "Python 3.12 o posterior disponible."))
    else:
        resultados.append(Comprobacion(
            "python", "ERROR", "Se requiere Python 3.12 o posterior para esta instalación.",
            "Ejecuta el diagnóstico con la instalación de Python 3.12.",
        ))

    if servidor.is_file():
        resultados.append(Comprobacion("servidor", "OK", "Archivo del servidor MCP localizado."))
    else:
        resultados.append(Comprobacion(
            "servidor", "ERROR", "No se encuentra el archivo del servidor MCP.",
            "Comprueba la ruta con --servidor. No se ha creado ni modificado ningún archivo.",
        ))

    if not perfil.is_file():
        resultados.append(Comprobacion(
            "perfil", "ERROR", "No se encuentra el perfil YAML del túnel.",
            "Comprueba la ruta con --perfil.",
        ))
    else:
        try:
            contenido = perfil.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            resultados.append(Comprobacion(
                "perfil", "ERROR", "No se puede leer el perfil YAML.",
                "Comprueba permisos y codificación UTF-8 del archivo.",
            ))
        else:
            # No volcamos el perfil ni intentamos analizar todo YAML sin dependencias.
            referencia = re.search(
                r"(?m)^\s*api_key\s*:\s*['\"]?env:CONTROL_PLANE_API_KEY['\"]?\s*(?:#.*)?$",
                contenido,
            )
            if referencia:
                resultados.append(Comprobacion(
                    "perfil", "OK", "El perfil referencia CONTROL_PLANE_API_KEY.",
                ))
            else:
                resultados.append(Comprobacion(
                    "perfil", "ERROR", "No se encontró la referencia esperada a la variable de control.",
                    "Comprueba que control_plane.api_key use env:CONTROL_PLANE_API_KEY.",
                ))

    if (entorno.get("CONTROL_PLANE_API_KEY") or "").strip():
        resultados.append(Comprobacion("control_key", "OK", "La variable de control está definida."))
    else:
        resultados.append(Comprobacion(
            "control_key", "ERROR", "CONTROL_PLANE_API_KEY no está definida o está vacía.",
            "Carga una clave vigente en la sesión actual de PowerShell; nunca la publiques.",
        ))

    if (entorno.get("OPENAI_API_KEY") or "").strip():
        resultados.append(Comprobacion("openai_key", "OK", "OPENAI_API_KEY está definida."))
    else:
        resultados.append(Comprobacion(
            "openai_key", "AVISO", "OPENAI_API_KEY no está definida en esta sesión.",
            "Solo se necesita para llamadas a la API de OpenAI, no para esta comprobación local.",
        ))

    return resultados


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verifica la configuración local de ZOTERO-ASTRA-NOVIO sin exponer secretos."
    )
    parser.add_argument("--servidor", type=Path, help="Ruta al archivo Python del servidor MCP.")
    parser.add_argument("--perfil", type=Path, help="Ruta al perfil YAML del túnel.")
    parser.add_argument("--json", action="store_true", help="Resultado estructurado para automatizaciones.")
    argumentos = parser.parse_args(argv)

    servidor_def, perfil_def = rutas_predeterminadas(os.environ, Path.home())
    resultados = evaluar(
        argumentos.servidor or servidor_def,
        argumentos.perfil or perfil_def,
        os.environ,
    )
    bloqueado = any(x.estado == "ERROR" for x in resultados)
    if argumentos.json:
        print(json.dumps({
            "listo_para_doctor": not bloqueado,
            "comprobaciones": [asdict(x) for x in resultados],
        }, ensure_ascii=False, indent=2))
    else:
        print("Diagnóstico local ZOTERO-ASTRA-NOVIO (no valida las claves contra el servidor)")
        for item in resultados:
            print(f"[{item.estado}] {item.descripcion}")
            if item.accion:
                print(f"       Siguiente paso: {item.accion}")
        if bloqueado:
            print("RESULTADO: existen bloqueos locales. Corrígelos antes de repetir el doctor.")
        else:
            print("RESULTADO: requisitos locales comprobados; repite tu comando doctor habitual.")
    return 1 if bloqueado else 0


if __name__ == "__main__":
    raise SystemExit(main())
