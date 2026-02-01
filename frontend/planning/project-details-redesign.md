# Project Details Feature Implementation Plan

## Overview

This plan covers the implementation of the Project Details feature with:

1. **Status-based routing** from dashboard project list
2. **Project Details page** with classified document tree and PDF viewer
3. **Document Upload redirect** for pending projects

---

## User Flow

```mermaid
flowchart TD
    A[Dashboard /app] --> B{Click Project Row}
    B --> C{Check Status}
    C -->|finished_processing| D[/app/$projectId/details]
    C -->|pending| E[/app/$projectId/document-upload]
    D --> F[Project Details Page]
    E --> G[Document Upload Page]
```

---

## Folder Structure

```
src/
├── routes/app/
│   └── $projectId/
│       ├── details.tsx              # Details route
│       └── document-upload.tsx      # Existing upload route
│
└── components/app/project-details/
    ├── index.ts                     # Barrel export
    ├── ProjectDetails.tsx           # Main compound component
    ├── DocumentTree.tsx             # Left panel: classified document tree
    ├── DocumentTreeItem.tsx         # Individual tree node/document
    ├── MergedDocumentViewer.tsx     # Right panel: PDF viewer
    └── types.ts                     # Type definitions
```

---

## Component Architecture

### Compound Pattern Usage

```tsx
<ProjectDetails projectId={projectId}>
	<ProjectDetails.Header />
	<ProjectDetails.Content>
		<ProjectDetails.DocumentTree />
		<ProjectDetails.MergedViewer />
	</ProjectDetails.Content>
</ProjectDetails>
```

---

## File-by-File Implementation

### 1. `src/components/app/project-details/types.ts`

**Purpose**: Shared type definitions

```typescript
// Classification with nested documents
export interface DocumentClassification {
	id: string;
	name: string; // e.g., "Invoices", "Contracts"
	count: number; // Number of documents
	documents: ClassifiedDocument[];
}

// Individual document
export interface ClassifiedDocument {
	id: string;
	filename: string;
	contentType: string; // MIME type
	url: string; // Download URL
	isViewable: boolean; // true for PDF/images
}

// API response shape (placeholder)
export interface ProjectDocumentsResponse {
	classifications: DocumentClassification[];
}

// Merged document response
export interface MergedDocumentResponse {
	url: string | null; // PDF URL or null if not ready
}
```

---

### 2. `src/components/app/project-details/index.ts`

```typescript
export { ProjectDetails } from "./ProjectDetails";
export { DocumentTree } from "./DocumentTree";
export { DocumentTreeItem } from "./DocumentTreeItem";
export { MergedDocumentViewer } from "./MergedDocumentViewer";
export type * from "./types";
```

---

### 3. `src/components/app/project-details/ProjectDetails.tsx`

**Purpose**: Main container with context

```tsx
import { createContext, useContext, type ReactNode } from "react";

interface ProjectDetailsContextValue {
	projectId: number;
}

const ProjectDetailsContext = createContext<ProjectDetailsContextValue | null>(
	null,
);

export function useProjectDetailsContext() {
	const context = useContext(ProjectDetailsContext);
	if (!context) {
		throw new Error(
			"useProjectDetailsContext must be used within ProjectDetails",
		);
	}
	return context;
}

interface ProjectDetailsProps {
	projectId: number;
	children: ReactNode;
}

export function ProjectDetails({ projectId, children }: ProjectDetailsProps) {
	return (
		<ProjectDetailsContext.Provider value={{ projectId }}>
			<div className="container mx-auto p-6 md:p-12">{children}</div>
		</ProjectDetailsContext.Provider>
	);
}

// Sub-components
ProjectDetails.Header = function Header() {
	const { projectId } = useProjectDetailsContext();
	return (
		<div className="mb-8">
			<h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 font-clash mb-2">
				📋 Project Details
			</h1>
			<p className="text-gray-400 font-mono text-sm">
				Project ID: <span className="text-cyan-400">{projectId}</span>
			</p>
		</div>
	);
};

ProjectDetails.Content = function Content({
	children,
}: {
	children: ReactNode;
}) {
	return (
		<div className="grid grid-cols-1 lg:grid-cols-2 gap-8">{children}</div>
	);
};
```

