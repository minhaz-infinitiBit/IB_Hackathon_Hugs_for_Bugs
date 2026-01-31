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
import { useNavigate } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { useState } from "react";

export function CreateProjectDialog() {
	const [projectName, setProjectName] = useState("");
	const [open, setOpen] = useState(false);
	const navigate = useNavigate();

	const handleCreate = () => {
		if (!projectName.trim()) return;

		// In a real app, we would make an API call here.
		// For now, we just navigate to the dynamic route.
		const slug = projectName.trim(); // We pass the raw name, route will handle param

		// Navigate to /app/$projectName/document-upload
		navigate({
			to: "/app/$projectName/document-upload",
			params: { projectName: slug },
		});
		setOpen(false);
	};

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
						/>
					</div>
				</div>
				<DialogFooter>
					<Button
						type="submit"
						onClick={handleCreate}
						className="bg-cyan-500 hover:bg-cyan-400 text-gray-950 font-bold">
						Create Project
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
