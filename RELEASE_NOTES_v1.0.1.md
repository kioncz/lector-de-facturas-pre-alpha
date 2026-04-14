# Release v1.0.1

Fecha: 2026-04-14

## Funcionalidades y mejoras

- Mejor deteccion de contenido en facturas usando estructura de documento.
- Mejor lectura de tablas en facturas para conservar columnas clave.
- Mejor lectura final del proceso para salida mas limpia.
- Mejor presentacion del resultado en DOCX.

## Fixed

- Corregido problema de doble deteccion en la salida final.
- Corregida duplicacion de contenido en exportaciones.
- Eliminacion de ruido de lecturas en el texto final.
- Ajustes de parseo para bloques estructurados de layout.

## Archivos impactados

- `scr/motor_ocr.py`
- `scr/procesador_imagen.py`
- `scr/procesador_pdf.py`
- `scr/proceso_principal.py`
- `README.md`
- `requirements.txt`
