# 🎵 BlaBlascribe API

Uma API robusta baseada em FastAPI construída para gerar ficheiros de letras sincronizadas (`.lrc`) para música, com foco especial em géneros como Trap, Hip-Hop e Underground. O sistema utiliza uma arquitetura híbrida inteligente para garantir que obténs sempre letras de alta qualidade e com o timing perfeito de forma rápida e estável.

## 🚀 Tecnologias (Stack)

* **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
* **Processamento de Áudio / IA:** PyTorch, WhisperX, Demucs, yt-dlp
* **Fontes de Letras:** LRCLIB & Genius API
* **Ambiente:** Windows-optimized com execução isolada de processos para estabilidade máxima.

## 🛠️ Endpoints Principais

* `POST /api/transcrever`
  * **Descrição:** Recebe um link do YouTube ou o nome da música, processa o áudio e gera o ficheiro `.lrc`.
  * **Body (JSON):** `{"entrada": "nome da musica ou link"}`
* `GET /api/download/lrc/{nome_arquivo}`
  * **Descrição:** Permite o download direto do ficheiro `.lrc` gerado.

## ⚙️ Como Executar Localmente

1. Clona o repositório e entra na pasta do projeto.
2. Cria e ativa um ambiente virtual (`venv`):
   ```bash
   python -m venv venvs
   # No Windows:
   venv\Scripts\activate