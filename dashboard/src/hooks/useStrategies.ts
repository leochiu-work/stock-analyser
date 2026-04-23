import useSWR from 'swr';
import { fetchStrategies } from '@/lib/api/strategies';
import { StrategyItem } from '@/lib/types';

export function useStrategies(params: { ticker?: string; status?: string } = {}) {
  const result = useSWR<StrategyItem[]>(
    ['strategies', JSON.stringify(params)],
    () => fetchStrategies(params),
    {
      refreshInterval: (data) => {
        const hasActive = data?.some(
          (s) => s.status === 'pending' || s.status === 'running'
        );
        return hasActive ? 4000 : 0;
      },
    }
  );
  return result;
}
