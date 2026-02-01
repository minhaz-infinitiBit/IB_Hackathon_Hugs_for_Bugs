import { Button } from "@/components/ui/button";
import { Upload } from "lucide-react";
import { createContext, useContext, useState, type ReactNode } from "react";
import { UploadMoreModal } from "./UploadMoreModal";

interface ProjectDetailsContextValue {
	projectId: number;
}

const ProjectDetailsContext = createContext<ProjectDetailsContextValue | null>(
	null,
);

export function useProjectDetailsContext() {
	const context = useContext(ProjectDetailsContext);
	if (!context) {
		throw new Error(
			"useProjectDetailsContext must be used within ProjectDetails",
		);
	}
	return context;
}

interface ProjectDetailsProps {
	projectId: number;
	children: ReactNode;
}

export function ProjectDetails({ projectId, children }: ProjectDetailsProps) {
	return (
		<ProjectDetailsContext.Provider value={{ projectId }}>
			<div className="container mx-auto p-6 md:p-12">{children}</div>
		</ProjectDetailsContext.Provider>
	);
}

// Sub-components
ProjectDetails.Header = function Header() {
	const { projectId } = useProjectDetailsContext();
	const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

	return (
		<>
			<div className="mb-8 flex items-start justify-between">
				<div>
					<h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 font-clash mb-2">
						📋 Project Details
					</h1>
					<p className="text-gray-400 font-mono text-sm">
						Project ID:{" "}
						<span className="text-cyan-400">{projectId}</span>
					</p>
				</div>
				<Button
					onClick={() => setIsUploadModalOpen(true)}
					className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold">
					<Upload className="w-4 h-4 mr-2" />
					Upload More Documents
				</Button>
			</div>

			<UploadMoreModal
				isOpen={isUploadModalOpen}
				onClose={() => setIsUploadModalOpen(false)}
				projectId={projectId}
			/>
		</>
	);
};

ProjectDetails.Content = function Content({
	children,
}: {
	children: ReactNode;
}) {
	return (
		<div className="grid grid-cols-1 lg:grid-cols-2 gap-8">{children}</div>
	);
};
