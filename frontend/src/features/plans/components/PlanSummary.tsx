import type { PlanDto } from '../model/types';
import { findPlanDateRange, formatDate } from '../utils/dateUtils';

type PlanSummaryProps = {
  plan: PlanDto;
  projectEndDate: string | null;
};

export function PlanSummary({ plan, projectEndDate }: PlanSummaryProps) {
  const taskRange = findPlanDateRange(plan);
  const displayEndDate = taskRange?.end ?? projectEndDate;

  return (
    <section className="plan-summary" aria-label="Project summary">
      <SummaryItem label="Start" value={formatDate(plan.start_date)} />
      <SummaryItem label="Tasks" value={plan.tasks.length.toString()} />
      <SummaryItem label="Project range" value={displayEndDate ? formatDate(displayEndDate) : 'No tasks'} />
      <SummaryItem label="Version" value={`v${plan.version}`} />
    </section>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
