import os, gguf
for f in os.listdir('modelo'):
    if f.endswith('.gguf'):
        try:
            r = gguf.GGUFReader(os.path.join('modelo', f))
            dim = 'unknown'
            for key in ['gemma.embedding_length', 'gemma2.embedding_length', 'llama.embedding_length', 'qwen2.embedding_length']:
                if key in r.fields:
                    dim = r.fields[key].parts[-1]
                    break
            print(f'- {f}: {dim} dimensiones')
        except Exception as e:
            print(f'- {f}: Error al leer: {e}')
