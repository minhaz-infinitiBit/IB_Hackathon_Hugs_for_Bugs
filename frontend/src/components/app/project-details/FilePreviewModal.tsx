import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { FileText, Image as ImageIcon, Loader2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface FilePreviewModalProps {
	isOpen: boolean;
	onClose: () => void;
	previewUrl: string; // API preview URL e.g. "/files/preview?file_path=..."
	fileName: string;
	contentType: string;
}

export function FilePreviewModal({
	isOpen,
	onClose,
	previewUrl,
	fileName,
	contentType,
}: FilePreviewModalProps) {
	const [blobUrl, setBlobUrl] = useState<string | null>(null);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	// Use ref to track blob URL for cleanup without triggering re-renders
	const blobUrlRef = useRef<string | null>(null);

	const isPdf = contentType === "application/pdf";
	const isImage = contentType.startsWith("image/");

	// Truncate long filenames for display
	const truncateFilename = (name: string, maxLength: number = 40): string => {
		if (name.length <= maxLength) return name;
		const ext =
			name.lastIndexOf(".") > 0 ? name.slice(name.lastIndexOf(".")) : "";
		const baseName = name.slice(0, name.length - ext.length);
		const truncatedBase = baseName.slice(0, maxLength - ext.length - 3);
		return `${truncatedBase}...${ext}`;
	};

	const displayFileName = truncateFilename(fileName);

	useEffect(() => {
		// Only fetch when modal opens with a valid previewUrl
		if (!isOpen || !previewUrl) {
			return;
		}

		// Avoid refetching if we already have a blob URL
		if (blobUrlRef.current) {
			return;
		}

		const fetchFile = async () => {
			setIsLoading(true);
			setError(null);

			try {
				const baseUrl =
					import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
					"http://localhost:8000";
				// previewUrl is like "/files/preview?file_path=..." - just append to baseUrl
				const response = await fetch(`${baseUrl}${previewUrl}`, {
					headers: {
						// Skip ngrok browser warning interstitial
						"ngrok-skip-browser-warning": "true",
					},
				});

				if (!response.ok) {
					throw new Error("Failed to fetch file");
				}

				const blob = await response.blob();
				const url = URL.createObjectURL(blob);
				blobUrlRef.current = url;
				setBlobUrl(url);
			} catch (err) {
				setError(
					err instanceof Error ? err.message : "Failed to load file",
				);
			} finally {
				setIsLoading(false);
			}
		};

		fetchFile();
	}, [isOpen, previewUrl]);

	// Cleanup when modal closes or component unmounts
	useEffect(() => {
		if (!isOpen && blobUrlRef.current) {
			URL.revokeObjectURL(blobUrlRef.current);
			blobUrlRef.current = null;
			setBlobUrl(null);
		}
	}, [isOpen]);

	const handleClose = () => {
		if (blobUrlRef.current) {
			URL.revokeObjectURL(blobUrlRef.current);
			blobUrlRef.current = null;
			setBlobUrl(null);
		}
		onClose();
	};

	return (
		<Dialog
			open={isOpen}
			onOpenChange={(open) => !open && handleClose()}>
			<DialogContent className="max-w-4xl h-[80vh] flex flex-col bg-gray-950 border-gray-800">
				<DialogHeader className="flex flex-row items-center justify-between">
					<div className="flex items-center gap-2">
						{isPdf ? (
							<FileText className="w-5 h-5 text-red-400" />
						) : (
							<ImageIcon className="w-5 h-5 text-blue-400" />
						)}
						<DialogTitle
							className="text-white font-clash truncate max-w-[500px]"
							title={fileName}>
							{displayFileName}
						</DialogTitle>
					</div>
					<Button
						variant="ghost"
						size="sm"
						onClick={handleClose}
						className="text-gray-400 hover:text-white">
						<X className="w-4 h-4" />
					</Button>
				</DialogHeader>

				<div className="flex-1 overflow-hidden rounded-lg bg-gray-900">
					{isLoading && (
						<div className="h-full flex items-center justify-center">
							<Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
						</div>
					)}

					{error && (
						<div className="h-full flex items-center justify-center">
							<p className="text-red-400 font-mono">{error}</p>
						</div>
					)}

					{!isLoading && !error && blobUrl && (
						<>
							{isPdf && (
								<iframe
									src={blobUrl}
									className="w-full h-full border-0"
									title={fileName}
								/>
							)}
							{isImage && (
								<div className="h-full flex items-center justify-center p-4">
									<img
										src={blobUrl}
										alt={fileName}
										className="max-w-full max-h-full object-contain"
									/>
								</div>
							)}
							{!isPdf && !isImage && (
								<div className="h-full flex items-center justify-center">
									<p className="text-gray-400 font-mono">
										Preview not available for this file type
									</p>
								</div>
							)}
						</>
					)}
				</div>
			</DialogContent>
		</Dialog>
	);
}
