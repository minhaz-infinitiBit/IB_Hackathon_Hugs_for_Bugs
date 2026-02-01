// Classification with nested documents
export interface DocumentClassification {
	id: string;
	name: string; // e.g., "Invoices", "Contracts"
	count: number; // Number of documents
	documents: ClassifiedDocument[];
}

// Individual document
export interface ClassifiedDocument {
	id: string;
	filename: string;
	contentType: string; // MIME type
	url: string; // Download URL
	isViewable: boolean; // true for PDF/images
}

// API response shape (placeholder)
export interface ProjectDocumentsResponse {
	classifications: DocumentClassification[];
}

// Merged document response
export interface MergedDocumentResponse {
	url: string | null; // PDF URL or null if not ready
}
