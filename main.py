import typing
import typing_extensions
if not hasattr(typing, "Self"):
    typing.Self = typing_extensions.Self

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re
import sys
import shutil
import subprocess
import requests
import lyricsgenius
import yt_dlp
import traceback
import urllib.parse
import tempfile

CACHE_DIR = os.path.abspath("./ia_cache").replace("\\", "/")
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TORCH_HOME"] = CACHE_DIR
os.environ["XDG_CACHE_HOME"] = CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

GENIUS_TOKEN = "KNQoUNKhbiYwYMryXuMdV6jHftds60mVOMdYAdIIUZpRh0BQS89yx_6oVbmnTN9o"
genius = lyricsgenius.Genius(GENIUS_TOKEN, remove_section_headers=True)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")

app = FastAPI(
    title="AI Music Transcriber API (Pro Studio + Rota Direta SoundCloud)",
    version="4.11.3"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("API v4.11.3 (Failsafe Total + Comando 'sc:') iniciada!")

class PedidoTranscricao(BaseModel):
    entrada: str

def limpar_alfanumerico(s: str) -> str:
    return "".join(c for c in s if c.isalnum()).lower()

def limpar_ansi(texto: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

def obter_token_spotify():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    try:
        auth_url = "https://accounts.spotify.com/api/token"
        response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
        }, auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET), timeout=5)
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"Erro ao autenticar no Spotify: {e}")
    return None

def buscar_musica_spotify(query: str) -> str:
    if query.startswith("http") or query.lower().startswith("sc:"):
        return query
    
    token = obter_token_spotify()
    if not token:
        return query
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api.spotify.com/v1/search?q={requests.utils.quote(query)}&type=track&limit=1"
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            tracks = data.get("tracks", {}).get("items", [])
            if tracks:
                track = tracks[0]
                nome_track = track["name"]
                artista = track["artists"][0]["name"]
                query_otimizada = f"{artista} - {nome_track}"
                print(f"Spotify encontrou com precisão: '{query_otimizada}'")
                return query_otimizada
    except Exception as e:
        print(f"Erro na busca do Spotify: {e}")
    
    return query

def buscar_letra_genius(query: str) -> str:
    try:
        print(f"A procurar letra exata no Genius para: {query}")
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
                        print("LRC oficial e verificado encontrado na LRCLIB!")
                        return {"tipo": "synced", "lrc": res["syncedLyrics"]}
    except Exception as e:
        print(f"Erro na LRCLIB: {e}")
    return {"tipo": "none"}

def extrair_titulo_oembed_youtube(url: str) -> str:
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
        resp = requests.get(oembed_url, timeout=5)
        if resp.status_code == 200:
            titulo = resp.json().get("title", "")
            titulo_limpo = re.sub(r'\(.*?\)|\[.*?\]', '', titulo).strip()
            return titulo_limpo or titulo
    except Exception as e:
        print(f"Aviso ao obter título via oEmbed: {e}")
    return ""

def baixar_via_soundcloud(query: str, ydl_opts: dict):
    print(f"A ativar ROTA SOUNDCLOUD para: '{query}'")
    opts_sc = ydl_opts.copy()
    opts_sc.pop('extractor_args', None)
    opts_sc.pop('cookiefile', None)

    with yt_dlp.YoutubeDL(opts_sc) as ydl:
        try:
            busca_sc = ydl.extract_info(f"scsearch5:{query}", download=False)
            entries = busca_sc.get('entries', []) if busca_sc else []
            for entry in entries:
                if not entry:
                    continue
                if entry.get("duration") and entry["duration"] > 800:
                    continue
                sc_url = entry.get("webpage_url") or entry.get("url")
                if sc_url:
                    try:
                        print(f"A descarregar do SoundCloud: {entry.get('title')}...")
                        info = ydl.extract_info(sc_url, download=True)
                        if info:
                            return info, ydl
                    except Exception as e:
                        print(f"Aviso no descarregamento do SoundCloud: {e}")
                        continue
        except Exception as e:
            print(f"Erro geral no SoundCloud: {e}")
    return None, None

