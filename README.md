# Lector de facturas con IA Gemma Multimodal

Proyecto Python para procesar facturas en PDF o imagen, con salida estructurada y lectura de tablas utilizando Inteligencia Artificial avanzada.

*Nota de Créditos:* Este proyecto utiliza los modelos **Gemma Multimodal**, creados y entrenados por **Google**, aprovechando sus capacidades visuales y de comprensión de lenguaje natural para un análisis de facturas eficiente y preciso.

**Atención sobre el modelo:** Debido al tamaño de `gemma-4-E4B-it-Q4_K_M.gguf` (aprox. 5GB), no se incluye dentro del repositorio. Por favor, descárgalo directamente desde Hugging Face y colócalo en la carpeta `modelo/` antes de ejecutar. El archivo del proyector visual (`mmproj-F16.gguf`) sí se incluye mediante Git LFS.

## Version actual

v1.0.1

## Novedades de v1.0.1

- Mejor deteccion y lectura de bloques con estructura de documento.
- Mejor lectura de tablas en facturas.
- Exportacion Excel mas limpia y legible.
- Correccion de duplicados en resultados.
- Eliminacion de ruido en la lectura final.
- Limpieza del motor OCR para dejar una base neutra sin dependencias acopladas.

## Requisitos

- Python 3.13
- Dependencias en `requirements.txt`

## Instalacion

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuracion del archivo de entrada

El archivo a procesar se define en `RUTA_ARCHIVO_ENTRADA` dentro de `scr/proceso_principal.py`.
Tambien puedes ajustar modo OCR con estas constantes en el mismo archivo:

- `CONFIANZA_MINIMA` (por defecto `0.35`)

Ejemplo:

```python
RUTA_ARCHIVO_ENTRADA = "entrada/ejemplo.pdf"
```

## Ejecucion

```powershell
.\.venv\Scripts\python.exe scr\proceso_principal.py
```

## Salidas

Se generan en la carpeta `salida/`:

- `resultado_<archivo>.json` con OCR y estructura.
- `texto_<archivo>.txt` con texto final limpio.
- `ocr_<archivo>.xlsx` con contenido final formateado.

## Estructura del proyecto

- `scr/proceso_principal.py`: flujo principal y exportaciones.
- `scr/procesador_pdf.py`: lectura PDF y conversion por pagina.
- `scr/procesador_imagen.py`: preprocesado y llamada OCR.
- `scr/motor_ocr.py`: motor OCR y parseo de estructura/layout.
- `requirements.txt`: dependencias del proyecto.

## Ajuste de rendimiento OCR

- El motor OCR actual esta en modo base, sin proveedor OCR acoplado.
- Puedes conectar un backend OCR nuevo en `scr/motor_ocr.py` manteniendo el mismo contrato de salida.

## Notas tecnicas

- Soporte de estructura/layout para aproximar salida al formato de factura original.
