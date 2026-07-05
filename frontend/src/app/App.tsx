const stageItems = [
  'Monorepo skeleton',
  'React and Vite shell',
  'FastAPI health endpoint',
  'PostgreSQL service',
  'Project documentation',
];

export function App() {
  return (
    <main className="app-shell">
      <section className="status-panel" aria-labelledby="app-title">
        <p className="eyebrow">Stage 1</p>
        <h1 id="app-title">GanttMind</h1>
        <p className="summary">
          Project skeleton is ready for the deterministic planning core that will follow in the
          next stage.
        </p>
        <ul className="stage-list" aria-label="Stage 1 scope">
          {stageItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
