import { Button } from "@/components/ui/button";
import {
	ChevronLeft,
	ChevronRight,
	FileText,
	Loader2,
	ZoomIn,
	ZoomOut,
} from "lucide-react";
import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface MergedDocumentViewerProps {
	pdfUrl: string | null;
	isLoading?: boolean;
}

export function MergedDocumentViewer({
	pdfUrl,
	isLoading,
}: MergedDocumentViewerProps) {
	const [numPages, setNumPages] = useState<number | null>(null);
	const [pageNumber, setPageNumber] = useState(1);
	const [scale, setScale] = useState(1.0);

	function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
		setNumPages(numPages);
		setPageNumber(1);
	}

	if (isLoading) {
		return (
			<div className="rounded-lg border border-gray-800 bg-gray-950/50 h-[600px] flex items-center justify-center">
				<Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
			</div>
		);
	}

	if (!pdfUrl) {
		return (
			<div className="rounded-lg border border-gray-800 bg-gray-950/50 h-[600px] flex flex-col items-center justify-center gap-4">
				<FileText className="w-16 h-16 text-gray-600" />
				<p className="text-gray-500 font-mono text-center">
					Merged document not available yet.
				</p>
			</div>
		);
	}

	return (
		<div className="rounded-lg border border-gray-800 bg-gray-950/50 overflow-hidden">
			{/* Header with controls */}
			<div className="p-4 border-b border-gray-800 flex items-center justify-between">
				<h2 className="text-lg font-bold text-white font-clash">
					📄 Merged Document
				</h2>
				<div className="flex items-center gap-2">
					<Button
						variant="ghost"
						size="sm"
						onClick={() => setScale((s) => Math.max(0.5, s - 0.1))}
						className="text-gray-400">
						<ZoomOut className="w-4 h-4" />
					</Button>
					<span className="text-sm text-gray-400 font-mono">
						{Math.round(scale * 100)}%
					</span>
					<Button
						variant="ghost"
						size="sm"
						onClick={() => setScale((s) => Math.min(2, s + 0.1))}
						className="text-gray-400">
						<ZoomIn className="w-4 h-4" />
					</Button>
				</div>
			</div>

			{/* PDF Viewer */}
			<div className="h-[500px] overflow-auto flex justify-center bg-gray-900 p-4">
				<Document
					file={pdfUrl}
					onLoadSuccess={onDocumentLoadSuccess}
					loading={
						<div className="flex items-center justify-center h-full">
							<Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
						</div>
					}>
					<Page
						pageNumber={pageNumber}
						scale={scale}
					/>
				</Document>
			</div>

			{/* Pagination */}
			{numPages && numPages > 1 && (
				<div className="p-4 border-t border-gray-800 flex items-center justify-center gap-4">
					<Button
						variant="ghost"
						size="sm"
						onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
						disabled={pageNumber <= 1}>
						<ChevronLeft className="w-4 h-4" />
					</Button>
					<span className="text-sm text-gray-400 font-mono">
						Page {pageNumber} of {numPages}
					</span>
					<Button
						variant="ghost"
						size="sm"
						onClick={() =>
							setPageNumber((p) => Math.min(numPages, p + 1))
						}
						disabled={pageNumber >= numPages}>
						<ChevronRight className="w-4 h-4" />
					</Button>
				</div>
			)}
		</div>
	);
}
