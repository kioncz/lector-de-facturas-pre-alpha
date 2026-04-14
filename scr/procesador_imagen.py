from __future__ import annotations

from pathlib import Path

from motor_ocr import MotorOCRPaddle


class ProcesadorImagenOpenCV:
    def __init__(self, motor_ocr: MotorOCRPaddle | None = None) -> None:
        self.motor_ocr = motor_ocr or MotorOCRPaddle()

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
        suavizada = cv2.GaussianBlur(gris, (3, 3), 0)
        binaria = cv2.equalizeHist(suavizada)

        salida_preproceso = carpeta_salida / f"pre_{ruta_imagen.stem}.png"
        cv2.imwrite(str(salida_preproceso), binaria)

        alto, ancho = gris.shape
        resultado_ocr = self.motor_ocr.procesar_imagen(ruta_imagen)

        return {
            "tipo": "imagen",
            "archivo": ruta_imagen.name,
            "ruta": str(ruta_imagen),
            "ancho": int(ancho),
            "alto": int(alto),
            "salida_preproceso": str(salida_preproceso),
            "nota": "Imagen detectada y preprocesada con OpenCV",
            "ocr": resultado_ocr,
        }
