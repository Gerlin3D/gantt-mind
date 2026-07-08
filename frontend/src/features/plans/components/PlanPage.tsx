import { useQueryClient } from '@tanstack/react-query';
import { useMemo, useRef, useState } from 'react';
import { ApiRequestError, isImportValidationErrorPayload } from '../api/plansApi';
import {
  planQueryKeys,
  useAiCommand,
  useDemoPlan,
  useExportPlan,
  useImportPlan,
  usePlan,
} from '../hooks/usePlans';
import type { ImportValidationErrorPayload, PlanDto } from '../model/types';
import { buildTimelineRange, generateTimelineDays, sortTasksByPosition } from '../utils/dateUtils';
import { type AiMessage, AiCommandPanel } from './AiCommandPanel';
import { GanttWorkspace } from './GanttWorkspace';
import { ImportPlanDialog } from './ImportPlanDialog';
import { PlanEmptyState } from './PlanEmptyState';
import { PlanErrorState } from './PlanErrorState';
import { PlanHeader } from './PlanHeader';
import { PlanSkeleton } from './PlanSkeleton';
import { PlanSummary } from './PlanSummary';
import { TaskDetailsDrawer } from './TaskDetailsDrawer';

export function PlanPage() {
  const queryClient = useQueryClient();
  const [activePlanId, setActivePlanId] = useState<string | null>(null);
  const demoPlanQuery = useDemoPlan();
  const activePlanQuery = usePlan(activePlanId ?? '');
  const importMutation = useImportPlan();
  const exportMutation = useExportPlan();
  const aiCommandMutation = useAiCommand();
  const [aiHistory, setAiHistory] = useState<AiMessage[]>([]);
  const [aiError, setAiError] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [hoveredTaskId, setHoveredTaskId] = useState<string | null>(null);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importValidationError, setImportValidationError] =
    useState<ImportValidationErrorPayload | null>(null);
  const [importGenericError, setImportGenericError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const tableScrollerRef = useRef<HTMLDivElement | null>(null);
  const timelineScrollerRef = useRef<HTMLDivElement | null>(null);
  const syncingScrollRef = useRef(false);

  const currentQuery = activePlanId ? activePlanQuery : demoPlanQuery;
  const currentQueryKey = activePlanId ? planQueryKeys.byId(activePlanId) : planQueryKeys.demo;
  const { data: plan, isPending, isError, error, refetch, isFetching } = currentQuery;
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

  async function handleImport(request: { file: File; planName: string; startDate: string }) {
    setImportValidationError(null);
    setImportGenericError(null);

    try {
      const importedPlan = await importMutation.mutateAsync(request);
      queryClient.setQueryData(planQueryKeys.byId(importedPlan.id), importedPlan);
      setActivePlanId(importedPlan.id);
      setSelectedTaskId(null);
      setIsImportDialogOpen(false);
    } catch (caughtError) {
      if (
        caughtError instanceof ApiRequestError &&
        isImportValidationErrorPayload(caughtError.payload)
      ) {
        setImportValidationError(caughtError.payload);
        return;
      }
      setImportGenericError(caughtError instanceof Error ? caughtError.message : 'Import failed.');
    }
  }

  async function handleExport(planToExport: PlanDto) {
    setExportError(null);

    try {
      const result = await exportMutation.mutateAsync(planToExport.id);
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = result.filename;
      document.body.append(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (caughtError) {
      setExportError(caughtError instanceof Error ? caughtError.message : 'Export failed.');
    }
  }

  async function handleAiSend(planForCommand: PlanDto, message: string) {
    setAiError(null);
    setAiHistory((previous) => [
      ...previous,
      { id: `user-${Date.now()}`, role: 'user', text: message },
    ]);

    try {
      const result = await aiCommandMutation.mutateAsync({ planId: planForCommand.id, message });
      queryClient.setQueryData(currentQueryKey, result.plan);
      setAiHistory((previous) => [
        ...previous,
        { id: `assistant-${Date.now()}`, role: 'assistant', text: result.change_summary },
      ]);
    } catch (caughtError) {
      const errorMessage =
        caughtError instanceof Error ? caughtError.message : 'AI command failed.';
      setAiError(errorMessage);
      setAiHistory((previous) => [
        ...previous,
        { id: `assistant-${Date.now()}`, role: 'assistant', text: errorMessage },
      ]);
    }
  }

  if (isPending) {
    return <PlanSkeleton />;
  }

  if (isError || !plan) {
    return <PlanErrorState error={error} onRetry={() => void refetch()} />;
  }

  return (
    <main className="plan-page">
      <PlanHeader
        planName={plan.name}
        isFetching={isFetching}
        isExporting={exportMutation.isPending}
        onImportClick={() => {
          setImportValidationError(null);
          setImportGenericError(null);
          setIsImportDialogOpen(true);
        }}
        onExportClick={() => void handleExport(plan)}
      />
      {exportError ? (
        <p className="form-error" role="alert">
          {exportError}
        </p>
      ) : null}
      <PlanSummary plan={plan} projectEndDate={timelineRange?.end ?? null} />
      <AiCommandPanel
        history={aiHistory}
        isSending={aiCommandMutation.isPending}
        error={aiError}
        onSend={(message) => void handleAiSend(plan, message)}
      />
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
      <ImportPlanDialog
        genericError={importGenericError}
        isImporting={importMutation.isPending}
        isOpen={isImportDialogOpen}
        onClose={() => setIsImportDialogOpen(false)}
        onImport={handleImport}
        validationError={importValidationError}
      />
    </main>
  );
}