---

### 4. `src/components/app/project-details/DocumentTree.tsx`

**Purpose**: Left panel with classified document tree

**shadcn/ui**: `Accordion`, `AccordionItem`, `AccordionTrigger`, `AccordionContent`, `ScrollArea`

```tsx
import {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "@/components/ui/accordion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Folder } from "lucide-react";
import { DocumentTreeItem } from "./DocumentTreeItem";
import type { DocumentClassification } from "./types";

interface DocumentTreeProps {
	classifications: DocumentClassification[];
	isLoading?: boolean;
}

export function DocumentTree({
	classifications,
	isLoading,
}: DocumentTreeProps) {
	if (isLoading) {
		return (
			<div className="rounded-lg border border-gray-800 bg-gray-950/50 p-6">
				<p className="text-gray-400 font-mono text-center">
					Loading documents...
				</p>
			</div>
		);
	}

	if (classifications.length === 0) {
		return (
			<div className="rounded-lg border border-gray-800 bg-gray-950/50 p-6">
				<p className="text-gray-500 font-mono text-center">
					No documents found.
				</p>
			</div>
		);
	}

	return (
		<div className="rounded-lg border border-gray-800 bg-gray-950/50 backdrop-blur-sm">
			<div className="p-4 border-b border-gray-800">
				<h2 className="text-lg font-bold text-white font-clash">
					📁 Classified Documents
				</h2>
			</div>
			<ScrollArea className="h-[500px]">
				<Accordion
					type="multiple"
					className="p-4">
					{classifications.map((classification) => (
						<AccordionItem
							key={classification.id}
							value={classification.id}>
							<AccordionTrigger className="hover:no-underline">
								<div className="flex items-center gap-2">
									<Folder className="w-4 h-4 text-cyan-400" />
									<span className="text-white">
										{classification.name}
									</span>
									<span className="ml-2 px-2 py-0.5 rounded-full bg-gray-800 text-xs text-gray-400">
										{classification.count}
									</span>
								</div>
							</AccordionTrigger>
							<AccordionContent>
								<div className="space-y-2 pl-6">
									{classification.documents.map((doc) => (
										<DocumentTreeItem
											key={doc.id}
											document={doc}
										/>
									))}
								</div>
							</AccordionContent>
						</AccordionItem>
					))}
				</Accordion>
			</ScrollArea>
		</div>
	);
}
```

---

### 5. `src/components/app/project-details/DocumentTreeItem.tsx`

**Purpose**: Individual document row with view/download actions

**shadcn/ui**: `Button`

```tsx
import { Button } from "@/components/ui/button";
import { Download, Eye, FileText, Image, File } from "lucide-react";
import type { ClassifiedDocument } from "./types";

interface DocumentTreeItemProps {
	document: ClassifiedDocument;
}

function getFileIcon(contentType: string) {
	if (contentType.startsWith("image/")) return Image;
	if (contentType === "application/pdf") return FileText;
	return File;
}

export function DocumentTreeItem({ document }: DocumentTreeItemProps) {
	const FileIcon = getFileIcon(document.contentType);

	const handleView = () => {
		window.open(document.url, "_blank");
	};

	const handleDownload = () => {
		const link = document.createElement("a");
		link.href = document.url;
		link.download = document.filename;
		link.click();
	};

	return (
		<div className="flex items-center justify-between p-2 rounded-md hover:bg-gray-800/50 transition-colors">
			<div className="flex items-center gap-2">
				<FileIcon className="w-4 h-4 text-gray-400" />
				<span className="text-sm text-gray-300 truncate max-w-[200px]">
					{document.filename}
				</span>
			</div>
			<div className="flex items-center gap-1">
				{document.isViewable && (
					<Button
						variant="ghost"
						size="sm"
						onClick={handleView}
						className="text-gray-400 hover:text-cyan-400">
						<Eye className="w-4 h-4" />
					</Button>
				)}
				<Button
					variant="ghost"
					size="sm"
					onClick={handleDownload}
					className="text-gray-400 hover:text-purple-400">
					<Download className="w-4 h-4" />
				</Button>
			</div>
		</div>
	);
}
```