def obter_audio_por_entrada(entrada: str) -> tuple[str, str, float, str]:
    if os.path.exists(entrada):
        nome_base = os.path.splitext(os.path.basename(entrada))[0]
        nome_base_limpo = "".join(c for c in nome_base if c.isalnum() or c in (' ', '-', '_')).strip()
        return entrada, nome_base_limpo, 180.0, ""

    os.makedirs("downloads", exist_ok=True)
    
    forcar_sc = entrada.lower().startswith("sc:")
    if forcar_sc:
        entrada = entrada[3:].strip()
        
    eh_url = entrada.startswith("http")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'no_color': True,
    }

    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = 'cookies.txt'
    else:
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['tv', 'ios', 'web']
            }
        }
    
    info = None
    ydl_usado = None
    precisa_fallback_sc = forcar_sc

    # TENTA YOUTUBE (Só se não foi forçado o SoundCloud)
    if not forcar_sc:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl_usado = ydl
            try:
                if eh_url:
                    info = ydl.extract_info(entrada, download=True)
                else:
                    queries_pesquisa = [
                        f"ytsearch3:{entrada} topic",
                        f"ytsearch3:{entrada}"
                    ]
                    for query_atual in queries_pesquisa:
                        if info: break
                        busca = ydl.extract_info(query_atual, download=False)
                        entries = busca.get('entries', []) if busca else []
                        for entry in entries:
                            if not entry: continue
                            video_url = entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
                            try:
                                print(f"A tentar YouTube: {entry.get('title')}...")
                                info = ydl.extract_info(video_url, download=True)
                                if info: break
                            except Exception as e_vid:
                                print(f"Bloqueio/Erro no YouTube ignorado. A saltar vídeo...")
                                continue
            except Exception as e:
                print(f"O YouTube bloqueou a extração completamente. A ativar Failsafe...")
                precisa_fallback_sc = True

            if not info:
                precisa_fallback_sc = True

    # ROTA EXCLUSIVA SOUNDCLOUD (Failsafe ou Forçado)
    if precisa_fallback_sc and not info:
        query_sc = extrair_titulo_oembed_youtube(entrada) if eh_url and "youtube.com" in entrada else entrada
        if query_sc:
            info, ydl_sc = baixar_via_soundcloud(query_sc, ydl_opts)
            if ydl_sc:
                ydl_usado = ydl_sc

    if not info:
        raise HTTPException(
            status_code=404,
            detail="Áudio indisponível. Usa o comando 'sc: [nome da musica]' para forçar a pesquisa no SoundCloud ou envia o ficheiro MP3."
        )

    if 'entries' in info and info['entries']:
        info = info['entries'][0]

    caminho_baixado = ydl_usado.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
    titulo = info.get("title", "audio")
    duracao = info.get("duration", 180.0)
    thumbnail = info.get("thumbnail", "")

    nome_base_limpo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).strip()
    if not nome_base_limpo:
        nome_base_limpo = "audio_downloaded"

    caminho_final = os.path.join("downloads", f"{nome_base_limpo}.mp3")
    if os.path.exists(caminho_baixado) and caminho_baixado != caminho_final:
        try:
            if os.path.exists(caminho_final):
                os.remove(caminho_final)
            os.rename(caminho_baixado, caminho_final)
        except Exception:
            caminho_final = caminho_baixado

    return caminho_final, nome_base_limpo, float(duracao), thumbnail

def pipeline_hibrido(entrada: str) -> dict:
    query_otimizada = buscar_musica_spotify(entrada)
    
    caminho_audio, titulo_musica, duracao_total, thumbnail = obter_audio_por_entrada(query_otimizada)
    nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
    lrc_out = f"{nome_base}.lrc"
    
    termo_busca_letra = titulo_musica if entrada.startswith("http") or os.path.exists(entrada) else query_otimizada

    dados_lrclib = buscar_lrc_lrclib(termo_busca_letra)
    if dados_lrclib["tipo"] == "synced":
        with open(lrc_out, "w", encoding="utf-8") as f:
            f.write(dados_lrclib["lrc"])
        
        with open(lrc_out, "r", encoding="utf-8") as f:
            conteudo_lrc = f.read()

        return {
            "status": "sucesso",
            "fonte": "LRC Oficial (Sincronizado)",
            "arquivo_lrc": lrc_out,
            "arquivo_audio": f"{nome_base}.mp3",
            "nome_base": nome_base,
            "conteudo_lrc": conteudo_lrc,
            "thumbnail": thumbnail
        }

    letra_genius = buscar_letra_genius(termo_busca_letra)
    if not letra_genius:
        conteudo_lrc = "Letra não encontrada automaticamente. Clica em 'Forçar IA Avançada' para transcrever."
    else:
        conteudo_lrc = letra_genius

    with open(lrc_out, "w", encoding="utf-8") as f:
        f.write(conteudo_lrc)

    return {
        "status": "sucesso",
        "fonte": "Genius (Sem Sincronização - Clica no botão para forçar IA)",
        "arquivo_lrc": lrc_out,
        "arquivo_audio": f"{nome_base}.mp3",
        "nome_base": nome_base,
        "conteudo_lrc": conteudo_lrc,
        "thumbnail": thumbnail
    }

