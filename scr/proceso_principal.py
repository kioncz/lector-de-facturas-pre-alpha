from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from motor_ocr import MotorOCRPaddle
from procesador_imagen import ProcesadorImagenOpenCV
from procesador_pdf import ProcesadorPDF


class TipoArchivo(str, Enum):
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"


EXTENSIONES_PERMITIDAS = {item.value for item in TipoArchivo}

# Flujo actual: procesar un solo archivo definido por ruta directa.
RUTA_ARCHIVO_ENTRADA = "entrada/ejemplo.pdf"  # Cambia esta ruta para probar con diferentes archivos.  


@dataclass(frozen=True)
class ArchivoEntrada:
    nombre: str
    ruta: Path
    tipo: TipoArchivo


def detectar_tipo_archivo(file_path: Path) -> TipoArchivo:
    extension = file_path.suffix.lower().lstrip(".")
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValueError(
            f"Tipo no soportado para {file_path.name}. "
            f"Permitidos: {', '.join(sorted(EXTENSIONES_PERMITIDAS))}"
        )
    return TipoArchivo(extension)


def cargar_archivo_directo(raiz_proyecto: Path) -> ArchivoEntrada:
    ruta_archivo = (raiz_proyecto / RUTA_ARCHIVO_ENTRADA).resolve()
    if not ruta_archivo.exists() or not ruta_archivo.is_file():
        raise FileNotFoundError(f"No existe el archivo configurado: {ruta_archivo}")

    tipo = detectar_tipo_archivo(ruta_archivo)
    return ArchivoEntrada(nombre=ruta_archivo.name, ruta=ruta_archivo, tipo=tipo)


class EnrutadorProcesamiento:
    def __init__(self) -> None:
        self.motor_ocr = MotorOCRPaddle()
        self.procesador_pdf = ProcesadorPDF()
        self.procesador_imagen = ProcesadorImagenOpenCV(motor_ocr=self.motor_ocr)

    def procesar(self, archivo: ArchivoEntrada, carpeta_salida: Path) -> dict:
        if archivo.tipo == TipoArchivo.PDF:
            resultado_pdf = self.procesador_pdf.procesar(archivo.ruta, carpeta_salida)
            rutas_png = resultado_pdf.get("rutas_png_para_ocr")
            if not rutas_png and resultado_pdf.get("ruta_png_para_ocr"):
                rutas_png = [resultado_pdf.get("ruta_png_para_ocr")]

            resultados_imagenes = []
            for ruta_png in rutas_png or []:
                ruta_png_path = Path(ruta_png)
                resultados_imagenes.append(self.procesador_imagen.procesar(ruta_png_path, carpeta_salida))

            resultado_pdf["ocr"] = [resultado.get("ocr", {}) for resultado in resultados_imagenes]
            resultado_pdf["vision_computer"] = resultados_imagenes
            resultado_pdf["nota"] = f'{resultado_pdf.get("nota", "")} -> OCR aplicado con PaddleOCR en todas las paginas'
            return resultado_pdf

        if archivo.tipo in {TipoArchivo.PNG, TipoArchivo.JPG, TipoArchivo.JPEG}:
            return self.procesador_imagen.procesar(archivo.ruta, carpeta_salida)

        raise ValueError(f"No existe procesador para el tipo: {archivo.tipo.value}")


