import { useReclassifyFilesFilesProjectsProjectIdReclassifyPost } from "@/api/generated/files/files";
import { Button } from "@/components/ui/button";
import { Loader2, MessageSquare, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface ReviewFeedbackModalProps {
	isOpen: boolean;
	onClose: () => void;
	projectId: number;
	onSubmitStart: () => void;
}

export function ReviewFeedbackModal({
	isOpen,
	onClose,
	projectId,
	onSubmitStart,
}: ReviewFeedbackModalProps) {
	const [feedback, setFeedback] = useState("");
	const reclassifyMutation =
		useReclassifyFilesFilesProjectsProjectIdReclassifyPost();

	const handleSubmit = async () => {
		if (!feedback.trim()) {
			toast.error("Please enter feedback");
			return;
		}

		try {
			await reclassifyMutation.mutateAsync({
				projectId,
				data: {
					prompt: feedback.trim(),
					regenerate_pdf: true,
				},
			});

			// Notify parent that processing started
			onSubmitStart();
			setFeedback("");
			onClose();
			toast.info("Reclassification started...", {
				description: "Processing your feedback",
			});
		} catch (error) {
			toast.error("Failed to submit feedback", {
				description: String(error),
			});
		}
	};

	if (!isOpen) return null;

	return (
		<div className="fixed inset-0 z-50 flex items-center justify-center">
			{/* Backdrop */}
			<div
				className="absolute inset-0 bg-black/80 backdrop-blur-sm"
				onClick={onClose}
			/>

			{/* Modal */}
			<div className="relative bg-gray-900 border border-gray-800 rounded-xl shadow-2xl w-full max-w-lg mx-4">
				{/* Header */}
				<div className="flex items-center justify-between p-6 border-b border-gray-800">
					<div className="flex items-center gap-3">
						<MessageSquare className="w-5 h-5 text-cyan-400" />
						<h2 className="text-xl font-bold text-white font-clash">
							Review Classifications
						</h2>
					</div>
					<Button
						variant="ghost"
						size="sm"
						onClick={onClose}
						className="text-gray-400 hover:text-white">
						<X className="w-5 h-5" />
					</Button>
				</div>

				{/* Content */}
				<div className="p-6">
					<p className="text-gray-400 text-sm mb-4">
						Provide feedback to reclassify documents. Use natural
						language to describe what should change.
					</p>

					<textarea
						value={feedback}
						onChange={(e) => setFeedback(e.target.value)}
						placeholder="e.g., Move the bank statement to Bankbescheinigungen category..."
						className="w-full h-32 px-4 py-3 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none"
					/>

					<div className="mt-2 text-xs text-gray-500">
						Examples:
						<ul className="mt-1 ml-4 list-disc space-y-1">
							<li>
								Move all bank documents to Bankbescheinigungen
							</li>
							<li>
								The contract.pdf should be in Arbeitsverträge
							</li>
							<li>Mark document123.pdf as Nicht Verwendbar</li>
						</ul>
					</div>
				</div>

				{/* Footer */}
				<div className="flex items-center justify-end gap-3 p-6 border-t border-gray-800">
					<Button
						variant="ghost"
						onClick={onClose}
						disabled={reclassifyMutation.isPending}
						className="text-gray-400 hover:text-white">
						Cancel
					</Button>
					<Button
						onClick={handleSubmit}
						disabled={
							!feedback.trim() || reclassifyMutation.isPending
						}
						className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white font-bold">
						{reclassifyMutation.isPending ? (
							<>
								<Loader2 className="w-4 h-4 mr-2 animate-spin" />
								Submitting...
							</>
						) : (
							<>
								<MessageSquare className="w-4 h-4 mr-2" />
								Submit Feedback
							</>
						)}
					</Button>
				</div>
			</div>
		</div>
	);
}
