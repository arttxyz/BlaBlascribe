import type { TranscriptionResult } from "../types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export class BlaBlascribeApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BlaBlascribeApiError";
  }
}

const getApiBaseUrl = () => {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL;
  return (configuredUrl === undefined ? DEFAULT_API_BASE_URL : configuredUrl).replace(/\/+$/, "");
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null;

const firstString = (record: Record<string, unknown>, keys: string[]) => {
  for (const key of keys) {
    if (typeof record[key] === "string" && record[key].trim()) {
      return record[key];
    }
  }

  return undefined;
};

const getErrorMessage = async (response: Response) => {
  try {
    const payload: unknown = await response.json();

    if (isRecord(payload) && typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // A API pode devolver uma resposta de erro sem JSON.
  }

  return `A API respondeu com o código ${response.status}.`;
};

export async function createTranscription(input: string): Promise<TranscriptionResult> {
  let response: Response;

  try {
    // Sem timeout: a API pode descarregar e processar faixas demoradas.
    response = await fetch(`${getApiBaseUrl()}/api/transcrever`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entrada: input }),
    });
  } catch {
    throw new BlaBlascribeApiError(
      "Não foi possível falar com a API local. Confirma se o FastAPI está a correr em http://127.0.0.1:8000 e se o CORS permite este frontend.",
    );
  }

  if (!response.ok) {
    throw new BlaBlascribeApiError(await getErrorMessage(response));
  }

  let payload: unknown;

  try {
    payload = await response.json();
  } catch {
    throw new BlaBlascribeApiError("A API devolveu uma resposta inválida. Tenta novamente.");
  }

  if (!isRecord(payload)) {
    throw new BlaBlascribeApiError("A API devolveu uma resposta inválida. Tenta novamente.");
  }

  const baseName = payload.nome_base;
  const fileName = payload.arquivo_lrc;

  if (typeof baseName !== "string" || typeof fileName !== "string") {
    throw new BlaBlascribeApiError(
      "A transcrição terminou, mas a API não indicou o ficheiro .lrc gerado.",
    );
  }

  return {
    status: typeof payload.status === "string" ? payload.status : "sucesso",
    source: typeof payload.fonte === "string" ? payload.fonte : "Fonte não informada",
    fileName,
    baseName,
    lrcContent: firstString(payload, ["conteudo_lrc", "conteudoLrc", "lrc"]) ?? "",
    thumbnail: firstString(payload, ["thumbnail"]),
  };
}

export function getDownloadUrl(baseName: string) {
  return `${getApiBaseUrl()}/api/download/lrc/${encodeURIComponent(baseName)}`;
}

export function getAudioDownloadUrl(baseName: string) {
  return `${getApiBaseUrl()}/api/download/audio/${encodeURIComponent(baseName)}`;
}
