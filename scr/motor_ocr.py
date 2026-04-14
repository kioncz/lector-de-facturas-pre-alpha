from __future__ import annotations

import os
from pathlib import Path


def _serializar(valor):
    try:
        from numpy import ndarray  # type: ignore
    except ImportError:
        ndarray = ()

    if isinstance(valor, Path):
        return str(valor)
    if isinstance(valor, dict):
        return {str(clave): _serializar(v) for clave, v in valor.items()}
    if isinstance(valor, list):
        return [_serializar(item) for item in valor]
    if isinstance(valor, tuple):
        return [_serializar(item) for item in valor]
    if ndarray and isinstance(valor, ndarray):
        return valor.tolist()
    if hasattr(valor, "item") and callable(getattr(valor, "item")):
        try:
            return valor.item()
        except Exception:
            return str(valor)
    return valor


class MotorOCRPaddle:
    def __init__(self, language: str = "es", use_angle_cls: bool = False, ocr_version: str = "PP-OCRv3") -> None:
        os.environ.setdefault("FLAGS_use_mkldnn", "0")
        os.environ.setdefault("FLAGS_use_onednn", "0")
        os.environ.setdefault("FLAGS_enable_pir_api", "0")
        os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        self.language = language
        self.use_angle_cls = use_angle_cls
        self.ocr_version = ocr_version
        self._ocr = None

    def _get_ocr(self):
        if self._ocr is None:
            try:
                import paddle  # type: ignore

                paddle.set_flags(
                    {
                        "FLAGS_use_mkldnn": False,
                        "FLAGS_use_onednn": False,
                        "FLAGS_enable_pir_api": False,
                        "FLAGS_enable_pir_in_executor": False,
                    }
                )
            except Exception:
                pass

            from paddleocr import PaddleOCR  # type: ignore

            self._ocr = PaddleOCR(
                lang=self.language,
                use_angle_cls=self.use_angle_cls,
                ocr_version=self.ocr_version,
            )
        return self._ocr

    def procesar_imagen(self, ruta_imagen: Path) -> dict:
        try:
            return self._procesar_con_paddle(ruta_imagen)
        except Exception as exc:
            return {
                "motor": "error",
                "archivo": ruta_imagen.name,
                "ruta": str(ruta_imagen),
                "texto_plano": "",
                "markdown_plano": "",
                "lineas": [],
                "estructura_documento": [],
                "warning": f"No se pudo ejecutar PaddleOCR: {exc}",
            }

    def _procesar_con_paddle(self, ruta_imagen: Path) -> dict:
        ocr = self._get_ocr()
        resultados = ocr.ocr(str(ruta_imagen))
        detecciones = self._normalizar_detecciones(resultados)
        bloques = self._agrupar_bloques(detecciones)

        texto_plano = "\n\n".join(bloque["texto"] for bloque in bloques if bloque.get("texto"))
        markdown_plano = self._bloques_a_markdown(bloques)

        return {
            "motor": "paddleocr",
            "archivo": ruta_imagen.name,
            "ruta": str(ruta_imagen),
            "texto_plano": texto_plano,
            "markdown_plano": markdown_plano,
            "lineas": [
                {
                    "texto": item["texto"],
                    "confianza": item["confianza"],
                    "bbox": item["bbox"],
                }
                for item in detecciones
            ],
            "estructura_documento": bloques,
        }

    def _normalizar_detecciones(self, resultados) -> list[dict]:
        detecciones: list[dict] = []
        for bbox, texto, confianza in self._iterar_detecciones(resultados):
            texto = (texto or "").strip()
            if not texto:
                continue
            detecciones.append(
                {
                    "texto": texto,
                    "confianza": float(confianza),
                    "bbox": self._bbox_a_coords(bbox),
                }
            )

        detecciones.sort(key=lambda item: (item["bbox"]["y_min"], item["bbox"]["x_min"]))
        return detecciones

    def _iterar_detecciones(self, resultados):
        if not resultados:
            return

        if self._parece_resultado_dict(resultados):
            yield from self._extraer_de_resultado_dict(resultados)
            return

        if isinstance(resultados, (list, tuple)) and len(resultados) == 1 and self._parece_lista_de_detecciones(resultados[0]):
            yield from self._extraer_de_lista(resultados[0])
            return

        if self._parece_lista_de_detecciones(resultados):
            yield from self._extraer_de_lista(resultados)
            return

        if isinstance(resultados, (list, tuple)):
            for item in resultados:
                if self._parece_resultado_dict(item):
                    yield from self._extraer_de_resultado_dict(item)
                elif self._parece_deteccion(item):
                    yield self._extraer_deteccion(item)
                elif self._parece_lista_de_detecciones(item):
                    yield from self._extraer_de_lista(item)

    def _parece_lista_de_detecciones(self, valor) -> bool:
        return isinstance(valor, (list, tuple)) and bool(valor) and self._parece_deteccion(valor[0])

    def _parece_deteccion(self, valor) -> bool:
        if not isinstance(valor, (list, tuple)):
            return False

        if len(valor) >= 2 and isinstance(valor[1], (list, tuple)) and len(valor[1]) >= 2:
            return True

        if len(valor) >= 3 and isinstance(valor[1], str):
            return True

        return False

    def _parece_resultado_dict(self, valor) -> bool:
        return isinstance(valor, dict) and "dt_polys" in valor and "rec_texts" in valor

    def _extraer_de_resultado_dict(self, resultado: dict):
        bboxes = resultado.get("dt_polys") or []
        textos = resultado.get("rec_texts") or []
        confianzas = resultado.get("rec_scores") or []
        total = min(len(bboxes), len(textos), len(confianzas))
        for i in range(total):
            yield bboxes[i], textos[i], confianzas[i]

    def _extraer_de_lista(self, lista):
        for item in lista:
            if self._parece_deteccion(item):
                yield self._extraer_deteccion(item)

    def _extraer_deteccion(self, item):
        bbox = item[0]
        if len(item) >= 3 and isinstance(item[1], str):
            texto, confianza = item[1], item[2]
        else:
            texto, confianza = item[1][0], item[1][1]
        return bbox, texto, confianza

    def _bbox_a_coords(self, bbox) -> dict:
        puntos = []
        if bbox is None:
            iterable_bbox = []
        else:
            iterable_bbox = bbox

        for punto in iterable_bbox:
            try:
                x_valor = float(punto[0])
                y_valor = float(punto[1])
            except Exception:
                continue
            puntos.append((x_valor, y_valor))

        if not puntos:
            return {"x_min": 0, "y_min": 0, "x_max": 0, "y_max": 0, "ancho": 0, "alto": 0}

        xs = [p[0] for p in puntos]
        ys = [p[1] for p in puntos]
        x_min = min(xs)
        x_max = max(xs)
        y_min = min(ys)
        y_max = max(ys)
        return {
            "x_min": int(round(x_min)),
            "y_min": int(round(y_min)),
            "x_max": int(round(x_max)),
            "y_max": int(round(y_max)),
            "ancho": int(round(x_max - x_min)),
            "alto": int(round(y_max - y_min)),
        }

    def _agrupar_bloques(self, detecciones: list[dict]) -> list[dict]:
        if not detecciones:
            return []

        bloques: list[dict] = []
        bloque_actual: list[dict] = [detecciones[0]]
        ultimo_y = detecciones[0]["bbox"]["y_max"]

        for item in detecciones[1:]:
            gap = item["bbox"]["y_min"] - ultimo_y
            if gap > 28:
                bloques.append(self._construir_bloque(bloque_actual))
                bloque_actual = [item]
            else:
                bloque_actual.append(item)
            ultimo_y = max(ultimo_y, item["bbox"]["y_max"])

        bloques.append(self._construir_bloque(bloque_actual))
        return bloques

    def _construir_bloque(self, items: list[dict]) -> dict:
        items_ordenados = sorted(items, key=lambda item: (item["bbox"]["y_min"], item["bbox"]["x_min"]))
        texto = " ".join(item["texto"] for item in items_ordenados).strip()
        caja = {
            "x_min": min(item["bbox"]["x_min"] for item in items_ordenados),
            "y_min": min(item["bbox"]["y_min"] for item in items_ordenados),
            "x_max": max(item["bbox"]["x_max"] for item in items_ordenados),
            "y_max": max(item["bbox"]["y_max"] for item in items_ordenados),
        }
        caja["ancho"] = caja["x_max"] - caja["x_min"]
        caja["alto"] = caja["y_max"] - caja["y_min"]
        tipo = "heading" if self._parece_titulo(texto) else "paragraph"
        return {
            "tipo": tipo,
            "texto": texto,
            "lineas": items_ordenados,
            "bbox": caja,
        }

    def _parece_titulo(self, texto: str) -> bool:
        limpio = texto.strip()
        if not limpio:
            return False
        palabras = limpio.split()
        return (len(limpio) <= 60 and limpio.isupper()) or limpio.endswith(":") or (len(palabras) <= 4 and limpio[:1].isupper())

    def _bloques_a_markdown(self, bloques: list[dict]) -> str:
        partes: list[str] = []
        for bloque in bloques:
            texto = bloque.get("texto", "").strip()
            if not texto:
                continue
            if bloque.get("tipo") == "heading":
                partes.append(f"## {texto}")
            else:
                partes.append(texto)
        return "\n\n".join(partes)