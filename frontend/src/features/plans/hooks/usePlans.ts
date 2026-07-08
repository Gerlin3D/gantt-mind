import { useMutation, useQuery } from '@tanstack/react-query';
import { exportPlan, getDemoPlan, getPlanById, importPlan, sendAiCommand } from '../api/plansApi';

export const planQueryKeys = {
  demo: ['plans', 'demo'] as const,
  byId: (planId: string) => ['plans', planId] as const,
};

export function useDemoPlan() {
  return useQuery({
    queryKey: planQueryKeys.demo,
    queryFn: getDemoPlan,
  });
}

export function usePlan(planId: string) {
  return useQuery({
    queryKey: planQueryKeys.byId(planId),
    queryFn: () => getPlanById(planId),
    enabled: planId.length > 0,
  });
}

export function useImportPlan() {
  return useMutation({
    mutationFn: importPlan,
  });
}

export function useExportPlan() {
  return useMutation({
    mutationFn: exportPlan,
  });
}

export function useAiCommand() {
  return useMutation({
    mutationFn: ({ planId, message }: { planId: string; message: string }) =>
      sendAiCommand(planId, message),
  });
}
