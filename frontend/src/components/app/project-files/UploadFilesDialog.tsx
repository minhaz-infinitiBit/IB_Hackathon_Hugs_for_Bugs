import {
	getListProjectFilesFilesProjectsProjectIdFilesGetQueryKey,
	useUploadPdfFilesUploadPdfProjectIdPost,
} from "@/api/generated/files/files";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from "@/components/ui/dialog";
import { useQueryClient } from "@tanstack/react-query";
import { FileText, Loader2, Upload, X } from "lucide-react";
import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { toast } from "sonner";
import { useProjectFilesContext } from "./ProjectFiles";

export function UploadFilesDialog() {
	const { projectId } = useProjectFilesContext();
	const [open, setOpen] = useState(false);
	const [files, setFiles] = useState<File[]>([]);
	const [isDragging, setIsDragging] = useState(false);
	const fileInputRef = useRef<HTMLInputElement>(null);
	const queryClient = useQueryClient();

	const uploadMutation = useUploadPdfFilesUploadPdfProjectIdPost();

	// Handle drag events
	const handleDragOver = (e: DragEvent) => {
		e.preventDefault();
		setIsDragging(true);
	};

	const handleDragLeave = (e: DragEvent) => {
		e.preventDefault();
		setIsDragging(false);
	};

	const handleDrop = (e: DragEvent) => {
		e.preventDefault();
		setIsDragging(false);
		const droppedFiles = Array.from(e.dataTransfer.files);
		setFiles((prev) => [...prev, ...droppedFiles]);
	};

	// Handle file input change
	const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
		if (e.target.files) {
			const selectedFiles = Array.from(e.target.files);
			setFiles((prev) => [...prev, ...selectedFiles]);
		}
	};

	// Remove a file from the list
	const removeFile = (index: number) => {
		setFiles((prev) => prev.filter((_, i) => i !== index));
	};

	// Handle upload
	const handleUpload = () => {
		if (files.length === 0) return;

		uploadMutation.mutate(
			{
				projectId,
				data: { files },
			},
			{
				onSuccess: () => {
					// Invalidate query to refresh file list
					queryClient.invalidateQueries({
						queryKey:
							getListProjectFilesFilesProjectsProjectIdFilesGetQueryKey(
								projectId,
							),
					});
					toast.success(
						`${files.length} file(s) uploaded successfully!`,
					);
					setFiles([]);
					setOpen(false);
				},
				onError: () => {
					toast.error("Failed to upload files. Please try again.");
				},
			},
		);
	};

	const isLoading = uploadMutation.isPending;

	return (
		<Dialog
			open={open}
			onOpenChange={setOpen}>
			<DialogTrigger asChild>
				<Button className="font-bold bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 text-gray-950 shadow-[0_0_20px_rgba(0,255,255,0.3)] hover:shadow-[0_0_30px_rgba(0,255,255,0.5)] transition-all">
					<Upload className="w-4 h-4 mr-2" />
					Upload Files
				</Button>
			</DialogTrigger>
			<DialogContent className="sm:max-w-[500px] bg-gray-900 border-gray-800 text-white font-cabinet">
				<DialogHeader>
					<DialogTitle className="text-xl font-clash text-cyan-400">
						Upload Documents
					</DialogTitle>
					<DialogDescription className="text-gray-400">
						Drag and drop files or click to select.
					</DialogDescription>
				</DialogHeader>

				{/* Drop Zone */}
				<div
					onDragOver={handleDragOver}
					onDragLeave={handleDragLeave}
					onDrop={handleDrop}
					onClick={() => fileInputRef.current?.click()}
					className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragging ? "border-cyan-400 bg-cyan-400/10" : "border-gray-700 hover:border-gray-600"}
          `}>
					<Upload className="w-10 h-10 mx-auto mb-4 text-gray-500" />
					<p className="text-gray-400 font-mono text-sm">
						Drop files here or click to browse
					</p>
					<input
						ref={fileInputRef}
						type="file"
						multiple
						onChange={handleFileChange}
						className="hidden"
					/>
				</div>

				{/* File List */}
				{files.length > 0 && (
					<div className="max-h-40 overflow-y-auto space-y-2">
						{files.map((file, index) => (
							<div
								key={index}
								className="flex items-center justify-between p-2 bg-gray-800 rounded">
								<div className="flex items-center gap-2">
									<FileText className="w-4 h-4 text-cyan-400" />
									<span className="text-sm text-gray-300 truncate max-w-[300px]">
										{file.name}
									</span>
								</div>
								<Button
									variant="ghost"
									size="sm"
									onClick={() => removeFile(index)}
									className="text-gray-500 hover:text-red-400">
									<X className="w-4 h-4" />
								</Button>
							</div>
						))}
					</div>
				)}

				<DialogFooter>
					<Button
						onClick={handleUpload}
						disabled={files.length === 0 || isLoading}
						className="bg-cyan-500 hover:bg-cyan-400 text-gray-950 font-bold">
						{isLoading ? (
							<>
								<Loader2 className="w-4 h-4 mr-2 animate-spin" />
								Uploading...
							</>
						) : (
							`Upload ${files.length} File(s)`
						)}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
