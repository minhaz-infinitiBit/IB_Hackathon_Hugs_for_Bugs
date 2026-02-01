import { DocumentUpload } from "@/components/app/document-upload";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/app/document-upload")({
	component: DocumentUploadPage,
});

function DocumentUploadPage() {
	return (
		<div className="flex items-center justify-center min-h-[calc(100vh-80px)] px-6">
			<DocumentUpload>
				<DocumentUpload.Header>
					📤 Upload Documents
				</DocumentUpload.Header>
				<DocumentUpload.Content className="p-8 text-center">
					<DocumentUpload.Zone />
					<DocumentUpload.Status status="AWAITING_INPUT" />
				</DocumentUpload.Content>
			</DocumentUpload>
		</div>
	);
}
