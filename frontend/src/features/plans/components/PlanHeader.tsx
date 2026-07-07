type PlanHeaderProps = {
  planName: string;
  isFetching: boolean;
};

export function PlanHeader({ planName, isFetching }: PlanHeaderProps) {
  return (
    <header className="plan-header">
      <div>
        <p className="eyebrow">GanttMind</p>
        <h1>{planName}</h1>
      </div>
      <div className="header-actions">
        <span className="sync-status" aria-live="polite">
          {isFetching ? 'Refreshing' : 'Read-only demo'}
        </span>
        <button className="secondary-button" type="button" disabled>
          Excel
        </button>
      </div>
    </header>
  );
}
