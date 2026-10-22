import os

# Força o cache para o Disco D e desativa avisos
CACHE_DIR = "D:/ia_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
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
  subprocess.run(["demucs", "-n", "htdemucs_ft", caminho_audio], check=True)

  nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
  caminho_voz = os.path.join(
      "separated", "htdemucs_ft", nome_base, "vocals.wav"
  )
  return caminho_voz


def segundos_para_lrc(segundos):
  """Converte segundos para o formato de tempo do LRC: [mm:ss.xx]"""
  minutos = int(segundos // 60)
  secs = int(segundos % 60)
  centesimos = int((segundos - int(segundos)) * 100)
  return f"[{minutos:02d}:{secs:02d}.{centesimos:02d}]"


def transcrever_para_lrc(caminho_voz, arquivo_saida_lrc, idioma=None):
  print("A carregar o modelo do Whisper (a funcionar no CPU)...")
  model_size = "large-v3"

  # Força o uso do CPU e otimização int8 para evitar erros de driver gráfico
  model = WhisperModel(model_size, device="cpu", compute_type="int8")

  print("A transcrever e a sincronizar a letra...")
  segments, info = model.transcribe(
      caminho_voz, beam_size=5, language=idioma, task="transcribe"
  )

  print(
      f"Idioma detetado/utilizado: {info.language} (Precisão:"
      f" {info.language_probability:.2f})"
  )

  linhas_lrc = []
  for segment in segments:
    tempo_formatado = segundos_para_lrc(segment.start)
    linha_lrc = f"{tempo_formatado}{segment.text.strip()}"
    print(linha_lrc)
    linhas_lrc.append(linha_lrc)

  # Guarda no formato .lrc
  with open(arquivo_saida_lrc, "w", encoding="utf-8") as f:
    f.write("\n".join(linhas_lrc))

  print(f"\nSucesso! Ficheiro de legendas guardado em '{arquivo_saida_lrc}'.")


if __name__ == "__main__":
  arquivo_musica = "minha_musica.mp3"

  if not os.path.exists(arquivo_musica):
    print(
        f"Erro: O ficheiro '{arquivo_musica}' não foi encontrado na pasta do"
        " projeto."
    )
  else:
    # Passo 1: Isolar a voz
    vocals_wav = separar_voz(arquivo_musica)

    # Passo 2: Transcrever e gerar o .lrc com o mesmo nome base do áudio
    nome_base = os.path.splitext(os.path.basename(arquivo_musica))[0]
    arquivo_lrc = f"{nome_base}.lrc"

    transcrever_para_lrc(vocals_wav, arquivo_lrc, idioma=None)