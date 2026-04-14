# Lector de facturas con PaddleOCR

Proyecto Python para procesar facturas en PDF o imagen, detectar si el PDF es escaneado, convertir paginas a PNG, aplicar OCR con PaddleOCR y exportar resultados en JSON/TXT/DOCX.

## Estado actual (v1.0.0)

- Motor OCR unificado: solo PaddleOCR.
- Compatibilidad estabilizada para Windows con Python 3.13.
- OCR multi-pagina para PDF.
- Exportacion de resultados estructurados y texto plano.

## Problema principal detectado

Durante las pruebas, el flujo devolvia salida vacia o `"motor": "error"` aun cuando el archivo de entrada era correcto. El error observado fue:

`ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]`

Ese fallo no era del enrutamiento del proyecto, sino una incompatibilidad de runtime en la combinacion Paddle/PaddleOCR usada en Windows.

## Como se resolvio

1. Se elimino RapidOCR del flujo y de dependencias para evitar rutas paralelas de ejecucion.
2. Se fijo el stack OCR en:
   - `paddleocr==3.4.0`
   - `paddlepaddle==3.2.2`
3. Se forzo `ocr_version="PP-OCRv3"` para mantener una combinacion estable con idioma espanol.
4. Se ajustaron flags de compatibilidad en runtime (`mkldnn/onednn/pir`) para evitar rutas problematicas.
5. Se adapto el parser al formato real de salida de PaddleOCR 3.x (`dt_polys`, `rec_texts`, `rec_scores`).

## Funcionalidades

- Deteccion de tipo de archivo (`pdf`, `png`, `jpg`, `jpeg`).
- Analisis PDF:
  - Verifica encabezado `%PDF-`.
  - Extrae metadatos y texto base.
  - Detecta PDF escaneado por cantidad de palabras.
  - Convierte todas las paginas a PNG a 500 DPI aprox.
- Analisis imagen:
  - Preprocesado con OpenCV.
  - OCR con PaddleOCR.
- Salidas:
  - `resultado_*.json` con estructura OCR y bounding boxes.
  - `texto_*.txt` con texto extraido.
  - `ocr_*.docx` con texto y estructura.

## Estructura principal

- `scr/proceso_principal.py`: orquestacion y guardado de salidas.
- `scr/procesador_pdf.py`: validacion y conversion PDF->PNG.
- `scr/procesador_imagen.py`: preprocesado OpenCV y llamada OCR.
- `scr/motor_ocr.py`: wrapper PaddleOCR y normalizacion de resultados.
- `requirements.txt`: dependencias del proyecto.

## Instalacion

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecucion

```powershell
.\.venv\Scripts\python.exe scr\proceso_principal.py
```

Por defecto procesa la ruta configurada en `RUTA_ARCHIVO_ENTRADA` dentro de `scr/proceso_principal.py`.

## Salidas esperadas

En carpeta `salida/` se generan:

- `resultado_<archivo>.json`
- `texto_<archivo>.txt`
- `ocr_<archivo>.docx`

## Seguridad y buenas practicas para Git

- No subir archivos sensibles (credenciales, tokens, llaves privadas).
- No subir artefactos temporales o de ejecucion local (`__pycache__`, salidas de prueba, configs locales IDE).
- Revisar siempre `git status` antes de commit/push para confirmar que solo viajan archivos de codigo y documentacion.
