import type { PlanDto } from '../features/plans/model/types';

export const demoPlanFixture: PlanDto = {
  id: 'demo-plan',
  name: 'GanttMind Demo Project',
  start_date: '2026-01-05',
  version: 1,
  tasks: [
    {
      id: 'discovery',
      name: 'Project discovery',
      description: 'Clarify goals and constraints.',
      assignee: 'Maya',
      duration_days: 2,
      start_date: '2026-01-05',
      end_date: '2026-01-06',
      position: 1,
    },
    {
      id: 'requirements',
      name: 'Requirements baseline',
      description: 'Prepare the product baseline.',
      assignee: 'Nikolai',
      duration_days: 3,
      start_date: '2026-01-07',
      end_date: '2026-01-09',
      position: 2,
    },
    {
      id: 'prototype',
      name: 'Interactive prototype',
      description: null,
      assignee: 'Anna',
      duration_days: 1,
      start_date: '2026-01-10',
      end_date: '2026-01-10',
      position: 3,
    },
  ],
  dependencies: [
    {
      predecessor_task_id: 'discovery',
      successor_task_id: 'requirements',
      dependency_type: 'finish_to_start',
    },
    {
      predecessor_task_id: 'requirements',
      successor_task_id: 'prototype',
      dependency_type: 'finish_to_start',
    },
  ],
};

export function buildNineTaskPlan(): PlanDto {
  return {
    ...demoPlanFixture,
    tasks: Array.from({ length: 9 }, (_, index) => ({
      id: `task-${index + 1}`,
      name: `Task ${index + 1}`,
      description: `Task ${index + 1} description`,
      assignee: index % 2 === 0 ? 'Maya' : 'Anna',
      duration_days: 1,
      start_date: `2026-01-${(index + 5).toString().padStart(2, '0')}`,
      end_date: `2026-01-${(index + 5).toString().padStart(2, '0')}`,
      position: index + 1,
    })),
    dependencies: Array.from({ length: 9 }, (_, index) => ({
      predecessor_task_id: `task-${(index % 9) + 1}`,
      successor_task_id: `task-${((index + 1) % 9) + 1}`,
      dependency_type: 'finish_to_start',
    })),
  };
}
