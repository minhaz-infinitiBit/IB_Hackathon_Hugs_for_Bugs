import { Button } from "@/components/ui/button";
import { useProcessingSocket } from "@/hooks/useProcessingSocket";
import { Loader2, Play } from "lucide-react";
import { useProjectFilesContext } from "./ProjectFiles";

export function ProcessButton() {
	const { projectId } = useProjectFilesContext();
	const { isProcessing, progress, startProcessing } = useProcessingSocket({
		projectId,
		maxRetries: 3,
	});

	return (
		<Button
			onClick={startProcessing}
			disabled={isProcessing}
			className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold">
			{isProcessing ? (
				<>
					<Loader2 className="w-4 h-4 mr-2 animate-spin" />
					Processing... {progress}%
				</>
			) : (
				<>
					<Play className="w-4 h-4 mr-2" />
					Process Documents
				</>
			)}
		</Button>
	);
}
