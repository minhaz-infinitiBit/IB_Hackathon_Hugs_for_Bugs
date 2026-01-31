/**
 * API client for communicating with the FastAPI backend
 * Base URL is configured via VITE_API_BASE_URL environment variable
 */

const API_BASE_URL =
	import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

interface RequestOptions extends RequestInit {
	params?: Record<string, string>;
}

/**
 * Base fetch wrapper with common configuration
 */
async function fetchWithConfig<T>(
	endpoint: string,
	options: RequestOptions = {},
): Promise<T> {
	const { params, ...init } = options;

	let url = `${API_BASE_URL}${endpoint}`;

	if (params) {
		const searchParams = new URLSearchParams(params);
		url += `?${searchParams.toString()}`;
	}

	const response = await fetch(url, {
		...init,
		headers: {
			"Content-Type": "application/json",
			...init.headers,
		},
	});

	if (!response.ok) {
		throw new Error(`API Error: ${response.status} ${response.statusText}`);
	}

	return response.json();
}

/**
 * API client methods
 */
export const api = {
	get: <T>(endpoint: string, options?: RequestOptions) =>
		fetchWithConfig<T>(endpoint, { ...options, method: "GET" }),

	post: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
		fetchWithConfig<T>(endpoint, {
			...options,
			method: "POST",
			body: data ? JSON.stringify(data) : undefined,
		}),

	put: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
		fetchWithConfig<T>(endpoint, {
			...options,
			method: "PUT",
			body: data ? JSON.stringify(data) : undefined,
		}),

	patch: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
		fetchWithConfig<T>(endpoint, {
			...options,
			method: "PATCH",
			body: data ? JSON.stringify(data) : undefined,
		}),

	delete: <T>(endpoint: string, options?: RequestOptions) =>
		fetchWithConfig<T>(endpoint, { ...options, method: "DELETE" }),
};

export { API_BASE_URL };
