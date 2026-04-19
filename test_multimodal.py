#!/usr/bin/env python3
from pathlib import Path
from llama_cpp import Llama

print("=== Test Multimodal ===\n")

# Cargar modelo
ruta_modelo = Path("modelo/google_gemma-4-E2B-it-Q4_K_M.gguf")
ruta_mmproj = Path("modelo/mmproj-F16.gguf")

print(f"Modelo: {ruta_modelo.exists()} ({ruta_modelo.stat().st_size / (1024**3):.2f} GB)")
print(f"mmproj: {ruta_mmproj.exists()} ({ruta_mmproj.stat().st_size / (1024**3):.2f} GB)")

print("\nCargando modelo con mmproj...")
llm = Llama(
    model_path=str(ruta_modelo),
    mmproj_path=str(ruta_mmproj),
    n_threads=2,
    n_ctx=2048,
    verbose=False,
)
print("✓ Modelo cargado")

# Probar con imagen
imagen_path = Path("salida/pagina_pdf__con_img2_1.png")
print(f"\nImagen: {imagen_path.exists()} ({imagen_path.stat().st_size / 1024:.1f} KB)")

print("\n--- Probando image_url con file:// ---")
resp = llm.create_chat_completion(
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"file://{imagen_path.absolute()}"},
                },
            ],
        }
    ],
    max_tokens=100,
)
print("Respuesta:")
print(resp["choices"][0]["message"]["content"][:300])
