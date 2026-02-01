import type { PDFUploadResponse } from "@/api/model";
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
import { FileText, Sparkles } from "lucide-react";

// Helper to create columns with newFileIds context
function createColumns(newFileIds: string[]): ColumnDef<PDFUploadResponse>[] {
	return [
		{
			accessorKey: "filename",
			header: "Filename",
			cell: ({ row }) => {
				const location = row.original.location;
				const isNew = newFileIds.includes(location);
				return (
					<div className="flex items-center gap-2">
						<FileText className="w-4 h-4 text-cyan-400" />
						<span className="font-medium text-white">
							{row.getValue("filename")}
						</span>
						{isNew && (
							<span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-gradient-to-r from-purple-600 to-pink-600 text-white">
								<Sparkles className="w-3 h-3" />
								NEW
							</span>
						)}
					</div>
				);
			},
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
}

interface FilesTableProps {
	data: PDFUploadResponse[];
	newFileIds?: string[];
}

export function FilesTable({ data, newFileIds = [] }: FilesTableProps) {
	const columns = createColumns(newFileIds);

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
