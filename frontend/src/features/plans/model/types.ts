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

export type ImportPlanRequest = {
  file: File;
  planName: string;
  startDate: string;
};

export type ImportValidationIssue = {
  worksheet: string | null;
  row: number | null;
  column: string | null;
  code: string;
  message: string;
};

export type ImportValidationErrorPayload = {
  code: 'excel_validation_failed';
  message: string;
  errors: ImportValidationIssue[];
};

export type ExportPlanResult = {
  blob: Blob;
  filename: string;
};

export type AiCommandRequest = {
  planId: string;
  message: string;
};

export type AiCommandResponse = {
  plan: PlanDto;
  change_summary: string;
  operations: Record<string, unknown>[];
};
