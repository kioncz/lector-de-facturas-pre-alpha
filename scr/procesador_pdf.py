from __future__ import annotations

from pathlib import Path


class ProcesadorPDF:
    def __init__(self, dpi_conversion: int = 320) -> None:
        self.dpi_conversion = dpi_conversion

    def procesar(self, ruta_pdf: Path, carpeta_salida: Path) -> dict:
        rutas_png = self._convertir_pdf_a_png(ruta_pdf, carpeta_salida)
        return {
            "tipo": "pdf",
            "archivo": ruta_pdf.name,
            "ruta": str(ruta_pdf),
            "paginas": len(rutas_png),
            "rutas_png": [str(ruta) for ruta in rutas_png],
        }

    def _convertir_pdf_a_png(self, ruta_pdf: Path, carpeta_salida: Path) -> list[Path]:
        with ruta_pdf.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError(f"El archivo no parece un PDF valido: {ruta_pdf.name}")

        try:
            import fitz  # type: ignore
        except ImportError as exc:
            raise ImportError("PyMuPDF no esta instalado. Ejecuta: pip install PyMuPDF") from exc

        carpeta_salida.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(str(ruta_pdf))
        if len(doc) == 0:
            doc.close()
            raise ValueError(f"El PDF esta vacio: {ruta_pdf.name}")

        zoom = float(self.dpi_conversion) / 72.0
        matriz = fitz.Matrix(zoom, zoom)
        rutas_png: list[Path] = []

        for numero_pagina in range(len(doc)):
            pagina = doc.load_page(numero_pagina)
            pixmap = pagina.get_pixmap(matrix=matriz)
            ruta_png = carpeta_salida / f"pagina_{ruta_pdf.stem}_{numero_pagina + 1}.png"
            pixmap.save(str(ruta_png))
            rutas_png.append(ruta_png)

        doc.close()
        return rutas_png
