/**
 * Project Document Upload Route
 *
 * Dynamic route for uploading documents to a specific project.
 * Path: /app/$projectId/document-upload
 *
 * The projectId is obtained from the URL params and will be used
 * for API calls to upload files to this specific project.
 */

import { useListProjectFilesFilesProjectsProjectIdFilesGet } from "@/api/generated/files/files";
import {
	FilesTable,
	ProcessButton,
	ProjectFiles,
	UploadFilesDialog,
} from "@/components/app/project-files";
import { createFileRoute } from "@tanstack/react-router";

export interface DocumentUploadSearch {
	newFileIds?: string;
}

export const Route = createFileRoute("/app/$projectId/document-upload")({
	component: ProjectDocumentUploadPage,
	validateSearch: (
		search: Record<string, unknown>,
	): DocumentUploadSearch => ({
		newFileIds:
			typeof search.newFileIds === "string"
				? search.newFileIds
				: undefined,
	}),
});

function ProjectDocumentUploadPage() {
	const { projectId } = Route.useParams();
	const { newFileIds: newFileIdsParam } = Route.useSearch();
	const numericProjectId = Number(projectId);

	// Parse newFileIds from comma-separated string
	const newFileIds = newFileIdsParam ? newFileIdsParam.split(",") : [];

	// Fetch files for this project
	const { data, isLoading, error } =
		useListProjectFilesFilesProjectsProjectIdFilesGet(numericProjectId);

	// Extract files from response
	const files = data?.status === 200 ? data.data : [];

	return (
		<ProjectFiles projectId={numericProjectId}>
			{/* Header with title and upload button */}
			<div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
				<ProjectFiles.Header />
				<UploadFilesDialog />
			</div>

			{/* Loading state */}
			{isLoading && (
				<div className="text-center py-12 text-gray-400 font-mono">
					Loading files...
				</div>
			)}

			{/* Error state */}
			{error && (
				<div className="text-center py-12 text-red-400 font-mono">
					Error loading files.
				</div>
			)}

			{/* Files table with NEW badge support */}
			{!isLoading && !error && (
				<FilesTable
					data={files}
					newFileIds={newFileIds}
				/>
			)}

			{/* Actions */}
			<ProjectFiles.Actions>
				<ProcessButton />
			</ProjectFiles.Actions>
		</ProjectFiles>
	);
}
