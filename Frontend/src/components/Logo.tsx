import { Icon } from "./Icon";

export function Logo() {
  return (
    <a className="brand" href="#top" aria-label="BlaBlascribe — início">
      <span className="brand-mark"><Icon name="wave" /></span>
      <span className="brand-name">BlaBla<span>scribe</span></span>
    </a>
  );
}
