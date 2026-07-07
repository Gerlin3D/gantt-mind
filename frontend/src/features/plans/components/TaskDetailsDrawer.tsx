import { useEffect, useRef } from 'react';
import type { TaskDependencyDto, TaskDto } from '../model/types';
import { formatDate } from '../utils/dateUtils';

type TaskDetailsDrawerProps = {
  task: TaskDto | null;
  tasks: TaskDto[];
  dependencies: TaskDependencyDto[];
  onClose: () => void;
};

export function TaskDetailsDrawer({ task, tasks, dependencies, onClose }: TaskDetailsDrawerProps) {
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!task) {
      return;
    }

    closeButtonRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose();
      }
    }

    window.addEventListener('keydown', handleKeyDown);

    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, task]);

  if (!task) {
    return null;
  }

  const taskById = new Map(tasks.map((item) => [item.id, item]));
  const predecessors = dependencies
    .filter((dependency) => dependency.successor_task_id === task.id)
    .map((dependency) => taskById.get(dependency.predecessor_task_id)?.name)
    .filter((name): name is string => Boolean(name));
  const successors = dependencies
    .filter((dependency) => dependency.predecessor_task_id === task.id)
    .map((dependency) => taskById.get(dependency.successor_task_id)?.name)
    .filter((name): name is string => Boolean(name));

  return (
    <div className="drawer-backdrop" role="presentation" onMouseDown={onClose}>
      <aside
        className="task-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="task-drawer-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="drawer-header">
          <div>
            <p className="eyebrow">Task details</p>
            <h2 id="task-drawer-title">{task.name}</h2>
          </div>
          <button ref={closeButtonRef} className="icon-button" type="button" onClick={onClose} aria-label="Close">
            X
          </button>
        </header>
        <dl className="detail-list">
          <DetailItem label="Description" value={task.description || 'No description'} />
          <DetailItem label="Assignee" value={task.assignee ?? 'Unassigned'} />
          <DetailItem label="Duration" value={`${task.duration_days} days`} />
          <DetailItem label="Start" value={formatDate(task.start_date)} />
          <DetailItem label="End" value={formatDate(task.end_date)} />
          <DetailItem label="Predecessors" value={predecessors.join(', ') || 'None'} />
          <DetailItem label="Successors" value={successors.join(', ') || 'None'} />
        </dl>
      </aside>
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
