import {
	useGetMergedPdfFilesProjectsProjectIdMergedPdfGet,
	useGetProjectGroupedByCategoryFilesProjectsProjectIdGroupedByCategoryGet,
} from "@/api/generated/files/files";
import {
	DocumentTree,
	MergedDocumentViewer,
	ProjectDetails,
} from "@/components/app/project-details";
import {
	transformApiResponse,
	type GroupedFilesResponse,
} from "@/components/app/project-details/types";
import { createProcessingSocket, parseMessage } from "@/lib/socket";
import { createFileRoute } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/app/$projectId/details")({
	component: ProjectDetailsPage,
});

interface MergedPdfResponse {
	project_id: number;
	status: string;
	merged_pdf_available: boolean;
	merged_pdf_path: string;
	merged_pdf_filename: string;
	preview_url: string;
	file_size_bytes: number;
	download_url: string;
}

function ProjectDetailsPage() {
	const { projectId } = Route.useParams();
	const numericProjectId = Number(projectId);

	// Reclassification state
	const [isReclassifying, setIsReclassifying] = useState(false);
	const [reclassifyStatus, setReclassifyStatus] = useState<string | null>(
		null,
	);
	const socketRef = useRef<WebSocket | null>(null);

	// Fetch grouped documents from API
	const {
		data: groupedApiResponse,
		isLoading: isGroupedLoading,
		refetch: refetchGrouped,
	} = useGetProjectGroupedByCategoryFilesProjectsProjectIdGroupedByCategoryGet(
		numericProjectId,
	);

	// Fetch merged PDF info
	const {
		data: mergedPdfResponse,
		isLoading: isMergedLoading,
		refetch: refetchMergedPdf,
	} = useGetMergedPdfFilesProjectsProjectIdMergedPdfGet(numericProjectId);

	// Handle reclassification start
	const handleReclassifyStart = useCallback(() => {
		setIsReclassifying(true);
		setReclassifyStatus("Connecting...");

		// Connect to WebSocket for progress updates
		const socket = createProcessingSocket(numericProjectId);
		socketRef.current = socket;

		socket.onopen = () => {
			setReclassifyStatus("Processing your feedback...");
		};

		socket.onmessage = (event) => {
			const message = parseMessage(event);
			if (!message) return;

			setReclassifyStatus(message.message);

			if (message.status === "completed") {
				// Refetch data
				refetchGrouped();
				refetchMergedPdf();
				setIsReclassifying(false);
				setReclassifyStatus(null);
				toast.success("Classifications updated!", {
					description:
						"Documents have been reclassified based on your feedback",
				});
				socket.close();
			} else if (message.status === "error") {
				setIsReclassifying(false);
				setReclassifyStatus(null);
				toast.error("Reclassification failed", {
					description: message.message,
				});
				socket.close();
			}
		};

		socket.onerror = () => {
			console.error("WebSocket error during reclassification");
		};

		socket.onclose = () => {
			socketRef.current = null;
		};
	}, [numericProjectId, refetchGrouped, refetchMergedPdf]);

	// Cleanup socket on unmount
	useEffect(() => {
		return () => {
			if (socketRef.current) {
				socketRef.current.close();
			}
		};
	}, []);

	// Transform API response to component format
	const classifications =
		groupedApiResponse?.status === 200
			? transformApiResponse(
					groupedApiResponse.data as unknown as GroupedFilesResponse,
				)
			: [];

	// Extract merged PDF URL from response
	const mergedPdfData =
		mergedPdfResponse?.status === 200
			? (mergedPdfResponse.data as MergedPdfResponse)
			: null;

	// Use preview_url from API response
	const mergedPdfUrl = mergedPdfData?.merged_pdf_available
		? mergedPdfData.preview_url
		: null;

	return (
		<>
			<ProjectDetails projectId={numericProjectId}>
				<ProjectDetails.Header
					onReclassifyStart={handleReclassifyStart}
				/>
				<ProjectDetails.Content>
					<DocumentTree
						classifications={classifications}
						isLoading={isGroupedLoading}
					/>
					<MergedDocumentViewer
						pdfUrl={mergedPdfUrl}
						isLoading={isMergedLoading}
						projectId={numericProjectId}
					/>
				</ProjectDetails.Content>
			</ProjectDetails>

			{/* Reclassification Processing Overlay */}
			{isReclassifying && (
				<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
					<div className="bg-gray-900 border border-gray-800 rounded-xl p-8 max-w-md mx-4 text-center">
						<Loader2 className="w-12 h-12 text-cyan-400 animate-spin mx-auto mb-4" />
						<h2 className="text-xl font-bold text-white mb-2 font-clash">
							Reclassifying Documents
						</h2>
						<p className="text-gray-400">
							{reclassifyStatus || "Processing..."}
						</p>
						<div className="mt-4 h-1 bg-gray-800 rounded-full overflow-hidden">
							<div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 animate-pulse w-full" />
						</div>
					</div>
				</div>
			)}
		</>
	);
}
