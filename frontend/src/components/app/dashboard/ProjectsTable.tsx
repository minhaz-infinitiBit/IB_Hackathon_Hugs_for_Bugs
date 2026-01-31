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
import React from "react";

// --- Types ---
export type Project = {
	project_id: string;
	project_name: string;
	created_at?: string;
};

// --- Sub-components ---

function Header({ table }: { table: any }) {
	return (
		<TableHeader>
			{table.getHeaderGroups().map((headerGroup: any) => (
				<TableRow
					key={headerGroup.id}
					className="border-gray-800 hover:bg-transparent">
					{headerGroup.headers.map((header: any) => {
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

function Body({ table, columns }: { table: any; columns: any }) {
	return (
		<TableBody>
			{table.getRowModel().rows?.length ? (
				table.getRowModel().rows.map((row: any) => (
					<TableRow
						key={row.id}
						data-state={row.getIsSelected() && "selected"}
						className="border-gray-800 hover:bg-gray-900/50 transition-colors">
						{row.getVisibleCells().map((cell: any) => (
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
						No projects found.
					</TableCell>
				</TableRow>
			)}
		</TableBody>
	);
}

// --- Root Component ---

interface ProjectsTableProps {
	data: Project[];
}

export const columns: ColumnDef<Project>[] = [
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
		accessorKey: "project_id",
		header: "Project ID",
		cell: ({ row }) => (
			<span className="font-mono text-xs text-cyan-400">
				{row.getValue("project_id")}
			</span>
		),
	},
	{
		accessorKey: "created_at",
		header: "Created At",
		cell: "2024-10-24", // Placeholder for now as per simplicity
	},
];

export function ProjectsTable({ data }: ProjectsTableProps) {
	const table = useReactTable({
		data,
		columns,
		getCoreRowModel: getCoreRowModel(),
	});

	return (
		<div className="rounded-md border border-gray-800 bg-gray-950/50 backdrop-blur-sm">
			<Table>
				<Header table={table} />
				<Body
					table={table}
					columns={columns}
				/>
			</Table>
		</div>
	);
}

// Attach sub-components if needed externally, but here we composed them internally for the 'ProjectsTable' export.
// If we wanted true 'Compound Component' usage from outside, we would export Root, Header, Body separately
// and let the parent compose them. The plan described "Root compound component", but usually tables are easier
// to use as a single component that takes data.
// However, to stick to the "Compound Component structure" request strictly:

ProjectsTable.Root = function ProjectsTableRoot({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<div className="rounded-md border border-gray-800 bg-gray-950/50 backdrop-blur-sm">
			<Table>{children}</Table>
		</div>
	);
};
