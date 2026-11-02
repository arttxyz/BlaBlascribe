# ToDo — BlaBlascribe

## 1. Interface principal, identidade e tema
- [x] Criar uma aplicação web minimalista e moderna focada em gerar e descarregar ficheiros de letras sincronizadas (.lrc) para música, com foco especial em Trap, Hip-Hop e Underground.
- [x] Aplicar dark mode por predefinição, com fundos pretos ou cinzentos carvão, fontes modernas e destaques subtis em verde néon ou roxo/magenta escuro, mantendo a estética underground/cyberpunk/clean.
- [x] Manter a interface limpa, centralizada e orientada à usabilidade, sem poluição visual.
- [x] Incluir no header o nome/logótipo “BlaBlascribe” e um botão para alternar entre modo escuro e modo claro, preservando a preferência do utilizador.
- [x] Incluir uma área hero com input proeminente para o utilizador escrever o nome da música, artista ou colar um link do YouTube, acompanhado pelo botão “Gerar .lrc”.

## 2. Geração de transcrição e estados da API
- [x] Comunicar diretamente com a API FastAPI, apontando para `http://127.0.0.1:8000` por predefinição e permitindo configurar a URL base da API sem alterar os componentes da interface.
- [x] Ao submeter, enviar `POST /api/transcrever` com o body JSON `{"entrada":"string"}`.
- [x] Aguardar a resposta da API sem timeout estático, permitindo downloads e processamento demorados sem falso erro de dois minutos.
- [x] Mostrar um estado de processamento amigável, com indicador visual animado e botão temporariamente indisponível enquanto a API trabalha.
- [x] Tratar validação, falhas de rede e respostas inválidas da API com mensagens de erro acionáveis e opção para tentar novamente.

## 3. Estúdio de sincronização e download do .lrc
- [x] Depois do sucesso, mostrar uma área de resultados com a música processada, a fonte da letra e o nome do ficheiro gerado.
- [x] Renderizar `conteudo_lrc` num viewer scrollável, preservando cada linha e destacando os timestamps.
- [x] Mostrar capa fornecida por `capa_url`/`cover_url` ou placeholder cyberpunk quando não houver imagem.
- [x] Disponibilizar o botão secundário “Copiar letra” e o botão “Descarregar .lrc”.
- [x] Efetuar o download por `GET /api/download/lrc/{nome_base}`, iniciando o descarregamento do ficheiro .lrc.
- [x] Mostrar uma indicação visual clara enquanto o download é iniciado.

## 4. Responsividade e acessibilidade básica
- [x] Manter o layout modular, responsivo e funcional em desktop e mobile.
- [x] Incluir acessibilidade básica, estados de foco claros e boa utilização por teclado.

## 5. Validação e entrega
- [x] Instalar dependências e confirmar que o typecheck e o build de produção terminam sem erros.
- [x] Confirmar o manifesto de rotas, o servidor local e os layouts de desktop e mobile.
- [x] Guardar a versão atualizada no repositório do projeto.
