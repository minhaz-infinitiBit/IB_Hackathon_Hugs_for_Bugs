/**
 * App.tsx
 *
 * Main application component that sets up providers.
 * - QueryClientProvider: Required for TanStack Query (React Query) hooks
 * - RouterProvider: Required for TanStack Router
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";
import { router } from "./router";

// Create a QueryClient instance for React Query
// This manages caching, background refetching, and stale data
const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			// Refetch on window focus for fresh data
			refetchOnWindowFocus: false,
			// Retry failed requests once
			retry: 1,
		},
	},
});

function App() {
	return (
		// QueryClientProvider must wrap any component using React Query hooks
		<QueryClientProvider client={queryClient}>
			<RouterProvider router={router} />
		</QueryClientProvider>
	);
}

export default App;