---

### 6. `src/components/app/project-details/MergedDocumentViewer.tsx`

**Purpose**: Right panel PDF viewer using react-pdf with pagination and zoom

```tsx
import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { Button } from "@/components/ui/button";
import {
	ChevronLeft,
	ChevronRight,
	FileText,
	Loader2,
	ZoomIn,
	ZoomOut,
} from "lucide-react";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface MergedDocumentViewerProps {
	pdfUrl: string | null;
	isLoading?: boolean;
}

export function MergedDocumentViewer({
	pdfUrl,
	isLoading,
}: MergedDocumentViewerProps) {
	const [numPages, setNumPages] = useState<number | null>(null);
	const [pageNumber, setPageNumber] = useState(1);
	const [scale, setScale] = useState(1.0);

	function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
		setNumPages(numPages);
		setPageNumber(1);
	}

	if (isLoading) {
		return (
			<div className="rounded-lg border border-gray-800 bg-gray-950/50 h-[600px] flex items-center justify-center">
				<Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
			</div>
		);
	}

	if (!pdfUrl) {
		return (
			<div className="rounded-lg border border-gray-800 bg-gray-950/50 h-[600px] flex flex-col items-center justify-center gap-4">
				<FileText className="w-16 h-16 text-gray-600" />
				<p className="text-gray-500 font-mono text-center">
					Merged document not available yet.
				</p>
			</div>
		);
	}

	return (
		<div className="rounded-lg border border-gray-800 bg-gray-950/50 overflow-hidden">
			{/* Header with controls */}
			<div className="p-4 border-b border-gray-800 flex items-center justify-between">
				<h2 className="text-lg font-bold text-white font-clash">
					📄 Merged Document
				</h2>
				<div className="flex items-center gap-2">
					<Button
						variant="ghost"
						size="sm"
						onClick={() => setScale((s) => Math.max(0.5, s - 0.1))}
						className="text-gray-400">
						<ZoomOut className="w-4 h-4" />
					</Button>
					<span className="text-sm text-gray-400 font-mono">
						{Math.round(scale * 100)}%
					</span>
					<Button
						variant="ghost"
						size="sm"
						onClick={() => setScale((s) => Math.min(2, s + 0.1))}
						className="text-gray-400">
						<ZoomIn className="w-4 h-4" />
					</Button>
				</div>
			</div>

			{/* PDF Viewer */}
			<div className="h-[500px] overflow-auto flex justify-center bg-gray-900 p-4">
				<Document
					file={pdfUrl}
					onLoadSuccess={onDocumentLoadSuccess}
					loading={
						<div className="flex items-center justify-center h-full">
							<Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
						</div>
					}>
					<Page
						pageNumber={pageNumber}
						scale={scale}
					/>
				</Document>
			</div>

			{/* Pagination */}
			{numPages && numPages > 1 && (
				<div className="p-4 border-t border-gray-800 flex items-center justify-center gap-4">
					<Button
						variant="ghost"
						size="sm"
						onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
						disabled={pageNumber <= 1}>
						<ChevronLeft className="w-4 h-4" />
					</Button>
					<span className="text-sm text-gray-400 font-mono">
						Page {pageNumber} of {numPages}
					</span>
					<Button
						variant="ghost"
						size="sm"
						onClick={() =>
							setPageNumber((p) => Math.min(numPages, p + 1))
						}
						disabled={pageNumber >= numPages}>
						<ChevronRight className="w-4 h-4" />
					</Button>
				</div>
			)}
		</div>
	);
}
```

