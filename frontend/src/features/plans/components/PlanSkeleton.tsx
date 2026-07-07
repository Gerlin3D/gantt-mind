export function PlanSkeleton() {
  return (
    <main className="plan-page" aria-busy="true">
      <div className="skeleton skeleton-header" />
      <div className="plan-summary">
        {Array.from({ length: 4 }, (_, index) => (
          <div className="summary-item skeleton-block" key={index} />
        ))}
      </div>
      <section className="gantt-workspace" aria-label="Loading Gantt workspace">
        <div className="task-table-pane">
          {Array.from({ length: 8 }, (_, index) => (
            <div className="skeleton skeleton-row" key={index} />
          ))}
        </div>
        <div className="timeline-pane">
          {Array.from({ length: 8 }, (_, index) => (
            <div className="skeleton skeleton-bar" key={index} />
          ))}
        </div>
      </section>
    </main>
  );
}
