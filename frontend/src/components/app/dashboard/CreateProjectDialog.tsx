/**
 * CreateProjectDialog Component
 *
 * Modal dialog for creating a new project.
 * - Calls the API to create a project
 * - Invalidates the projects query to refresh the table
 * - Redirects to the new project's document upload page
 * - Shows toast notification on error
 */

import {
	getListProjectsFilesProjectsGetQueryKey,
	useCreateProjectFilesProjectsPost,
} from "@/api/generated/files/files";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { Loader2, Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export function CreateProjectDialog() {
	const [projectName, setProjectName] = useState("");
	const [open, setOpen] = useState(false);
	const navigate = useNavigate();
	const queryClient = useQueryClient();

	// Use the Orval-generated mutation hook for creating projects
	const createProjectMutation = useCreateProjectFilesProjectsPost();

	const handleCreate = () => {
		if (!projectName.trim()) return;

		// Call the API to create the project
		createProjectMutation.mutate(
			{
				data: {
					project_name: projectName.trim(),
				},
			},
			{
				onSuccess: (response) => {
					// Extract project ID from successful response
					// Response structure: { data: ProjectResponse, status: 200 }
					if (response.status === 200) {
						const newProjectId = response.data.id;

						// Invalidate the projects list query to refetch and show new project
						queryClient.invalidateQueries({
							queryKey: getListProjectsFilesProjectsGetQueryKey(),
						});

						// Close the dialog
						setOpen(false);
						setProjectName("");

						// Navigate to the new project's document upload page
						navigate({
							to: "/app/$projectId/document-upload",
							params: { projectId: String(newProjectId) },
						});

						// Show success toast
						toast.success("Project created successfully!");
					}
				},
				onError: (error) => {
					// Show error toast notification
					console.error("Failed to create project:", error);
					toast.error("Failed to create project. Please try again.");
				},
			},
		);
	};

	const isLoading = createProjectMutation.isPending;

	return (
		<Dialog
			open={open}
			onOpenChange={setOpen}>
			<DialogTrigger asChild>
				<Button className="font-bold bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 text-gray-950 shadow-[0_0_20px_rgba(0,255,255,0.3)] hover:shadow-[0_0_30px_rgba(0,255,255,0.5)] transition-all">
					<Plus className="w-5 h-5 mr-2" />
					Create New Project
				</Button>
			</DialogTrigger>
			<DialogContent className="sm:max-w-[425px] bg-gray-900 border-gray-800 text-white font-cabinet">
				<DialogHeader>
					<DialogTitle className="text-xl font-clash text-cyan-400">
						Create New Project
					</DialogTitle>
					<DialogDescription className="text-gray-400">
						Enter a name for your project. This will identify your
						workspace.
					</DialogDescription>
				</DialogHeader>
				<div className="grid gap-4 py-4">
					<div className="grid grid-cols-4 items-center gap-4">
						<Label
							htmlFor="name"
							className="text-right text-gray-300">
							Name
						</Label>
						<Input
							id="name"
							value={projectName}
							onChange={(e) => setProjectName(e.target.value)}
							placeholder="My Awesome Project"
							className="col-span-3 bg-gray-950 border-gray-700 text-white focus:border-cyan-500"
							disabled={isLoading}
							onKeyDown={(e) => {
								if (e.key === "Enter") handleCreate();
							}}
						/>
					</div>
				</div>
				<DialogFooter>
					<Button
						type="submit"
						onClick={handleCreate}
						disabled={isLoading || !projectName.trim()}
						className="bg-cyan-500 hover:bg-cyan-400 text-gray-950 font-bold">
						{isLoading ? (
							<>
								<Loader2 className="w-4 h-4 mr-2 animate-spin" />
								Creating...
							</>
						) : (
							"Create Project"
						)}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
