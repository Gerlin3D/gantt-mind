import { useQuery } from '@tanstack/react-query';
import { getDemoPlan, getPlanById } from '../api/plansApi';

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
