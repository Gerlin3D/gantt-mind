import type { TaskDependencyDto, TaskDto } from '../model/types';
import { ganttLayout, getDependencyGeometries } from '../utils/ganttLayout';

type DependencyLayerProps = {
  dependencies: TaskDependencyDto[];
  tasks: TaskDto[];
  timelineStart: string;
  activeTaskId: string | null;
};

export function DependencyLayer({ dependencies, tasks, timelineStart, activeTaskId }: DependencyLayerProps) {
  const lines = getDependencyGeometries(dependencies, tasks, timelineStart);

  return (
    <svg
      className="dependency-layer"
      data-testid="dependency-layer"
      height={tasks.length * ganttLayout.rowHeight + ganttLayout.dependencyMarkerPadding * 2}
      width="100%"
      aria-label="Task dependencies"
      role="img"
    >
      <defs>
        <marker
          id="dependency-arrow"
          markerHeight="9"
          markerUnits="strokeWidth"
          markerWidth="9"
          orient="auto"
          refX="0"
          refY="4.5"
        >
          <path d="M0,0 L9,4.5 L0,9 Z" />
        </marker>
      </defs>
      {lines.map((line) => (
        <path
          aria-label={line.label}
          className={[
            'dependency-line',
            activeTaskId ? 'is-muted' : '',
            activeTaskId === line.predecessorTaskId || activeTaskId === line.successorTaskId
              ? 'is-highlighted'
              : '',
          ]
            .filter(Boolean)
            .join(' ')}
          d={line.d}
          key={line.id}
          markerEnd="url(#dependency-arrow)"
          role="img"
        >
          <title>{line.label}</title>
        </path>
      ))}
    </svg>
  );
}
