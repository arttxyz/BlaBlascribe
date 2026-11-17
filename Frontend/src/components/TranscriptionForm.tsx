import type { FormEvent, RefObject } from "react";

interface TranscriptionFormProps {
  inputRef: RefObject<HTMLInputElement | null>;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}

export function TranscriptionForm({ inputRef, value, disabled, onChange, onSubmit }: TranscriptionFormProps) {
  return (
    <form className="transcription-form" onSubmit={onSubmit}>
      <label className="sr-only" htmlFor="music-input">Nome da música e do artista</label>
      <div className="input-shell">
        <input
          ref={inputRef}
          id="music-input"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Escreve o nome da música e do artista..."
          disabled={disabled}
          autoComplete="off"
        />
        <span className="input-key">↵</span>
      </div>
      <button className="generate-button" type="submit" disabled={disabled}>
        <span>{disabled ? "A processar" : "Gerar .lrc"}</span>
        {disabled ? <span className="button-loader" aria-hidden="true" /> : <span aria-hidden="true">→</span>}
      </button>
    </form>
  );
}
