from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import re
import subprocess
import json
from faster_whisper import WhisperModel
import yt_dlp

# Configuração do cache no Disco D
CACHE_DIR = "D:/ia_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TORCH_HOME"] = CACHE_DIR
os.environ["XDG_CACHE_HOME"] = CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="AI Music Transcriber API",
    description="API para isolamento de voz, transcrição com Whisper e geração de LRC",
    version="1.1"
)

# Carregamento global do modelo Whisper para evitar recarregamento a cada requisição
print("A carregar o modelo Whisper (large-v3)...")
whisper_model = WhisperModel("large-v3", device="cpu", compute_type="int8")
print("Modelo Whisper carregado com sucesso!")

class PedidoTranscricao(BaseModel):
    entrada: str

def obter_audio_por_entrada(entrada: str) -> str:
    if os.path.exists(entrada):
        return entrada

    os.makedirs("downloads", exist_ok=True)
    query = entrada if entrada.startswith("http") else f"ytsearch1:{entrada}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if 'entries' in info:
            info = info['entries'][0]
        caminho_baixado = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
        return caminho_baixado

def separar_voz(caminho_audio: str) -> str:
    subprocess.run(["demucs", "-n", "htdemucs_ft", caminho_audio], check=True)
    nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
    caminho_voz = os.path.join("separated", "htdemucs_ft", nome_base, "vocals.wav")
    return caminho_voz

def segundos_para_lrc(segundos: float) -> str:
    minutos = int(segundos // 60)
    secs = int(segundos % 60)
    centesimos = int((segundos - int(segundos)) * 100)
    return f"[{minutos:02d}:{secs:02d}.{centesimos:02d}]"

def checar_idioma_misto(texto_completo: str) -> bool:
    tem_latin = bool(re.search(r'[a-zA-Z]', texto_completo))
    tem_asian = bool(re.search(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]', texto_completo))
    return tem_latin and tem_asian

def calcular_score_qualidade(precisao_idioma: float, idioma_misto: bool, avg_logprob: float):
    if precisao_idioma < 0.60 or avg_logprob < -1.0:
        status = "Duvidável"
        motivo = "Baixa precisão no idioma ou probabilidade fraca no áudio."
    elif idioma_misto or precisao_idioma < 0.85:
        status = "Boa"
        motivo = "Transcrição consistente com idioma misto ou variação."
    else:
        status = "Correta"
        motivo = "Alta precisão e clareza detectadas."
    return status, motivo

def pipeline_transcricao(entrada: str) -> dict:
    caminho_audio = obter_audio_por_entrada(entrada)
    caminho_voz = separar_voz(caminho_audio)

    # Configuração ajustada para detecção automática e suporte a múltiplos idiomas/gírias
    segments, info = whisper_model.transcribe(
        caminho_voz, 
        beam_size=5, 
        language=None, # Deixa automático para detetar japonês, coreano, inglês, etc.
        task="transcribe",
        initial_prompt="Song lyrics, featuring mixed languages, slang, and foreign terms like English, Japanese, and Korean."
    )

    linhas_lrc = []
    texto_completo = ""
    soma_logprobs = 0
    total_segmentos = 0

    for segment in list(segments):
        tempo_fmt = segundos_para_lrc(segment.start)
        texto_segmento = segment.text.strip()
        linhas_lrc.append(f"{tempo_fmt}{texto_segmento}")
        texto_completo += " " + texto_segmento
        soma_logprobs += segment.avg_logprob
        total_segmentos += 1

    logprob_medio = (soma_logprobs / total_segmentos) if total_segmentos > 0 else 0
    idioma_misto = checar_idioma_misto(texto_completo)
    status_q, motivo_q = calcular_score_qualidade(info.language_probability, idioma_misto, logprob_medio)

    nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
    lrc_out = f"{nome_base}.lrc"
    json_out = f"{nome_base}_metricas.json"

    with open(lrc_out, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_lrc))

    relatorio = {
        "idioma_detectado": info.language,
        "precisao_idioma": round(info.language_probability, 2),
        "status_qualidade": status_q,
        "motivo_status": motivo_q,
        "idioma_misto_detectado": idioma_misto,
        "arquivo_lrc": lrc_out,
        "nome_base": nome_base
    }

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=4, ensure_ascii=False)

    return relatorio

# --- ROTAS DA API ---

@app.get("/")
def home():
    return {"mensagem": "API do Transcritor de Música a funcionar!"}

@app.post("/api/transcrever")
def processar_transcricao(pedido: PedidoTranscricao):
    try:
        if not pedido.entrada:
            raise HTTPException(status_code=400, detail="A entrada não pode estar vazia.")
        
        resultado = pipeline_transcricao(pedido.entrada)
        return {
            "status": "sucesso",
            "dados": resultado
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/lrc/{nome_arquivo}")
def baixar_lrc(nome_arquivo: str):
    caminho = f"{nome_arquivo}.lrc" if not nome_arquivo.endswith(".lrc") else nome_arquivo
    if os.path.exists(caminho):
        return FileResponse(caminho, media_type="text/plain", filename=os.path.basename(caminho))
    raise HTTPException(status_code=404, detail="Ficheiro .lrc não encontrado.")

@app.get("/api/download/metrics/{nome_arquivo}")
def baixar_metricas(nome_arquivo: str):
    caminho = f"{nome_arquivo}_metricas.json" if not nome_arquivo.endswith("_metricas.json") else nome_arquivo
    if os.path.exists(caminho):
        return FileResponse(caminho, media_type="application/json", filename=os.path.basename(caminho))
    raise HTTPException(status_code=404, detail="Relatório de métricas não encontrado.")