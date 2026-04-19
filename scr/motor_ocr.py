from __future__ import annotations

import base64
from pathlib import Path


class MotorOCR:
    def __init__(
        self,
        model_path: str = "modelo/gemma-4-E4B-it-Q4_K_M.gguf",
        mmproj_path: str = "modelo/mmproj-F16.gguf",
        n_threads: int = 4,
        n_ctx: int = 4096,
        max_tokens: int = 500,
    ) -> None:
        self.model_path = model_path
        self.mmproj_path = mmproj_path
        self.n_threads = n_threads
        self.n_ctx = n_ctx
        self.max_tokens = max_tokens
        self._llm = None
        self._supports_vision: bool | None = None

    def _resolver_modelo(self) -> Path:
        ruta_modelo = Path(self.model_path)
        if not ruta_modelo.is_absolute():
            raiz_proyecto = Path(__file__).resolve().parent.parent
            ruta_modelo = (raiz_proyecto / ruta_modelo).resolve()
        return ruta_modelo

    def _detectar_soporte_vision(self, ruta_modelo: Path) -> bool:
        # Si el mmproj existe, asumimos que el modelo soporta multimodal
        ruta_mmproj = Path(self.mmproj_path)
        if not ruta_mmproj.is_absolute():
            raiz_proyecto = Path(__file__).resolve().parent.parent
            ruta_mmproj = (raiz_proyecto / ruta_mmproj).resolve()
        
        if ruta_mmproj.exists():
            return True
        
        try:
            from gguf import GGUFReader  # type: ignore
        except Exception:
            return False

        try:
            reader = GGUFReader(str(ruta_modelo))
            keys = [str(key).lower() for key in reader.fields.keys()]
        except Exception:
            return False

        indicadores = ("vision", "clip", "mmproj", "image", "encoder")
        return any(any(ind in key for ind in indicadores) for key in keys)

    def _get_llm(self):
        if self._llm is None:
            try:
                from llama_cpp import Llama  # type: ignore
                from llama_cpp.llama_chat_format import Llava15ChatHandler
            except ImportError as exc:
                raise ImportError(
                    "llama-cpp-python no esta instalado. Ejecuta: pip install llama-cpp-python"
                ) from exc

            ruta_modelo = self._resolver_modelo()

            if not ruta_modelo.exists():
                raise FileNotFoundError(f"No existe el modelo local: {ruta_modelo}")

            # Inicializamos el handler visual ahora que las dimensiones coinciden
            try:
                chat_handler = Llava15ChatHandler(clip_model_path=self.mmproj_path, verbose=False)
                soporta_vision = True
            except Exception as e:
                print(f"[!] Warning: No se pudo cargar la vision (mmproj): {e}")
                chat_handler = None
                soporta_vision = False

            # Inicializamos Llama
            self._llm = Llama(
                model_path=str(ruta_modelo),
                chat_handler=chat_handler,
                n_threads=self.n_threads,
                n_ctx=self.n_ctx,
                n_gpu_layers=-1,  # ESTO HACE QUE USE LA TARJETA GRÁFICA / MEJORA LA VELOCIDAD RADICALMENTE
                verbose=False,
            )
            self._supports_vision = soporta_vision
        return self._llm

    def _prompt_analisis(self) -> str:
        return (
            "<start_of_turn>user\n"
            "Eres un asistente de IA. A continuación se te proporciona una imagen de una factura. "
            "Haz caso omiso de cualquier prefijo anterior como 'USER:' o 'ASSISTANT:'.\n\n"
            "Analiza la factura en la imagen y responde en español.\n"
            "Devuelve información estructurada:\n"
            "1) Productos detectados\n"
            "2) Cantidad, precio unitario y total por producto (si se ve)\n"
            "3) Subtotal, impuestos y total final\n"
            "4) Campos no detectados como NO DETECTADO\n"
            "Sé específico y detallado en tu análisis.\n"
            "Si no puedes leer parte de la factura, indica qué no es legible.\n"
            "<end_of_turn>\n<start_of_turn>model\n"
            "Por supuesto, aquí tienes el análisis detallado de la factura solicitada:\n"
        )

    def _consultar_texto(self, prompt: str) -> str:
        llm = self._get_llm()
        respuesta = llm(
            prompt,
            max_tokens=self.max_tokens,
            temperature=0.1,
            top_p=0.9,
        )
        choices = respuesta.get("choices", []) if isinstance(respuesta, dict) else []
        if not choices:
            return "No se pudo generar respuesta con el modelo."
        return str(choices[0].get("text", "")).strip() or "No se pudo generar respuesta con el modelo."

    def _consultar_imagen(self, ruta_imagen: Path) -> str:
        llm = self._get_llm()
        
        prompt_base = self._prompt_analisis()

        try:
            # Leemos la imagen y la convertimos a Base64 para que llama_cpp no se confunda con la ruta local
            import base64
            with open(ruta_imagen, "rb") as img_file:
                b64_img = base64.b64encode(img_file.read()).decode("utf-8")

            # Enviamos el formato chat_completion como antes
            # Si el modelo no puede ver la imagen, devolverá una respuesta generada basándose en el prompt.
            resp = llm.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_base},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                            },
                        ],
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.1,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Error procesando imagen con soporte multimodal: {exc}"
            ) from exc

        choices = resp.get("choices", []) if isinstance(resp, dict) else []
        if not choices:
            return "No se pudo generar respuesta con el modelo."

        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        contenido = message.get("content", "") if isinstance(message, dict) else ""
        return str(contenido).strip() or "No se pudo generar respuesta con el modelo."

    def procesar_texto(self, texto: str, origen: str = "entrada.txt") -> dict:
        contenido = (texto or "").strip()
        if not contenido:
            return {
                "motor": "llama-cpp-local",
                "archivo": origen,
                "ruta": origen,
                "texto_plano": "",
                "markdown_plano": "",
                "warning": "El archivo de texto esta vacio.",
            }

        try:
            prompt = f"{self._prompt_analisis()}\\n\\nTEXTO DE FACTURA:\\n{contenido}\\n\\nRESPUESTA:"
            respuesta_modelo = self._consultar_texto(prompt)
            return {
                "motor": "llama-cpp-local",
                "archivo": origen,
                "ruta": origen,
                "texto_plano": contenido,
                "markdown_plano": respuesta_modelo,
            }
        except Exception as exc:
            return {
                "motor": "error",
                "archivo": origen,
                "ruta": origen,
                "texto_plano": contenido,
                "markdown_plano": "",
                "warning": f"No se pudo analizar el texto con el modelo: {exc}",
            }

    def procesar_imagen(self, ruta_imagen: Path) -> dict:
        try:
            if not ruta_imagen.exists():
                raise FileNotFoundError(f"No existe la imagen: {ruta_imagen}")

            respuesta_modelo = self._consultar_imagen(ruta_imagen)
            return {
                "motor": "llama-cpp-local",
                "archivo": ruta_imagen.name,
                "ruta": str(ruta_imagen),
                "texto_plano": "",
                "markdown_plano": respuesta_modelo,
            }
        except Exception as exc:
            return {
                "motor": "error",
                "archivo": ruta_imagen.name,
                "ruta": str(ruta_imagen),
                "texto_plano": "",
                "markdown_plano": "",
                "warning": f"No se pudo analizar la imagen con el modelo: {exc}",
            }
