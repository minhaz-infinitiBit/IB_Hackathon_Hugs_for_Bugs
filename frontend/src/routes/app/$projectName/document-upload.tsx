import { DocumentUpload } from "@/components/app/document-upload";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/app/$projectName/document-upload")({
	component: ProjectDocumentUploadPage,
});

function ProjectDocumentUploadPage() {
	const { projectName } = Route.useParams();

	return (
		<div className="flex items-center justify-center min-h-[calc(100vh-80px)] px-6">
			<DocumentUpload>
				<DocumentUpload.Header>
					<div className="flex flex-col gap-1">
						<span>📤 Upload Documents</span>
						<span className="text-sm font-mono text-gray-500 font-normal">
							Project:{" "}
							<span className="text-cyan-400">{projectName}</span>
						</span>
					</div>
				</DocumentUpload.Header>
				<DocumentUpload.Content className="p-8 text-center">
					<DocumentUpload.Zone />
					<DocumentUpload.Status status="AWAITING_INPUT" />
				</DocumentUpload.Content>
			</DocumentUpload>
		</div>
	);
}
