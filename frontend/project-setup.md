---
name: initializing-frontend
description: Sets up a production-ready React SPA with TypeScript, Vite, Tailwind CSS, shadcn/ui, and the full TanStack ecosystem (Router, Query, Table, Form) to work with a FastAPI backend.
---

# Initializing Frontend Project

## Overview

This skill automates the setup of a robust frontend architecture using React 19, TypeScript, Vite, and the TanStack ecosystem. It ensures a standardized project structure and pre-configured tools for routing, state management, forms, and UI components.

> [!NOTE]
> This frontend is designed to work with a **Python FastAPI backend**. All API logic resides in the backend; this frontend is a SPA (Single Page Application) that consumes the FastAPI endpoints.

## Tech Stack (Mandatory)

| Category            | Technology               | Notes                          |
| ------------------- | ------------------------ | ------------------------------ |
| **UI**              | React 19 + TypeScript    | Strict type safety required    |
| **Styling**         | Tailwind CSS + shadcn/ui | Tokenized colors only          |
| **Routing**         | TanStack Router          | Client-side file-based routing |
| **Server State**    | TanStack Query           | For **all** FastAPI calls      |
| **Forms**           | TanStack Form + Zod      | Never use react-hook-form      |
| **Tables**          | TanStack Table           | With DataTable wrapper         |
| **Client State**    | Zustand                  | Only when truly necessary      |
| **Charts**          | Recharts                 | For visualizations             |
| **Build**           | Vite                     | Fast dev/build                 |
| **Package Manager** | pnpm                     | **REQUIRED** (never npm/yarn)  |
| **Backend**         | FastAPI (Python)         | Separate backend service       |

## Workflow

Follow these steps sequentially to set up the project.

### 1. Project Initialization

1.  **Initialize Vite Project**

    ```bash
    npm create vite@latest . -- --template react-ts
    ```

2.  **Configure Package Manager**
    Ensure `pnpm` is available. If not, install node (which typically includes npm) and then enable pnpm `corepack enable` or install via npm `npm install -g pnpm`.
    Delete `package-lock.json` if created and setup `pnpm-lock.yaml` by running install later.

3.  **Install Core Dependencies**
    ```bash
    pnpm add @tanstack/react-router @tanstack/react-query @tanstack/react-table @tanstack/react-form zod lucide-react recharts @supabase/supabase-js clsx tailwind-merge date-fns sonner react-day-picker
    ```
4.  **Install Styles & UI Utils**
    ```bash
    pnpm add tailwindcss @tailwindcss/vite
    ```

### 2. UI Configuration

1.  **Initialize shadcn/ui**
    Run the initialization command. Use "New York" style, "Zinc" base color, and CSS variables.

    ```bash
    pnpm dlx shadcn@latest init
    ```

2.  **Configure Tailwind**
    Ensure `vite.config.ts` includes the tailwindcss plugin.

    ```typescript
    import { defineConfig } from "vite";
    import react from "@vitejs/plugin-react";
    import tailwindcss from "@tailwindcss/vite";

    // https://vite.dev/config/
    export default defineConfig({
    	plugins: [react(), tailwindcss()],
    });
    ```

3.  **Install Essential Components**
    ```bash
    pnpm dlx shadcn@latest add button input card dialog table form select dropdown-menu toast separator sheet skeleton switch tabs avatar
    ```

### 3. Directory Structure Setup

Create the following folder structure in `src/`:

```
src/
├── assets/
├── components/
│   ├── ui/           # shadcn components
│   ├── common/       # app-wide reusable components
│   └── features/     # domain-specific feature components
├── hooks/            # custom hooks
├── lib/              # utilities, clients (supabase, axios)
├── routes/           # TanStack Router file-based routes
├── services/         # API calls and service definitions
├── store/            # Global state (Zustand - only if needed)
├── types/            # TypeScript type definitions
├── utils/            # Helper functions
└── main.tsx          # Entry point
```

### 4. Configuration Details

1.  **TanStack Router**:
    - Set up `src/routes/__root.tsx` as the root layout.
    - Configure `createRouter` in `src/main.tsx` and register the `RouterProvider`.
    - Ensure strict type safety for routes.

2.  **TanStack Query**:
    - Initialize `QueryClient` in `src/lib/query-client.ts` or `src/main.tsx`.
    - Wrap the app in `QueryClientProvider`.

3.  **Shadcn/UI**:
    - Verify `components.json` points to the correct paths (`@/components/ui` and `@/lib/utils`).
    - Verify `tsconfig.json` has path aliases configured for `@/*`.

## Verification

After setup, run:

```bash
pnpm dev
```

- Verify the app loads without errors.
- Check that the router is working.
- Verify that a shadcn component (e.g., Button) renders correctly with styles.
