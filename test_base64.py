import base64
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
try:
    handler = Llava15ChatHandler(clip_model_path='modelo/mmproj-F16.gguf', verbose=False)
    llm = Llama(model_path='modelo/gemma-4-E4B-it-Q4_K_M.gguf', chat_handler=handler, n_ctx=2048, verbose=False)
    print('Model Loaded')
    with open('salida/texto_pdf_con_img.txt', 'wb') as f: pass  # Dummy check if file exists, we'll just test a blank image
    img_b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=' # 1x1 px
    res = llm.create_chat_completion(messages=[{'role': 'user', 'content': [{'type': 'text', 'text': 'Describe la imagen'}, {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}}]}], max_tokens=50)
    print(res['choices'][0]['message']['content'])
except Exception as e:
    print(f'ERROR: {e}')
