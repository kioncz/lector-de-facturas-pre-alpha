from __future__ import annotations

from pathlib import Path

from motor_ocr import MotorOCR


class ProcesadorImagen:
    def __init__(self, motor_ocr: MotorOCR | None = None) -> None:
        self.motor_ocr = motor_ocr or MotorOCR()

    def procesar(self, ruta_imagen: Path) -> dict:
        resultado_modelo = self.motor_ocr.procesar_imagen(ruta_imagen)
        return {
            "tipo": "imagen",
            "archivo": ruta_imagen.name,
            "ruta": str(ruta_imagen),
            "modelo": resultado_modelo,
        }
