/**
 * Custom fetch instance for Orval
 *
 * Orval-generated hooks expect the response to include { data, status, headers }
 * This wrapper ensures the response format matches what the generated code expects.
 */

// Remove trailing slash from base URL to prevent double slashes
const baseURL = (
	import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/+$/, "");

export const customInstance = async <T>(
	url: string,
	options?: RequestInit,
): Promise<T> => {
	// Ensure url starts with / for proper joining
	const normalizedUrl = url.startsWith("/") ? url : `/${url}`;

	const response = await fetch(`${baseURL}${normalizedUrl}`, {
		...options,
		headers: {
			// Bypass ngrok browser warning interstitial
			"ngrok-skip-browser-warning": "true",
			...(options?.headers || {}),
		},
	});

	const responseData = await response.json().catch(() => ({}));

	// Orval expects { data, status, headers } structure
	// We construct this from the fetch response
	const result = {
		data: responseData,
		status: response.status,
		headers: response.headers,
	};

	if (!response.ok) {
		// For error responses, throw the structured result
		throw result;
	}

	// Return the structured response that matches Orval's expected type
	return result as T;
};
