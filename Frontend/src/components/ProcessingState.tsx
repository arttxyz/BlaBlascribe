export function ProcessingState() {
  return (
    <section className="processing-state" aria-live="polite" aria-label="A processar transcrição">
      <div className="equalizer" aria-hidden="true">
        <i /><i /><i /><i /><i />
      </div>
      <div>
        <p className="eyebrow">Motor em ação</p>
        <p className="processing-copy">A procurar letra, a alinhar cada verso.</p>
      </div>
      <span className="processing-pulse">A processar</span>
    </section>
  );
}
