import { DocumentPrepApp } from "@/components/features/DocumentPrepApp";
import { LandingPage } from "@/components/features/LandingPage";
import {
	createRootRoute,
	createRoute,
	createRouter,
} from "@tanstack/react-router";

// Create the root route
const rootRoute = createRootRoute();

// Create child routes
const indexRoute = createRoute({
	getParentRoute: () => rootRoute,
	path: "/",
	component: LandingPage,
});

const appRoute = createRoute({
	getParentRoute: () => rootRoute,
	path: "/app",
	component: DocumentPrepApp,
});

// Create the route tree
const routeTree = rootRoute.addChildren([indexRoute, appRoute]);

// Create the router
export const router = createRouter({ routeTree });

// Register router types
declare module "@tanstack/react-router" {
	interface Register {
		router: typeof router;
	}
}
