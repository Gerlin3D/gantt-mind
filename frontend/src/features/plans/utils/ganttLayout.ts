import type { TaskDependencyDto, TaskDto } from '../model/types';
import { calculateTaskOffset } from './dateUtils';

export const ganttLayout = {
  dayWidth: 42,
  rowHeight: 44,
  barInsetX: 5,
  barInsetY: 9,
  barHeight: 26,
  dependencyMarkerPadding: 12,
  dependencyArrowGap: 13,
  dependencyFinalSegmentLength: 7,
  dependencyMinControlOffset: 22,
  dependencyMaxControlOffset: 64,
} as const;

export type GanttTaskGeometry = {
  left: number;
  top: number;
  width: number;
  height: number;
  rightAnchor: {
    x: number;
    y: number;
  };
  leftAnchor: {
    x: number;
    y: number;
  };
};

export type DependencyGeometry = {
  id: string;
  label: string;
  predecessorTaskId: string;
  successorTaskId: string;
  d: string;
  start: {
    x: number;
    y: number;
  };
  end: {
    x: number;
    y: number;
  };
  visibleEnd: {
    x: number;
    y: number;
  };
  arrowBase: {
    x: number;
    y: number;
  };
  curveEnd: {
    x: number;
    y: number;
  };
  controlStart: {
    x: number;
    y: number;
  };
  controlEnd: {
    x: number;
    y: number;
  };
};

export function getTaskGeometry(task: TaskDto, rowIndex: number, timelineStart: string): GanttTaskGeometry {
  const left = calculateTaskOffset(timelineStart, task) * ganttLayout.dayWidth + ganttLayout.barInsetX;
  const top = rowIndex * ganttLayout.rowHeight + ganttLayout.barInsetY;
  const width = task.duration_days * ganttLayout.dayWidth - ganttLayout.barInsetX * 2;
  const centerY = top + ganttLayout.barHeight / 2;

  return {
    left,
    top,
    width,
    height: ganttLayout.barHeight,
    rightAnchor: {
      x: left + width,
      y: centerY,
    },
    leftAnchor: {
      x: left,
      y: centerY,
    },
  };
}

export function getTaskBarStyle(task: TaskDto, rowIndex: number, timelineStart: string) {
  const geometry = getTaskGeometry(task, rowIndex, timelineStart);

  return {
    left: `${geometry.left}px`,
    top: `${ganttLayout.barInsetY}px`,
    width: `${geometry.width}px`,
  };
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

export function getDependencyCurvePath(start: { x: number; y: number }, end: { x: number; y: number }) {
  const arrowBase = {
    x: end.x - ganttLayout.dependencyArrowGap,
    y: end.y,
  };
  const curveEnd = {
    x: arrowBase.x - ganttLayout.dependencyFinalSegmentLength,
    y: arrowBase.y,
  };
  const horizontalDistance = Math.abs(curveEnd.x - start.x);
  const controlOffset = clamp(
    horizontalDistance * 0.55,
    ganttLayout.dependencyMinControlOffset,
    ganttLayout.dependencyMaxControlOffset,
  );
  const controlStart = {
    x: start.x + controlOffset,
    y: start.y,
  };
  const controlEnd = {
    x: curveEnd.x - controlOffset,
    y: curveEnd.y,
  };

  return {
    visibleEnd: arrowBase,
    arrowBase,
    curveEnd,
    controlStart,
    controlEnd,
    d: `M ${start.x} ${start.y} C ${controlStart.x} ${controlStart.y}, ${controlEnd.x} ${controlEnd.y}, ${curveEnd.x} ${curveEnd.y} L ${arrowBase.x} ${arrowBase.y}`,
  };
}

export function getDependencyGeometries(
  dependencies: TaskDependencyDto[],
  tasks: TaskDto[],
  timelineStart: string,
): DependencyGeometry[] {
  const taskRows = new Map(tasks.map((task, index) => [task.id, { task, index }]));

  return dependencies.flatMap((dependency) => {
    const predecessor = taskRows.get(dependency.predecessor_task_id);
    const successor = taskRows.get(dependency.successor_task_id);

    if (!predecessor || !successor) {
      return [];
    }

    const predecessorGeometry = getTaskGeometry(predecessor.task, predecessor.index, timelineStart);
    const successorGeometry = getTaskGeometry(successor.task, successor.index, timelineStart);
    const start = predecessorGeometry.rightAnchor;
    const end = successorGeometry.leftAnchor;
    const curve = getDependencyCurvePath(start, end);

    return [
      {
        id: `${dependency.predecessor_task_id}-${dependency.successor_task_id}`,
        label: `${predecessor.task.name} → ${successor.task.name}`,
        predecessorTaskId: dependency.predecessor_task_id,
        successorTaskId: dependency.successor_task_id,
        d: curve.d,
        start,
        end,
        visibleEnd: curve.visibleEnd,
        arrowBase: curve.arrowBase,
        curveEnd: curve.curveEnd,
        controlStart: curve.controlStart,
        controlEnd: curve.controlEnd,
      },
    ];
  });
}