---

### 7. Route: `src/routes/app/$projectId/details.tsx`

```tsx
import { createFileRoute } from "@tanstack/react-router";
import {
	ProjectDetails,
	DocumentTree,
	MergedDocumentViewer,
} from "@/components/app/project-details";
import type { DocumentClassification } from "@/components/app/project-details";

export const Route = createFileRoute("/app/$projectId/details")({
	component: ProjectDetailsPage,
});

function ProjectDetailsPage() {
	const { projectId } = Route.useParams();
	const numericProjectId = Number(projectId);

	// TODO: Replace with actual API hook
	// const { data: documentsData, isLoading: docsLoading } = useGetProjectDocuments(numericProjectId);
	// const { data: mergedData, isLoading: mergedLoading } = useGetMergedDocument(numericProjectId);

	// Placeholder data
	const classifications: DocumentClassification[] = [];
	const mergedPdfUrl: string | null = null;
	const isLoading = false;

	return (
		<ProjectDetails projectId={numericProjectId}>
			<ProjectDetails.Header />
			<ProjectDetails.Content>
				<DocumentTree
					classifications={classifications}
					isLoading={isLoading}
				/>
				<MergedDocumentViewer
					pdfUrl={mergedPdfUrl}
					isLoading={isLoading}
				/>
			</ProjectDetails.Content>
		</ProjectDetails>
	);
}
```

---

### 8. Dashboard Row Click Handler

**Update**: `src/components/app/dashboard/ProjectsTable.tsx`

Add navigation logic based on project status:

```tsx
import { useNavigate } from "@tanstack/react-router";

// Inside the component:
const navigate = useNavigate();

const handleRowClick = (project: ProjectResponse) => {
	if (project.status === "finished_processing") {
		navigate({
			to: "/app/$projectId/details",
			params: { projectId: String(project.id) },
		});
	} else {
		navigate({
			to: "/app/$projectId/document-upload",
			params: { projectId: String(project.id) },
		});
	}
};

// In the table row:
<TableRow
	onClick={() => handleRowClick(row.original)}
	className="cursor-pointer hover:bg-gray-900/50">
	...
</TableRow>;
```

---

## Checklist

- [ ] Create `src/components/app/project-details/` folder
- [ ] Create `types.ts` with type definitions
- [ ] Create `ProjectDetails.tsx` (compound component with context)
- [ ] Create `DocumentTree.tsx` (classification accordion)
- [ ] Create `DocumentTreeItem.tsx` (document row with actions)
- [ ] Create `MergedDocumentViewer.tsx` (PDF iframe or placeholder)
- [ ] Create `index.ts` (barrel export)
- [ ] Create `src/routes/app/$projectId/details.tsx` route
- [ ] Update `ProjectsTable.tsx` with status-based navigation
- [ ] Install shadcn/ui `Accordion` if not present
- [ ] Install shadcn/ui `ScrollArea` if not present
- [ ] Run `pnpm build` to verify

---

## API Integration Points (To Be Added Later)

| Feature              | Hook Placeholder                    | Expected Response                               |
| -------------------- | ----------------------------------- | ----------------------------------------------- |
| Classified Documents | `useGetProjectDocuments(projectId)` | `{ classifications: DocumentClassification[] }` |
| Merged PDF           | `useGetMergedDocument(projectId)`   | `{ url: string \| null }`                       |

---

## Dependencies

**New packages to install:**

```bash
# shadcn/ui components
pnpm dlx shadcn@latest add accordion scroll-area

# PDF viewer
pnpm add react-pdf
```

---

## Notes

- **react-pdf** is used for PDF rendering with built-in pagination and zoom controls
- The PDF.js worker is loaded from unpkg CDN for simplicity
- Document view action opens in new tab. Download creates a programmatic anchor click.
- All APIs are stubbed with placeholders and TODO comments for easy replacement.
