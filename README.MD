🎵 AI Music Transcriber API

Servidor backend em FastAPI para transcrição automática de músicas, isolamento de vocais e geração de ficheiros sincronizados .lrc, acompanhado por um sistema de métricas de qualidade.

🚀 Tecnologias Utilizadas

FastAPI & Uvicorn: Framework web e servidor ASGI para a API REST.

faster-whisper (large-v3, CPU, int8): Transcrição de alta precisão em múltiplos idiomas.

Demucs (htdemucs_ft): Isolamento e separação de faixas vocais.

yt-dlp: Orquestração e descarregamento de áudio a partir de links ou termos de pesquisa.

📥 Formatos de Entrada Suportados

A API aceita total flexibilidade no campo entrada:

Links Diretos: URLs de plataformas suportadas (YouTube, SoundCloud, etc.).

Termos de Pesquisa: Nome da música e artista (ex: "GO - Cortis").

Ficheiro Local: Caminho para um ficheiro de áudio bruto (.mp3 ou .wav).

📌 Endpoints da API

1. Estado da API

GET /

Retorna uma mensagem de confirmação de que o servidor está ativo.

2. Processamento e Transcrição

POST /api/transcrever

Payload (JSON):

{
  "entrada": "https://www.youtube.com/watch?v=..."
}


Resposta: Retorna o relatório detalhado de métricas, idioma detetado, status de qualidade e o nome base do ficheiro gerado.

3. Descarregamento de Ficheiros

GET /api/download/lrc/{nome_arquivo}

Descarrega diretamente o ficheiro de letra sincronizada (.lrc).

GET /api/download/metrics/{nome_arquivo}

Descarrega o relatório completo em formato JSON (_metricas.json).

⚙️ Como Executar Localmente

Ativa o ambiente virtual:

venv\Scripts\activate


Inicia o servidor com o Uvicorn:

uvicorn main:app --reload


Acede à documentação interativa (Swagger UI) em:
http://127.0.0.1:8000/docs