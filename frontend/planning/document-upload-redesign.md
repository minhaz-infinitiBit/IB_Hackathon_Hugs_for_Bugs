# Document Upload Page Implementation Plan

## Overview

This plan outlines the implementation of the Document Upload page (`/app/$projectId/document-upload`) with:

- A table displaying uploaded files
- An upload modal with drag-and-drop support
- A placeholder "Process Documents" button

---

## Folder Structure

```
src/components/app/project-files/
├── index.ts                    # Barrel export
├── ProjectFiles.tsx            # Main compound component container
├── FilesTable.tsx              # Table displaying uploaded files
├── UploadFilesDialog.tsx       # Modal for uploading files
└── ProcessButton.tsx           # Placeholder process button
```

---

## Component Architecture (Compound Pattern)

```tsx
// Usage in route:
<ProjectFiles projectId={projectId}>
	<ProjectFiles.Header />
	<ProjectFiles.Table />
	<ProjectFiles.Actions>
		<ProjectFiles.UploadDialog />
		<ProjectFiles.ProcessButton />
	</ProjectFiles.Actions>
</ProjectFiles>
```

---

## File-by-File Implementation

### 1. `src/components/app/project-files/index.ts`

```typescript
// Barrel export for project-files components
export { ProjectFiles } from "./ProjectFiles";
export { FilesTable } from "./FilesTable";
export { UploadFilesDialog } from "./UploadFilesDialog";
export { ProcessButton } from "./ProcessButton";
```

---

### 2. `src/components/app/project-files/ProjectFiles.tsx`

**Purpose**: Main container with context for projectId

```tsx
import { createContext, useContext, type ReactNode } from "react";

// Context to share projectId across sub-components
interface ProjectFilesContextValue {
	projectId: number;
}

const ProjectFilesContext = createContext<ProjectFilesContextValue | null>(
	null,
);

export function useProjectFilesContext() {
	const context = useContext(ProjectFilesContext);
	if (!context) {
		throw new Error(
			"useProjectFilesContext must be used within ProjectFiles",
		);
	}
	return context;
}

// -----------------------------------------------------------
// Main Component
// -----------------------------------------------------------

interface ProjectFilesProps {
	projectId: number;
	children: ReactNode;
}

export function ProjectFiles({ projectId, children }: ProjectFilesProps) {
	return (
		<ProjectFilesContext.Provider value={{ projectId }}>
			<div className="container mx-auto p-6 md:p-12">{children}</div>
		</ProjectFilesContext.Provider>
	);
}

// -----------------------------------------------------------
// Sub-components
// -----------------------------------------------------------

ProjectFiles.Header = function Header() {
	const { projectId } = useProjectFilesContext();
	return (
		<div className="mb-8">
			<h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 font-clash mb-2">
				📄 Project Documents
			</h1>
			<p className="text-gray-400 font-mono text-sm">
				Project ID: <span className="text-cyan-400">{projectId}</span>
			</p>
		</div>
	);
};

ProjectFiles.Table = function Table() {
	// Import and render FilesTable here
	// This is just the slot for the table
	return null; // Replaced by actual usage
};

ProjectFiles.Actions = function Actions({ children }: { children: ReactNode }) {
	return <div className="flex justify-end gap-4 mt-6">{children}</div>;
};

// Re-export sub-components for compound pattern
export { UploadFilesDialog } from "./UploadFilesDialog";
export { ProcessButton } from "./ProcessButton";
```

---

### 3. `src/components/app/project-files/FilesTable.tsx`

**Purpose**: Display uploaded files using TanStack Table

**shadcn/ui components used**: `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableCell`, `TableHead`

