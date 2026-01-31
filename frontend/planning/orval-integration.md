# Orval Integration Plan

## Goal

Integrate **Orval** to auto-generate type-safe API clients and **TanStack Query** hooks from the FastAPI backend's OpenAPI (Swagger) specification.

---

## Prerequisites

- FastAPI backend running and exposing `/openapi.json` (or `/docs`)
- `.env` file configured with `VITE_API_BASE_URL`

---

## Step 1: Install Dependencies

```bash
pnpm add -D orval
pnpm add axios
```

> **Note**: Orval uses Axios by default for HTTP requests. TanStack Query is already installed.

---

## Step 2: Create Orval Configuration

Create `orval.config.ts` in the project root (`frontend/`):

```typescript
import { defineConfig } from "orval";

export default defineConfig({
	api: {
		input: {
			// FastAPI OpenAPI JSON endpoint
			target: "http://localhost:8000/openapi.json", // Or use your ngrok URL
		},
		output: {
			mode: "tags-split", // Splits generated code by API tags
			target: "src/api/generated", // Output directory for hooks
			schemas: "src/api/model", // Output directory for TypeScript types
			client: "react-query", // Generate TanStack Query hooks
			baseUrl: "import.meta.env.VITE_API_BASE_URL", // Dynamic base URL from .env
			override: {
				mutator: {
					path: "./src/api/axios-instance.ts", // Custom Axios instance (optional)
					name: "customInstance",
				},
			},
		},
	},
});
```

---

## Step 3: Create Custom Axios Instance (Optional but Recommended)

Create `src/api/axios-instance.ts`:

```typescript
import axios, { type AxiosRequestConfig } from "axios";

const axiosInstance = axios.create({
	baseURL: import.meta.env.VITE_API_BASE_URL,
	headers: {
		"Content-Type": "application/json",
	},
});

export const customInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
	const source = axios.CancelToken.source();
	const promise = axiosInstance({
		...config,
		cancelToken: source.token,
	}).then(({ data }) => data);
	// @ts-expect-error - Adding cancel method
	promise.cancel = () => {
		source.cancel("Query was cancelled");
	};
	return promise;
};
```

---

## Step 4: Add NPM Script

Add to `package.json`:

```json
{
	"scripts": {
		"generate-api": "orval"
	}
}
```

---

## Step 5: Generate API Hooks

Run:

```bash
pnpm generate-api
```

This will:

1. Fetch OpenAPI spec from FastAPI
2. Generate TypeScript types in `src/api/model/`
3. Generate TanStack Query hooks in `src/api/generated/`

---

## Step 6: Usage Example

```tsx
import { useGetProjects } from "@/api/generated/projects";

function ProjectsList() {
	const { data, isLoading, error } = useGetProjects();

	if (isLoading) return <p>Loading...</p>;
	if (error) return <p>Error: {error.message}</p>;

	return (
		<ul>
			{data?.map((project) => (
				<li key={project.project_id}>{project.project_name}</li>
			))}
		</ul>
	);
}
```

---

## File Structure After Integration

```
frontend/
├── orval.config.ts           # Orval configuration
├── src/
│   ├── api/
│   │   ├── axios-instance.ts # Custom Axios instance
│   │   ├── generated/        # Auto-generated hooks (DO NOT EDIT)
│   │   └── model/            # Auto-generated types (DO NOT EDIT)
│   └── ...
```

---

## Regenerating on API Changes

Whenever the backend API changes, simply run:

```bash
pnpm generate-api
```

Consider adding this to your CI/CD pipeline or as a pre-build step.

---

## Troubleshooting

| Issue               | Solution                                              |
| ------------------- | ----------------------------------------------------- |
| CORS errors         | Ensure FastAPI has CORS middleware configured         |
| OpenAPI fetch fails | Verify the `input.target` URL is accessible           |
| Types missing       | Check that FastAPI routes have proper Pydantic models |

---

## References

- [Orval Documentation](https://orval.dev/docs)
- [Orval React Query Guide](https://orval.dev/docs/guides/react-query)
- [TanStack Query Docs](https://tanstack.com/query/latest)
