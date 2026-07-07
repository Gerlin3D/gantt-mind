import { useMemo, useRef, useState } from 'react';
import { useDemoPlan } from '../hooks/usePlans';
import { buildTimelineRange, generateTimelineDays, sortTasksByPosition } from '../utils/dateUtils';
import { GanttWorkspace } from './GanttWorkspace';
import { PlanEmptyState } from './PlanEmptyState';
import { PlanErrorState } from './PlanErrorState';
import { PlanHeader } from './PlanHeader';
import { PlanSkeleton } from './PlanSkeleton';
import { PlanSummary } from './PlanSummary';
import { TaskDetailsDrawer } from './TaskDetailsDrawer';

export function PlanPage() {
  const { data: plan, isPending, isError, error, refetch, isFetching } = useDemoPlan();
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [hoveredTaskId, setHoveredTaskId] = useState<string | null>(null);
  const tableScrollerRef = useRef<HTMLDivElement | null>(null);
  const timelineScrollerRef = useRef<HTMLDivElement | null>(null);
  const syncingScrollRef = useRef(false);

  const sortedTasks = useMemo(() => (plan ? sortTasksByPosition(plan.tasks) : []), [plan]);
  const selectedTask = sortedTasks.find((task) => task.id === selectedTaskId) ?? null;
  const timelineRange = plan ? buildTimelineRange(plan) : null;
  const timelineDays = timelineRange ? generateTimelineDays(timelineRange.start, timelineRange.end) : [];

  function syncVerticalScroll(source: 'table' | 'timeline', scrollTop: number) {
    if (syncingScrollRef.current) {
      return;
    }

    const target = source === 'table' ? timelineScrollerRef.current : tableScrollerRef.current;

    if (!target || target.scrollTop === scrollTop) {
      return;
    }

    syncingScrollRef.current = true;
    target.scrollTop = scrollTop;
    window.requestAnimationFrame(() => {
      syncingScrollRef.current = false;
    });
  }

  if (isPending) {
    return <PlanSkeleton />;
  }

  if (isError || !plan) {
    return <PlanErrorState error={error} onRetry={() => void refetch()} />;
  }

  return (
    <main className="plan-page">
      <PlanHeader planName={plan.name} isFetching={isFetching} />
      <PlanSummary plan={plan} projectEndDate={timelineRange?.end ?? null} />
      {sortedTasks.length === 0 || !timelineRange ? (
        <PlanEmptyState planName={plan.name} />
      ) : (
        <GanttWorkspace
          dependencies={plan.dependencies}
          hoveredTaskId={hoveredTaskId}
          onHoverTask={setHoveredTaskId}
          onScrollSync={syncVerticalScroll}
          onSelectTask={setSelectedTaskId}
          selectedTaskId={selectedTaskId}
          tableScrollerRef={tableScrollerRef}
          tasks={sortedTasks}
          timelineDays={timelineDays}
          timelineScrollerRef={timelineScrollerRef}
          timelineStart={timelineRange.start}
        />
      )}
      <TaskDetailsDrawer
        dependencies={plan.dependencies}
        onClose={() => setSelectedTaskId(null)}
        task={selectedTask}
        tasks={sortedTasks}
      />
    </main>
  );
}
