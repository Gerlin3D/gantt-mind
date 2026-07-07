import type { TaskDto } from '../model/types';
import { formatDate } from '../utils/dateUtils';

type TaskTableProps = {
  tasks: TaskDto[];
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
  onHoverTask: (taskId: string | null) => void;
};

export function TaskTable({ tasks, selectedTaskId, onSelectTask, onHoverTask }: TaskTableProps) {
  return (
    <div className="task-table" role="table" aria-label="Tasks">
      <div className="task-row task-row-header" role="row">
        <span role="columnheader">#</span>
        <span role="columnheader">Task</span>
        <span role="columnheader">Owner</span>
        <span role="columnheader">Days</span>
        <span role="columnheader">Start</span>
        <span role="columnheader">End</span>
      </div>
      {tasks.map((task) => (
        <button
          className={`task-row task-row-button ${selectedTaskId === task.id ? 'is-selected' : ''}`}
          key={task.id}
          type="button"
          role="row"
          onClick={() => onSelectTask(task.id)}
          onMouseEnter={() => onHoverTask(task.id)}
          onMouseLeave={() => onHoverTask(null)}
          onFocus={() => onHoverTask(task.id)}
          onBlur={() => onHoverTask(null)}
          aria-label={`Open details for ${task.name}`}
        >
          <span role="cell">{task.position}</span>
          <span className="task-name" role="cell" title={task.name}>
            {task.name}
          </span>
          <span role="cell">{task.assignee ?? 'Unassigned'}</span>
          <span role="cell">{task.duration_days}</span>
          <span role="cell">{formatDate(task.start_date)}</span>
          <span role="cell">{formatDate(task.end_date)}</span>
        </button>
      ))}
    </div>
  );
}