def guardar_resultado_json(resultado: dict, carpeta_salida: Path, nombre_base: str) -> Path:
    ruta_salida = carpeta_salida / f"resultado_{nombre_base}.json"
    ruta_salida.write_text(json.dumps(_serializar(resultado), ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta_salida


def guardar_resultado_word(resultado: dict, carpeta_salida: Path, nombre_base: str) -> Path:
    from docx import Document  # type: ignore

    texto_plano = _extraer_markdown_o_texto(resultado)
    estructura = _serializar(_extraer_estructura(resultado))
    ruta_salida = carpeta_salida / f"ocr_{nombre_base}.docx"

    document = Document()
    document.add_heading("Resultado OCR", level=1)
    document.add_paragraph(f"Archivo: {resultado.get('archivo', 'N/A')}")
    document.add_paragraph(f"Motor: {_extraer_motor(resultado)}")

    document.add_heading("Texto OCR / Markdown", level=2)
    _agregar_bloques_al_documento(document, estructura, texto_plano)

    document.add_heading("Estructura", level=2)
    document.add_paragraph(json.dumps(estructura, ensure_ascii=False, indent=2))

    document.save(str(ruta_salida))
    return ruta_salida


def _agregar_bloques_al_documento(document, estructura, texto_plano: str) -> None:
    if isinstance(estructura, list) and estructura:
        for bloque in estructura:
            if not isinstance(bloque, dict):
                continue
            texto = str(bloque.get("texto", "")).strip()
            if not texto:
                continue
            tipo = str(bloque.get("tipo", "paragraph"))
            if tipo == "heading":
                document.add_heading(texto, level=2)
            else:
                document.add_paragraph(texto)
        return

    if texto_plano:
        for linea in texto_plano.splitlines():
            linea = linea.strip()
            if not linea:
                continue
            if linea.startswith("## "):
                document.add_heading(linea[3:].strip(), level=2)
            else:
                document.add_paragraph(linea)
        return

    document.add_paragraph("(sin texto detectado)")


def _extraer_markdown_o_texto(resultado: dict) -> str:
    ocr = resultado.get("ocr")
    if isinstance(ocr, dict) and ocr.get("markdown_plano"):
        return str(ocr.get("markdown_plano"))

    if isinstance(ocr, list):
        partes = []
        for item in ocr:
            if isinstance(item, dict):
                markdown = item.get("markdown_plano")
                texto = item.get("texto_plano")
                if markdown:
                    partes.append(str(markdown))
                elif texto:
                    partes.append(str(texto))
        if partes:
            return "\n\n".join(partes)

    ocr = resultado.get("ocr")
    if isinstance(ocr, dict) and ocr.get("texto_plano"):
        texto = ocr.get("texto_plano")
        if isinstance(texto, list):
            return "\n".join(str(item) for item in texto if str(item).strip())
        return str(texto)

    if resultado.get("texto_plano"):
        texto = resultado.get("texto_plano")
        if isinstance(texto, list):
            return "\n".join(str(item) for item in texto if str(item).strip())
        return str(texto)

    vision_computer = resultado.get("vision_computer")
    if isinstance(vision_computer, list):
        partes = []
        for item in vision_computer:
            if not isinstance(item, dict):
                continue
            ocr_vision = item.get("ocr")
            if not isinstance(ocr_vision, dict):
                continue
            if ocr_vision.get("markdown_plano"):
                partes.append(str(ocr_vision.get("markdown_plano")))
            elif ocr_vision.get("texto_plano"):
                texto = ocr_vision.get("texto_plano")
                if isinstance(texto, list):
                    partes.append("\n".join(str(item) for item in texto if str(item).strip()))
                elif texto:
                    partes.append(str(texto))
        if partes:
            return "\n\n".join(partes)

    if isinstance(vision_computer, dict):
        ocr_vision = vision_computer.get("ocr")
        if isinstance(ocr_vision, dict) and ocr_vision.get("texto_plano"):
            if ocr_vision.get("markdown_plano"):
                return str(ocr_vision.get("markdown_plano"))
            texto = ocr_vision.get("texto_plano")
            if isinstance(texto, list):
                return "\n".join(str(item) for item in texto if str(item).strip())
            if texto:
                return str(texto)

    return ""


def _extraer_motor(resultado: dict) -> str:
    ocr = resultado.get("ocr")
    if isinstance(ocr, dict) and ocr.get("motor"):
        return str(ocr.get("motor"))

    if isinstance(ocr, list):
        motores = []
        for item in ocr:
            if isinstance(item, dict) and item.get("motor"):
                motores.append(str(item.get("motor")))
        if motores:
            return ", ".join(motores)

    return str(resultado.get("motor", "N/A"))


def _extraer_estructura(resultado: dict):
    ocr = resultado.get("ocr")
    if isinstance(ocr, dict) and ocr.get("estructura_documento") is not None:
        return ocr.get("estructura_documento")

    if isinstance(ocr, list):
        estructuras = []
        for item in ocr:
            if isinstance(item, dict) and item.get("estructura_documento"):
                estructuras.extend(item.get("estructura_documento") or [])
        if estructuras:
            return estructuras

    vision_computer = resultado.get("vision_computer")
    if isinstance(vision_computer, list):
        estructuras = []
        for item in vision_computer:
            if not isinstance(item, dict):
                continue
            ocr_vision = item.get("ocr")
            if isinstance(ocr_vision, dict) and ocr_vision.get("estructura_documento"):
                estructuras.extend(ocr_vision.get("estructura_documento") or [])
        if estructuras:
            return estructuras

    if isinstance(vision_computer, dict):
        ocr_vision = vision_computer.get("ocr")
        if isinstance(ocr_vision, dict):
            return ocr_vision.get("estructura_documento")

    return []


def _serializar(valor):
    if isinstance(valor, Path):
        return str(valor)
    if isinstance(valor, dict):
        return {str(clave): _serializar(v) for clave, v in valor.items()}
    if isinstance(valor, list):
        return [_serializar(item) for item in valor]
    if isinstance(valor, tuple):
        return [_serializar(item) for item in valor]
    return valor


def main() -> None:
    raiz_proyecto = Path(__file__).resolve().parent.parent
    carpeta_salida = raiz_proyecto / "salida"
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    archivo = cargar_archivo_directo(raiz_proyecto)
    enrutador = EnrutadorProcesamiento()
    resultado = enrutador.procesar(archivo, carpeta_salida)
    json_generado = guardar_resultado_json(resultado, carpeta_salida, archivo.ruta.stem)
    docx_generado = guardar_resultado_word(resultado, carpeta_salida, archivo.ruta.stem)

    print("Archivo configurado detectado correctamente:")
    print(f"- {archivo.nombre} -> tipo={archivo.tipo.value}")
    print(f"Resultado guardado en: {json_generado}")
    print(f"Documento Word guardado en: {docx_generado}")
    for clave in ("salida_pdf", "salida_texto", "salida_preview", "salida_preproceso"):
        valor = resultado.get(clave)
        if valor:
            print(f"- {clave}: {valor}")


if __name__ == "__main__":
    main()
