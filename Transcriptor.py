import os

# 1. Cria a pasta no disco D imediatamente se ela não existir
CACHE_DIR = "D:/ia_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# 2. Força todas as bibliotecas de IA a usarem o Disco D como única rota de cache
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TORCH_HOME"] = CACHE_DIR
os.environ["XDG_CACHE_HOME"] = CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import subprocess
from faster_whisper import WhisperModel


def separar_voz(caminho_audio):
  print(
      "A separar a voz do instrumental com o Demucs (a usar o Disco D para os"
      " modelos)..."
  )
  # O Demucs vai descarregar os pesos do PyTorch diretamente para D:/ia_cache
  subprocess.run(["demucs", "-n", "htdemucs_ft", caminho_audio], check=True)

  nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
  caminho_voz = os.path.join(
      "separated", "htdemucs_ft", nome_base, "vocals.wav"
  )
  return caminho_voz


def transcrever_audio(caminho_voz, idioma=None):
  print("A carregar o modelo do Whisper (a guardar no Disco D)...")
  model_size = "large-v3"

  # O Whisper vai descarregar os pesos do Hugging Face diretamente para D:/ia_cache
  model = WhisperModel(model_size, device="cpu", compute_type="int8")

  print("A transcrever a letra...")
  segments, info = model.transcribe(
      caminho_voz, beam_size=5, language=idioma, task="transcribe"
  )

  print(
      f"Idioma detetado/utilizado: {info.language} (Precisão:"
      f" {info.language_probability:.2f})"
  )

  letra_final = []
  for segment in segments:
    linha = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}"
    print(linha)
    letra_final.append(segment.text)

  return "\n".join(letra_final)


if __name__ == "__main__":
  arquivo_musica = "minha_musica.mp3"

  if not os.path.exists(arquivo_musica):
    print(
        f"Erro: O ficheiro '{arquivo_musica}' não foi encontrado na pasta do"
        " projeto."
    )
  else:
    vocals_wav = separar_voz(arquivo_musica)
    letra = transcrever_audio(vocals_wav, idioma=None)

    with open("letra_gerada.txt", "w", encoding="utf-8") as f:
      f.write(letra)

    print("\nProcesso concluído! Letra guardada em 'letra_gerada.txt'.")