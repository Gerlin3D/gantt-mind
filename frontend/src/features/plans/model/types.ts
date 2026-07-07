export type DependencyType = 'finish_to_start';

export type TaskDto = {
  id: string;
  name: string;
  description: string | null;
  assignee: string | null;
  duration_days: number;
  start_date: string;
  end_date: string;
  position: number;
};

export type TaskDependencyDto = {
  predecessor_task_id: string;
  successor_task_id: string;
  dependency_type: DependencyType;
};

export type PlanDto = {
  id: string;
  name: string;
  start_date: string;
  version: number;
  tasks: TaskDto[];
  dependencies: TaskDependencyDto[];
};
