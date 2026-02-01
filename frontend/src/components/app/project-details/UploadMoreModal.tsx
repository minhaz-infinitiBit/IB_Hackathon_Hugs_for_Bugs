import { useUploadPdfFilesUploadPdfProjectIdPost } from "@/api/generated/files/files";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { useNavigate } from "@tanstack/react-router";
import { FileText, Loader2, Upload, X } from "lucide-react";
import { useCallback, useState } from "react";
import { toast } from "sonner";

interface UploadMoreModalProps {
	isOpen: boolean;
	onClose: () => void;
	projectId: number;
}

export function UploadMoreModal({
	isOpen,
	onClose,
	projectId,
}: UploadMoreModalProps) {
	const [files, setFiles] = useState<File[]>([]);
	const [isDragOver, setIsDragOver] = useState(false);
	const navigate = useNavigate();

	const uploadMutation = useUploadPdfFilesUploadPdfProjectIdPost();

	const handleDragOver = useCallback((e: React.DragEvent) => {
		e.preventDefault();
		setIsDragOver(true);
	}, []);

	const handleDragLeave = useCallback((e: React.DragEvent) => {
		e.preventDefault();
		setIsDragOver(false);
	}, []);

	const handleDrop = useCallback((e: React.DragEvent) => {
		e.preventDefault();
		setIsDragOver(false);
		const droppedFiles = Array.from(e.dataTransfer.files).filter(
			(file) =>
				file.type === "application/pdf" ||
				file.type.startsWith("image/"),
		);
		setFiles((prev) => [...prev, ...droppedFiles]);
	}, []);

	const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
		if (e.target.files) {
			const selectedFiles = Array.from(e.target.files);
			setFiles((prev) => [...prev, ...selectedFiles]);
		}
	};

	const removeFile = (index: number) => {
		setFiles((prev) => prev.filter((_, i) => i !== index));
	};

	const handleUpload = async () => {
		if (files.length === 0) {
			toast.error("Please select files to upload");
			return;
		}

		try {
			const response = await uploadMutation.mutateAsync({
				projectId,
				data: { files },
			});

			// Extract new file IDs from response
			const newFileIds =
				response.status === 200
					? response.data.map((f) => f.location)
					: [];

			toast.success(`${files.length} file(s) uploaded successfully!`);

			// Close modal and navigate with new file info
			onClose();
			setFiles([]);

			navigate({
				to: "/app/$projectId/document-upload",
				params: { projectId: String(projectId) },
				search: { newFileIds: newFileIds.join(",") },
			});
		} catch (error) {
			toast.error("Failed to upload files", {
				description: String(error),
			});
		}
	};

	const handleClose = () => {
		setFiles([]);
		onClose();
	};

	return (
		<Dialog
			open={isOpen}
			onOpenChange={(open) => !open && handleClose()}>
			<DialogContent className="max-w-lg bg-gray-950 border-gray-800">
				<DialogHeader>
					<DialogTitle className="text-white font-clash flex items-center gap-2">
						<Upload className="w-5 h-5 text-purple-400" />
						Upload More Documents
					</DialogTitle>
				</DialogHeader>

				{/* Dropzone */}
				<div
					onDragOver={handleDragOver}
					onDragLeave={handleDragLeave}
					onDrop={handleDrop}
					className={`
						border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
						${isDragOver ? "border-purple-400 bg-purple-400/10" : "border-gray-700 hover:border-gray-600"}
					`}>
					<input
						type="file"
						multiple
						accept=".pdf,image/*"
						onChange={handleFileSelect}
						className="hidden"
						id="file-upload"
					/>
					<label
						htmlFor="file-upload"
						className="cursor-pointer">
						<Upload className="w-10 h-10 text-gray-500 mx-auto mb-4" />
						<p className="text-gray-400 font-cabinet">
							Drag & drop files here, or{" "}
							<span className="text-purple-400">browse</span>
						</p>
						<p className="text-gray-600 text-sm mt-2">
							Supports PDF and image files
						</p>
					</label>
				</div>

				{/* File List */}
				{files.length > 0 && (
					<div className="max-h-40 overflow-y-auto space-y-2">
						{files.map((file, index) => (
							<div
								key={index}
								className="flex items-center justify-between p-2 bg-gray-900 rounded-md">
								<div className="flex items-center gap-2 truncate">
									<FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
									<span className="text-sm text-gray-300 truncate">
										{file.name}
									</span>
								</div>
								<Button
									variant="ghost"
									size="sm"
									onClick={() => removeFile(index)}
									className="text-gray-400 hover:text-red-400 flex-shrink-0">
									<X className="w-4 h-4" />
								</Button>
							</div>
						))}
					</div>
				)}

				<DialogFooter>
					<Button
						variant="ghost"
						onClick={handleClose}
						className="text-gray-400">
						Cancel
					</Button>
					<Button
						onClick={handleUpload}
						disabled={
							files.length === 0 || uploadMutation.isPending
						}
						className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white">
						{uploadMutation.isPending ? (
							<>
								<Loader2 className="w-4 h-4 mr-2 animate-spin" />
								Uploading...
							</>
						) : (
							<>
								<Upload className="w-4 h-4 mr-2" />
								Upload ({files.length})
							</>
						)}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