@app.get("/")
def home():
    return {"mensagem": "API v4.11.3 a funcionar!"}

@app.post("/api/transcrever")
def processar_transcricao(pedido: PedidoTranscricao):
    try:
        if not pedido.entrada:
            raise HTTPException(status_code=400, detail="A entrada não pode estar vazia.")
        
        resultado = pipeline_hibrido(pedido.entrada)
        return resultado
    except HTTPException as he:
        raise he
    except Exception as e:
        print("\n--- ERRO NA API ---")
        traceback.print_exc()
        print("---------------------\n")
        raise HTTPException(status_code=500, detail=limpar_ansi(str(e)))

@app.post("/api/upload")
async def upload_audio_direto(file: UploadFile = File(...)):
    try:
        os.makedirs("downloads", exist_ok=True)
        nome_orig = os.path.splitext(file.filename)[0]
        nome_limpo = "".join(c for c in nome_orig if c.isalnum() or c in (' ', '-', '_')).strip() or "audio_upload"
        caminho_destino = os.path.join("downloads", f"{nome_limpo}.mp3")

        with open(caminho_destino, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return pipeline_hibrido(caminho_destino)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forcar-ia")
def forcar_processamento_ia(pedido: PedidoTranscricao):
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, "run_whisper_isolated_tmp.py")
    
    try:
        nome_base = pedido.entrada
        if nome_base.lower().startswith("sc:"):
            nome_base = nome_base[3:].strip()
            
        caminho_audio = None
        nome_base_limpo = limpar_alfanumerico(nome_base)

        if os.path.exists("downloads"):
            for f in os.listdir("downloads"):
                if f.endswith(".mp3"):
                    f_limpo = limpar_alfanumerico(f)
                    if nome_base_limpo in f_limpo or f_limpo in nome_base_limpo:
                        caminho_audio = os.path.join("downloads", f)
                        break
                    
        if not caminho_audio or not os.path.exists(caminho_audio):
            caminho_audio = os.path.join("downloads", f"{nome_base}.mp3")

        if not os.path.exists(caminho_audio):
            raise HTTPException(status_code=404, detail=f"Ficheiro de áudio original não encontrado para '{nome_base}'.")

        lrc_out = os.path.abspath(f"{nome_base}.lrc")
        txt_temp = os.path.abspath(f"{nome_base}_letra.txt")
        caminho_audio_abs = os.path.abspath(caminho_audio)
        
        letra_genius = buscar_letra_genius(nome_base)
        with open(txt_temp, "w", encoding="utf-8") as f:
            f.write(letra_genius or "")

        python_exec = os.path.abspath(os.path.join("venvs", "Scripts", "python.exe"))
        if not os.path.exists(python_exec):
            python_exec = sys.executable

        venv_site_pkgs = os.path.abspath(os.path.join("venvs", "Lib", "site-packages"))
        diretorio_trabalho = os.path.abspath(os.getcwd())

        script_isolado_codigo = f"""
import os
import sys

site_pkgs = r"{venv_site_pkgs}"
if site_pkgs not in sys.path:
    sys.path.insert(0, site_pkgs)

os.environ["HF_HOME"] = r"{CACHE_DIR}"
os.environ["TORCH_HOME"] = r"{CACHE_DIR}"
os.environ["XDG_CACHE_HOME"] = r"{CACHE_DIR}"

import whisperx
import subprocess

caminho_audio = r"{caminho_audio_abs}"
nome_base = r"{nome_base}"
txt_temp = r"{txt_temp}"
lrc_out = r"{lrc_out}"
python_venv = r"{python_exec}"
cwd_proj = r"{diretorio_trabalho}"

os.chdir(cwd_proj)

print("1. A separar vocais via Demucs...")
res_demucs = subprocess.run(
    [python_venv, "-m", "demucs.separate", "-n", "htdemucs", caminho_audio],
    capture_output=True,
    text=True
)
if res_demucs.returncode != 0:
    print("\\n--- ERRO DETALHADO DO DEMUCS ---")
    print("STDOUT:", res_demucs.stdout)
    print("STDERR:", res_demucs.stderr)
    print("--------------------------------\\n")
    sys.exit(res_demucs.returncode)

caminho_voz = os.path.join("separated", "htdemucs", os.path.splitext(os.path.basename(caminho_audio))[0], "vocals.wav")

print("2. A carregar WhisperX (modelo medium)...")
device = "cpu"
model = whisperx.load_model("medium", device, compute_type="int8")

print("3. A transcrever audio vocal...")
audio = whisperx.load_audio(caminho_voz)
result = model.transcribe(audio, batch_size=8)

with open(txt_temp, "r", encoding="utf-8") as f:
    letra_genius = f.read().strip()

if "language" in result:
    try:
        lang = result["language"]
        print(f"4. A alinhar fonemas para o idioma: {{lang}}...")
        model_a, metadata = whisperx.load_align_model(language_code=lang, device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
    except Exception as e:
        print(f"Aviso no alinhamento: {{e}}")

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
print("Sincronizacao de IA concluida com sucesso!")
"""

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_isolado_codigo)

        env_sub = os.environ.copy()
        env_sub["PYTHONPATH"] = venv_site_pkgs
        env_sub["PATH"] = f"{os.path.dirname(python_exec)};{env_sub.get('PATH', '')}"

        subprocess.run(
            [python_exec, script_path],
            env=env_sub,
            check=True
        )

        with open(lrc_out, "r", encoding="utf-8") as f:
            conteudo_lrc = f.read()

        return {
            "status": "sucesso",
            "fonte": "Demucs + WhisperX (IA Avançada Otimizada)",
            "conteudo_lrc": conteudo_lrc,
            "arquivo_lrc": lrc_out
        }

    except subprocess.CalledProcessError:
        print("\n--- ERRO NO SUBPROCESSO IA ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Erro na IA durante o processamento. Verifica a consola da API.")
    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=limpar_ansi(str(e)))
    finally:
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
            except Exception:
                pass

