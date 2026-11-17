import type { Theme } from "../types";
import { Icon } from "./Icon";

interface ThemeToggleProps {
  theme: Theme;
  onToggle: () => void;
}

export function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  const isDark = theme === "dark";

  return (
    <button
      className="theme-toggle"
      type="button"
      onClick={onToggle}
      aria-label={isDark ? "Ativar modo claro" : "Ativar modo escuro"}
      title={isDark ? "Ativar modo claro" : "Ativar modo escuro"}
    >
      <span className="theme-toggle-icon"><Icon name={isDark ? "moon" : "sun"} /></span>
      <span>{isDark ? "Escuro" : "Claro"}</span>
    </button>
  );
}