```tsx
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import {
	flexRender,
	getCoreRowModel,
	useReactTable,
	type ColumnDef,
} from "@tanstack/react-table";
import type { PDFUploadResponse } from "@/api/model";
import { FileText } from "lucide-react";

// Column definitions
const columns: ColumnDef<PDFUploadResponse>[] = [
	{
		accessorKey: "filename",
		header: "Filename",
		cell: ({ row }) => (
			<div className="flex items-center gap-2">
				<FileText className="w-4 h-4 text-cyan-400" />
				<span className="font-medium text-white">
					{row.getValue("filename")}
				</span>
			</div>
		),
	},
	{
		accessorKey: "content_type",
		header: "Type",
		cell: ({ row }) => (
			<span className="font-mono text-xs text-gray-400">
				{row.getValue("content_type")}
			</span>
		),
	},
	{
		accessorKey: "message",
		header: "Status",
		cell: ({ row }) => (
			<span className="px-2 py-1 rounded-full text-xs font-mono bg-green-900/50 text-green-400">
				{row.getValue("message")}
			</span>
		),
	},
];

interface FilesTableProps {
	data: PDFUploadResponse[];
}

export function FilesTable({ data }: FilesTableProps) {
	const table = useReactTable({
		data,
		columns,
		getCoreRowModel: getCoreRowModel(),
	});

	return (
		<div className="rounded-md border border-gray-800 bg-gray-950/50 backdrop-blur-sm">
			<Table>
				<TableHeader>
					{table.getHeaderGroups().map((headerGroup) => (
						<TableRow
							key={headerGroup.id}
							className="border-gray-800 hover:bg-transparent">
							{headerGroup.headers.map((header) => (
								<TableHead
									key={header.id}
									className="text-gray-400 font-mono">
									{header.isPlaceholder
										? null
										: flexRender(
												header.column.columnDef.header,
												header.getContext(),
											)}
								</TableHead>
							))}
						</TableRow>
					))}
				</TableHeader>
				<TableBody>
					{table.getRowModel().rows?.length ? (
						table.getRowModel().rows.map((row) => (
							<TableRow
								key={row.id}
								className="border-gray-800 hover:bg-gray-900/50 transition-colors">
								{row.getVisibleCells().map((cell) => (
									<TableCell
										key={cell.id}
										className="text-gray-300">
										{flexRender(
											cell.column.columnDef.cell,
											cell.getContext(),
										)}
									</TableCell>
								))}
							</TableRow>
						))
					) : (
						<TableRow>
							<TableCell
								colSpan={columns.length}
								className="h-24 text-center text-gray-500 font-mono">
								No files uploaded yet.
							</TableCell>
						</TableRow>
					)}
				</TableBody>
			</Table>
		</div>
	);
}
```

---

### 4. `src/components/app/project-files/UploadFilesDialog.tsx`

**Purpose**: Modal with drag-and-drop file upload

**shadcn/ui components used**: `Dialog`, `DialogTrigger`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogFooter`, `Button`

**APIs used**: `useUploadPdfFilesUploadPdfProjectIdPost`, `getListProjectFilesFilesProjectsProjectIdFilesGetQueryKey`

```tsx
import { useState, useRef, type DragEvent, type ChangeEvent } from "react";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from "@/components/ui/dialog";
import { Upload, Loader2, X, FileText } from "lucide-react";
import { useUploadPdfFilesUploadPdfProjectIdPost } from "@/api/generated/files/files";
import { getListProjectFilesFilesProjectsProjectIdFilesGetQueryKey } from "@/api/generated/files/files";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useProjectFilesContext } from "./ProjectFiles";

export function UploadFilesDialog() {
	const { projectId } = useProjectFilesContext();
	const [open, setOpen] = useState(false);
	const [files, setFiles] = useState<File[]>([]);
	const [isDragging, setIsDragging] = useState(false);
	const fileInputRef = useRef<HTMLInputElement>(null);
	const queryClient = useQueryClient();

	const uploadMutation = useUploadPdfFilesUploadPdfProjectIdPost();

	// Handle drag events
	const handleDragOver = (e: DragEvent) => {
		e.preventDefault();
		setIsDragging(true);
	};

	const handleDragLeave = (e: DragEvent) => {
		e.preventDefault();
		setIsDragging(false);
	};

	const handleDrop = (e: DragEvent) => {
		e.preventDefault();
		setIsDragging(false);
		const droppedFiles = Array.from(e.dataTransfer.files).filter(
			(file) => file.type === "application/pdf",
		);
		setFiles((prev) => [...prev, ...droppedFiles]);
	};

	// Handle file input change
	const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
		if (e.target.files) {
			const selectedFiles = Array.from(e.target.files);
			setFiles((prev) => [...prev, ...selectedFiles]);
		}
	};

	// Remove a file from the list
	const removeFile = (index: number) => {
		setFiles((prev) => prev.filter((_, i) => i !== index));
	};

	// Handle upload
	const handleUpload = () => {
		if (files.length === 0) return;

		uploadMutation.mutate(
			{
				projectId,
				data: { files },
			},
			{
				onSuccess: () => {
					// Invalidate query to refresh file list
					queryClient.invalidateQueries({
						queryKey:
							getListProjectFilesFilesProjectsProjectIdFilesGetQueryKey(
								projectId,
							),
					});
					toast.success(
						`${files.length} file(s) uploaded successfully!`,
					);
					setFiles([]);
					setOpen(false);
				},
				onError: () => {
					toast.error("Failed to upload files. Please try again.");
				},
			},
		);
	};

	const isLoading = uploadMutation.isPending;

	return (
		<Dialog
			open={open}
			onOpenChange={setOpen}>
			<DialogTrigger asChild>
				<Button className="font-bold bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 text-gray-950">
					<Upload className="w-4 h-4 mr-2" />
					Upload Files
				</Button>
			</DialogTrigger>
			<DialogContent className="sm:max-w-[500px] bg-gray-900 border-gray-800 text-white">
				<DialogHeader>
					<DialogTitle className="text-xl font-clash text-cyan-400">
						Upload Documents
					</DialogTitle>
					<DialogDescription className="text-gray-400">
						Drag and drop PDF files or click to select.
					</DialogDescription>
				</DialogHeader>

				{/* Drop Zone */}
				<div
					onDragOver={handleDragOver}
					onDragLeave={handleDragLeave}
					onDrop={handleDrop}
					onClick={() => fileInputRef.current?.click()}
					className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragging ? "border-cyan-400 bg-cyan-400/10" : "border-gray-700 hover:border-gray-600"}
          `}>
					<Upload className="w-10 h-10 mx-auto mb-4 text-gray-500" />
					<p className="text-gray-400 font-mono text-sm">
						Drop PDF files here or click to browse
					</p>
					<input
						ref={fileInputRef}
						type="file"
						multiple
						accept=".pdf"
						onChange={handleFileChange}
						className="hidden"
					/>
				</div>

				{/* File List */}
				{files.length > 0 && (
					<div className="max-h-40 overflow-y-auto space-y-2">
						{files.map((file, index) => (
							<div
								key={index}
								className="flex items-center justify-between p-2 bg-gray-800 rounded">
								<div className="flex items-center gap-2">
									<FileText className="w-4 h-4 text-cyan-400" />
									<span className="text-sm text-gray-300 truncate max-w-[300px]">
										{file.name}
									</span>
								</div>
								<Button
									variant="ghost"
									size="sm"
									onClick={() => removeFile(index)}
									className="text-gray-500 hover:text-red-400">
									<X className="w-4 h-4" />
								</Button>
							</div>
						))}
					</div>
				)}

				<DialogFooter>
					<Button
						onClick={handleUpload}
						disabled={files.length === 0 || isLoading}
						className="bg-cyan-500 hover:bg-cyan-400 text-gray-950 font-bold">
						{isLoading ? (
							<>
								<Loader2 className="w-4 h-4 mr-2 animate-spin" />
								Uploading...
							</>
						) : (
							`Upload ${files.length} File(s)`
						)}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
```

