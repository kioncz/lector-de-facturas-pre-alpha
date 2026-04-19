from __future__ import annotations

import argparse
import json
from pathlib import Path

from motor_ocr import MotorOCR
from procesador_imagen import ProcesadorImagen
from procesador_pdf import ProcesadorPDF


EXTENSIONES_IMAGEN = {"png", "jpg", "jpeg"}
EXTENSION_PDF = "pdf"
EXTENSION_TXT = "txt"
ENTRADA_POR_DEFECTO = "entrada/pdf__con_img2.pdf"


def _leer_argumentos() -> str:
    parser = argparse.ArgumentParser(description="Analiza factura con modelo local (sin OCR).")
    parser.add_argument(
        "archivo",
        nargs="?",
        default=ENTRADA_POR_DEFECTO,
        help="Ruta de entrada (pdf, png, jpg, jpeg, txt)",
    )
    args = parser.parse_args()
    return str(args.archivo)


def _resolver_ruta(raiz_proyecto: Path, entrada: str) -> Path:
    ruta = Path(entrada)
    if not ruta.is_absolute():
        ruta = (raiz_proyecto / ruta).resolve()
    if not ruta.exists() or not ruta.is_file():
        raise FileNotFoundError(f"No existe el archivo de entrada: {ruta}")
    return ruta


def _guardar_json(resultado: dict, carpeta_salida: Path, nombre_base: str) -> Path:
    ruta = carpeta_salida / f"resultado_{nombre_base}.json"
    ruta.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def _extraer_respuesta_modelo(resultado: dict) -> str:
    modelo = resultado.get("modelo")
    if isinstance(modelo, dict):
        respuesta = modelo.get("markdown_plano")
        if respuesta:
            return str(respuesta)

    if resultado.get("tipo") == "pdf":
        partes: list[str] = []
        paginas = resultado.get("paginas_modelo", [])
        if isinstance(paginas, list):
            for i, pagina in enumerate(paginas, start=1):
                if isinstance(pagina, dict):
                    texto = str(pagina.get("markdown_plano", "")).strip()
                    if texto:
                        partes.append(f"Pagina {i}:\n{texto}")
        if partes:
            return "\n\n".join(partes)

    return "No se obtuvo respuesta del modelo."


def _guardar_txt_respuesta(resultado: dict, carpeta_salida: Path, nombre_base: str) -> Path:
    ruta = carpeta_salida / f"respuesta_modelo_{nombre_base}.txt"
    ruta.write_text(_extraer_respuesta_modelo(resultado), encoding="utf-8")
    return ruta


def _procesar_txt(ruta: Path, motor: MotorOCR) -> dict:
    contenido = ruta.read_text(encoding="utf-8", errors="replace")
    resultado_modelo = motor.procesar_texto(contenido, origen=ruta.name)
    return {
        "tipo": "txt",
        "archivo": ruta.name,
        "ruta": str(ruta),
        "modelo": resultado_modelo,
    }


def _procesar_imagen(ruta: Path, motor: MotorOCR) -> dict:
    procesador_imagen = ProcesadorImagen(motor_ocr=motor)
    return procesador_imagen.procesar(ruta)


def _procesar_pdf(ruta: Path, carpeta_salida: Path, motor: MotorOCR) -> dict:
    procesador_pdf = ProcesadorPDF()
    info_pdf = procesador_pdf.procesar(ruta, carpeta_salida)

    paginas_modelo: list[dict] = []
    for ruta_png in info_pdf.get("rutas_png", []):
        resultado = motor.procesar_imagen(Path(str(ruta_png)))
        paginas_modelo.append(resultado)

    return {
        **info_pdf,
        "paginas_modelo": paginas_modelo,
    }


def main() -> None:
    raiz_proyecto = Path(__file__).resolve().parent.parent
    carpeta_salida = raiz_proyecto / "salida"
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    entrada = _leer_argumentos()
    ruta_entrada = _resolver_ruta(raiz_proyecto, entrada)
    extension = ruta_entrada.suffix.lower().lstrip(".")

    motor = MotorOCR()

    if extension == EXTENSION_TXT:
        resultado = _procesar_txt(ruta_entrada, motor)
    elif extension in EXTENSIONES_IMAGEN:
        resultado = _procesar_imagen(ruta_entrada, motor)
    elif extension == EXTENSION_PDF:
        resultado = _procesar_pdf(ruta_entrada, carpeta_salida, motor)
    else:
        raise ValueError("Tipo de archivo no soportado. Usa pdf, png, jpg, jpeg o txt.")

    json_generado = _guardar_json(resultado, carpeta_salida, ruta_entrada.stem)
    txt_generado = _guardar_txt_respuesta(resultado, carpeta_salida, ruta_entrada.stem)

    print("Archivo procesado correctamente:")
    print(f"- entrada: {ruta_entrada}")
    print(f"- json: {json_generado}")
    print(f"- txt_modelo: {txt_generado}")


if __name__ == "__main__":
    main()
