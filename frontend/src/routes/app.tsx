import { Navbar } from "@/components/common/Navbar";
import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/app")({
	component: AppLayout,
});

function AppLayout() {
	return (
		<div className="min-h-screen bg-gray-950 text-white font-cabinet">
			{/* Background Grid - Persistent across app routes */}
			<div className="fixed inset-0 pointer-events-none">
				<div className="absolute inset-0 bg-[linear-gradient(rgba(0,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
				<div className="absolute inset-0 bg-gradient-to-b from-transparent via-purple-900/10 to-cyan-900/20" />
			</div>

			<Navbar />

			<main className="relative z-10">
				<Outlet />
			</main>
		</div>
	);
}