---

### 5. `src/components/app/project-files/ProcessButton.tsx`

**Purpose**: Placeholder button for future processing functionality

```tsx
import { Button } from "@/components/ui/button";
import { Sparkles } from "lucide-react";

export function ProcessButton() {
	return (
		<Button
			disabled
			className="bg-purple-600 hover:bg-purple-500 text-white font-bold opacity-50 cursor-not-allowed">
			<Sparkles className="w-4 h-4 mr-2" />
			Process Documents
		</Button>
	);
}
```

---

### 6. Route Update: `src/routes/app/$projectId/document-upload.tsx`

```tsx
import { createFileRoute } from "@tanstack/react-router";
import { useListProjectFilesFilesProjectsProjectIdFilesGet } from "@/api/generated/files/files";
import {
	ProjectFiles,
	FilesTable,
	UploadFilesDialog,
	ProcessButton,
} from "@/components/app/project-files";

export const Route = createFileRoute("/app/$projectId/document-upload")({
	component: ProjectDocumentUploadPage,
});

function ProjectDocumentUploadPage() {
	const { projectId } = Route.useParams();
	const numericProjectId = Number(projectId);

	// Fetch files for this project
	const { data, isLoading, error } =
		useListProjectFilesFilesProjectsProjectIdFilesGet(numericProjectId);

	// Extract files from response
	const files = data?.status === 200 ? data.data : [];

	return (
		<ProjectFiles projectId={numericProjectId}>
			{/* Header with title and upload button */}
			<div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
				<ProjectFiles.Header />
				<UploadFilesDialog />
			</div>

			{/* Loading state */}
			{isLoading && (
				<div className="text-center py-12 text-gray-400 font-mono">
					Loading files...
				</div>
			)}

			{/* Error state */}
			{error && (
				<div className="text-center py-12 text-red-400 font-mono">
					Error loading files.
				</div>
			)}

			{/* Files table */}
			{!isLoading && !error && <FilesTable data={files} />}

			{/* Actions */}
			<ProjectFiles.Actions>
				<ProcessButton />
			</ProjectFiles.Actions>
		</ProjectFiles>
	);
}
```

---

## Checklist

- [ ] Create `src/components/app/project-files/` folder
- [ ] Create `ProjectFiles.tsx` (compound component with context)
- [ ] Create `FilesTable.tsx` (TanStack Table)
- [ ] Create `UploadFilesDialog.tsx` (Modal with drag-drop)
- [ ] Create `ProcessButton.tsx` (Placeholder)
- [ ] Create `index.ts` (Barrel export)
- [ ] Update route `src/routes/app/$projectId/document-upload.tsx`
- [ ] Test file fetching
- [ ] Test file upload
- [ ] Run `pnpm build` to verify no errors

---

## Dependencies

All required shadcn/ui components are already installed:

- `Dialog`
- `Button`
- `Table`

No new dependencies needed.
