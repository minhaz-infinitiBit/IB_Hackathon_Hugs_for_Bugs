// API Response from useGetProjectGroupedByCategoryFilesProjectsProjectIdGroupedByCategoryGet
export interface GroupedFilesResponse {
	project_id: number;
	project_name: string;
	total_files: number;
	total_categories: number;
	grouped_files: CategoryGroup[];
}

export interface CategoryGroup {
	category: string;
	files: ClassifiedFile[];
}

export interface ClassifiedFile {
	file_id: number;
	file_name: string;
	file_path: string;
	preview_url: string;
	confidence: string;
	reasoning: string;
}

// Transformed type for DocumentTree component
export interface DocumentClassification {
	id: string;
	name: string; // Category name (e.g., "Rechnungen", "Nicht Verwendbar")
	count: number; // Number of documents in this category
	documents: ClassifiedDocument[];
}

// Individual document for DocumentTreeItem
export interface ClassifiedDocument {
	id: string;
	filename: string;
	contentType: string; // MIME type inferred from extension
	previewUrl: string; // preview_url from API for file viewing
	isViewable: boolean; // true for PDF/images
	confidence: string;
	reasoning: string;
}

// Helper function to infer content type from filename
export function getContentTypeFromFilename(filename: string): string {
	const ext = filename.split(".").pop()?.toLowerCase() || "";
	const mimeTypes: Record<string, string> = {
		pdf: "application/pdf",
		png: "image/png",
		jpg: "image/jpeg",
		jpeg: "image/jpeg",
		gif: "image/gif",
		webp: "image/webp",
		xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
		xls: "application/vnd.ms-excel",
		doc: "application/msword",
		docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
	};
	return mimeTypes[ext] || "application/octet-stream";
}

// Helper function to determine if file is viewable
export function isFileViewable(contentType: string): boolean {
	return (
		contentType.startsWith("image/") || contentType === "application/pdf"
	);
}

// Transform API response to DocumentClassification[]
export function transformApiResponse(
	response: GroupedFilesResponse,
): DocumentClassification[] {
	if (!response?.grouped_files) {
		return [];
	}

	return response.grouped_files.map((group, index) => ({
		id: `category-${index}`,
		name: group.category,
		count: group.files?.length || 0,
		documents: (group.files || []).map((file) => {
			const contentType = getContentTypeFromFilename(file.file_name);
			return {
				id: String(file.file_id),
				filename: file.file_name,
				contentType,
				previewUrl: file.preview_url || "",
				isViewable: isFileViewable(contentType),
				confidence: file.confidence,
				reasoning: file.reasoning,
			};
		}),
	}));
}
