import { defineConfig } from "orval";

export default defineConfig({
	api: {
		input: {
			target: "http://backend:8000/openapi.json",
		},
		output: {
			mode: "tags-split",
			target: "src/api/generated",
			schemas: "src/api/model",
			client: "react-query",
			override: {
				mutator: {
					path: "./src/api/axios-instance.ts",
					name: "customInstance",
				},
			},
		},
	},
});
