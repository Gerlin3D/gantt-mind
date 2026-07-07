type PlanErrorStateProps = {
  error: Error | null;
  onRetry: () => void;
};

export function PlanErrorState({ error, onRetry }: PlanErrorStateProps) {
  return (
    <main className="state-page">
      <section className="state-panel" aria-labelledby="error-title">
        <p className="eyebrow">Demo plan</p>
        <h1 id="error-title">Could not load the plan</h1>
        <p>Check that the backend is running and the demo seed was applied.</p>
        {import.meta.env.DEV && error ? <pre>{error.message}</pre> : null}
        <button className="primary-button" type="button" onClick={onRetry}>
          Retry
        </button>
      </section>
    </main>
  );
}
