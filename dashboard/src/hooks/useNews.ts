import useSWR from 'swr';
import { fetchNews } from '@/lib/api/news';
import { NewsQueryParams, NewsListResponse } from '@/lib/types';

export function useNews(params: NewsQueryParams | null) {
  return useSWR<NewsListResponse>(
    params ? ['news', JSON.stringify(params)] : null,
    () => fetchNews(params!),
    { keepPreviousData: true }
  );
}
