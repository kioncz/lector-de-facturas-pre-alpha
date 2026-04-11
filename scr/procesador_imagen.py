from pathlib import Path


class ProcesadorImagenOpenCV:
    def procesar(self, ruta_imagen: Path, carpeta_salida: Path) -> dict:
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "OpenCV no esta instalado. Ejecuta: pip install opencv-python"
            ) from exc

        imagen = cv2.imread(str(ruta_imagen))
        if imagen is None:
            raise ValueError(f"No se pudo leer la imagen: {ruta_imagen.name}")

        gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        _, binaria = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        salida_preproceso = carpeta_salida / f"pre_{ruta_imagen.stem}.png"
        cv2.imwrite(str(salida_preproceso), binaria)

        alto, ancho = gris.shape
        return {
            "tipo": "imagen",
            "archivo": ruta_imagen.name,
            "ruta": str(ruta_imagen),
            "ancho": int(ancho),
            "alto": int(alto),
            "salida_preproceso": str(salida_preproceso),
            "nota": "Imagen detectada y preprocesada con OpenCV",
        }
