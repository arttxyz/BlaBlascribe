import type { FormEvent, RefObject } from "react";
import { Icon } from "./Icon";

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
      <label className="sr-only" htmlFor="music-input">Música, artista ou link do YouTube</label>
      <div className="input-shell">
        <Icon className="input-icon" name="link" />
        <input
          ref={inputRef}
          id="music-input"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Escreve a música, artista ou cola um link do YouTube..."
          disabled={disabled}
          autoComplete="off"
        />
        <span className="input-key">↵</span>
      </div>
      <button className="generate-button" type="submit" disabled={disabled}>
        <span>{disabled ? "A processar" : "Gerar .lrc"}</span>
        {disabled ? <span className="button-loader" aria-hidden="true" /> : <Icon name="arrow" />}
      </button>
    </form>
  );
}
