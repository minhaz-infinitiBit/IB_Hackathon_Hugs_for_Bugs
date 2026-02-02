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
import { createFileRoute } from "@tanstack/react-router";
import { useCallback } from "react";

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

	// Handle background data refresh after reclassification request
	const handleReclassifyStart = useCallback(async () => {
		// Silently refetch data in background - no loader shown
		// User will see updated data on next page load or manual refresh
		try {
			console.log("Starting silent background refresh...");
			await Promise.all([refetchGrouped(), refetchMergedPdf()]);
		} catch {
			// Silently fail - user can manually refresh
			console.error("Failed to refresh data after reclassification");
		}
	}, [refetchGrouped, refetchMergedPdf]);

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
		</>
	);
}
