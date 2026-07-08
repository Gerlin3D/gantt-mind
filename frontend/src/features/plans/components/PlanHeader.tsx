type PlanHeaderProps = {
  planName: string;
  isFetching: boolean;
  isExporting: boolean;
  onImportClick: () => void;
  onExportClick: () => void;
};

export function PlanHeader({
  planName,
  isFetching,
  isExporting,
  onImportClick,
  onExportClick,
}: PlanHeaderProps) {
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
        <button className="secondary-button" type="button" onClick={onImportClick}>
          Import Excel
        </button>
        <button className="primary-button" type="button" onClick={onExportClick} disabled={isExporting}>
          {isExporting ? 'Exporting' : 'Export Excel'}
        </button>
      </div>
    </header>
  );
}
