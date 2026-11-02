import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { createTranscription } from "./lib/api";
import { Logo } from "./components/Logo";
import { ProcessingState } from "./components/ProcessingState";
import { ResultCard } from "./components/ResultCard";
import { ThemeToggle } from "./components/ThemeToggle";
import { TranscriptionForm } from "./components/TranscriptionForm";
import type { RequestState, Theme, TranscriptionResult } from "./types";

const THEME_STORAGE_KEY = "blablascribe-theme";

function getInitialTheme(): Theme {
  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);

  if (storedTheme === "dark" || storedTheme === "light") {
    return storedTheme;
  }

  return "dark";
}

function formatTrackName(baseName: string, submittedValue: string) {
  const name = baseName.replace(/_/g, " ").replace(/\s+/g, " ").trim();
  return name || submittedValue;
}

export default function App() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [input, setInput] = useState("");
  const [submittedValue, setSubmittedValue] = useState("");
  const [state, setState] = useState<RequestState>("idle");
  const [result, setResult] = useState<TranscriptionResult | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const displayName = useMemo(
    () => (result ? formatTrackName(result.baseName, submittedValue) : ""),
    [result, submittedValue],
  );

  const submitTranscription = async (rawEntry: string) => {
    const entry = rawEntry.trim();

    if (!entry) {
      setResult(null);
      setSubmittedValue("");
      setState("error");
      setErrorMessage("Escreve o nome de uma música, um artista ou cola um link do YouTube.");
      return;
    }

    setState("processing");
    setResult(null);
    setErrorMessage("");
    setSubmittedValue(entry);

    try {
      const transcription = await createTranscription(entry);
      setResult(transcription);
      setState("success");
    } catch (error) {
      setState("error");
      setErrorMessage(
        error instanceof Error ? error.message : "Ocorreu um erro inesperado. Tenta novamente.",
      );
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void submitTranscription(input);
  };

  const handleRetry = () => {
    if (submittedValue) {
      void submitTranscription(submittedValue);
      return;
    }

    setState("idle");
    window.setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleDownload = () => {
    setIsDownloading(true);
    window.setTimeout(() => setIsDownloading(false), 1500);
  };

  return (
    <div className="app-shell" id="top">
      <header className="topbar">
        <Logo />
        <ThemeToggle
          theme={theme}
          onToggle={() => setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"))}
        />
      </header>

      <main className="page-main">
        <section className="hero" aria-labelledby="hero-title">
          <p className="kicker">Sincronização de letras · Trap / Hip-Hop / Underground</p>
          <h1 id="hero-title">A tua letra, <em>no tempo certo.</em></h1>
          <p className="hero-copy">
            Cola um link ou procura uma faixa. Nós fazemos o resto e entregamos um ficheiro .lrc pronto a usar.
          </p>

          <TranscriptionForm
            inputRef={inputRef}
            value={input}
            disabled={state === "processing"}
            onChange={setInput}
            onSubmit={handleSubmit}
          />

          <div className="helper-row" aria-label="Características">
            <span>Link YouTube ou pesquisa</span>
            <span>Timing por IA</span>
            <span>Exportação .lrc</span>
          </div>
        </section>

        <div className="feedback-area">
          {state === "processing" && <ProcessingState />}

          {state === "error" && (
            <section className="error-state" role="alert">
              <span className="error-icon" aria-hidden="true">!</span>
              <div>
                <p className="eyebrow">Não foi possível gerar</p>
                <p className="error-copy">{errorMessage}</p>
              </div>
              <button className="retry-button" type="button" onClick={handleRetry}>Tentar novamente</button>
            </section>
          )}

          {state === "success" && result && (
            <ResultCard
              result={result}
              displayName={displayName}
              downloading={isDownloading}
              onDownload={handleDownload}
            />
          )}
        </div>
      </main>

      <footer className="footer">
        <p className="status-dot">API FastAPI local</p>
        <p>Feito para versos que batem certo.</p>
      </footer>
    </div>
  );
}
