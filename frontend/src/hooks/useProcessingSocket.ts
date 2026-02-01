import { useProcessProjectFilesProcessProjectProjectIdPost } from "@/api/generated/files/files";
import { createProcessingSocket, parseMessage } from "@/lib/socket";
import { useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

interface UseProcessingSocketOptions {
	projectId: number;
	maxRetries?: number;
}

interface UseProcessingSocketReturn {
	isProcessing: boolean;
	progress: number;
	startProcessing: () => void;
}

export function useProcessingSocket({
	projectId,
	maxRetries = 3,
}: UseProcessingSocketOptions): UseProcessingSocketReturn {
	const [isProcessing, setIsProcessing] = useState(false);
	const [progress, setProgress] = useState(0);
	const socketRef = useRef<WebSocket | null>(null);
	const retryCountRef = useRef(0);
	const navigate = useNavigate();

	const processProject = useProcessProjectFilesProcessProjectProjectIdPost();

	const cleanup = useCallback(() => {
		if (socketRef.current) {
			socketRef.current.close();
			socketRef.current = null;
		}
		setIsProcessing(false);
		setProgress(0);
		retryCountRef.current = 0;
	}, []);

	const handleMessage = useCallback(
		(event: MessageEvent) => {
			const message = parseMessage(event);
			if (!message) return;

			setProgress(message.progress);

			switch (message.status) {
				case "processing":
					// Show processing toast with progress
					toast.loading(message.message, {
						id: `process-${projectId}`,
						description: `Progress: ${message.progress}%`,
					});
					break;

				case "completed":
					toast.success("Processing Complete!", {
						id: `process-${projectId}`,
						description: message.message,
						duration: 5000,
					});
					cleanup();
					// Redirect to details page
					navigate({
						to: "/app/$projectId/details",
						params: { projectId: String(projectId) },
					});
					break;

				case "error":
					toast.error("Processing Failed", {
						id: `process-${projectId}`,
						description: message.message,
						duration: 8000,
					});
					cleanup();
					break;
			}
		},
		[projectId, navigate, cleanup],
	);

	const connectSocketRef = useRef<() => void>(null);

	const connectSocket = useCallback(() => {
		const socket = createProcessingSocket(projectId);
		socketRef.current = socket;

		socket.onopen = () => {
			retryCountRef.current = 0;
			toast.info("Connected to processing server", {
				id: `connect-${projectId}`,
				duration: 2000,
			});

			// Trigger the processing API after socket is connected
			processProject.mutate(
				{ projectId },
				{
					onSuccess: () => {
						toast.loading("Processing started...", {
							id: `process-${projectId}`,
							description: "Waiting for updates...",
						});
					},
					onError: (error) => {
						toast.error("Failed to start processing", {
							description: String(error),
						});
						cleanup();
					},
				},
			);
		};

		socket.onmessage = handleMessage;

		socket.onerror = () => {
			console.error("WebSocket error");
		};

		socket.onclose = () => {
			// Only retry if we haven't received completion and haven't exceeded retries
			if (isProcessing && retryCountRef.current < maxRetries) {
				retryCountRef.current += 1;
				toast.warning(
					`Connection lost. Retrying... (${retryCountRef.current}/${maxRetries})`,
					{
						id: `retry-${projectId}`,
						duration: 3000,
					},
				);
				setTimeout(() => {
					if (connectSocketRef.current) {
						connectSocketRef.current();
					}
				}, 2000);
			} else if (retryCountRef.current >= maxRetries) {
				toast.error("Connection failed after multiple attempts", {
					description: "Please try again later",
					duration: 8000,
				});
				cleanup();
			}
		};
	}, [
		projectId,
		handleMessage,
		isProcessing,
		maxRetries,
		processProject,
		cleanup,
	]);

	// Assign the function to the ref so it can be called recursively
	useEffect(() => {
		connectSocketRef.current = connectSocket;
	}, [connectSocket]);

	const startProcessing = useCallback(() => {
		if (isProcessing) return;
		setIsProcessing(true);
		setProgress(0);
		retryCountRef.current = 0;
		if (connectSocketRef.current) {
			connectSocketRef.current();
		}
	}, [isProcessing]);

	return {
		isProcessing,
		progress,
		startProcessing,
	};
}
