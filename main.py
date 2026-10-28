from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import re
import subprocess
import requests
import lyricsgenius
import yt_dlp
import traceback

CACHE_DIR = "D:/ia_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TORCH_HOME"] = CACHE_DIR
os.environ["XDG_CACHE_HOME"] = CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

GENIUS_TOKEN = "KNQoUNKhbiYwYMryXuMdV6jHftds60mVOMdYAdIIUZpRh0BQS89yx_6oVbmnTN9o"
genius = lyricsgenius.Genius(GENIUS_TOKEN, remove_section_headers=True)

app = FastAPI(
    title="AI Music Transcriber API (Bulletproof)",
    version="4.1"
)

print("API Blindada v4.1 iniciada com sucesso!")

class PedidoTranscricao(BaseModel):
    entrada: str

def buscar_letra_genius(query: str) -> str:
    try:
        song = genius.search_song(query)
        if song and song.lyrics:
            letra_limpa = re.sub(r'^\d+ Contributors.*Lyrics', '', song.lyrics)
            letra_limpa = re.sub(r'Embed$', '', letra_limpa)
            linhas = [l.strip() for l in letra_limpa.split('\n') if l.strip() and not l.startswith('[')]
            return "\n".join(linhas)
    except Exception as e:
        print(f"Erro ao procurar no Genius: {e}")
    return ""

def buscar_lrc_lrclib(track_name: str) -> dict:
    try:
        query_limpa = track_name.replace("Official Music Video", "").replace("MV", "").strip()
        url = f"https://lrclib.net/api/search?q={query_limpa}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            results = response.json()
            if results:
                for res in results:
                    if res.get("syncedLyrics"):
                        return {"tipo": "synced", "lrc": res["syncedLyrics"]}
    except Exception as e:
        print(f"Erro na LRCLIB: {e}")
    return {"tipo": "none"}

def obter_audio_por_entrada(entrada: str) -> tuple[str, str]:
    if os.path.exists(entrada):
        nome_base = os.path.splitext(os.path.basename(entrada))[0]
        return entrada, nome_base

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
        titulo = info.get("title", "")
        return caminho_baixado, titulo

def pipeline_hibrido(entrada: str) -> dict:
    caminho_audio, titulo_musica = obter_audio_por_entrada(entrada)
    nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
    nome_base = "".join(c for c in nome_base if c.isalnum() or c in (' ', '-', '_')).strip()
    lrc_out = f"{nome_base}.lrc"
    
    # --- CAMADA 1: LRCLIB ---
    dados_lrclib = buscar_lrc_lrclib(titulo_musica)
    if dados_lrclib["tipo"] == "synced":
        with open(lrc_out, "w", encoding="utf-8") as f:
            f.write(dados_lrclib["lrc"])
        return {
            "status": "sucesso",
            "fonte": "LRCLIB (Oficial Sincronizado)",
            "arquivo_lrc": lrc_out,
            "nome_base": nome_base
        }

    # --- CAMADA 2: WhisperX Isolado usando o Python da VENV ---
    print("Música não encontrada na LRCLIB. A invocar o motor WhisperX na Venv...")
    
    letra_genius = buscar_letra_genius(entrada if not entrada.startswith("http") else titulo_musica)
    
    txt_temp = f"{nome_base}_letra.txt"
    with open(txt_temp, "w", encoding="utf-8") as f:
        f.write(letra_genius)

    script_isolado_codigo = f"""
import os
import whisperx
import subprocess

os.environ["HF_HOME"] = "D:/ia_cache"
os.environ["TORCH_HOME"] = "D:/ia_cache"

caminho_audio = r"{caminho_audio}"
nome_base = r"{nome_base}"
txt_temp = r"{txt_temp}"
lrc_out = r"{lrc_out}"

print("A separar vocais via Demucs...")
subprocess.run(["demucs", "-n", "htdemucs_ft", caminho_audio], check=True)
caminho_voz = os.path.join("separated", "htdemucs_ft", os.path.splitext(os.path.basename(caminho_audio))[0], "vocals.wav")

print("A carregar WhisperX...")
device = "cpu"
model = whisperx.load_model("large-v3", device, compute_type="int8")

print("A transcrever...")
audio = whisperx.load_audio(caminho_voz)
result = model.transcribe(audio, batch_size=16)

with open(txt_temp, "r", encoding="utf-8") as f:
    letra_genius = f.read().strip()

if letra_genius and "language" in result:
    try:
        print("A alinhar fonemas...")
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
    except Exception as e:
        print(f"Erro no alinhamento: {{e}}")

linhas_lrc = []
for segment in result["segments"]:
    texto = segment["text"].strip()
    segundos = segment["start"]
    minutos = int(segundos // 60)
    secs = int(segundos % 60)
    centesimos = int((segundos - int(segundos)) * 100)
    tempo_fmt = f"[{{minutos:02d}}:{{secs:02d}}.{{centesimos:02d}}]"
    linhas_lrc.append(f"{{tempo_fmt}}{{texto}}")

with open(lrc_out, "w", encoding="utf-8") as f:
    f.write("\\n".join(linhas_lrc))

if os.path.exists(txt_temp):
    os.remove(txt_temp)
print("Processo isolado concluído com sucesso!")
"""

    script_path = "run_whisper_isolated.py"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_isolado_codigo)

    try:
        # Usa explicitamente o python de dentro da venv
        python_venv = os.path.join("venv", "Scripts", "python.exe") if os.name == "nt" else "venv/bin/python"
        resultado_sub = subprocess.run([python_venv, script_path], capture_output=True, text=True, check=True)
        print(resultado_sub.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Erro no subprocesso WhisperX:\n{e.stderr}")
        raise HTTPException(status_code=500, detail=f"Erro interno no motor de IA isolado: {e.stderr}")
    finally:
        if os.path.exists(script_path):
            os.remove(script_path)

    return {
        "status": "sucesso",
        "fonte": "WhisperX Isolado + Genius",
        "arquivo_lrc": lrc_out,
        "nome_base": nome_base
    }

@app.get("/")
def home():
    return {"mensagem": "API Blindada v4.1 a funcionar!"}

@app.post("/api/transcrever")
def processar_transcricao(pedido: PedidoTranscricao):
    try:
        if not pedido.entrada:
            raise HTTPException(status_code=400, detail="A entrada não pode estar vazia.")
        
        resultado = pipeline_hibrido(pedido.entrada)
        return resultado
    except Exception as e:
        print("\n--- ERRO NA API ---")
        traceback.print_exc()
        print("---------------------\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/lrc/{nome_arquivo}")
def baixar_lrc(nome_arquivo: str):
    caminho = f"{nome_arquivo}.lrc" if not nome_arquivo.endswith(".lrc") else nome_arquivo
    if os.path.exists(caminho):
        return FileResponse(caminho, media_type="text/plain", filename=os.path.basename(caminho))
    raise HTTPException(status_code=404, detail="Ficheiro .lrc não encontrado.")