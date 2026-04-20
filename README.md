# Lector de facturas con IA Gemma Multimodal

Proyecto Python para procesar facturas en PDF o imagen, con salida estructurada y lectura de tablas utilizando Inteligencia Artificial avanzada.

*Nota de Créditos:* Este proyecto utiliza los siguientes modelos alojados mediante Git LFS:
- **Gemma 4-E4B-it-Q4_K_M** creado y entrenado por **Google**. Este es el motor de razonamiento de lenguaje natural (LLM) que estructura e interpreta la factura.
- **Proyector Multimodal mmproj-F16** también creado por **Google / AI community**. Es el encargado de convertir las imágenes para que el LLM pueda interpretar visualmente la tabla y campos.

Ambos modelos son parte integral del procesamiento de facturas con IA avanzada.

## Version actual

v2.0.0

## Novedades de v2.0.0

- Implementación del motor OCR avanzado basado en Google Gemma 4-E4B Multimodal.
- Procesador PDF con detección automática de escaneados.
- Salida estructurada JSON con metadatos.
- Eliminación total de scripts de test obsoletos para limpiar el repositorio.
- **Importante:** Debido a los límites de tamaño de GitHub, el archivo de 5GB (`gemma-4-E4B-it-Q4_K_M.gguf`) no se incluye en el repositorio. Debes descargarlo y colocarlo dentro de la carpeta `/modelo/`.

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
