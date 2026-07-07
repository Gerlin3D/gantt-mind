type PlanEmptyStateProps = {
  planName: string;
};

export function PlanEmptyState({ planName }: PlanEmptyStateProps) {
  return (
    <section className="empty-state" aria-labelledby="empty-title">
      <p className="eyebrow">{planName}</p>
      <h2 id="empty-title">No tasks yet</h2>
      <p>This plan exists, but it does not contain tasks to render on the timeline.</p>
    </section>
  );
}
