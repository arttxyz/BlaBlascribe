import json
import os
import re

# Configuração do cache no Disco D
CACHE_DIR = "D:/ia_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TORCH_HOME"] = CACHE_DIR
os.environ["XDG_CACHE_HOME"] = CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import subprocess
from faster_whisper import WhisperModel


def separar_voz(caminho_audio):
  print("A separar a voz do instrumental com o Demucs...")
  subprocess.run(["demucs", "-n", "htdemucs_ft", caminho_audio], check=True)

  nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
  caminho_voz = os.path.join(
      "separated", "htdemucs_ft", nome_base, "vocals.wav"
  )
  return caminho_voz


def segundos_para_lrc(segundos):
  """Converte segundos para formato LRC: [mm:ss.xx]"""
  minutos = int(segundos // 60)
  secs = int(segundos % 60)
  centesimos = int((segundos - int(segundos)) * 100)
  return f"[{minutos:02d}:{secs:02d}.{centesimos:02d}]"


def checar_idioma_misto(texto_completo):
  """Verifica se há mistura de alfabeitos no texto (ex: Inglês + Coreano/Japonês)"""
  tem_latin = bool(re.search(r"[a-zA-Z]", texto_completo))
  tem_asian = bool(
      re.search(
          r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]",
          texto_completo,
      )
  )
  return tem_latin and tem_asian


def calcular_score_qualidade(precisao_idioma, idioma_misto, avg_logprob):
  """Define a qualidade da transcrição para o Dashboard"""
  if precisao_idioma < 0.60 or avg_logprob < -1.0:
    status = "Duvidável"
    motivo = (
        "Baixa precisão no idioma ou probabilidade fraca no áudio. Recomenda-se"
        " selecionar o idioma manualmente."
    )
  elif idioma_misto or precisao_idioma < 0.85:
    status = "Boa"
    motivo = (
        "Transcrição consistente, mas há presença de idioma misto ou variação"
        " de sotaque."
    )
  else:
    status = "Correta"
    motivo = "Alta precisão e clareza detectadas no áudio."

  return status, motivo


def transcrever_com_metricas(
    caminho_voz, arquivo_lrc_saida, arquivo_json_saida, idioma=None
):
  print("A carregar o modelo do Whisper...")
  model_size = "large-v3"
  model = WhisperModel(model_size, device="cpu", compute_type="int8")

  print("A transcrever e a analisar métricas...")
  segments, info = model.transcribe(
      caminho_voz,
      beam_size=5,
      language=idioma,
      task="transcribe",
      initial_prompt="Song lyrics with possible mixed languages.",
  )

  linhas_lrc = []
  texto_completo_acumulado = ""
  soma_logprobs = 0
  total_segmentos = 0

  segments_list = list(segments)

  for segment in segments_list:
    tempo_fmt = segundos_para_lrc(segment.start)
    texto_segmento = segment.text.strip()

    linha_lrc = f"{tempo_fmt}{texto_segmento}"
    linhas_lrc.append(linha_lrc)

    texto_completo_acumulado += " " + texto_segmento
    soma_logprobs += segment.avg_logprob
    total_segmentos += 1

    print(linha_lrc)

  # Cálculo das métricas para o Dashboard
  logprob_medio = (soma_logprobs / total_segmentos) if total_segmentos > 0 else 0
  idioma_misto_detectado = checar_idioma_misto(texto_completo_acumulado)
  status_qualidade, motivo_qualidade = calcular_score_qualidade(
      info.language_probability, idioma_misto_detectado, logprob_medio
  )

  # 1. Salvar o arquivo de legenda .lrc
  with open(arquivo_lrc_saida, "w", encoding="utf-8") as f:
    f.write("\n".join(linhas_lrc))

  # 2. Salvar o relatório JSON para o Dashboard
  relatorio_dashboard = {
      "idioma_detectado": info.language,
      "precisao_idioma": round(info.language_probability, 2),
      "status_qualidade": status_qualidade,
      "motivo_status": motivo_qualidade,
      "idioma_misto_detectado": idioma_misto_detectado,
      "arquivo_lrc": arquivo_lrc_saida,
  }

  with open(arquivo_json_saida, "w", encoding="utf-8") as f:
    json.dump(relatorio_dashboard, f, indent=4, ensure_ascii=False)

  print("\n--- Relatório do Dashboard ---")
  print(f"Status: {status_qualidade}")
  print(f"Precisão: {info.language_probability:.2f}")
  print(f"Idioma Misto: {idioma_misto_detectado}")
  print(f"Motivo: {motivo_qualidade}")
  print(f"\nArquivos gerados: '{arquivo_lrc_saida}' e '{arquivo_json_saida}'")


if __name__ == "__main__":
  arquivo_musica = "minha_musica.mp3"

  if not os.path.exists(arquivo_musica):
    print(
        f"Erro: O arquivo '{arquivo_musica}' não foi encontrado na pasta do"
        " projeto."
    )
  else:
    vocals_wav = separar_voz(arquivo_musica)

    nome_base = os.path.splitext(os.path.basename(arquivo_musica))[0]
    lrc_out = f"{nome_base}.lrc"
    json_out = f"{nome_base}_metricas.json"

    transcrever_com_metricas(
        vocals_wav, lrc_out, json_out, idioma=None
    )