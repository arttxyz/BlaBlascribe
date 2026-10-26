# 🎵 AI Music Transcriber & Synchronizer

> Uma aplicação inteligente para isolamento de vocais, transcrição multilíngue e geração automática de legendas sincronizadas (`.lrc`) utilizando inteligência artificial.

## 🚀 Sobre o Projeto
Este projeto tem como objetivo processar ficheiros de áudio ou links de música para extrair a voz de forma limpa, transcrever a letra com alta precisão e classificar a qualidade do resultado através de um sistema de métricas. Foi desenhado para alimentar um dashboard completo de gestão de transcrições.

## 🛠️ Tecnologias Utilizadas
* **Python** (Linguagem principal)
* **Faster-Whisper** (Modelo `large-v3` otimizado para transcrição rápida em CPU)
* **Demucs** (`htdemucs_ft` para separação de vocais e instrumental)
* **yt-dlp** (Gestão de downloads e pesquisas diretas por links ou nomes)
* **FastAPI** *(Em desenvolvimento)* para a arquitetura web do backend

## ⚙️ Funcionalidades Principais
* **Entrada Flexível:** Aceita ficheiros locais (`.mp3`/`.wav`), links diretos do YouTube ou termos de pesquisa por nome.
* **Isolamento de Voz:** Remove o instrumental para garantir que o Whisper analise apenas as frequências vocais.
* **Deteção de Idioma Dinâmica:** Suporte a músicas monolíngues e bilíngues (como K-Pop misturado com Inglês).
* **Geração de Ficheiros .lrc:** Criação automática de legendas sincronizadas com marcação temporal precisa (`[mm:ss.xx]`).
* **Dashboard Quality Scoring:** Exportação de um relatório em JSON contendo precisão de idioma, flags de idiomas mistos e status de qualidade (*Correta*, *Boa*, *Duvidável*).

## 📂 Estrutura do Projeto
```text
├── transcritor.py          # Script principal com todo o pipeline de IA
├── downloads/              # Pasta temporária para áudios descarregados
├── separated/              # Ficheiros separados pelo Demucs (vocais e instrumental)
├── *.lrc                   # Ficheiros de legendas gerados
└── *_metricas.json         # Relatórios de métricas para o dashboard