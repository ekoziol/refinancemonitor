import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CalculatorPage } from './components';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <CalculatorPage />
    </QueryClientProvider>
  );
}

export default App;
