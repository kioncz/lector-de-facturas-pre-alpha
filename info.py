import gguf
import sys
print('Loading...')
r = gguf.GGUFReader('modelo/google_gemma-4-E2B-it-Q4_K_M.gguf')
for k in ['general.architecture', 'gemma2.embedding_length', 'qwen2.embedding_length']:
    if k in r.fields:
        print(k, ''.join(chr(c) for c in getattr(r.fields[k], 'parts', [[0]])[-1]))
