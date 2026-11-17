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

const parseJsonResponse = async (response: Response) => {
  if (!response.ok) {
    throw new BlaBlascribeApiError(await getErrorMessage(response));
  }

  try {
    return await response.json();
  } catch {
    throw new BlaBlascribeApiError("A API devolveu uma resposta inválida. Tenta novamente.");
  }
};

export async function createTranscription(input: string): Promise<TranscriptionResult> {
  let response: Response;

  try {
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

  const payload: unknown = await parseJsonResponse(response);

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

export async function forceAdvancedAi(baseName: string): Promise<{ lrcContent: string; fileName?: string }> {
  let response: Response;

  try {
    response = await fetch(`${getApiBaseUrl()}/api/forcar-ia`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entrada: baseName }),
    });
  } catch {
    throw new BlaBlascribeApiError(
      "Não foi possível ligar à IA avançada. Confirma se o FastAPI está a correr e tenta novamente.",
    );
  }

  const payload: unknown = await parseJsonResponse(response);

  if (!isRecord(payload)) {
    throw new BlaBlascribeApiError("A IA avançada devolveu uma resposta inválida.");
  }

  const lrcContent = firstString(payload, ["conteudo_lrc", "conteudoLrc", "lrc"]);

  if (!lrcContent) {
    throw new BlaBlascribeApiError("A IA avançada terminou, mas não devolveu o conteúdo LRC.");
  }

  return {
    lrcContent,
    fileName: firstString(payload, ["arquivo_lrc", "fileName"]),
  };
}

// Aliases para garantir compatibilidade com qualquer nome que o ResultCard chame
export const forceAi = forceAdvancedAi;
export const forcarIa = forceAdvancedAi;

export function getDownloadUrl(baseName: string) {
  return `${getApiBaseUrl()}/api/download/lrc/${encodeURIComponent(baseName)}`;
}

export function getAudioDownloadUrl(baseName: string) {
  return `${getApiBaseUrl()}/api/download/audio/${encodeURIComponent(baseName)}`;
}