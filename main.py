from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re
import requests
import lyricsgenius
import yt_dlp
import traceback

CACHE_DIR = "D:/ia_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

GENIUS_TOKEN = "KNQoUNKhbiYwYMryXuMdV6jHftds60mVOMdYAdIIUZpRh0BQS89yx_6oVbmnTN9o"
genius = lyricsgenius.Genius(GENIUS_TOKEN, remove_section_headers=True)

app = FastAPI(
    title="AI Music Transcriber API (Pro Studio)",
    version="4.6"
)

# --- PERMISSÃO DE CORS PARA O FRONTEND ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("API v4.6 (Com suporte a capa e download de MP3) iniciada!")

class PedidoTranscricao(BaseModel):
    entrada: str

def buscar_letra_genius(query: str) -> str:
    try:
        print(f"A procurar letra no Genius para: {query}")
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
        query_limpa = re.sub(r'\(.*?\)|\[.*?\]', '', track_name)
        remover_termos = ["Official Music Video", "Official Video", "Music Video", "MV", "Audio", "Visualizer", "HD", "4K", "remix", "prod."]
        for termo in remover_termos:
            query_limpa = query_limpa.replace(termo, "").replace(termo.lower(), "")
        
        query_limpa = query_limpa.strip()
        print(f"A procurar na LRCLIB por: '{query_limpa}'")
        
        url = f"https://lrclib.net/api/search?q={query_limpa}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            results = response.json()
            if results:
                for res in results:
                    if res.get("syncedLyrics"):
                        print(f"LRC oficial encontrado na LRCLIB!")
                        return {"tipo": "synced", "lrc": res["syncedLyrics"]}
    except Exception as e:
        print(f"Erro na LRCLIB: {e}")
    return {"tipo": "none"}

def obter_audio_por_entrada(entrada: str) -> tuple[str, str, float, str]:
    """Descarrega o áudio e devolve o caminho, título, duração e a imagem de capa (thumbnail)"""
    if os.path.exists(entrada):
        nome_base = os.path.splitext(os.path.basename(entrada))[0]
        return entrada, nome_base, 180.0, ""

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
        duracao = info.get("duration", 180.0)
        thumbnail = info.get("thumbnail", "")
        return caminho_baixado, titulo, float(duracao), thumbnail

def pipeline_hibrido(entrada: str) -> dict:
    caminho_audio, titulo_musica, duracao_total, thumbnail = obter_audio_por_entrada(entrada)
    nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
    nome_base = "".join(c for c in nome_base if c.isalnum() or c in (' ', '-', '_')).strip()
    lrc_out = f"{nome_base}.lrc"
    
    # 1. Tenta LRCLIB
    dados_lrclib = buscar_lrc_lrclib(titulo_musica if not entrada.startswith("http") else entrada)
    if dados_lrclib["tipo"] == "synced":
        with open(lrc_out, "w", encoding="utf-8") as f:
            f.write(dados_lrclib["lrc"])
        
        with open(lrc_out, "r", encoding="utf-8") as f:
            conteudo_lrc = f.read()

        return {
            "status": "sucesso",
            "arquivo_lrc": lrc_out,
            "arquivo_audio": f"{nome_base}.mp3",
            "nome_base": nome_base,
            "conteudo_lrc": conteudo_lrc,
            "thumbnail": thumbnail
        }

    # 2. Camada Genius + Timestamps proporcionais
    letra_genius = buscar_letra_genius(entrada if not entrada.startswith("http") else titulo_musica)
    if not letra_genius:
        letra_genius = "Letra não encontrada automaticamente."

    linhas_lrc = []
    linhas = [l.strip() for l in letra_genius.split('\n') if l.strip()]
    total_linhas = len(linhas)
    tempo_por_linha = (duracao_total * 0.9) / max(total_linhas, 1)
    
    for i, linha in enumerate(linhas):
        segundos_totais = i * tempo_por_linha
        minutos = int(segundos_totais // 60)
        secs = int(segundos_totais % 60)
        centesimos = int((segundos_totais - int(segundos_totais)) * 100)
        tempo_fmt = f"[{minutos:02d}:{secs:02d}.{centesimos:02d}]"
        linhas_lrc.append(f"{tempo_fmt}{linha}")

    conteudo_lrc = "\n".join(linhas_lrc)
    with open(lrc_out, "w", encoding="utf-8") as f:
        f.write(conteudo_lrc)

    return {
        "status": "sucesso",
        "arquivo_lrc": lrc_out,
        "arquivo_audio": f"{nome_base}.mp3",
        "nome_base": nome_base,
        "conteudo_lrc": conteudo_lrc,
        "thumbnail": thumbnail
    }

@app.get("/")
def home():
    return {"mensagem": "API v4.6 a funcionar!"}

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

@app.get("/api/download/audio/{nome_arquivo}")
def baixar_audio(nome_arquivo: str):
    caminho = os.path.join("downloads", f"{nome_arquivo}.mp3" if not nome_arquivo.endswith(".mp3") else nome_arquivo)
    if os.path.exists(caminho):
        return FileResponse(caminho, media_type="audio/mpeg", filename=os.path.basename(caminho))
    raise HTTPException(status_code=404, detail="Ficheiro de áudio não encontrado.")