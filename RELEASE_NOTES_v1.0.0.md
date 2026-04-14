# Release v1.0.0

Fecha: 2026-04-13

## Resumen

Primera version estable del pipeline OCR con PaddleOCR para facturas PDF/imagen en Windows, con soporte multi-pagina y exportacion en JSON/TXT/DOCX.

## Problema corregido

- Se resolvio el error runtime de Paddle:
  - `ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]`
- Se elimino el estado de salida vacia que reportaba `"motor": "error"`.

## Cambios principales

- OCR unificado en PaddleOCR (RapidOCR eliminado del flujo).
- Dependencias actualizadas:
  - `paddleocr==3.4.0`
  - `paddlepaddle==3.2.2`
  - `PyMuPDF==1.25.1`
  - `python-docx==1.2.0`
- Forzado `ocr_version="PP-OCRv3"` para estabilidad con espanol.
- Soporte OCR para todas las paginas del PDF.
- Parser de resultados adaptado a formato PaddleOCR 3.x (`dt_polys`, `rec_texts`, `rec_scores`).
- Exportacion DOCX mejorada con texto y estructura OCR.

## Archivos relevantes

- `requirements.txt`
- `scr/motor_ocr.py`
- `scr/procesador_pdf.py`
- `scr/procesador_imagen.py`
- `scr/proceso_principal.py`
- `README.md`

## Validacion

- Ejecucion end-to-end completada con `scr/proceso_principal.py`.
- Se generan salidas:
  - `salida/resultado_pdf_con_img.json`
  - `salida/texto_pdf_con_img.txt`
  - `salida/ocr_pdf_con_img.docx`
- OCR detecta contenido real de factura (cabeceras, datos de cliente, lineas e importes).
