import type { CSSProperties, RefObject } from 'react';
import type { TaskDependencyDto, TaskDto } from '../model/types';
import type { TimelineDay } from '../utils/dateUtils';
import { DependencyLayer } from './DependencyLayer';
import { GanttGrid } from './GanttGrid';
import { TaskTable } from './TaskTable';
import { TimelineHeader } from './TimelineHeader';

type GanttWorkspaceProps = {
  tasks: TaskDto[];
  dependencies: TaskDependencyDto[];
  timelineDays: TimelineDay[];
  timelineStart: string;
  selectedTaskId: string | null;
  hoveredTaskId: string | null;
  tableScrollerRef: RefObject<HTMLDivElement | null>;
  timelineScrollerRef: RefObject<HTMLDivElement | null>;
  onSelectTask: (taskId: string) => void;
  onHoverTask: (taskId: string | null) => void;
  onScrollSync: (source: 'table' | 'timeline', scrollTop: number) => void;
};

export function GanttWorkspace({
  tasks,
  dependencies,
  timelineDays,
  timelineStart,
  selectedTaskId,
  hoveredTaskId,
  tableScrollerRef,
  timelineScrollerRef,
  onSelectTask,
  onHoverTask,
  onScrollSync,
}: GanttWorkspaceProps) {
  const timelineStyle = {
    width: `${timelineDays.length * 42}px`,
    '--timeline-days': timelineDays.length,
  } as CSSProperties;

  return (
    <section className="gantt-workspace" aria-label="Gantt workspace">
      <div
        className="task-table-pane"
        ref={tableScrollerRef}
        onScroll={(event) => onScrollSync('table', event.currentTarget.scrollTop)}
      >
        <TaskTable
          tasks={tasks}
          selectedTaskId={selectedTaskId}
          onSelectTask={onSelectTask}
          onHoverTask={onHoverTask}
        />
      </div>
      <div
        className="timeline-pane"
        ref={timelineScrollerRef}
        onScroll={(event) => onScrollSync('timeline', event.currentTarget.scrollTop)}
      >
        <div
          className="timeline-canvas"
          style={timelineStyle}
          data-testid="timeline-canvas"
        >
          <TimelineHeader days={timelineDays} />
          <GanttGrid
            tasks={tasks}
            timelineDays={timelineDays}
            timelineStart={timelineStart}
            selectedTaskId={selectedTaskId}
            onSelectTask={onSelectTask}
            onHoverTask={onHoverTask}
          />
          <DependencyLayer
            dependencies={dependencies}
            tasks={tasks}
            timelineStart={timelineStart}
            activeTaskId={hoveredTaskId ?? selectedTaskId}
          />
        </div>
      </div>
    </section>
  );
}
