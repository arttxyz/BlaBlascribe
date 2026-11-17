# BlaBlascribe — Frontend

Interface React + Vite para gerar e descarregar letras sincronizadas em formato `.lrc`. A aplicação foi desenhada para uma experiência rápida, responsiva e com estética dark/underground.

## Requisitos

- Node.js 20 ou superior;
- pnpm 11 ou superior;
- A API FastAPI do BlaBlascribe a correr, por defeito, em `http://127.0.0.1:8000`.

## Executar localmente

```bash
pnpm install
pnpm dev
```

O frontend fica disponível em `http://127.0.0.1:3000`.

Para criar a versão de produção:

```bash
pnpm build
pnpm preview
```

## Configurar o endereço da API

Por defeito, o cliente chama `http://127.0.0.1:8000`. Para usar outro endereço, crie um ficheiro `.env.local` a partir de `.env.example`:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Também existe um proxy Vite apenas para desenvolvimento. Com a API local ativa, defina a variável abaixo vazia para que o browser chame `/api` no mesmo endereço do Vite; o Vite encaminha a chamada para `127.0.0.1:8000`, evitando CORS durante o desenvolvimento local:

```bash
VITE_API_BASE_URL=
```

## CORS no FastAPI

O backend atual do repositório não declara middleware CORS. Para chamadas diretas pelo browser — necessárias quando se usa o valor predefinido de `VITE_API_BASE_URL` ou uma build estática/produção — acrescente esta configuração em `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Contrato da API

A interface envia `POST /api/transcrever` com `{ "entrada": "..." }` e aguarda a resposta sem timeout estático, permitindo que o backend conclua downloads e processamento demorados. Em caso de sucesso, lê `status`, `fonte`, `arquivo_lrc`, `nome_base`, `conteudo_lrc` e `thumbnail` devolvidos pelo backend. O viewer mostra o `conteudo_lrc` linha a linha, com timestamps destacados. Os downloads apontam para `GET /api/download/lrc/{nome_base}` e `GET /api/download/audio/{nome_base}`. A thumbnail é exibida diretamente; quando vier vazia ou falhar, a interface usa apenas um ícone minimalista de música.
