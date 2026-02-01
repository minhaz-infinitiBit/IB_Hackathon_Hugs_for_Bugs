import { Toaster } from "@/components/ui/sonner";
import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";

export const Route = createRootRoute({
	component: () => (
		<>
			<Outlet />
			<Toaster
				richColors
				position="top-right"
			/>
			<TanStackRouterDevtools />
		</>
	),
	errorComponent: ({ error }) => {
		return (
			<div className="p-4 bg-red-900 text-white overflow-auto max-h-screen">
				<h1 className="text-xl font-bold">Something went wrong!</h1>
				<pre className="mt-2 text-sm">{error.message}</pre>
				<pre className="mt-2 text-xs opacity-70">{error.stack}</pre>
			</div>
		);
	},
});
