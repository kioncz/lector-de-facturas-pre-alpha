from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from procesador_imagen import ProcesadorImagenOpenCV
from procesador_pdf import ProcesadorPDF


class TipoArchivo(str, Enum):
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"


EXTENSIONES_PERMITIDAS = {item.value for item in TipoArchivo}

# Flujo actual: procesar un solo archivo definido por ruta directa.
RUTA_ARCHIVO_ENTRADA = "entrada/factura_ejemplo.pdf"


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
        self.procesador_pdf = ProcesadorPDF()
        self.procesador_imagen = ProcesadorImagenOpenCV()

    def procesar(self, archivo: ArchivoEntrada, carpeta_salida: Path) -> dict:
        if archivo.tipo == TipoArchivo.PDF:
            resultado_pdf = self.procesador_pdf.procesar(archivo.ruta, carpeta_salida)
            
            # Si es un PDF escaneado que se convirtió a PNG, procésalo con OpenCV
            if resultado_pdf.get("tipo") == "pdf_escaneado_convertido":
                ruta_png = Path(resultado_pdf.get("ruta_png_para_ocr"))
                resultado_imagen = self.procesador_imagen.procesar(ruta_png, carpeta_salida)
                # Fusiona ambos resultados
                resultado_pdf["vision_computer"] = resultado_imagen
                resultado_pdf["nota"] += " -> Procesado con OpenCV"
                return resultado_pdf
            
            return resultado_pdf

        if archivo.tipo in {TipoArchivo.PNG, TipoArchivo.JPG, TipoArchivo.JPEG}:
            return self.procesador_imagen.procesar(archivo.ruta, carpeta_salida)

        raise ValueError(f"No existe procesador para el tipo: {archivo.tipo.value}")


def guardar_resultado_json(resultado: dict, carpeta_salida: Path, nombre_base: str) -> Path:
    ruta_salida = carpeta_salida / f"resultado_{nombre_base}.json"
    ruta_salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta_salida


def main() -> None:
    raiz_proyecto = Path(__file__).resolve().parent.parent
    carpeta_salida = raiz_proyecto / "salida"
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    archivo = cargar_archivo_directo(raiz_proyecto)
    enrutador = EnrutadorProcesamiento()
    resultado = enrutador.procesar(archivo, carpeta_salida)
    json_generado = guardar_resultado_json(resultado, carpeta_salida, archivo.ruta.stem)

    print("Archivo configurado detectado correctamente:")
    print(f"- {archivo.nombre} -> tipo={archivo.tipo.value}")
    print(f"Resultado guardado en: {json_generado}")
    for clave in ("salida_pdf", "salida_texto", "salida_preview", "salida_preproceso"):
        valor = resultado.get(clave)
        if valor:
            print(f"- {clave}: {valor}")


if __name__ == "__main__":
    main()
