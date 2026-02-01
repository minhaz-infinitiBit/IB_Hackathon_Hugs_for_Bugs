import { Button } from "@/components/ui/button";
import { Download, Eye, File, FileText, Image } from "lucide-react";
import type { ClassifiedDocument } from "./types";

interface DocumentTreeItemProps {
	document: ClassifiedDocument;
}

function getFileIcon(contentType: string) {
	if (contentType.startsWith("image/")) return Image;
	if (contentType === "application/pdf") return FileText;
	return File;
}

export function DocumentTreeItem({ document: docItem }: DocumentTreeItemProps) {
	const FileIcon = getFileIcon(docItem.contentType);

	const handleView = () => {
		window.open(docItem.url, "_blank");
	};

	const handleDownload = () => {
		const link = document.createElement("a");
		link.href = docItem.url;
		link.download = docItem.filename;
		link.click();
	};

	return (
		<div className="flex items-center justify-between p-2 rounded-md hover:bg-gray-800/50 transition-colors">
			<div className="flex items-center gap-2">
				<FileIcon className="w-4 h-4 text-gray-400" />
				<span className="text-sm text-gray-300 truncate max-w-[200px]">
					{docItem.filename}
				</span>
			</div>
			<div className="flex items-center gap-1">
				{docItem.isViewable && (
					<Button
						variant="ghost"
						size="sm"
						onClick={handleView}
						className="text-gray-400 hover:text-cyan-400">
						<Eye className="w-4 h-4" />
					</Button>
				)}
				<Button
					variant="ghost"
					size="sm"
					onClick={handleDownload}
					className="text-gray-400 hover:text-purple-400">
					<Download className="w-4 h-4" />
				</Button>
			</div>
		</div>
	);
}
