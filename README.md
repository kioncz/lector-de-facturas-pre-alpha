# Lector de facturas con PaddleOCR

Proyecto Python para procesar facturas en PDF o imagen usando PaddleOCR, con salida estructurada y lectura de tablas.

## Version actual

v1.0.1

## Novedades de v1.0.1

- Mejor deteccion y lectura de bloques con estructura de documento.
- Mejor lectura de tablas en facturas.
- Exportacion DOCX mas limpia y legible.
- Correccion de duplicados en resultados.
- Eliminacion de ruido en la lectura final.

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
- `ocr_<archivo>.docx` con contenido final formateado.

## Estructura del proyecto

- `scr/proceso_principal.py`: flujo principal y exportaciones.
- `scr/procesador_pdf.py`: lectura PDF y conversion por pagina.
- `scr/procesador_imagen.py`: preprocesado y llamada OCR.
- `scr/motor_ocr.py`: motor OCR y parseo de estructura/layout.
- `requirements.txt`: dependencias del proyecto.

## Notas tecnicas

- OCR principal basado en PaddleOCR 3.4.0.
- Runtime estable con PaddlePaddle 3.2.2.
- Soporte de estructura/layout para aproximar salida al formato de factura original.
