export type Theme = "dark" | "light";

export type RequestState = "idle" | "processing" | "success" | "error";

export interface TranscriptionResult {
  status: string;
  source: string;
  fileName: string;
  baseName: string;
  lrcContent: string;
  thumbnail?: string;
}
