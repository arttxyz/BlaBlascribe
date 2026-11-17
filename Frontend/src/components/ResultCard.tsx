import { useEffect, useState } from "react";
import type { TranscriptionResult } from "../types";
import { forceAdvancedAi, getAudioDownloadUrl, getDownloadUrl } from "../lib/api";
import { Icon } from "./Icon";

interface ResultCardProps {
  result: TranscriptionResult;
  displayName: string;
  downloading: boolean;
  onDownload: () => void;
}

function LrcLine({ line }: { line: string }) {
  const match = line.match(/^(\[\d{1,3}:\d{2}(?:[.:]\d{1,3})?\])(\s*)(.*)$/);

  if (!match) {
    return <div className="lrc-line lrc-line-plain">{line || "\u00a0"}</div>;
  }

  return (
    <div className="lrc-line">
      <span className="lrc-timestamp">{match[1]}</span>
      <span className="lrc-text">{match[3] || "\u00a0"}</span>
    </div>
  );
}

export function ResultCard({ result, displayName, downloading, onDownload }: ResultCardProps) {
  const [copied, setCopied] = useState(false);
  const [thumbnailFailed, setThumbnailFailed] = useState(false);
  const [audioDownloading, setAudioDownloading] = useState(false);
  const [lrcContent, setLrcContent] = useState(result.lrcContent);
  const [isForcingAi, setIsForcingAi] = useState(false);
  const [aiMessage, setAiMessage] = useState("");
  const [aiError, setAiError] = useState("");
  const lines = lrcContent.split(/\r?\n/);

  useEffect(() => {
    setLrcContent(result.lrcContent);
    setAiMessage("");
    setAiError("");
  }, [result.lrcContent]);

  const handleCopy = async () => {
    if (!lrcContent) return;

    try {
      await navigator.clipboard.writeText(lrcContent);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  const handleAudioDownload = () => {
    setAudioDownloading(true);
    window.setTimeout(() => setAudioDownloading(false), 1500);
  };

  const handleForceAdvancedAi = async () => {
    setIsForcingAi(true);
    setAiMessage("");
    setAiError("");

    try {
      const response = await forceAdvancedAi(result.baseName);
      setLrcContent(response.lrcContent);
      setAiMessage("Sincronização ajustada com sucesso via IA!");
    } catch (error) {
      setAiError(error instanceof Error ? error.message : "Não foi possível refazer a sincronização.");
    } finally {
      setIsForcingAi(false);
    }
  };

  return (
    <section className="result-card studio-card" aria-live="polite">
      <div className="result-topline">
        <span className="success-badge"><Icon name="check" /> Pronto a tocar</span>
        <span className="result-format">LRC / SYNC STUDIO</span>
      </div>

      <div className="studio-layout">
        <div className="cover-column">
          <div className={`cover-art${thumbnailFailed || !result.thumbnail ? " cover-placeholder" : ""}`}>
            {result.thumbnail && !thumbnailFailed ? (
              <img
                src={result.thumbnail}
                alt={`Capa de ${displayName}`}
                onError={() => setThumbnailFailed(true)}
              />
            ) : (
              <Icon name="music" />
            )}
          </div>
          <div className="cover-meta">
            <p className="eyebrow">Faixa processada</p>
            <h2 title={displayName}>{displayName}</h2>
          </div>
        </div>

        <div className="lrc-column">
          <div className="lrc-heading">
            <div>
              <p className="eyebrow">Preview sincronizado</p>
              <p className="lrc-heading-copy">Confere cada verso antes de exportar.</p>
            </div>
            <span className="line-count">{lrcContent ? `${lines.length} linhas` : "Sem conteúdo"}</span>
          </div>
          <div className={`lrc-viewer${isForcingAi ? " lrc-viewer-processing" : ""}`} tabIndex={0} aria-label="Pré-visualização do conteúdo LRC">
            {isForcingAi ? (
              <div className="lrc-empty">
                <span className="button-loader" aria-hidden="true" />
                <span>A isolar vocais e a reordenar com IA...</span>
              </div>
            ) : lrcContent ? (
              lines.map((line, index) => <LrcLine key={`${index}-${line}`} line={line} />)
            ) : (
              <div className="lrc-empty">
                <Icon name="wave" />
                <span>A API não devolveu o conteúdo LRC para pré-visualização.</span>
              </div>
            )}
          </div>
          <div className="ai-feedback" aria-live="polite">
            {aiMessage && <span className="ai-success">{aiMessage}</span>}
            {aiError && <span className="ai-error">{aiError}</span>}
          </div>
          <button className="advanced-ai-button" type="button" onClick={handleForceAdvancedAi} disabled={isForcingAi}>
            {isForcingAi ? <span className="button-loader" aria-hidden="true" /> : <span aria-hidden="true">⚠</span>}
            <span>{isForcingAi ? "A isolar vocais e a reordenar com IA..." : "Letra incorreta? Forçar IA Avançada"}</span>
          </button>
        </div>
      </div>

      <div className="result-bottom studio-actions">
        <span className="file-name" title={result.fileName}>{result.fileName}</span>
        <div className="action-buttons">
          <button className="copy-button" type="button" onClick={handleCopy} disabled={!lrcContent}>
            <Icon name={copied ? "check" : "copy"} />
            <span>{copied ? "Copiada" : "Copiar letra"}</span>
          </button>
          <a
            className="download-button audio-button"
            href={getAudioDownloadUrl(result.baseName)}
            download
            onClick={handleAudioDownload}
            aria-busy={audioDownloading}
          >
            {audioDownloading ? <span className="button-loader" aria-hidden="true" /> : <Icon name="music" />}
            <span>{audioDownloading ? "A preparar..." : "Descarregar música (.mp3)"}</span>
          </a>
          <a
            className="download-button"
            href={getDownloadUrl(result.baseName)}
            download={result.fileName}
            onClick={onDownload}
            aria-busy={downloading}
          >
            {downloading ? <span className="button-loader" aria-hidden="true" /> : <Icon name="download" />}
            <span>{downloading ? "A descarregar..." : "Descarregar .lrc"}</span>
          </a>
        </div>
      </div>
    </section>
  );
}
