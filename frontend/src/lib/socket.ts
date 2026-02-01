export interface ProcessingMessage {
	project_id: number;
	status: "processing" | "completed" | "error";
	message: string;
	progress: number;
}

export function createProcessingSocket(projectId: number): WebSocket {
	const baseUrl = import.meta.env.VITE_API_BASE_URL?.replace(
		/^https?:\/\//,
		"",
	).replace(/\/$/, "");
	const protocol = import.meta.env.VITE_API_BASE_URL?.startsWith("https")
		? "wss"
		: "ws";
	const url = `${protocol}://${baseUrl}/ws/${projectId}`;
	return new WebSocket(url);
}

export function parseMessage(event: MessageEvent): ProcessingMessage | null {
	try {
		return JSON.parse(event.data) as ProcessingMessage;
	} catch {
		console.error("Failed to parse WebSocket message:", event.data);
		return null;
	}
}
