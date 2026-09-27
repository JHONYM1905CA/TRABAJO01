# ASTRA Zotero: diagnóstico local

Herramienta de solo lectura para Windows. Comprueba Python 3.12+, existencia del servidor MCP y del perfil YAML, referencia a `env:CONTROL_PLANE_API_KEY` y presencia (nunca el valor) de variables de entorno.

## Uso

Desde PowerShell, en esta carpeta:

    python .\scripts\diagnostico_zotero.py
    python .\scripts\diagnostico_zotero.py --json
    python -m unittest discover -s tests -v

Si tus archivos están en otra carpeta, utiliza `--servidor 'RUTA_AL_SERVIDOR.py' --perfil 'RUTA_AL_PERFIL.yaml'`.

## Si perdiste CONTROL_PLANE_API_KEY

La API key del proyecto OpenAI **no** sustituye la clave del plano de control del túnel. Recupera o regenera esta credencial únicamente en el servicio oficial que administra tu túnel y revoca la anterior si procede. Después de cargarla en la sesión de PowerShell, repite el diagnóstico y el comando `doctor` del túnel.

La prueba solo comprueba requisitos **locales**. No autentica ante OpenAI, no conecta Zotero ni demuestra que la clave sea válida. El repositorio es público: no subas claves, archivos `.env`, perfiles reales o datos privados.
