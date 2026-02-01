import { getDownloadMergedPdfFilesProjectsProjectIdMergedPdfDownloadGetUrl } from "@/api/generated/files/files";
import { Button } from "@/components/ui/button";
import {
	ChevronLeft,
	ChevronRight,
	Download,
	FileText,
	Loader2,
	ZoomIn,
	ZoomOut,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { toast } from "sonner";

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface MergedDocumentViewerProps {
	pdfUrl: string | null; // This is the preview_url from API
	isLoading?: boolean;
	projectId: number;
}

export function MergedDocumentViewer({
	pdfUrl,
	isLoading,
	projectId,
}: MergedDocumentViewerProps) {
	const [numPages, setNumPages] = useState<number | null>(null);
	const [pageNumber, setPageNumber] = useState(1);
	const [scale, setScale] = useState(1.0);
	const [isDownloading, setIsDownloading] = useState(false);
	const [blobUrl, setBlobUrl] = useState<string | null>(null);
	const [isFetchingPdf, setIsFetchingPdf] = useState(false);
	const [fetchError, setFetchError] = useState<string | null>(null);
	const blobUrlRef = useRef<string | null>(null);

	// Fetch PDF as blob to avoid ngrok interstitial
	useEffect(() => {
		if (!pdfUrl) return;

		// Avoid refetching if we already have a blob URL for this pdfUrl
		if (blobUrlRef.current) return;

		const fetchPdf = async () => {
			setIsFetchingPdf(true);
			setFetchError(null);

			try {
				const baseUrl =
					import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
					"http://localhost:8000";
				const fullUrl = `${baseUrl}${pdfUrl}`;

				const response = await fetch(fullUrl, {
					headers: {
						"ngrok-skip-browser-warning": "true",
					},
				});

				if (!response.ok) {
					throw new Error(
						`Failed to fetch merged PDF (status: ${response.status})`,
					);
				}

				const blob = await response.blob();

				const url = URL.createObjectURL(blob);
				blobUrlRef.current = url;
				setBlobUrl(url);
			} catch (err) {
				setFetchError(
					err instanceof Error ? err.message : "Failed to load PDF",
				);
			} finally {
				setIsFetchingPdf(false);
			}
		};

		fetchPdf();

		// Cleanup on unmount
		return () => {
			if (blobUrlRef.current) {
				URL.revokeObjectURL(blobUrlRef.current);
				blobUrlRef.current = null;
			}
		};
	}, [pdfUrl]);

	function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
		setNumPages(numPages);
		setPageNumber(1);
	}

	const handleDownload = async () => {
		setIsDownloading(true);
		try {
			const baseUrl =
				import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
				"http://localhost:8000";
			const downloadPath =
				getDownloadMergedPdfFilesProjectsProjectIdMergedPdfDownloadGetUrl(
					projectId,
				);
			const response = await fetch(`${baseUrl}${downloadPath}`, {
				headers: {
					"ngrok-skip-browser-warning": "true",
					Accept: "application/pdf",
				},
			});

			if (!response.ok) {
				throw new Error("Failed to download merged PDF");
			}

			const blob = await response.blob();
			const url = URL.createObjectURL(blob);
			const link = document.createElement("a");
			link.href = url;
			link.download = `merged-document-project-${projectId}.pdf`;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			URL.revokeObjectURL(url);

			toast.success("Download started!");
		} catch (error) {
			toast.error("Failed to download merged PDF", {
				description: String(error),
			});
		} finally {
			setIsDownloading(false);
		}
	};

	if (isLoading || isFetchingPdf) {
		return (
			<div className="rounded-lg border border-gray-800 bg-gray-950/50 h-[600px] flex items-center justify-center">
				<Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
			</div>
		);
	}

	if (fetchError) {
		return (
			<div className="rounded-lg border border-gray-800 bg-gray-950/50 h-[600px] flex flex-col items-center justify-center gap-4">
				<FileText className="w-16 h-16 text-red-500" />
				<p className="text-red-400 font-mono text-center">
					{fetchError}
				</p>
			</div>
		);
	}

	if (!pdfUrl || !blobUrl) {
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
					file={blobUrl}
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

			{/* Download Button */}
			<div className="p-4 border-t border-gray-800">
				<Button
					onClick={handleDownload}
					disabled={isDownloading}
					className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white font-bold">
					{isDownloading ? (
						<>
							<Loader2 className="w-4 h-4 mr-2 animate-spin" />
							Downloading...
						</>
					) : (
						<>
							<Download className="w-4 h-4 mr-2" />
							Download Merged PDF
						</>
					)}
				</Button>
			</div>
		</div>
	);
}
