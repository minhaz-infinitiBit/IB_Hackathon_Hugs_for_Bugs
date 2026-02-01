import { Button } from "@/components/ui/button";
import { MessageSquare, Upload } from "lucide-react";
import { createContext, useContext, useState, type ReactNode } from "react";
import { ReviewFeedbackModal } from "./ReviewFeedbackModal";
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
ProjectDetails.Header = function Header({
	onReclassifyStart,
}: {
	onReclassifyStart?: () => void;
}) {
	const { projectId } = useProjectDetailsContext();
	const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
	const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

	const handleReviewSubmitStart = () => {
		onReclassifyStart?.();
	};

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
				<div className="flex items-center gap-3">
					<Button
						onClick={() => setIsReviewModalOpen(true)}
						className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white font-bold">
						<MessageSquare className="w-4 h-4 mr-2" />
						Review Classifications
					</Button>
					<Button
						onClick={() => setIsUploadModalOpen(true)}
						className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold">
						<Upload className="w-4 h-4 mr-2" />
						Upload More Documents
					</Button>
				</div>
			</div>

			<UploadMoreModal
				isOpen={isUploadModalOpen}
				onClose={() => setIsUploadModalOpen(false)}
				projectId={projectId}
			/>

			<ReviewFeedbackModal
				isOpen={isReviewModalOpen}
				onClose={() => setIsReviewModalOpen(false)}
				projectId={projectId}
				onSubmitStart={handleReviewSubmitStart}
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
