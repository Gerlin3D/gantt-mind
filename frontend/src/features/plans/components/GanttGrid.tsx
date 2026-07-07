import type { TaskDto } from '../model/types';
import type { TimelineDay } from '../utils/dateUtils';
import { getTaskBarStyle } from '../utils/ganttLayout';

type GanttGridProps = {
  tasks: TaskDto[];
  timelineDays: TimelineDay[];
  timelineStart: string;
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
  onHoverTask: (taskId: string | null) => void;
};

export function GanttGrid({
  tasks,
  timelineDays,
  timelineStart,
  selectedTaskId,
  onSelectTask,
  onHoverTask,
}: GanttGridProps) {
  return (
    <div className="gantt-grid" role="grid" aria-label="Gantt timeline">
      {tasks.map((task, rowIndex) => (
        <div className="gantt-row" key={task.id} role="row">
          {timelineDays.map((day) => (
            <span
              aria-hidden="true"
              className={`gantt-cell ${day.isWeekend ? 'is-weekend' : ''} ${
                day.isMonthStart ? 'is-month-start' : ''
              }`}
              key={day.isoDate}
            />
          ))}
          <button
            className={`gantt-bar ${selectedTaskId === task.id ? 'is-selected' : ''}`}
            data-testid={`gantt-bar-${task.id}`}
            style={getTaskBarStyle(task, rowIndex, timelineStart)}
            type="button"
            onClick={() => onSelectTask(task.id)}
            onMouseEnter={() => onHoverTask(task.id)}
            onMouseLeave={() => onHoverTask(null)}
            onFocus={() => onHoverTask(task.id)}
            onBlur={() => onHoverTask(null)}
            aria-label={`Open details for ${task.name}`}
          >
            <span>{task.name}</span>
          </button>
        </div>
      ))}
    </div>
  );
}
