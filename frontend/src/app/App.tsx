import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1, refetchOnWindowFocus: false },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <main>
        <h1>Vacancy Max</h1>
        <p>M4 builds the real UI here.</p>
      </main>
    </QueryClientProvider>
  );
}
