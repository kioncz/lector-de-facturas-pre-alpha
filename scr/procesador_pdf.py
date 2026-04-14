from __future__ import annotations

from pathlib import Path
import shutil

# Umbral de palabras para considerar un PDF como escaneado
UMBRAL_PALABRAS_ESCANEADO = 50


class ProcesadorPDF:
    def __init__(self, dpi_conversion: int = 500) -> None:
        self.dpi_conversion = dpi_conversion

    def procesar(self, ruta_pdf: Path, carpeta_salida: Path) -> dict:
        info = self._leer_info_pdf(ruta_pdf, carpeta_salida)
        return {
            "tipo": "pdf",
            "archivo": ruta_pdf.name,
            "ruta": str(ruta_pdf),
            **info,
        }

    def _leer_info_pdf(self, ruta_pdf: Path, carpeta_salida: Path) -> dict:
        # Validacion ligera de firma PDF para cortar errores pronto.
        with ruta_pdf.open("rb") as stream:
            header = stream.read(5)
        if header != b"%PDF-":
            raise ValueError(f"El archivo no parece un PDF valido: {ruta_pdf.name}")

        carpeta_salida.mkdir(parents=True, exist_ok=True)
        copia_pdf = carpeta_salida / f"copia_{ruta_pdf.name}"
        shutil.copy2(ruta_pdf, copia_pdf)

        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError:
            return {
                "paginas": None,
                "es_escaneado": None,
                "salida_pdf": str(copia_pdf),
                "salida_palabras_detectadas": 0,
                "nota": "Instala pypdf para procesar PDF",
            }

        reader = PdfReader(str(ruta_pdf))
        paginas = len(reader.pages)
        texto_paginas: list[str] = []
        total_palabras = 0

        for i, page in enumerate(reader.pages, start=1):
            texto = page.extract_text() or ""
            texto_paginas.append(f"--- PAGINA {i} ---\n{texto}\n")
            total_palabras += len(texto.split())

        es_escaneado = total_palabras < UMBRAL_PALABRAS_ESCANEADO

        salida_texto = carpeta_salida / f"texto_{ruta_pdf.stem}.txt"
        salida_texto.write_text("\n".join(texto_paginas), encoding="utf-8")

        resultado = {
            "paginas": paginas,
            "es_escaneado": es_escaneado,
            "salida_palabras_detectadas": total_palabras,
            "salida_pdf": str(copia_pdf),
            "salida_texto": str(salida_texto),
        }

        if es_escaneado:
            resultado["nota"] = f"PDF escaneado detectado ({total_palabras} palabras). Se enviara a OCR via PNG"
        else:
            resultado["nota"] = "PDF con contenido legible. Se enviara a OCR via PNG"

        rutas_png = self._convertir_pdf_a_png(ruta_pdf, carpeta_salida)
        resultado["salida_png_500dpi"] = [str(ruta_png) for ruta_png in rutas_png]
        resultado["rutas_png_para_ocr"] = [str(ruta_png) for ruta_png in rutas_png]
        resultado["ruta_png_para_ocr"] = str(rutas_png[0]) if rutas_png else None
        return resultado

    def _convertir_pdf_a_png(self, ruta_pdf: Path, carpeta_salida: Path) -> list[Path]:
        try:
            import fitz  # type: ignore
        except ImportError:
            raise ImportError(
                "fitz (PyMuPDF) no esta instalado. Ejecuta: pip install PyMuPDF"
            )

        doc = fitz.open(str(ruta_pdf))
        if len(doc) == 0:
            raise ValueError(f"El PDF esta vacio: {ruta_pdf.name}")

        matriz = fitz.Matrix(6.94, 6.94)  # Aproximadamente 500 DPI
        rutas_png: list[Path] = []

        for numero_pagina in range(len(doc)):
            pagina = doc.load_page(numero_pagina)
            pixmap = pagina.get_pixmap(matrix=matriz)
            ruta_png = carpeta_salida / f"convertido_{ruta_pdf.stem}_p{numero_pagina + 1}.png"
            pixmap.save(str(ruta_png))
            rutas_png.append(ruta_png)

        doc.close()
        return rutas_png
