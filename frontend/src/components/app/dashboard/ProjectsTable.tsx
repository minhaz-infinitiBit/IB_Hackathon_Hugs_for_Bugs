/**
 * ProjectsTable Component
 *
 * Displays a table of projects using TanStack Table.
 * Accepts data from parent component (fetched via React Query).
 */

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

// Import the generated type from Orval
import type { ProjectResponse } from "@/api/model";

// --- Column Definitions ---
// Defines how each column should render data from the ProjectResponse type

export const columns: ColumnDef<ProjectResponse>[] = [
	{
		accessorKey: "project_name",
		header: "Project Name",
		cell: ({ row }) => (
			<span className="font-bold text-white">
				{row.getValue("project_name")}
			</span>
		),
	},
	{
		accessorKey: "id",
		header: "Project ID",
		cell: ({ row }) => (
			<span className="font-mono text-xs text-cyan-400">
				{row.getValue("id")}
			</span>
		),
	},
	{
		accessorKey: "status",
		header: "Status",
		cell: ({ row }) => {
			const status = row.getValue("status") as string;
			// Status badge with color coding
			return (
				<span
					className={`px-2 py-1 rounded-full text-xs font-mono ${
						status === "active"
							? "bg-green-900/50 text-green-400"
							: "bg-gray-800 text-gray-400"
					}`}>
					{status}
				</span>
			);
		},
	},
];

// --- Sub-components for internal composition ---

function Header({
	table,
}: {
	table: ReturnType<typeof useReactTable<ProjectResponse>>;
}) {
	return (
		<TableHeader>
			{table.getHeaderGroups().map((headerGroup) => (
				<TableRow
					key={headerGroup.id}
					className="border-gray-800 hover:bg-transparent">
					{headerGroup.headers.map((header) => {
						return (
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
						);
					})}
				</TableRow>
			))}
		</TableHeader>
	);
}

function Body({
	table,
}: {
	table: ReturnType<typeof useReactTable<ProjectResponse>>;
}) {
	return (
		<TableBody>
			{table.getRowModel().rows?.length ? (
				table.getRowModel().rows.map((row) => (
					<TableRow
						key={row.id}
						data-state={row.getIsSelected() && "selected"}
						className="border-gray-800 hover:bg-gray-900/50 transition-colors">
						{row.getVisibleCells().map((cell) => (
							<TableCell
								key={cell.id}
								className="text-gray-300 font-cabinet">
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
						No projects found. Create your first project above.
					</TableCell>
				</TableRow>
			)}
		</TableBody>
	);
}

// --- Main Component ---

interface ProjectsTableProps {
	/** Array of projects from useListProjectsFilesProjectsGet hook */
	data: ProjectResponse[];
}

export function ProjectsTable({ data }: ProjectsTableProps) {
	// Initialize TanStack Table with project data and column definitions
	const table = useReactTable({
		data,
		columns,
		getCoreRowModel: getCoreRowModel(),
	});

	return (
		<div className="rounded-md border border-gray-800 bg-gray-950/50 backdrop-blur-sm">
			<Table>
				<Header table={table} />
				<Body table={table} />
			</Table>
		</div>
	);
}
