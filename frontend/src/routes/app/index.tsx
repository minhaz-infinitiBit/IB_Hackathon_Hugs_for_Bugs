import {
	CreateProjectDialog,
	ProjectsTable,
	type Project,
} from "@/components/app/dashboard";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/app/")({
	component: Dashboard,
});

const placeholderProjects: Project[] = [
	{
		project_id: "proj_001",
		project_name: "Annual Report 2025",
		created_at: "2025-01-15",
	},
	{
		project_id: "proj_002",
		project_name: "Q4 Financial Summary",
		created_at: "2024-12-20",
	},
	{
		project_id: "proj_003",
		project_name: "Legal Contract Review",
		created_at: "2024-11-05",
	},
];

function Dashboard() {
	return (
		<div className="container mx-auto p-6 md:p-12">
			<div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
				<div>
					<h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 font-clash mb-2">
						Your Projects
					</h1>
					<p className="text-gray-400 font-mono text-sm">
						// Select a project to begin document preparation
					</p>
				</div>
				<CreateProjectDialog />
			</div>

			<ProjectsTable data={placeholderProjects} />
		</div>
	);
}
