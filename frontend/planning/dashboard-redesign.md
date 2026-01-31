# Implementation Plan: Dashboard Redesign

## Goal

Redesign the `/app` route (Dashboard) to display a list of past projects using **TanStack Table** and add a "Create New Project" button that opens a dialog, then navigates to a dynamic route `/app/$projectName/document-upload`.

---

## User Review Required

> [!IMPORTANT]
> This plan introduces a **dynamic route segment** (`$projectName`). Ensure the backend API can handle project names with special characters or consider slugifying them.

---

## Proposed Changes

### 1. Install Dependencies

```bash
pnpm add @tanstack/react-table
```

---

### 2. Project List Component (`src/components/app/dashboard/`)

#### [NEW] `src/components/app/dashboard/index.ts`

Barrel export.

#### [NEW] `src/components/app/dashboard/ProjectsTable.tsx`

Root compound component for the projects table.

**Sub-components:**

- `ProjectsTable.Root` – Wrapper with TanStack Table instance.
- `ProjectsTable.Header` – Column headers.
- `ProjectsTable.Body` – Rows mapping project data.
- `ProjectsTable.Row` – Single project row.
- `ProjectsTable.EmptyState` – Shown when no projects exist.

**Columns:**
| Column | Description |
|--------|-------------|
| `project_name` | Name of the project |
| `project_id` | Unique identifier |
| `created_at` | Timestamp (optional, for future) |
| Actions | View / Delete buttons (optional, for future) |

---

### 3. Create Project Dialog (`src/components/app/dashboard/`)

#### [NEW] `src/components/app/dashboard/CreateProjectDialog.tsx`

A shadcn `Dialog` component.

**Structure:**

- `CreateProjectDialog.Trigger` – Button that opens the dialog.
- `CreateProjectDialog.Content` – Form with project name input.
- Uses `useNavigate()` from TanStack Router to redirect to `/app/$projectName/document-upload` on submit.

---

### 4. Dynamic Route

#### [NEW] `src/routes/app/$projectName/document-upload.tsx`

Creates the route `/app/:projectName/document-upload`.

```tsx
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/app/$projectName/document-upload")({
	component: ProjectDocumentUpload,
});

function ProjectDocumentUpload() {
	const { projectName } = Route.useParams();
	// ... render DocumentUpload with projectName context
}
```

---

### 5. Update Dashboard Route

#### [MODIFY] `src/routes/app/index.tsx`

- Remove placeholder card.
- Import `ProjectsTable` and `CreateProjectDialog`.
- Render:
    ```tsx
    <div className="p-6">
    	<div className="flex justify-between items-center mb-6">
    		<h1>Your Projects</h1>
    		<CreateProjectDialog.Trigger />
    	</div>
    	<ProjectsTable projects={placeholderProjects} />
    </div>
    ```

---

### 6. Placeholder Data

```ts
const placeholderProjects = [
	{ project_id: "proj_001", project_name: "Annual Report 2025" },
	{ project_id: "proj_002", project_name: "Q4 Financial Summary" },
	{ project_id: "proj_003", project_name: "Legal Contract Review" },
];
```

---

## File Structure Summary

```
src/
├── components/
│   └── app/
│       └── dashboard/
│           ├── index.ts                  # Barrel export
│           ├── ProjectsTable.tsx         # Compound component
│           └── CreateProjectDialog.tsx   # Dialog component
├── routes/
│   └── app/
│       ├── index.tsx                     # Dashboard (modified)
│       └── $projectName/
│           └── document-upload.tsx       # Dynamic route
```

---

## Verification Plan

### Manual Verification

1. Navigate to `/app` → Project list should display placeholder data.
2. Click "Create New Project" → Dialog should open.
3. Enter project name, submit → Should navigate to `/app/{projectName}/document-upload`.
4. Verify `projectName` is accessible via `Route.useParams()`.