@app.get("/api/download/lrc/{nome_arquivo}")
def baixar_lrc(nome_arquivo: str):
    nome_decodificado = urllib.parse.unquote(nome_arquivo)
    caminho = f"{nome_decodificado}.lrc" if not nome_decodificado.endswith(".lrc") else nome_decodificado
    if os.path.exists(caminho):
        return FileResponse(caminho, media_type="text/plain", filename=os.path.basename(caminho))
    
    alvo_limpo = limpar_alfanumerico(nome_decodificado)
    for f in os.listdir("."):
        if f.endswith(".lrc"):
            f_limpo = limpar_alfanumerico(f)
            if alvo_limpo in f_limpo or f_limpo in alvo_limpo:
                return FileResponse(f, media_type="text/plain", filename=f)

    raise HTTPException(status_code=404, detail="Ficheiro .lrc não encontrado.")

@app.get("/api/download/audio/{nome_arquivo}")
def baixar_audio(nome_arquivo: str):
    nome_decodificado = urllib.parse.unquote(nome_arquivo)
    
    caminho = os.path.join("downloads", f"{nome_decodificado}.mp3" if not nome_decodificado.endswith(".mp3") else nome_decodificado)
    if os.path.exists(caminho):
        return FileResponse(caminho, media_type="audio/mpeg", filename=os.path.basename(caminho))
    
    if os.path.exists("downloads"):
        alvo_limpo = limpar_alfanumerico(nome_decodificado)
        for f in os.listdir("downloads"):
            if f.endswith(".mp3"):
                f_limpo = limpar_alfanumerico(f)
                if alvo_limpo in f_limpo or f_limpo in alvo_limpo:
                    caminho_encontrado = os.path.join("downloads", f)
                    return FileResponse(caminho_encontrado, media_type="audio/mpeg", filename=f)

    raise HTTPException(status_code=404, detail="Ficheiro de áudio não encontrado.")