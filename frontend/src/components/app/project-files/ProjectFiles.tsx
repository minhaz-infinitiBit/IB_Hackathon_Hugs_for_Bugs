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

// End of file
