import { describe, expect, it } from 'vitest';
import { demoPlanFixture } from '../../../test/planFixtures';
import type { TaskDto } from '../model/types';
import { getDependencyCurvePath, getDependencyGeometries, getTaskGeometry } from './ganttLayout';

function task(overrides: Partial<TaskDto>): TaskDto {
  return {
    id: 'task',
    name: 'Task',
    description: null,
    assignee: null,
    duration_days: 1,
    start_date: '2026-01-05',
    end_date: '2026-01-05',
    position: 1,
    ...overrides,
  };
}

describe('ganttLayout', () => {
  it('calculates predecessor right-edge and successor left-edge anchors in one timeline coordinate system', () => {
    const [predecessor, successor] = demoPlanFixture.tasks;
    const predecessorGeometry = getTaskGeometry(predecessor, 0, '2026-01-03');
    const successorGeometry = getTaskGeometry(successor, 1, '2026-01-03');

    expect(predecessorGeometry.rightAnchor).toEqual({ x: 163, y: 22 });
    expect(successorGeometry.leftAnchor).toEqual({ x: 173, y: 66 });
  });

  it('builds dependency paths from exact task bar anchors', () => {
    const [line] = getDependencyGeometries(
      [demoPlanFixture.dependencies[0]],
      demoPlanFixture.tasks,
      '2026-01-03',
    );

    expect(line.label).toBe('Project discovery → Requirements baseline');
    expect(line.start).toEqual({ x: 163, y: 22 });
    expect(line.end).toEqual({ x: 173, y: 66 });
    expect(line.visibleEnd).toEqual({ x: 160, y: 66 });
    expect(line.arrowBase).toEqual({ x: 160, y: 66 });
    expect(line.curveEnd).toEqual({ x: 153, y: 66 });
    expect(line.controlStart).toEqual({ x: 185, y: 22 });
    expect(line.controlEnd).toEqual({ x: 131, y: 66 });
    expect(line.d).toBe('M 163 22 C 185 22, 131 66, 153 66 L 160 66');
  });

  it('keeps a minimum horizontal tangent for dependencies between adjacent days', () => {
    const curve = getDependencyCurvePath({ x: 163, y: 22 }, { x: 173, y: 66 });

    expect(curve.arrowBase).toEqual({ x: 160, y: 66 });
    expect(curve.curveEnd).toEqual({ x: 153, y: 66 });
    expect(curve.controlStart.x - 163).toBe(22);
    expect(curve.curveEnd.x - curve.controlEnd.x).toBe(22);
    expect(curve.d.endsWith('L 160 66')).toBe(true);
  });

  it('does not collapse into a nearly vertical line when task anchors have almost the same X', () => {
    const curve = getDependencyCurvePath({ x: 200, y: 22 }, { x: 202, y: 110 });

    expect(curve.arrowBase).toEqual({ x: 189, y: 110 });
    expect(curve.curveEnd).toEqual({ x: 182, y: 110 });
    expect(curve.controlStart).toEqual({ x: 222, y: 22 });
    expect(curve.controlEnd).toEqual({ x: 160, y: 110 });
    expect(curve.d).toBe('M 200 22 C 222 22, 160 110, 182 110 L 189 110');
  });

  it('limits control point spread for long dependencies', () => {
    const curve = getDependencyCurvePath({ x: 80, y: 22 }, { x: 520, y: 154 });

    expect(curve.arrowBase).toEqual({ x: 507, y: 154 });
    expect(curve.curveEnd).toEqual({ x: 500, y: 154 });
    expect(curve.controlStart.x - 80).toBe(64);
    expect(curve.curveEnd.x - curve.controlEnd.x).toBe(64);
  });

  it('creates stable curves for dependencies upward and downward in the task list', () => {
    const tasks = [
      task({ id: 'top', name: 'Top', start_date: '2026-01-08', end_date: '2026-01-08', position: 1 }),
      task({ id: 'middle', name: 'Middle', start_date: '2026-01-05', end_date: '2026-01-05', position: 2 }),
      task({ id: 'bottom', name: 'Bottom', start_date: '2026-01-08', end_date: '2026-01-08', position: 3 }),
    ];
    const [downward, upward] = getDependencyGeometries(
      [
        {
          predecessor_task_id: 'middle',
          successor_task_id: 'bottom',
          dependency_type: 'finish_to_start',
        },
        {
          predecessor_task_id: 'middle',
          successor_task_id: 'top',
          dependency_type: 'finish_to_start',
        },
      ],
      tasks,
      '2026-01-03',
    );

    expect(downward.start.y).toBe(66);
    expect(downward.end.y).toBe(110);
    expect(upward.start.y).toBe(66);
    expect(upward.end.y).toBe(22);
    expect(downward.d).toContain('C');
    expect(upward.d).toContain('C');
  });
});
